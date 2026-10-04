"""Stage + package batch AR-T1-MIX2-20261003-v1 into ONE upload zip.

Reads artifacts/autoresearch/t1-20261003-v1/FINAL_BUILD_v2.json (written by
.auto/build_t1_finals_v2.py), hardlinks the 5 contract-PASS lanes into
stage_art1mix2/ with portal member names, writes MANIFEST / UPLOAD_MANIFEST /
RUN_ID_MAP / EVIDENCE_MANIFEST_POINTERS / HANDOFF / README, then zips them into
deliveries/art1mix2__t1__upload__20261003.zip + receipt json.

Versions v0052-v0056 are PROPOSED (coordinator owns INDEX allocation).
No INDEX/registry/coordination writes.
"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(".").resolve()
BOUT = ROOT / "artifacts/autoresearch/t1-20261003-v1"
BUILD = json.loads((BOUT / "FINAL_BUILD_v2.json").read_text())
STAGE = BOUT / "stage_art1mix2"
ZIP = ROOT / "deliveries/art1mix2__t1__upload__20261003.zip"
RECEIPT = ROOT / "deliveries/art1mix2__t1__upload__20261003.zip.receipt.json"
RUN_ID = "AR-T1-MIX2-20261003-v1"
GROUP = "AR-T1-MIX2-20261003"

MEMBER = {  # lane -> portal member name (<=50 chars, per manual-upload rule)
    "P1": "t1_val__mix3538even__v0052.h5ad",
    "P2": "t1_val__mix3538evenb__v0053.h5ad",
    "P3": "t1_val__mix3638even__v0054.h5ad",
    "P4": "t1_val__mix3way__v0055.h5ad",
    "P5": "t1_val__mix3538f030__v0056.h5ad",
}
ROLE = {
    "P1": "requested 50/50 v0035 x v0038 lane (M5 analogue; report median +1q, vario beats baseline)",
    "P2": "seed-pair partner of P1 (server row-luck read; same design, second draw)",
    "P3": "50/50 v0036 x v0038 -> more v0038 than v0051 53.92 (server-best pair variant)",
    "P4": "three-pool equal thirds v0035 x v0036 x v0038 (M4 analogue; new mechanism)",
    "P5": "30/70 v0035 x v0038 (M6 analogue; best report mmd of the +1q points)",
}
PARENTS = {
    "P1": "v0035 x v0038 @frac0.5/seed20260921",
    "P2": "v0035 x v0038 @frac0.5/seed20261023",
    "P3": "v0036 x v0038 @frac0.5/seed20260921",
    "P4": "v0035 x v0036 x v0038 equal thirds/seed20260921",
    "P5": "v0035 x v0038 @frac0.3/seed20260921",
}
REPORT_ANALOG = {
    "P1": "T1-12 f0.5 3-seed median de +1q (0.6111); vario 0.000396 < baseline; M5 material",
    "P2": "same design as P1, different draw (no seed-mining: batch-convention seed)",
    "P3": "server 36x38 at 70/30 = v0051 53.92 (current T1 best); 50/50 = more cov-OT donor",
    "P4": "T1-11 three-way equal-thirds 3-seed median pin (0.5926), best seed +1q; M4 material",
    "P5": "T1-15 f0.3 3-seed median pin; seed20260921 +1q with best report mmd (0.00926); M6 material",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(4 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if ZIP.exists() or RECEIPT.exists():
        raise SystemExit(f"refusing to overwrite existing package: {ZIP}")
    if STAGE.exists():
        raise SystemExit(f"refusing to reuse existing stage dir: {STAGE}")
    STAGE.mkdir(parents=True)
    lanes = {r["lane"]: r for r in BUILD}
    assert set(lanes) == set(MEMBER), lanes.keys()
    members = []
    for lane, member in MEMBER.items():
        src = ROOT / lanes[lane]["path"]
        assert lanes[lane]["contract"] == "PASS", lane
        dst = STAGE / member
        assert not dst.exists()
        os.link(src, dst)  # hardlink: identical bytes, zero copy
        assert sha(dst) == lanes[lane]["sha256"], f"{lane} sha mismatch after staging"
        members.append({"lane": lane, "member": member, "bytes": dst.stat().st_size,
                        "sha256": lanes[lane]["sha256"],
                        "canonical": lanes[lane]["path"],
                        "proposed_version": lanes[lane]["proposed_version"].split("_")[0],
                        "parents": PARENTS[lane], "contract": lanes[lane]["contract"]})
        print(f"staged {lane}: {member} {dst.stat().st_size} bytes {lanes[lane]['sha256'][:12]}…")
    (STAGE / "MANIFEST.tsv").write_text(
        "filename\tbytes\tsha256\n"
        + "".join(f"{m['member']}\t{m['bytes']}\t{m['sha256']}\n" for m in members))
    (STAGE / "UPLOAD_MANIFEST.tsv").write_text(
        "member\tcanonical_staged_path\tsha256\tproposed_version\tparents\tcontract\n"
        + "".join(f"{m['member']}\t{m['canonical']}\t{m['sha256']}\t{m['proposed_version']}_PROPOSED"
                  f"\t{m['parents']}\t{m['contract']}\n" for m in members))
    (STAGE / "RUN_ID_MAP.tsv").write_text(f"run_id\tgroup\tdate\n{RUN_ID}\t{GROUP}\t{date.today()}\n")
    (STAGE / "EVIDENCE_MANIFEST_POINTERS.tsv").write_text(
        "filename\tcontract\trun_log\tmethod_doc\tqueue_note\n"
        + "".join(f"{m['member']}\t.auto/log.jsonl\t.auto/build_t1_finals_v2.py"
                  f"\tartifacts/autoresearch/t1-20261003-v1/SESSION_SUMMARY.md"
                  f"\tartifacts/autoresearch/t1-20261003-v1/FINAL_BUILD_v2.json\n" for m in members))
    handoff = f"""# Handoff {RUN_ID} — batch of 5 T1 mix lanes

