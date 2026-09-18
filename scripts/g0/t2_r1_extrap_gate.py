#!/usr/bin/env python3
"""G1-T2-R1 extrap gate establishment: proxy slices + baseline/diag local scores.

No established extrap pseudo-target scorer invocation existed (B4-T2-R3 used backtest
only). Fixed proxy (disclosed, same-easiness discipline as T1: target from training data,
comparisons valid only under identical target/seed):
  target    = E9.5 cardiac cells (SV-CM/aCM3/vCM3/OFT-CM/aCM5/vCM4/vCM5/aCM4, n=12083)
  reference = E8.75 cardiac cells (vCM1/vCM2/aCM1/aCM2/aSHF/pSHF/OFT/RV-CM/JCF/SV-CM/
              FHF/JCF/aPHM/pPHM, n=5404)
Scored: extrap baseline v0001 (GATE BASELINE) + B4-T2-R3 v0008/v0009/v0010 (free
calibration of existing unscored candidates; no new modeling this round).
Frozen: seeds. Caps: single process, deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import anndata as ad
import numpy as np
import pandas as pd

TASK_ID = "G1-T2-R1-EXTRAP-GATE"
RUN_SEED = 20260916
E95 = REPO / "data" / "E9.5.h5ad"
E875 = REPO / "data" / "E8.75.h5ad"
CARDIAC_E95 = ["SV-CM", "aCM3", "vCM3", "OFT-CM", "aCM5", "vCM4", "vCM5", "aCM4"]
CARDIAC_E875 = ["vCM1", "vCM2", "aCM1", "aCM2", "aSHF", "pSHF", "OFT/RV-CM",
                "JCF/SV-CM", "FHF/JCF", "aPHM", "pPHM"]
CANDS = {
    "v0001_baseline": "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad",
    "v0008_damp050": "submissions/candidates/T2_heart_val_extrap/v0008_b4_t2_r3_l1_damp050/submission.h5ad",
    "v0009_time1333": "submissions/candidates/T2_heart_val_extrap/v0009_b4_t2_r3_l2_time1333/submission.h5ad",
    "v0010_popmix050": "submissions/candidates/T2_heart_val_extrap/v0010_b4_t2_r3_l3_popmix050/submission.h5ad",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()
    RUN = Path(args.run_dir)
    (RUN / "intermediates").mkdir(parents=True, exist_ok=True)
    (RUN / "metrics").mkdir(parents=True, exist_ok=True)
    diag: dict = {"task": TASK_ID, "seed": RUN_SEED,
                  "proxy": "target=E9.5-cardiac(12083), ref=E8.75-cardiac(5404), fixed upfront"}
    t00 = time.time()

    e95 = ad.read_h5ad(E95)
    e875 = ad.read_h5ad(E875)
    assert set(e95.obs["cm_celltype"].astype(str)) == set(CARDIAC_E95) | {"Unknown"}
    cm8 = set(e875.obs["cm_celltype"].astype(str))
    assert set(CARDIAC_E875) <= cm8, "E8.75 cm namespace drift"
    tgt = e95[e95.obs["cm_celltype"].isin(CARDIAC_E95)].copy()
    ref = e875[e875.obs["cm_celltype"].isin(CARDIAC_E875)].copy()
    assert len(tgt) == 12083 and len(ref) == 5404, (len(tgt), len(ref))
    tgt.write_h5ad(RUN / "intermediates" / "proxy_target_e95_cardiac.h5ad")
    ref.write_h5ad(RUN / "intermediates" / "proxy_ref_e875_cardiac.h5ad")
    diag["proxy_built"] = {"n_target": len(tgt), "n_ref": len(ref)}

    out = {}
    for name, rel in CANDS.items():
        p = REPO / rel
        assert p.exists(), f"missing {rel}"
        mp = RUN / "metrics" / f"scorer_{name}.json"
        cmd = ["env", "LD_LIBRARY_PATH=/opt/anaconda3/lib", "PYTHONPATH=third_party/veckit",
               "python", "third_party/veckit/score_h5ad.py", "--task", "T2", "--setting", "heart",
               "--input", str(p), "--target", str(RUN / "intermediates" / "proxy_target_e95_cardiac.h5ad"),
               "--reference", str(RUN / "intermediates" / "proxy_ref_e875_cardiac.h5ad"),
               "--seed", str(RUN_SEED), "--out", str(mp)]
        r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            raise RuntimeError(f"scorer failed {name}: " + r.stderr[-1500:])
        m = json.loads(mp.read_text())["metrics"]
        keep = {k: m.get(k) for k in ("de_score", "de_direction", "energy_distance", "mmd_u",
                                      "variogram", "d2_shape", "occupancy_dice",
                                      "scale_log_ratio", "neighborhood_mmd", "composition_JSD",
                                      "pseudobulk_pearson", "pb_rel_err")}
        (RUN / "metrics" / f"scorer_{name}_slim.json").write_text(json.dumps(keep, indent=1))
        keep["sha"] = sha256(p)
        out[name] = keep
        print(name, json.dumps({k: keep[k] for k in ("de_score", "de_direction", "variogram",
                                                     "neighborhood_mmd")}), flush=True)
    diag["local"] = out
    diag["wall_s"] = time.time() - t00
    (RUN / "RESULT.json").write_text(json.dumps(diag, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
