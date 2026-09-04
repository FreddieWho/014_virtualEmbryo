#!/usr/bin/env python3
"""Package the T1 n=1706 floor probe delivery (run exactly once)."""
import hashlib
import zipfile
from pathlib import Path

RUN = Path("artifacts/batch4/B4-P0-T1-FLOOR-PROBE2-20260904-v1")
EXPECT = "6994a38e108a29ba6791f3d81bde6347f92cf92e8c9c28153e385b973ff54a18"
RUN_ID = "B4-P0-STATE-FLOOR-PARITY-2026-09-04T164205.780061+0000"

stage = RUN / "deliveries" / "stage_t1"
stage.mkdir(parents=True, exist_ok=True)
member = "t1_val__l0floor1706__v0010.h5ad"
h5 = stage / member
h5.write_bytes((RUN / "candidates" / "T1_val" / "L0_EXACT_FLOOR_N1706" / "submission.h5ad").read_bytes())
s = hashlib.sha256(h5.read_bytes()).hexdigest()
b = h5.stat().st_size
assert s == EXPECT, s
TAB = chr(9)
NL = chr(10)
(stage / "MANIFEST.tsv").write_text(
    TAB.join(["filename", "bytes", "sha256"]) + NL + TAB.join([member, str(b), s]) + NL)
(stage / "UPLOAD_MANIFEST.tsv").write_text(
    TAB.join(["member", "board", "version", "canonical_path", "canonical_sha256", "target_used"]) + NL
    + TAB.join([member, "T1:val", "v0010",
                "submissions/candidates/T1_val/v0010_b4p0_l0floor_n1706/submission.h5ad", s, "false"]) + NL)
(stage / "RUN_ID_MAP.tsv").write_text(
    TAB.join(["member", "run_id", "task_id"]) + NL
    + TAB.join([member, RUN_ID, "B4-P0-STATE-FLOOR-PARITY"]) + NL)
(stage / "EVIDENCE_MANIFEST_POINTERS.tsv").write_text(
    TAB.join(["member", "evidence_manifest"]) + NL
    + TAB.join([member, "artifacts/batch4/B4-P0-T1-FLOOR-PROBE2-20260904-v1/evidence/EVIDENCE_MANIFEST.json"]) + NL)
z = RUN / "deliveries" / "b4p0p2__t1__upload__20260904.zip"
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in [h5, stage / "MANIFEST.tsv", stage / "UPLOAD_MANIFEST.tsv",
              stage / "RUN_ID_MAP.tsv", stage / "EVIDENCE_MANIFEST_POINTERS.tsv"]:
        zf.write(f, f.name)
print("zip bytes", z.stat().st_size, "member", member, len(member), "chars")
print(sorted(zipfile.ZipFile(z).namelist()))
