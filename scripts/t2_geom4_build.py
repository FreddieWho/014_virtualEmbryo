#!/usr/bin/env python3
"""Build the four frozen T2 geometry candidates. No held-out targets."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "docs" / "batch3" / "interfaces"))

from virtual_embryo_tools import contract_io  # noqa: E402

FORBIDDEN = ("E7.5", "E7.75", "E8.5", "E10.5", "E12.5")
SCORER_LOCK = ROOT / "artifacts/tool_integration/P0-LOCK/locks/SCORER_LOCK.json"
OUT = ROOT / "artifacts/t2_geom4_20261007-v1"
RUN_ID = "T2-GEOM4-20261007-v1"

LANES = [
    {
        "board_key": "T2:heart:val_interp",
        "contract_board": "heart:val_interp",
        "board_dir": "T2_heart_val_interp",
        "board_short": "hrt_int",
        "version": "v0023",
        "method": "h_aniso50",
        "kind": "aniso",
        "t": 0.5,
        "parent_version": "v0019",
        "parent": "submissions/candidates/T2_heart_val_interp/v0019_h_o1_shrinkmerge/submission.h5ad",
        "parent_sha": "d84de17486a6685cd0e82cec926c9710dbbd60d08900854e8f91dfd561012a92",
        "early": "data/E8.25_late.h5ad",
        "late": "data/E8.75.h5ad",
    },
    {
        "board_key": "T2:heart:val_interp",
        "contract_board": "heart:val_interp",
        "board_dir": "T2_heart_val_interp",
        "board_short": "hrt_int",
        "version": "v0024",
        "method": "h_qaxis",
        "kind": "qaxis",
        "t": 0.5,
        "parent_version": "v0019",
        "parent": "submissions/candidates/T2_heart_val_interp/v0019_h_o1_shrinkmerge/submission.h5ad",
        "parent_sha": "d84de17486a6685cd0e82cec926c9710dbbd60d08900854e8f91dfd561012a92",
        "early": "data/E8.25_late.h5ad",
        "late": "data/E8.75.h5ad",
    },
    {
        "board_key": "T2:heart:val_extrap",
        "contract_board": "heart:val_extrap",
        "board_dir": "T2_heart_val_extrap",
        "board_short": "hrt_ext",
        "version": "v0035",
        "method": "x_grows",
        "kind": "grows",
        "t": None,
        "parent_version": "v0030",
        "parent": "submissions/candidates/T2_heart_val_extrap/v0030_x_r3_medlib09/submission.h5ad",
        "parent_sha": "71f587ed68177b7cdbea27f27333523caa33668badc08efd782afb3d541d53a3",
        "early": "data/E8.25_late.h5ad",
        "mid": "data/E8.75.h5ad",
        "late": "data/E9.5.h5ad",
    },
    {
        "board_key": "T2:embryo:val_interp",
        "contract_board": "embryo:val_interp",
        "board_dir": "T2_embryo_val_interp",
        "board_short": "emb_int",
        "version": "v0018",
        "method": "e_qaxis",
        "kind": "qaxis",
        "t": (7.5 - 7.25) / (8.0 - 7.25),
        "parent_version": "v0014",
        "parent": "submissions/candidates/T2_embryo_val_interp/v0014_e_o1_shrinkmerge/submission.h5ad",
        "parent_sha": "1ea0c69631d59ae5d9909a9b1878f820c74c50c4a89dc009fd1bcf349c71677d",
        "early": "data/E7.25.h5ad",
        "late": "data/E8.0.h5ad",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_xyz(path: Path) -> np.ndarray:
    if any(tok in path.name for tok in FORBIDDEN):
        raise SystemExit(f"refusing held-out path: {path}")
    with h5py.File(path, "r") as handle:
        xyz = np.asarray(handle["obsm"]["spatial_3D"][:, :3], dtype=np.float64)
    if not np.isfinite(xyz).all():
        raise SystemExit(f"non-finite coordinates: {path}")
    return xyz


def center_rms(cloud: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    mu = cloud.mean(axis=0)
    centered = cloud - mu
    rms = float(np.sqrt((centered ** 2).sum(axis=1).mean()))
    return centered, mu, rms


def spectrum(cloud: np.ndarray) -> np.ndarray:
    centered, _, rms = center_rms(cloud)
    _, singular, _ = np.linalg.svd(centered, full_matrices=False)
    lam = (singular ** 2) / centered.shape[0]
    return np.sqrt(lam) / rms


def warp_to(cloud: np.ndarray, target_aspects: np.ndarray, target_rms: float) -> np.ndarray:
    centered, mu, _ = center_rms(cloud)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    aspects = spectrum(cloud)
    stretched = ((centered @ vt.T) * (target_aspects / aspects)) @ vt
    restored = stretched * (target_rms / float(np.sqrt((stretched ** 2).sum(axis=1).mean())))
    return restored + mu


def aniso(inc: np.ndarray, early: np.ndarray, late: np.ndarray, t: float) -> np.ndarray:
    _, _, rms = center_rms(inc)
    target = (1.0 - t) * spectrum(early) + t * spectrum(late)
    return warp_to(inc, target, rms)


def canonical(cloud: np.ndarray):
    centered, mu, rms = center_rms(cloud)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    return (centered @ vt.T) / rms, vt, mu, rms


def qaxis(inc: np.ndarray, early: np.ndarray, late: np.ndarray, t: float) -> np.ndarray:
    z_i, vt, mu, rms = canonical(inc)
    z_e, _, _, _ = canonical(early)
    z_l, _, _, _ = canonical(late)
    skew_i = (z_i ** 3).mean(axis=0)
    for z in (z_e, z_l):
        skew = (z ** 3).mean(axis=0)
        for axis in range(3):
            if abs(skew[axis]) >= 1e-8 and abs(skew_i[axis]) >= 1e-8 and skew[axis] * skew_i[axis] < 0:
                z[:, axis] *= -1
    n = z_i.shape[0]
    out = np.empty_like(z_i)
    for axis in range(3):
        order = np.argsort(z_i[:, axis], kind="mergesort")
        percent = np.empty(n)
        percent[order] = (np.arange(n) + 0.5) / n
        out[:, axis] = (1.0 - t) * np.quantile(z_e[:, axis], percent) + t * np.quantile(z_l[:, axis], percent)
    spatial = (out * rms) @ vt + mu
    centered, _, rms2 = center_rms(spatial)
    return centered * (rms / rms2) + mu


def ols(y: np.ndarray, time: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(time)), time])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return coef


def grows(inc: np.ndarray, stages: list[np.ndarray]) -> tuple[np.ndarray, dict]:
    time = np.array([8.25, 8.75, 9.5])
    rms = np.array([center_rms(s)[2] for s in stages])
    aspects = np.vstack([spectrum(s) for s in stages])
    log_coef = ols(np.log(rms), time)
    pred_rms = float(np.exp(log_coef[0] + log_coef[1] * 10.5))
    _, _, inc_rms = center_rms(inc)
    ratio = pred_rms / inc_rms
    raw = np.array([float(ols(aspects[:, i], time)[0] + ols(aspects[:, i], time)[1] * 10.5) for i in range(3)])
    notes = {"pred_rms": pred_rms, "inc_rms": inc_rms, "ratio": ratio, "raw_aspects": raw.tolist()}
    if np.any(raw <= 0):
        target_aspects = spectrum(inc)
        notes["shape"] = "SHAPE_HELD"
    else:
        target_aspects = raw / np.sqrt((raw ** 2).sum())
        notes["shape"] = "EXTRAPOLATED"
    if 0.75 <= ratio <= 1.25:
        target_rms = pred_rms
        notes["scale"] = "EXTRAPOLATED"
    else:
        target_rms = inc_rms
        notes["scale"] = "SCALE_HELD"
    notes["target_aspects"] = target_aspects.tolist()
    notes["target_rms"] = target_rms
    return warp_to(inc, target_aspects, target_rms), notes


def self_check() -> None:
    rng = np.random.default_rng(0)
    cloud = rng.normal(size=(40, 3))
    early = cloud * np.array([1.2, 0.8, 1.0])
    late = cloud * np.array([0.7, 1.1, 1.3])
    out = aniso(cloud, early, late, 0.5)
    _, _, r0 = center_rms(cloud)
    _, _, r1 = center_rms(out)
    if abs(r1 / r0 - 1) > 1e-8:
        raise SystemExit("aniso RMS lock failed on synthetic data")
    out_q = qaxis(cloud, early, late, 0.5)
    _, _, r2 = center_rms(out_q)
    if abs(r2 / r0 - 1) > 1e-8:
        raise SystemExit("qaxis RMS lock failed on synthetic data")


def build_coords(spec: dict) -> tuple[np.ndarray, dict]:
    inc = load_xyz(ROOT / spec["parent"])
    if spec["kind"] == "grows":
        stages = [load_xyz(ROOT / spec[k]) for k in ("early", "mid", "late")]
        coords, notes = grows(inc, stages)
        return coords, notes
    early = load_xyz(ROOT / spec["early"])
    late = load_xyz(ROOT / spec["late"])
    if spec["kind"] == "aniso":
        coords = aniso(inc, early, late, spec["t"])
    else:
        coords = qaxis(inc, early, late, spec["t"])
    _, _, r0 = center_rms(inc)
    _, _, r1 = center_rms(coords)
    if abs(r1 / r0 - 1) > 1e-8:
        raise SystemExit(f"{spec['method']}: RMS lock failed")
    return coords, {"rms_rel": abs(r1 / r0 - 1)}


def main() -> None:
    self_check()
    index_text = (ROOT / "submissions/INDEX.tsv").read_text()
    for spec in LANES:
        if f"\t{spec['board_key']}\t{spec['version']}\t" in index_text:
            raise SystemExit(f"version already registered: {spec['board_key']} {spec['version']}")
        parent = ROOT / spec["parent"]
        if sha256(parent) != spec["parent_sha"]:
            raise SystemExit(f"parent sha mismatch: {parent}")
        dest = ROOT / "submissions/candidates" / spec["board_dir"] / f"{spec['version']}_{spec['method']}" / "submission.h5ad"
        if dest.exists():
            raise SystemExit(f"refusing to overwrite {dest}")

    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for spec in LANES:
        coords, notes = build_coords(spec)
        parent = ROOT / spec["parent"]
        dest = ROOT / "submissions/candidates" / spec["board_dir"] / f"{spec['version']}_{spec['method']}" / "submission.h5ad"
        import anndata as ad
        parent_ad = ad.read_h5ad(parent)
        row_names = [str(x) for x in parent_ad.obs_names]
        backed = getattr(parent_ad, "file", None)
        if backed is not None:
            backed.close()
        contract_io.write_candidate_from_parent(
            parent_path=parent,
            output_path=dest,
            spatial_3d=coords,
            row_names=row_names,
            normalization="log_normalized",
            parent_sha256=spec["parent_sha"],
            metadata_updates={"ve_t2_geom4": json.dumps({"run": RUN_ID, "method": spec["method"], **notes}, sort_keys=True)},
        )
        report = contract_io.validate_h5ad_contract(
            dest, task="T2", board=spec["contract_board"], scorer_lock=SCORER_LOCK,
            parent_path=parent, parent_sha256=spec["parent_sha"],
        )
        if report["status"] != "PASS":
            raise SystemExit(f"contract FAIL {spec['method']}: {report['errors']}")
        digest = sha256(dest)
        portal = f"t2_{spec['board_short']}__{spec['method']}__{spec['version']}.h5ad"
        if len(portal) > 50:
            raise SystemExit(f"name too long: {portal}")
        row = {
            **{k: spec[k] for k in ("board_key", "version", "method", "parent_version")},
            "path": str(dest.relative_to(ROOT)),
            "sha256": digest,
            "bytes": dest.stat().st_size,
            "portal": portal,
            "notes_mech": notes,
            "n_obs": int(coords.shape[0]),
        }
        results.append(row)
        print(json.dumps({"method": spec["method"], "sha256": digest, "contract": "PASS", "notes": notes}, default=str), flush=True)

    (OUT / "BUILD.json").write_text(json.dumps(results, indent=2, default=str) + "\n")
    index_path = ROOT / "submissions/INDEX.tsv"
    fresh = index_path.read_text()
    extra = []
    for row in results:
        if f"\t{row['board_key']}\t{row['version']}\t" in fresh:
            raise SystemExit(f"race: {row['version']} appeared during build")
        note = (
            f"{RUN_ID} {row['method']}: geometry-only, expression locked to {row['parent_version']}; "
            f"contract PASS; score_pending; not a server claim; artifacts/t2_geom4_20261007-v1/"
        )
        extra.append(
            "\t".join([
                "candidate", RUN_ID, row["board_key"], row["version"], row["method"], row["path"],
                str(row["n_obs"]), "500" if "heart" in row["board_key"] else "498",
                "none", "false", "pass", row["sha256"], "", "score_pending", note,
            ])
        )
    with index_path.open("a") as handle:
        if not fresh.endswith("\n"):
            handle.write("\n")
        handle.write("\n".join(extra) + "\n")

    zip_path = ROOT / "deliveries/t2geom__t2__upload__20261007.zip"
    if zip_path.exists():
        raise SystemExit(f"zip exists: {zip_path}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED) as zf:
        manifest, upload, runmap, evid = [], [
            "portal_model_name\tboard\tversion\tmethod\tcanonical_path\tsha256\tlocal_contract\tscore_status\n"
        ], ["filename\trun_id\tparent_version\n"], ["filename\tfreeze\tbuild\n"]
        for row in results:
            src = ROOT / row["path"]
            zf.write(src, row["portal"])
            manifest.append(f"{row['portal']}\t{row['bytes']}\t{row['sha256']}")
            upload.append(
                f"{row['portal']}\t{row['board_key']}\t{row['version']}\t{row['method']}\t{row['path']}\t{row['sha256']}\tpass\tscore_pending\n"
            )
            runmap.append(f"{row['portal']}\t{RUN_ID}\t{row['parent_version']}\n")
            evid.append(f"{row['portal']}\treports/T2_GEOM4_FREEZE_20261007.md\tartifacts/t2_geom4_20261007-v1/BUILD.json\n")
        zf.writestr("MANIFEST.tsv", "filename\tbytes\tsha256\n" + "\n".join(manifest) + "\n")
        zf.writestr("UPLOAD_MANIFEST.tsv", "".join(upload))
        zf.writestr("RUN_ID_MAP.tsv", "".join(runmap))
        zf.writestr("EVIDENCE_MANIFEST_POINTERS.tsv", "".join(evid))
    with zipfile.ZipFile(zip_path) as zf:
        if zf.testzip() is not None:
            raise SystemExit("zip crc failed")
        for row in results:
            if hashlib.sha256(zf.read(row["portal"])).hexdigest() != row["sha256"]:
                raise SystemExit(f"zip sha mismatch {row['portal']}")
    receipt = {"zip": str(zip_path.relative_to(ROOT)), "sha256": sha256(zip_path), "status": "READY_NOT_SUBMITTED", "n": 4}
    (zip_path.parent / (zip_path.name + ".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
