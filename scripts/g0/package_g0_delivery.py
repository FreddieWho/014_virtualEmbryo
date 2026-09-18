#!/usr/bin/env python3
"""G0 unified delivery packager: one zip per task with renamed members + MANIFEST.

Upload set (FULL coverage after audit: every G1 candidate ships; user may skip
marked optionals at upload time; all within server 8/task/day: T1 7, T3 5, T2 6):
  T1 (7): v0015 tie, v0016/v0017 regressions (marked OPTIONAL), v0018-v0021 promoted
  T3 (5 mechanism bets): v0013-v0017 (v0009 anchor already scored)
  T2-extrap (6): v0011 negative + v0013 flat (marked OPTIONAL), v0012/v0014/v0015/v0016
Member rule: <task>_<board>__<lane>__vNNNN.h5ad, lowercase, <=50 chars.
Zip rule: <atom>__<task>__upload__<YYYYMMDD>.zip, <=50 chars.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO = Path(__file__).resolve().parents[2]
DATE = "20260916"

PACKS = {
    "g0t1__t1__upload__20260916.zip": [
        ("submissions/candidates/T1_val/v0015_g0_t1_r1_neural_ode/submission.h5ad",
         "t1_val__r1node__v0015.h5ad"),
        ("submissions/candidates/T1_val/v0016_g0_t1_r2_substate/submission.h5ad",
         "t1_val__r2sub__v0016.h5ad"),
        ("submissions/candidates/T1_val/v0017_g0_t1_r3_maturity/submission.h5ad",
         "t1_val__r3mat__v0017.h5ad"),
        ("submissions/candidates/T1_val/v0018_g0_t1_r4_shrink/submission.h5ad",
         "t1_val__r4c2__v0018.h5ad"),
        ("submissions/candidates/T1_val/v0019_g0_t1_r5_c1/submission.h5ad",
         "t1_val__r5c1__v0019.h5ad"),
        ("submissions/candidates/T1_val/v0020_g0_t1_r5_c2/submission.h5ad",
         "t1_val__r5c2__v0020.h5ad"),
        ("submissions/candidates/T1_val/v0021_g0_t1_r5_c4/submission.h5ad",
         "t1_val__r5c4__v0021.h5ad"),
    ],
    "g0t3__t3__upload__20260916.zip": [
        ("submissions/candidates/T3_gata4/v0013_g0_t3_r1_directprop/submission.h5ad",
         "t3_gata4__r1prop__v0013.h5ad"),
        ("submissions/candidates/T3_gata4/v0014_g0_t3_r2_gradeddose/submission.h5ad",
         "t3_gata4__r2tert__v0014.h5ad"),
        ("submissions/candidates/T3_gata4/v0015_g0_t3_r3_lineagedose/submission.h5ad",
         "t3_gata4__r3lin__v0015.h5ad"),
        ("submissions/candidates/T3_gata4/v0016_g0_t3_r4_combo/submission.h5ad",
         "t3_gata4__r4combo__v0016.h5ad"),
        ("submissions/candidates/T3_gata4/v0017_g0_t3_r5_amp2/submission.h5ad",
         "t3_gata4__r5amp2__v0017.h5ad"),
    ],
    "g0t2__t2__upload__20260916.zip": [
        ("submissions/candidates/T2_heart_val_extrap/v0011_g0_t2_r2_shrink/submission.h5ad",
         "t2_hrt_ext__r2shr__v0011.h5ad"),
        ("submissions/candidates/T2_heart_val_extrap/v0012_g0_t2_r3_spatial/submission.h5ad",
         "t2_hrt_ext__r3k15__v0012.h5ad"),
        ("submissions/candidates/T2_heart_val_extrap/v0013_g0_t2_r4_k07/submission.h5ad",
         "t2_hrt_ext__r4k07__v0013.h5ad"),
        ("submissions/candidates/T2_heart_val_extrap/v0014_g0_t2_r4_k15/submission.h5ad",
         "t2_hrt_ext__r4k15__v0014.h5ad"),
        ("submissions/candidates/T2_heart_val_extrap/v0015_g0_t2_r4_k30/submission.h5ad",
         "t2_hrt_ext__r4k30__v0015.h5ad"),
        ("submissions/candidates/T2_heart_val_extrap/v0016_g0_t2_r5_k60/submission.h5ad",
         "t2_hrt_ext__r5k60__v0016.h5ad"),
    ],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    out_dir = REPO / "deliveries"
    out_dir.mkdir(exist_ok=True)
    for zname, members in PACKS.items():
        assert len(zname) <= 50, zname
        rows = ["member\tsource\tsha256\tn_bytes"]
        zp = out_dir / zname
        if zp.exists():
            zp.unlink()
        with ZipFile(zp, "w", ZIP_DEFLATED) as z:
            for src_rel, member in members:
                assert len(member) <= 50 and member == member.lower(), member
                src = REPO / src_rel
                assert src.exists(), src_rel
                h = sha256(src)
                z.write(src, member)
                rows.append(f"{member}\t{src_rel}\t{h}\t{src.stat().st_size}")
            z.writestr("MANIFEST.tsv", "\n".join(rows) + "\n")
        # Verify: re-read zip member hashes.
        with ZipFile(zp) as z:
            for src_rel, member in members:
                data = z.read(member)
                h1 = hashlib.sha256(data).hexdigest()
                h0 = sha256(REPO / src_rel)
                assert h1 == h0, f"zip member hash mismatch: {member}"
        print(f"{zname}: {len(members)} members OK, {zp.stat().st_size/1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
