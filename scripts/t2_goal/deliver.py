"""Register + pack for T2 goal round (adapts t2_round2 deliver pattern).

Usage:
  python -m scripts.t2_goal.deliver register --root RUN_DIR
  python -m scripts.t2_goal.deliver zip      --root RUN_DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from scripts.t2_round2 import common

REPO = common.REPO
RUN_ID = "T2-GOAL-20261001-v1"
ZIP_NAME = "t2goal__t2__upload__20261001.zip"
BOARD_DIR = {"embryo": "T2_embryo_val_interp", "heart": "T2_heart_val_interp",
             "extrap": "T2_heart_val_extrap"}
BOARD_SHORT = {"embryo": "emb_int", "heart": "hrt_int", "extrap": "hrt_ext"}
LANE_SHORT = {"e_r1": "e_r1compotrend", "e_r2": "e_r2shrinkc1", "h_r1": "h_r1compotrend",
              "h_r2": "h_r2shrinkc1", "x_r1": "x_r1lateref", "x_r2": "x_r2shrinkc1"}
PARENT_VERSION = {"embryo": "v0014_e_o1_shrinkmerge", "heart": "v0019_h_o1_shrinkmerge",
                  "extrap": "v0001_baseline"}
METHOD_BLURB = {
    "e_r1": "trend-share resample + incumbent expression",
    "e_r2": "mean bridge shrunk C=1 + mass",
    "h_r1": "trend-share resample + incumbent expression",
    "h_r2": "mean bridge shrunk C=1 + mass",
    "x_r1": "E8.25late-anchored baseline shift",
    "x_r2": "baseline shift shrunk C=1 float32",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _rows(root: Path) -> list[dict]:
    cfg = json.loads((REPO / "configs" / "t2_goal" / "design_20261001.json").read_text())
    summ = json.loads((root / "BUILD_SUMMARY.json").read_text())
    rows = []
    for lane, r in summ.items():
        board = r["board"]
        chk = json.loads((root / "checks" / f"{lane}_{r['version']}.json").read_text())
        verdict = chk["contract"]["verdict"]
        rows.append({**r, "contract_verdict": verdict,
                     "board_key": cfg["boards"][board]["key"],
                     "parent": cfg["boards"][board]["parent"]})
    return rows


def cmd_register(root: Path) -> None:
    rows = _rows(root)
    index_path = REPO / "submissions" / "INDEX.tsv"
    lines = index_path.read_text().splitlines()
    existing = set()
    for line in lines[1:]:
        f = line.split("\t")
        if len(f) >= 4:
            existing.add((f[2], f[3]))
    new_lines = []
    for r in rows:
        board, lane, version = r["board"], r["lane"], r["version"]
        if (r["board_key"], version) in existing:
            raise AssertionError(f"version already registered: {r['board_key']} {version}")
        dst = REPO / "submissions" / "candidates" / BOARD_DIR[board] / f"{version}_{lane}" / "submission.h5ad"
        if dst.exists():
            if _sha(dst) != r["sha256"]:
                raise AssertionError(f"dst exists with different bytes: {dst}")
            # verified-identical copy from a prior partial run; reuse without rewrite
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src = REPO / r["output"]
            with open(src, "rb") as fi, open(dst, "wb") as fo:
                fo.write(fi.read())
            sha = _sha(dst)
            if sha != r["sha256"]:
                raise AssertionError(f"sha mismatch after copy for {board}/{lane}")
        sha = r["sha256"]
        verdict = r["contract_verdict"]
        lc = "pass" if verdict == "pass" else "pass_with_deviation"
        note = (f"T2-GOAL {lane}: {METHOD_BLURB[lane]} parent {PARENT_VERSION[board]}; "
                f"contract {verdict}; artifacts/t2_goal/{RUN_ID}/; "
                f"design reports/T2_GOAL_DESIGN_20261001.md")
        cols = ["candidate", RUN_ID, r["board_key"], version, lane,
                f"submissions/candidates/{BOARD_DIR[board]}/{version}_{lane}/submission.h5ad",
                str(r["n_obs"]), str(r["n_vars"]), "20261001", "false", lc, sha,
                "", "score_pending", note]
        new_lines.append("\t".join(cols))
    with index_path.open("a") as f:
        for line in new_lines:
            f.write(line + "\n")
    print(json.dumps({"registered": len(new_lines)}))


def cmd_zip(root: Path) -> None:
    rows = _rows(root)
    zip_path = REPO / "deliveries" / ZIP_NAME
    if zip_path.exists():
        raise FileExistsError(str(zip_path))
    members = []
    for r in rows:
        board, lane, version = r["board"], r["lane"], r["version"]
        portal = f"t2_{BOARD_SHORT[board]}__{LANE_SHORT[lane]}__{version}.h5ad"
        if len(portal) > 50 or portal != portal.lower():
            raise AssertionError(f"portal name rule violation: {portal}")
        src = REPO / "submissions" / "candidates" / BOARD_DIR[board] / f"{version}_{lane}" / "submission.h5ad"
        if not src.exists():
            raise AssertionError(f"missing registered candidate: {src}")
        members.append({"filename": portal, "src": src, "sha256": _sha(src),
                        "bytes": src.stat().st_size, "board": r["board_key"],
                        "version": version, "lane": lane,
                        "contract": r["contract_verdict"]})
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as zf:
        for m in members:
            zf.write(m["src"], m["filename"])
        zf.writestr("MANIFEST.tsv", "".join(
            f"{m['filename']}\t{m['bytes']}\t{m['sha256']}\n" for m in members))
        upload = "portal_model_name\tboard\tversion\tmethod\tcanonical_path\tsha256\tlocal_contract\tscore_status\n"
        for m in members:
            bdir = BOARD_DIR[[b for b in BOARD_DIR if BOARD_SHORT[b] in m["filename"]][0]]
            upload += (f"{m['filename']}\t{m['board']}\t{m['version']}\t{m['lane']}\t"
                       f"submissions/candidates/{bdir}/{m['version']}_{m['lane']}/submission.h5ad\t"
                       f"{m['sha256']}\t{m['contract']}\tscore_pending\n")
        zf.writestr("UPLOAD_MANIFEST.tsv", upload)
        runmap = "filename\trun_id\tparent_version\n"
        for m in members:
            bkey = [b for b in BOARD_DIR if BOARD_SHORT[b] in m["filename"]][0]
            runmap += f"{m['filename']}\tartifacts/t2_goal/{RUN_ID}\t{PARENT_VERSION[bkey]}\n"
        zf.writestr("RUN_ID_MAP.tsv", runmap)
        evid = "filename\tcontract\tcheck\tinput_evidence\n"
        for m in members:
            evid += (f"{m['filename']}\tartifacts/t2_goal/{RUN_ID}/checks/{m['lane']}_{m['version']}.json\t"
                     f"artifacts/t2_goal/{RUN_ID}/intermediates/mass_plan_"
                     f"{[b for b in BOARD_DIR if BOARD_SHORT[b] in m['filename']][0]}_{m['lane']}.tsv\t"
                     f"configs/t2_goal/design_20261001.json\n")
        zf.writestr("EVIDENCE_MANIFEST_POINTERS.tsv", evid)
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise AssertionError(f"zip CRC failure: {bad}")
        for m in members:
            if hashlib.sha256(zf.read(m["filename"])).hexdigest() != m["sha256"]:
                raise AssertionError(f"zip member sha mismatch: {m['filename']}")
    receipt = {"zip": str(zip_path), "members": [m["filename"] for m in members],
               "status": "READY_NOT_SUBMITTED", "sha256": _sha(zip_path), "run_id": RUN_ID}
    common.write_json(Path(str(zip_path) + ".receipt.json"), receipt)
    print(json.dumps(receipt, sort_keys=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["register", "zip"])
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    root = Path(a.root)
    if not root.is_absolute():
        root = REPO / root
    if a.command == "register":
        cmd_register(root)
    else:
        cmd_zip(root)


if __name__ == "__main__":
    main()
