"""Build the T3 board candidate for the lam15+unmasked response route.

Replays the frozen v0087 deploy_diagnostics fit EXACTLY, changing only which
CrossKOHurdle subclass supplies summarize_response. The frozen SELECTION criteria
decide method and mode; the seed (20260904), the 7449-row WT carrier, the E8.75
stage, the all_supported variant, the geometry and every contract assert are
carried over unchanged from the archived recipe.

Local source-side composite gain is +0.1985 (autoresearch/loop-261009-1845).
That is development evidence, NOT a server forecast. No submission is implied.
"""
import os

for k in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[k] = "4"
import hashlib
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

sys.path.insert(0, "/home/huyudi/vework/board")
sys.path.insert(0, "/home/huyudi/014_virtualEmbryo/third_party/veckit")
sys.path.insert(0, "/home/huyudi/vework/eval")

from common import core_metrics as cm  # noqa: E402
from crossko_hurdle_v2_variant import CrossKOHurdleVariant  # noqa: E402

S = Path("/home/huyudi/vework/prepared/source_panel/normalized")
REBUILD = Path("/home/huyudi/vework/rebuilt_model")
OUT = Path("/home/huyudi/vework/board/gata4_lam15unmask")
GENES = ["Dnmt3a", "Kmt2a", "Kdm2b", "Dnmt1", "Dnmt3b", "Ehmt2", "Kmt2b"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Frozen method/mode from the archived source-side selection.
    sel = json.loads(
        (Path(
            "/home/huyudi/014_virtualEmbryo/research/t3_20261008/snapshots/v0087"
            "/crossko7_hurdle_v2_results/SELECTION.json"
        )).read_text()
    )
    eligible = [x for x in sel["criteria"] if x["passes"]]
    assert eligible, "No source-eligible method"
    chosen = sorted(eligible, key=lambda x: (-x["mean_direction"], x["mse"]))[0]["model"]
    method, mode = chosen.split("_")
    print("frozen selection ->", chosen, flush=True)

    data = {}
    for gene in ["WT"] + GENES:
        a = ad.read_h5ad(S / f"{gene}_whitelisted_panel10000.h5ad")
        data[gene] = (a.X, a.obs)
    wt, wo = data["WT"]

    rng = np.random.default_rng(711)
    controls = {}
    for sex in wo.sex.unique():
        blocks = []
        for e in wo.loc[wo.sex == sex, "embryo"].unique():
            ix = np.flatnonzero((wo.sex == sex) & (wo.embryo == e))
            blocks.append(wt[rng.choice(ix, 500, replace=len(ix) < 500)])
        controls[sex] = np.concatenate(blocks)
    print("controls", {k: v.shape for k, v in controls.items()}, flush=True)

    records = []
    for gene, (x, o) in data.items():
        if gene == "WT":
            continue
        for e in sorted(o.embryo.unique()):
            mask = o.embryo == e
            sex = o.loc[mask, "sex"].iloc[0]
            records.append(
                dict(gene=gene, sample_unit=e, unit_kind="embryo",
                     control=controls[sex], ko=x[mask])
            )
    print("records", len(records), flush=True)

    emb = np.load("/home/huyudi/vework/go_expanded7/GO_EXPANDED_EMBEDDING.npz")
    priors = dict(zip(emb["genes"].astype(str), emb["embedding"]))

    model = CrossKOHurdleVariant(states=8, min_cells=10).fit_atlas(wt)
    model.fit_interventions(records, priors, "Gata4")
    response = model.predict("Gata4", method)
    print("response fitted; support", response["support"].astype(int).tolist(), flush=True)

    a = ad.read_h5ad("/home/huyudi/vework/official/E8.75.h5ad")
    X = a.X.toarray() if hasattr(a.X, "toarray") else np.asarray(a.X)
    ix = np.sort(np.random.default_rng(20260904).choice(len(X), 7449, replace=False))
    base = X[ix].copy()
    obs = a.obs.iloc[ix].copy()

    state = model.assign(base)
    supported = response["support"][state]
    pred = base.copy()
    pred[supported] = model.emit(base[supported], response, mode=mode)[0]

    out = ad.AnnData(pred, obs=obs, var=a.var.copy())
    out.obsm["spatial_3D"] = np.asarray(a.obsm["spatial_3D"])[ix].copy()
    out.uns["scope"] = (
        "Experimental seven-KO developmental prior; not target causal evidence; "
        "no hidden target outcomes"
    )
    out.uns["source_method"] = chosen
    out.uns["source_genes"] = model.training_genes
    out.uns["RNA_knockout_forced"] = False
    out.uns["route"] = "response structure lam15 + global_valid mask removed"
    out.uns["local_composite_delta"] = "+0.1985 vs frozen v0088 (source-side, 7 held-out genotypes)"
    out.uns["local_caveat"] = (
        "Local source-side score is not a server forecast; v0086 improved source-side "
        "and scored below v0084 on the server."
    )
    out.uns["provenance"] = (
        "GSE137337 seven permitted E8.5 epigenetic KO identities; GSE122187 WT; "
        "original publisher SNP embryo whitelists; seven-gene source leave-intervention-out"
    )

    file = OUT / "gata4_all_supported.h5ad"
    out.write_h5ad(file, compression="gzip")

    # Frozen contract asserts, replayed.
    r = ad.read_h5ad(file)
    assert np.array_equal(r.X, pred), "roundtrip X mismatch"
    assert np.array_equal(r.var_names, a.var_names), "gene order"
    assert np.array_equal(r.X[~supported], base[~supported]), "protected rows moved"
    assert np.isfinite(r.X).all() and (r.X >= 0).all(), "finite/non-negative"
    assert np.isfinite(r.obsm["spatial_3D"]).all(), "geometry"
    mass = np.max(np.abs(np.expm1(pred.astype(float)).sum(1) - 10000))
    assert mass < 0.02, f"panel closure {mass}"
    assert r.shape == (7449, 500), f"shape {r.shape}"

    changed = int(np.any(pred != base, axis=1).sum())
    zero_to_pos = int(((base == 0) & (pred > 0)).sum())
    pos_to_zero = int(((base > 0) & (pred == 0)).sum())
    delta = pred.mean(0, dtype=float) - base.mean(0, dtype=float)

    receipt = dict(
        variant="gata4_all_supported",
        stage="E8.75",
        source_method=chosen,
        response_route="lam15 + global_valid mask removed",
        local_composite_delta_vs_v0088=0.1985,
        mask_cells=int(supported.sum()),
        changed_cells=changed,
        detection=float((pred > 0).mean()),
        base_detection=float((base > 0).mean()),
        zero_to_positive=zero_to_pos,
        positive_to_zero=pos_to_zero,
        delta_L2=float(np.linalg.norm(delta)),
        max_log_change=float(np.abs(pred - base).max()),
        max_mass_error=float(mass),
        shape=list(r.shape),
        sha256=sha(file),
        parent="T3:gata4 v0088 condhurdle (server 53.69)",
        submission_status="NOT_SUBMITTED",
        blocks_submission=False,
    )
    (OUT / "RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()