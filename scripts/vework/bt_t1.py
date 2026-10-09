#!/usr/bin/env python
"""T1 temporal backtest with the official T1 construction (10% copies, truth half/ceiling half, weights .25/.25/.30/.20).
Today : --train E8.5_RNA:8.5 --target E9.5_RNA:9.5   (only one input stage -> single-stage recipes only)
10-20 : --train E8.5_RNA:8.5,E9.5_RNA:9.5 --target E10.5_RNA:10.5   (the real proxy for E9.5,E10.5 -> E12.5)
Recipes are run through t1_recipe.py so the backtested code is exactly the shipped code."""
import argparse, sys, subprocess, json, tempfile
from pathlib import Path
import numpy as np, anndata as ad
sys.path.insert(0, str(Path(__file__).parent))
from backtest import Board, fmt
from vecommon import DATA

VE = Path("/workspace/ve")


def load_sub(name, seed):
    a = ad.read_h5ad(DATA / f"{name}.h5ad")
    rng = np.random.default_rng(seed); r = np.sort(rng.choice(a.n_obs, int(round(a.n_obs * 0.1)), replace=False))
    b = a[r].copy(); b.X = b.X.toarray().astype(np.float32); del a
    return b


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--train", required=True); ap.add_argument("--target", required=True)
    ap.add_argument("--recipes", default="copy_last,shift,shift_zp"); ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    train = a.train.split(","); tname, ttime = a.target.rsplit(":", 1)
    last = train[-1].rsplit(":", 1)[0]
    genes = [str(x) for x in ad.read_h5ad(DATA / f"{last}.h5ad", backed="r").var_names]
    res = {}
    for s in range(a.seeds):
        T = load_sub(tname, 1000 + s); Rf = load_sub(last, 2000 + s)   # reference = last training stage (copy_last floor)
        B = Board("T1", genes, T, Rf, seed=s); del T
        print(fmt(f"[s{s}] floor", B.skills(B.floor)))
        print("  local ceiling:", {k: B.ceil.get(k) for k in ("de_score", "de_direction", "mmd_u", "variogram")})
        for rn in a.recipes.split(","):
            if rn != "copy_last" and len(train) < 2: print(f"[s{s}] {rn}: needs >=2 training stages, skipped"); continue
            with tempfile.TemporaryDirectory(dir="/workspace/ve/work") as td:
                out = Path(td) / "p.h5ad"
                cmd = [str(VE / "venv/bin/python"), str(VE / "vework/t1_recipe.py"), "--last", train[-1], "--target", ttime,
                       "--out", str(out), "--seed", str(300 + s), "--board", "T1:val"]
                if rn == "copy_last": cmd += ["--method", "copy_last"]
                else: cmd += ["--method", "shift", "--prev", train[-2]] + (["--zero-preserve"] if rn == "shift_zp" else [])
                subprocess.run(cmd, check=True, capture_output=True)
                P = ad.read_h5ad(out); P.X = P.X.toarray() if hasattr(P.X, "toarray") else P.X
                m = B.raw(P); sk = B.skills(m); ska = B.skills(m, ceil_from="T1:val"); del P
                print(fmt(f"[s{s}] {rn} (published ceilings)", ska))
            res.setdefault(rn, []).append(sk); print(fmt(f"[s{s}] {rn}", sk), flush=True)
    if a.out: Path(a.out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
