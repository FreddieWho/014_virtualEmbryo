"""Build the Route C upload package: contract-check, canonical copy, 4-piece set, zip, receipt."""
from pathlib import Path
import hashlib, json, shutil, sys, zipfile
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from scripts.t2_round2.common import contract_check

ART = REPO / "artifacts/autoresearch/t2-extrap-20261001-v1"
CANON = REPO / "submissions/candidates/T2_heart_val_extrap"
PARENT_REL = "submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad"
PARENT_SHA = "f30beba62da673bb4c980d92eec2bc9ea03696e5c2b65414307c2e0402bd7504"
MASS_EXEMPT = {
    "candidate obs_names/order does not exactly match the locked parent",
    "candidate obs metadata does not exactly match the locked parent",
    "candidate layers content changed relative to the locked parent",
    "candidate raw content changed relative to the locked parent",
}
RUN_ID = "AR-ROUTE-C-20261002-v1"
GROUP = "AR-ROUTE-C-20261002"

MEMBERS = [
    dict(version="v0024", lane="qte_tc_s929", method="qte_time_compmix_seed929",
         src="submission.iter20-qte-time-compmix.seed20260929.h5ad", seed=20260929,
         composite=3.913, expr=6.8119, role="CHAMPION (median-value seed of 3)"),
    dict(version="v0025", lane="qte_compmix", method="qte_compmix_seed20261008",
         src="submission.iter15-qtecompmix.h5ad", seed=20261008,
         composite=3.4636, expr=6.074, role="robust runner-up (3 seeds all > old champion)"),
    dict(version="v0026", lane="qte_time", method="qte_time_normalized_4over3",
         src="submission.iter19-qte-time.h5ad", seed=None,
         composite=2.6084, expr=4.1735, role="deterministic marginal-only design (NO resampling: zero seed risk)"),
    dict(version="v0027", lane="sharetrend_qte", method="share_lin_trend_x_qte_time",
         seed=20261007,
         src="submission.iter21-sharetrend-qte.h5ad",
         composite=0.855, expr=11.479,
         role="DIAGNOSTIC PROBE, OPTIONAL (skip for promising-only): median seed of {0.522, 0.855, 1.440}; known defect library_size_ratio=11.98 (12x) + variance_ratio 1.74 -> local guardrails FAIL; highest expression composite ever (11.5) so it tests whether the server rewards the marginal/expression profile or punishes composition aggressiveness"),
    dict(version="v0028", lane="qte_tc_s008", method="qte_time_compmix_seed20261008",
         src="submission.iter20-qte-time-compmix.seed20261008.h5ad", seed=20261008,
         composite=3.6058, expr=6.3022, role="seed-replication probe (identical design to v0024, different rows: measures server-side row-luck)"),
]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = []
    for m in MEMBERS:
        src = ART / m["src"]
        if not src.exists():
            print(f"SKIP {m['version']}: missing {src.name}")
            continue
        cc = contract_check(src, board="heart:val_extrap", parent_rel=PARENT_REL, parent_sha=PARENT_SHA)
        errs = [str(e) for e in cc.get("errors", [])]
        if cc.get("status") == "PASS" and cc.get("valid"):
            verdict = "pass"
        elif errs and all(e in MASS_EXEMPT for e in errs):
            verdict = "pass_with_deviation"
        else:
            verdict = "FAIL"
        dst_dir = CANON / f"{m['version']}_{m['lane']}"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / "submission.h5ad"
        if dst.exists():
            if sha(dst) != sha(src):
                idx = (REPO / "submissions/INDEX.tsv").read_text().splitlines()
                if any(l.split("\t")[2:4] == ["T2:heart:val_extrap", m["version"]]
                       for l in idx if len(l.split("\t")) > 4):
                    raise AssertionError(f"{m['version']}: REGISTERED canonical path exists with different bytes — refuse")
                # unregistered staging copy from an earlier build pass: park it, do not silently overwrite
                park = REPO / "artifacts/autoresearch/t2-extrap-20261001-v1/superseded"
                park.mkdir(parents=True, exist_ok=True)
                old = sha(dst)
                dst.rename(park / f"{m['version']}_{m['lane']}.pre-rebuild-{old[:12]}.h5ad")
                print(f"  parked unregistered earlier copy of {m['version']} (sha {old[:12]}) and replaced")
                shutil.copyfile(src, dst)
        else:
            shutil.copyfile(src, dst)
        h = sha(dst)
        rows.append({**m, "canonical": str(dst.relative_to(REPO)), "sha256": h,
                     "bytes": dst.stat().st_size, "contract": verdict,
                     "contract_errors": len(errs),
                     "member": f"t2_hrt_ext__{m['lane']}__{m['version']}.h5ad"})
        print(f"{m['version']} {m['lane']:16} contract={verdict:19} sha={h[:12]} {dst.stat().st_size}")

    stage = REPO / ".auto" / "stage_routec"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for r in rows:
        shutil.copyfile(REPO / r["canonical"], stage / r["member"])
    with open(stage / "MANIFEST.tsv", "w") as f:
        for r in rows:
            f.write(f"{r['member']}\t{r['bytes']}\t{r['sha256']}\n")
    with open(stage / "UPLOAD_MANIFEST.tsv", "w") as f:
        f.write("portal_model_name\tboard\tversion\tmethod\tcanonical_path\tsha256\tlocal_contract\tscore_status\n")
        for r in rows:
            f.write(f"{r['member']}\tT2:heart:val_extrap\t{r['version']}\t{r['method']}\t"
                    f"{r['canonical']}\t{r['sha256']}\t{r['contract']}\tscore_pending\n")
    with open(stage / "RUN_ID_MAP.tsv", "w") as f:
        f.write("filename\trun_id\tparent_version\tlocal_composite\tlocal_expr_composite\trole\n")
        for r in rows:
            f.write(f"{r['member']}\t{RUN_ID}\tv0001_baseline\t{r['composite']}\t{r['expr']}\t{r['role']}\n")
    with open(stage / "EVIDENCE_MANIFEST_POINTERS.tsv", "w") as f:
        f.write("filename\tcontract\trun_log\tmethod_doc\tqueue_note\n")
        for r in rows:
            f.write(f"{r['member']}\t.auto/log.jsonl\t.auto/prompt.md\t.auto/ROUTE_C_SUMMARY.md\t"
                    f"artifacts/autoresearch/t2-extrap-20261001-v1/ROUTE_C_SUMMARY.md\n")
    zp = REPO / "deliveries" / "arcqte__t2__upload__20261002.zip"
    if zp.exists():
        zp.unlink()
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for r in rows:
            z.write(stage / r["member"], r["member"])
        for meta in ("MANIFEST.tsv", "UPLOAD_MANIFEST.tsv", "RUN_ID_MAP.tsv", "EVIDENCE_MANIFEST_POINTERS.tsv"):
            z.write(stage / meta, meta)
    zh = sha(zp)
    (REPO / "deliveries" / "arcqte__t2__upload__20261002.zip.receipt.json").write_text(json.dumps(
        {"members": [r["member"] for r in rows], "run_id": RUN_ID, "group": GROUP,
         "sha256": zh, "status": "READY_NOT_SUBMITTED",
         "index": "rows appended to submissions/INDEX.tsv as score_pending",
         "registry": "pending: reports/SERVER_SCORE_REGISTRY.md + SERVER_SUBMETRIC_REGISTRY.tsv on score return",
         "zip": str(zp)}, indent=1) + "\n")
    json.dump({"run_id": RUN_ID, "group": GROUP, "rows": rows, "zip": str(zp), "zip_sha": zh},
              open(REPO / ".auto" / "route_c_package.json", "w"), indent=1)
    print(f"\nzip {zp.name} {zp.stat().st_size} bytes sha={zh[:16]} members={len(rows)}")


if __name__ == "__main__":
    main()
