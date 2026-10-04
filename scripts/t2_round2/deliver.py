"""Delivery for T2 round2: register candidates into submissions/candidates +
INDEX.tsv, and build the single manual-upload zip with 4 TSVs.

Usage:
  python -m scripts.t2_round2.deliver register --root RUN_DIR
  python -m scripts.t2_round2.deliver zip --root RUN_DIR --zip deliveries/t2r2__t2__upload__20260929.zip

No upload is performed. Existing INDEX versions are never overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

from scripts.t2_round2 import common
from scripts.t2_round2.run import BOARD_DIR, LANES

REPO = common.REPO
RUN_ID = "T2-ROUND2-20260929-v1"
ZIP_LANE_SHORT = {}  # lane names are short enough to use verbatim

BOARD_SHORT = {"embryo": "emb_int", "heart": "hrt_int", "extrap": "hrt_ext"}
PARENT_VERSION = {"embryo": "v0010", "heart": "v0013", "extrap": "v0001"}


def _sha(path: Path) -> str:
    return common.sha256(path)


def _atomic_copy(src: Path, dst: Path) -> None:
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(str(dst))
    fd, tmp = tempfile.mkstemp(prefix="." + dst.name + ".", dir=dst.parent)
    os.close(fd)
    shutil.copyfile(src, tmp)
    if _sha(src) != _sha(tmp):
        os.unlink(tmp)
        raise AssertionError(f"copy verification failed: {dst}")
    Path(tmp).replace(dst)


def _lane_rows(root: Path, cfg: dict) -> list[dict]:
    summ = json.loads((root / "BUILD_SUMMARY.json").read_text())
    contract = pd.read_csv(root / "checks" / "contract_checks.tsv", sep="\t")
    cmap = {(r["board"], r["lane"]): r for _, r in contract.iterrows()}
    rows = []
    for r in summ["results"]:
        board, lane = r["board"], r["lane"]
        c = cmap[(board, lane)]
        rows.append({**r, "contract_verdict": c["verdict"], "contract_errors": c["errors"]})
    return rows


def cmd_register(root: Path, cfg: dict) -> None:
    rows = _lane_rows(root, cfg)
    index_path = REPO / "submissions" / "INDEX.tsv"
    index = index_path.read_text().splitlines()
    existing = set()
    for line in index[1:]:
        f = line.split("\t")
        if len(f) >= 4:
            existing.add((f[2], f[3]))
    new_lines = []
    for r in rows:
        board, lane, version = r["board"], r["lane"], r["version"]
        bc = cfg["boards"][board]
        if (bc["key"], version) in existing:
            raise AssertionError(f"version already registered: {bc['key']} {version}")
        dst = REPO / "submissions" / "candidates" / BOARD_DIR[board] / f"{version}_{lane}" / "submission.h5ad"
        _atomic_copy(REPO / r["output"], dst)
        sha = _sha(dst)
        if sha != r["sha256"]:
            raise AssertionError(f"sha mismatch after copy for {board}/{lane}")
        lc = "pass" if r["contract_verdict"] == "PASS" else "pass_with_deviation"
        note = (f"T2-ROUND2 {lane}: {r['diag'].get('method', '') if isinstance(r['diag'], dict) else ''} "
                f"parent {PARENT_VERSION[board]}; contract {r['contract_verdict']}"
                + (f" ({r['contract_errors']})" if r["contract_verdict"] != "PASS" else "")
                + f"; artifacts/t2_round2/{RUN_ID}/; design reports/T2_ROUND2_DESIGN_20260929.md")
        cols = ["candidate", RUN_ID, bc["key"], version, lane,
                f"submissions/candidates/{BOARD_DIR[board]}/{version}_{lane}/submission.h5ad",
                str(r["n_obs"]), str(r["n_vars"]), str(cfg["seed"]), "false", lc, sha,
                "", "score_pending", note]
        new_lines.append("\t".join(cols))
    with index_path.open("a") as f:
        for line in new_lines:
            f.write(line + "\n")
    common.write_json(root / "checks" / "register.json",
                      {"registered": len(new_lines), "index": "submissions/INDEX.tsv"})
    print(json.dumps({"registered": len(new_lines)}))


def cmd_zip(root: Path, cfg: dict, zip_path: Path) -> None:
    rows = _lane_rows(root, cfg)
    zip_path = Path(zip_path)
    if zip_path.exists():
        raise FileExistsError(str(zip_path))
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    members: list[dict] = []
    for r in rows:
        board, lane, version = r["board"], r["lane"], r["version"]
        portal = f"t2_{BOARD_SHORT[board]}__{lane}__{version}.h5ad"
        if len(portal) > 50 or portal != portal.lower():
            raise AssertionError(f"portal name rule violation: {portal}")
        src = REPO / "submissions" / "candidates" / BOARD_DIR[board] / f"{version}_{lane}" / "submission.h5ad"
        members.append({"filename": portal, "src": src, "sha256": _sha(src),
                        "bytes": src.stat().st_size, "board": cfg["boards"][board]["key"],
                        "version": version, "lane": lane, "contract": r["contract_verdict"]})
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as zf:
        for m in members:
            zf.write(m["src"], m["filename"])
        manifest = "".join(f"{m['filename']}\t{m['bytes']}\t{m['sha256']}\n" for m in members)
        zf.writestr("MANIFEST.tsv", manifest)
        upload = "portal_model_name\tboard\tversion\tmethod\tcanonical_path\tsha256\tlocal_contract\tscore_status\n"
        for m in members:
            board_slug = BOARD_DIR[[b for b in LANES if cfg["boards"][b]["key"] == m["board"]][0]]
            upload += (f"{m['filename']}\t{m['board']}\t{m['version']}\t{m['lane']}\t"
                       f"submissions/candidates/{board_slug}/{m['version']}_{m['lane']}/submission.h5ad\t"
                       f"{m['sha256']}\t{m['contract']}\tscore_pending\n")
        zf.writestr("UPLOAD_MANIFEST.tsv", upload)
        runmap = "filename\trun_id\tparent_version\n"
        for m in members:
            bkey = [b for b in LANES if cfg["boards"][b]["key"] == m["board"]][0]
            runmap += f"{m['filename']}\tartifacts/t2_round2/{RUN_ID}\t{PARENT_VERSION[bkey]}\n"
        zf.writestr("RUN_ID_MAP.tsv", runmap)
        evid = "filename\tcontract\tresult\tinput_lock\n"
        for m in members:
            bkey = [b for b in LANES if cfg["boards"][b]["key"] == m["board"]][0]
            evid += (f"{m['filename']}\tartifacts/t2_round2/{RUN_ID}/checks/contract_checks.tsv\t"
                     f"artifacts/t2_round2/{RUN_ID}/intermediates/diag_{bkey}_{m['lane']}.json\t"
                     f"artifacts/t2_round2/{RUN_ID}/INPUT_LOCK.json\n")
        zf.writestr("EVIDENCE_MANIFEST_POINTERS.tsv", evid)
    # verify: member sha + CRC
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise AssertionError(f"zip CRC failure: {bad}")
        for m in members:
            data = zf.read(m["filename"])
            if hashlib.sha256(data).hexdigest() != m["sha256"]:
                raise AssertionError(f"zip member sha mismatch: {m['filename']}")
    receipt = {"zip": str(zip_path), "members": len(members), "status": "READY_NOT_SUBMITTED",
               "sha256": _sha(zip_path), "run_id": RUN_ID}
    common.write_json(Path(str(zip_path) + ".receipt.json"), receipt)
    common.write_json(root / "checks" / "deliver.json", receipt)
    print(json.dumps(receipt, sort_keys=True))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["register", "zip"])
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--zip", type=Path, default=None)
    args = ap.parse_args(argv)
    cfg = common.load_config()
    if args.command == "register":
        cmd_register(args.root, cfg)
    else:
        if args.zip is None:
            raise ValueError("--zip required")
        cmd_zip(args.root, cfg, args.zip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
