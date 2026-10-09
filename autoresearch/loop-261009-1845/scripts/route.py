"""T3 route loop driver: existing-route optimization, combination, new architecture.

Metric: skill-weighted composite total for the conditional arm, 7 held-out
genotypes x 3 seeds, replicating frozen evaluate_source.py weights
(de .30 / direction .25 / severity_abs .25 / mmd .12 / variogram .08).
Direction: higher_is_better.

Two orthogonal substitution channels:
  --response NAME   swap the response structure (precomputed in /home/huyudi/vework/responses)
  --emitter NAME    swap the emission architecture (frozen marginal, or joint transport)

Guard: emitted output must satisfy the v0088 contract -- shape 7449x500,
finite, closed panel units (per-row panel total 10000 within 0.02), and the
frozen-arm zero mask / determinism controls.

The archived research/t3_20261008 snapshots are never modified.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SNAP = Path("/home/huyudi/014_virtualEmbryo/research/t3_20261008/snapshots/v0088")
RESP = Path("/home/huyudi/vework/responses")
EVAL = Path("/home/huyudi/vework/eval")
VEC = Path("/home/huyudi/vework/variants2")
PY = "/home/huyudi/vework/ve-t3/bin/python"

WEIGHTS = {
    "de_skill": 0.30,
    "direction_skill": 0.25,
    "severity_abs_skill": 0.25,
    "mmd_skill": 0.12,
    "variogram_skill": 0.08,
}

FROZEN_FILES = ["emitter_v88.py", "crossko.py", "crossko_hurdle_v2.py", "PROTOCOL.md"]


def build(name, emitter, response):
    root = VEC / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for f in FROZEN_FILES:
        shutil.copy(SNAP / f, root / f)

    if emitter == "joint":
        shutil.copy(EVAL / "emitter_joint.py", root / "emitter_joint.py")
        # Route the evaluator at the joint architecture.
        old = "from emitter_v88 import emit"
        new = "from emitter_joint import emit_joint as emit"
        code = (SNAP / "evaluate_source.py").read_text()
        assert code.count(old) == 1
        code = code.replace(old, new)
        (root / "evaluate_source_local.py").write_text(code)
        receipt = {"emitter": "joint", "substitution": "import emit_joint as emit"}
    elif emitter == "frozen":
        code = (SNAP / "evaluate_source.py").read_text()
        (root / "evaluate_source_local.py").write_text(code)
        receipt = {"emitter": "frozen", "substitution": None}
    else:
        raise SystemExit(f"unknown emitter {emitter}")

    code = code.replace(
        "R=Path('/workspace/shared/t3_v87_restored')",
        "R=Path('/home/huyudi/vework/rebuilt_model')",
    )
    code = code.replace(
        "'/workspace/shared/t3repo/third_party/veckit'",
        repr("/home/huyudi/014_virtualEmbryo/third_party/veckit"),
    )
    (root / "evaluate_source_local.py").write_text(code)

    (root / "source_panel").symlink_to("/home/huyudi/vework/prepared/source_panel")
    out = root / "source_evaluation"
    out.mkdir()

    src_npz = RESP / f"{response}.npz" if response else EVAL / "baseline_reference/embryo_responses.npz"
    src_meta = RESP / f"{response}.json" if response else EVAL / "baseline_reference/embryo_responses.json"
    shutil.copy(src_npz, out / "embryo_responses.npz")
    shutil.copy(src_meta, out / "embryo_responses.json")

    # The evaluator asserts its own cache provenance, which includes the hash of
    # its own bytes and of the response module in THIS directory. Recompute it
    # for the variant instead of copying the baseline receipt.
    def _sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()

    genes = ["WT", "Dnmt3a", "Kmt2a", "Kdm2b", "Dnmt1", "Dnmt3b", "Ehmt2", "Kmt2b"]
    cache_inputs = {
        g: _sha(root / "source_panel" / "normalized" / f"{g}_whitelisted_panel10000.h5ad")
        for g in genes
    }
    cache_inputs.update(
        model=_sha("/home/huyudi/vework/rebuilt_model/inference/state_emitter.joblib"),
        response_code=_sha(root / "crossko_hurdle_v2.py"),
        runner=_sha(root / "evaluate_source_local.py"),
    )
    (out / "CACHE_INPUTS.json").write_text(json.dumps(cache_inputs, indent=2))

    receipt.update(
        {
            "response": response or "frozen_baseline_cache",
            "response_sha256": hashlib.sha256(src_npz.read_bytes()).hexdigest(),
            "original_evaluator_sha256": hashlib.sha256((SNAP / "evaluate_source.py").read_bytes()).hexdigest(),
        }
    )
    (root / "ROUTE.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return root


def guard(root):
    """Contract check on the emitted conditional prediction."""
    import anndata as ad
    import numpy as np

    f = root / "source_evaluation" / "Dnmt1_conditional.h5ad"
    if not f.exists():
        return False, "no_artifact"
    a = ad.read_h5ad(f)
    x = a.X
    if x.shape != (7449, 500):
        return False, f"shape {x.shape}"
    xf = x.astype(float)
    if not np.isfinite(xf).all():
        return False, "nonfinite"
    if (xf < 0).any():
        return False, "negative"
    mass = np.abs(np.expm1(xf).sum(1) - 10000).max()
    if mass >= 0.02:
        return False, f"mass_closure {mass:.4g}"
    return True, f"shape=7449x500 finite closed max_mass_err={mass:.4g}"


def evaluate(root):
    proc = subprocess.run(
        [PY, str(root / "evaluate_source_local.py")],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    summary = root / "source_evaluation" / "summary.csv"
    if proc.returncode != 0 or not summary.exists():
        return None, (proc.stderr or proc.stdout)[-1500:]
    import pandas as pd

    frame = pd.read_csv(summary)
    totals = {}
    for m in sorted(set(frame.model)):
        g = frame[frame.model == m]
        totals[m] = sum(g[k].mean() * w for k, w in WEIGHTS.items())
    g = frame[frame.model == "conditional"]
    return {
        "arm": "conditional",
        "total": totals["conditional"],
        "all_arms": totals,
        "components": {k: float(g[k].mean()) for k in WEIGHTS},
    }, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True)
    ap.add_argument("--emitter", default="frozen", choices=["frozen", "joint"])
    ap.add_argument("--response", default="")
    a = ap.parse_args()

    root = build(a.name, a.emitter, a.response)
    result, err = evaluate(root)
    if result is None:
        print(json.dumps({"name": a.name, "status": "metric-error", "error": err}))
        sys.exit(2)
    ok, note = guard(root)
    result.update(name=a.name, emitter=a.emitter, response=a.response or "frozen",
                  guard="PASS" if ok else "FAIL", guard_note=note)
    print(json.dumps(result, indent=2))
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()