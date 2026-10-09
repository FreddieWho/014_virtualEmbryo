#!/usr/bin/env python
"""Config-driven builder for test-phase (and validation-shaped dry-run) submissions.

python vework/test_pipeline.py --config vework/configs/<cfg>.json [--index /path/to/new/index.json] [--only KEY] [--outdir DIR]

Each config entry: board key -> {"slot": "S1"|"S2", "recipe": ..., recipe args..., "panel": optional ordered gene file,
"limits": optional [min,max] for provisional boards}. Board panels come from the official index.json when the board
is listed there (pass --index on 10-20); otherwise a PROVISIONAL panel = ordered intersection of all loaded stages
(order of the latest stage) is registered and flagged in the manifest - such a file must be rebuilt once the official
panel is published. One heavy job at a time: entries run sequentially in a single process (T1 entries in a subprocess).
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from types import SimpleNamespace as NS
import anndata as ad
sys.path.insert(0, str(Path(__file__).parent))
import vecommon as V
import t2_recipes as R
import t3_build as T3

VE = Path("/workspace/ve")


def stage_genes(stage):
    return [str(g) for g in ad.read_h5ad(V.DATA / f"{stage.rsplit(':', 1)[0]}.h5ad", backed="r").var_names]


def ensure_board(key, cfg, stages):
    if key in V.INDEX and not V.INDEX[key].get("provisional"):
        return "official"
    if cfg.get("panel"):
        genes = [l.strip() for l in Path(cfg["panel"]).read_text().splitlines() if l.strip()]; src = cfg["panel"]
    else:
        sets = [stage_genes(s) for s in stages]
        common = set.intersection(*map(set, sets)); genes = [g for g in sets[-1] if g in common]; src = "intersection"
    lo, hi = cfg.get("limits", [1000, 25000])
    V.register_board(key, genes, lo, hi, obsm_required=[] if key.startswith("T1") else ["spatial_3D"])
    return f"PROVISIONAL({src}, {len(genes)} genes)"


def run_entry(name, cfg, outdir, a_index=None):
    key, rec = cfg["board"], cfg["recipe"]; out = outdir / f"{name}.h5ad"
    if rec in ("interp", "interp_baseline"):
        stages = [s for s in (cfg.get("prev"), cfg["left"], cfg["right"]) if s]
        status = ensure_board(key, cfg, stages)
        a = NS(board=key, left=cfg["left"], right=cfg["right"], target=cfg["target"], n=cfg["n"], seed=cfg.get("seed", 20261020),
               label="celltype", C=cfg.get("C", 2.0), geometry=cfg.get("geometry", "logrms"),
               zero_preserve=cfg.get("zero_preserve", False), carrier="baseline" if rec == "interp_baseline" else "left",
               prev=cfg.get("prev"), base_n=cfg.get("base_n", cfg["n"]), base_seed=cfg.get("base_seed", 20260821),
               bridge_seed=cfg.get("bridge_seed", 20260904))
        A, prov = R.run_interp(a)
    elif rec == "extrap":
        status = ensure_board(key, cfg, [cfg["prev"], cfg["last"]])
        a = NS(board=key, prev=cfg["prev"], last=cfg["last"], target=cfg["target"], n=cfg["n"], seed=cfg.get("seed", 20261020),
               label="celltype", damp=cfg.get("damp", 0.9), stat=cfg.get("stat", "median"), lib_preserve=cfg.get("lib_preserve", True),
               timescale=cfg.get("timescale", "none"), min_cells=30, rows=cfg.get("rows", "repo"), row_seed=cfg.get("row_seed", 20260821))
        A, prov = R.run_extrap(a)
    elif rec == "t3":
        status = ensure_board(key, cfg, [cfg["wt"] + ":0"])
        prog = T3.WNT_PROGRAM if cfg.get("program") == "WNT" else cfg.get("program", [])
        A, prov = T3.build(wt=cfg["wt"], n=cfg["n"], seed=cfg.get("seed", 20261020), carrier=cfg.get("carrier", "uniform"),
                           lineage=cfg.get("lineage", "mesp1"), zero=cfg.get("zero", []), half=cfg.get("half", []),
                           program=prog, strength=cfg.get("strength", 0.0), board=key)
    elif rec in ("t1_shift", "t1_copy_last", "t1_mix"):
        status = ensure_board(key, cfg, cfg["train"])
        py = str(VE / "venv/bin/python")
        if rec == "t1_mix":
            parts = [outdir / f"{p}.h5ad" for p in cfg["parts"]]
            cmd = [py, str(VE / "vework/t1_mix.py"), "--a", str(parts[0]), "--b", str(parts[1]), "--frac-a", str(cfg.get("frac_a", 0.7)),
                   "--n", str(cfg["n"]), "--board", key, "--out", str(out)]
        else:
            cmd = [py, str(VE / "vework/t1_recipe.py"), "--method", "copy_last" if rec == "t1_copy_last" else "shift",
                   "--prev", cfg["train"][-2] if len(cfg["train"]) > 1 else cfg["train"][-1], "--last", cfg["train"][-1],
                   "--target", str(cfg["target"]), "--n", str(cfg["n"]), "--w", str(cfg.get("w", 0.5)), "--damp", str(cfg.get("damp", 0.5)),
                   "--timescale", cfg.get("timescale", "linear"), "--board", key, "--out", str(out)] + (["--zero-preserve"] if cfg.get("zero_preserve") else [])
        env = dict(**__import__("os").environ)
        if status.startswith("PROVISIONAL"):
            xf = outdir / f"{name}.extra_index.json"
            xf.write_text(json.dumps({key: {**V.INDEX[key], "genes": V.panel(key)}})); env["VE_EXTRA_INDEX_FILE"] = str(xf)
        elif a_index:
            env["VE_INDEX_FILE"] = a_index
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if r.returncode != 0: raise RuntimeError(r.stderr[-2000:])
        fc = V.format_check(out, key)
        return {"entry": name, "board": key, "slot": cfg.get("slot"), "file": str(out), "panel": status, "format_check": fc,
                "recipe": rec, "cfg": cfg}
    else:
        raise ValueError(rec)
    A.uns["ve_provenance"] = json.dumps({**prov, "pipeline_entry": name, "external_sources": cfg.get("external_sources", "none")}, default=str)
    A.write_h5ad(out)
    fc = V.format_check(out, key)
    return {"entry": name, "board": key, "slot": cfg.get("slot"), "file": str(out), "panel": status, "format_check": fc,
            "recipe": rec, "cfg": cfg}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--config", required=True); ap.add_argument("--index", default=None)
    ap.add_argument("--only", default=None); ap.add_argument("--outdir", default=None)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    if a.index: V.load_index(a.index)
    outdir = Path(a.outdir or cfg.get("outdir", VE / "work/pipeline_out")); outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for name, ent in cfg["entries"].items():
        if a.only and a.only not in name: continue
        print(f"== {name}", flush=True)
        r = run_entry(name, ent, outdir, a.index); results.append(r)
        print(f"   {r['board']} {r['slot']} panel={r['panel']} format={'PASS' if r['format_check']['pass'] else r['format_check']['errors']} n={r['format_check']['n_obs']}", flush=True)
    (outdir / "PIPELINE_MANIFEST.json").write_text(json.dumps(results, indent=1, default=str))


if __name__ == "__main__":
    main()
