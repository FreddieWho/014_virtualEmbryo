"""Append the v0089 candidate row to submissions/INDEX.tsv.

Schema-faithful append: 15 tab-separated fields matching the existing rows.
No existing row is touched.
"""
from pathlib import Path

IDX = Path("/home/huyudi/014_virtualEmbryo/submissions/INDEX.tsv")

NOTES = (
    "parent=v0088; response_structure=lam15+global_valid_mask_removed; "
    "method=mean_combined (frozen selection); mode=combined; seed=20260904; "
    "E8.75 WT carrier 7449x500; contract PASS (roundtrip X, gene order, protected "
    "rows unchanged, finite/non-negative, spatial_3D finite, panel closure max "
    "mass error 0.00346); local source-side composite 74.936110 vs v0088 "
    "74.737588 (+0.1985, 4/7 held-out genotypes, frozen gate PASS); "
    "NOT_SUBMITTED; blocks_submission:false (T3 budget unresolved, no further "
    "attempt authorized); local score is not a server forecast (v0086 source-side "
    "gain scored below v0084 on the server); build scripts "
    "autoresearch/loop-261009-1845/scripts/"
)

row = [
    "candidate",
    "T3-RESPLAM15-20261009-v1",
    "T3:gata4",
    "v0089",
    "resplam15unmask",
    "submissions/candidates/T3_gata4/v0089_resplam15unmask/submission.h5ad",
    "7449",
    "500",
    "20260904",
    "false",
    "pass",
    "ddac99703587e2c35713dcf0e3eb09bb6a0dfff88298bb94548a08d1fa115f3a",
    "",
    "score_pending",
    NOTES,
]

line = "\t".join(row)
assert len(row) == 15
assert "\t" not in NOTES

with IDX.open("a") as f:
    f.write(line + "\n")

# verify the last line round-trips to exactly 15 fields
last = IDX.read_text().rstrip("\n").split("\n")[-1].split("\t")
assert len(last) == 15, len(last)
assert last[3] == "v0089" and last[13] == "score_pending"
print("appended v0089; fields =", len(last))
print("board/version:", last[2], last[3], "score_status:", last[13])