task: T1:val (5 lanes, whole-row winner mixes; batch AR-T1-MIX2-20261003-v1)
contract parent (all lanes): v0035_three_r2joint (seven precedent)
donors: v0035_three_r2joint / v0036_three_r3mix / v0038_seven_n2covot (scored finals, sha re-verified vs INDEX)
method: stratified whole-row mixture (s2mix recipe verbatim) for P1/P2/P3/P5;
        equal-thirds three-pool construction (report M4 generator) for P4; frozen seeds
artifacts: artifacts/autoresearch/t1-20261003-v1/final_<lane>_*/submission.h5ad (sha in MANIFEST.tsv)
contract: 5/5 PASS (per-lane CONTRACT.json; validator = frozen contract_io + P0-LOCK)
versions: v0052–v0056 PROPOSED — coordinator owns INDEX allocation / canonical placement
report evidence: see SESSION_SUMMARY.md (T1-11/T1-12/T1-15); target_used=false throughout
known risks: (1) report-level de quanta are row-lottery (±1q) — server row-luck was ±0.40 on the
        previous batch, this is why P1/P2 ship as a seed pair; (2) local proxy does not rank the
        server champions (documented) — no lane is claimed to beat v0051 53.92; (3) P4/P5 report
        medians are pin, not +1q (honest: they are diversity/complement lanes, not local winners)
recommended_upload_order: P3, P1, P4, P2, P5 (see deliveries receipt + chat report for rationale)
proposed_decision: user uploads the members manually; coordinator adds INDEX rows (score_pending)
        after upload/score return; no promotion claim until portal scores return
blocker: none (target_used=false; no E10.5 truth; no scored artifact touched; nothing overwritten)
evidence pointers: .auto/log.jsonl (phase T1), artifacts/autoresearch/t1-20261003-v1/
"""
    (STAGE / "HANDOFF_ART1MIX2.md").write_text(handoff)
    (STAGE / "README_PENDING_INDEX.md").write_text(
        "# Batch AR-T1-MIX2-20261003-v1 — PENDING coordinator INDEX allocation\n\n"
        "Members carry PROPOSED versions v0052–v0056 (INDEX last registered T1:val version = v0047;\n"
        "v0048–v0051 are informally used by the closed D2R3 run and the 2026-10-02 AR-T1-MIX batch\n"
        "whose score return is logged but whose INDEX rows were not yet added by the coordinator).\n\n"
        "If the coordinator allocates different version numbers, rename the members inside this zip\n"
        "accordingly (identity of record = SHA256, see MANIFEST.tsv).\n\n"
        f"run_id: {RUN_ID}\ngroup: {GROUP}\ndate: {date.today()}\n"
        "portal naming: `<task>_<board>__<lane>__v<NNNN>.h5ad` (rule fixed 2026-09-03); all members <=50 chars.\n")
    files = [m["member"] for m in members] + ["MANIFEST.tsv", "UPLOAD_MANIFEST.tsv", "RUN_ID_MAP.tsv",
                                             "EVIDENCE_MANIFEST_POINTERS.tsv", "HANDOFF_ART1MIX2.md",
                                             "README_PENDING_INDEX.md"]
    subprocess.run(["zip", "-X", "-9", str(ZIP)] + files, cwd=STAGE, check=True)
    zsha = sha(ZIP)
    RECEIPT.write_text(json.dumps({
        "zip": str(ZIP), "status": "READY_PENDING_INDEX_ALLOCATION",
        "sha256": zsha, "bytes": ZIP.stat().st_size, "run_id": RUN_ID, "group": GROUP,
        "members": [m["member"] for m in members],
        "member_sha256": {m["member"]: m["sha256"] for m in members},
        "proposed_versions": {m["member"]: m["proposed_version"] for m in members},
        "contract_all_pass": all(m["contract"] == "PASS" for m in members),
        "report_evidence": "artifacts/autoresearch/t1-20261003-v1/SESSION_SUMMARY.md",
        "index_status": "NOT_REGISTERED_pending_coordinator",
        "upload": "manual by user; server arbitrates; no local promotion claim",
    }, indent=1))
    print(f"ZIP {ZIP} {ZIP.stat().st_size} bytes sha256={zsha}")


if __name__ == "__main__":
    main()
