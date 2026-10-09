"""Component variant harness for the T3 v0088 composite loop.

Applies exactly one documented substitution to the frozen emitter, re-runs the
adapted frozen evaluator against the rebuilt model, and reports the composite.

The archived research/t3_20261008 snapshots are never modified: every variant
lives in its own directory with its own emitter copy.

Metric: skill-weighted composite total for one arm, 7 held-out genotypes x 3 seeds.
Weights replicate frozen evaluate_source.py:
    de .30 / direction .25 / severity_abs .25 / mmd .12 / variogram .08
Direction: higher_is_better.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SNAP = Path("/home/huyudi/014_virtualEmbryo/research/t3_20261008/snapshots/v0088")
VEC = Path("/home/huyudi/vework/variants")
PY = "/home/huyudi/vework/ve-t3/bin/python"

WEIGHTS = {
    "de_skill": 0.30,
    "direction_skill": 0.25,
    "severity_abs_skill": 0.25,
    "mmd_skill": 0.12,
    "variogram_skill": 0.08,
}

# Frozen emitter anchors that variants substitute exactly once.
ANCHORS = {
    "propensity_penalty": (
        "penalty = .1 * max(float(np.trace(c))/len(l), 1.)",
        "penalty = {v} * max(float(np.trace(c))/len(l), 1.)",
    ),
    "propensity_min_cells": (
        "if len(rows) < 20: continue",
        "if len(rows) < {v}: continue",
    ),
    "composition_clip": (
        "mass*=np.exp(np.clip(response['composition'],-2,2))",
        "mass*=np.exp(np.clip(response['composition'],-{v},{v}))",
    ),
    "detection_offset": (
        "frac=np.clip((local[:,j]>0).mean()+d[-1],0,1)",
        "frac=np.clip((local[:,j]>0).mean()+{v}*d[-1],0,1)",
    ),
    "zero_frac_scale": (
        "frac=np.clip((local[:,j]>0).mean()+d[-1],0,1)",
        "frac=np.clip({v}*(local[:,j]>0).mean()+d[-1],0,1)",
    ),
}


def build_variant(name, axis, value):
    """Materialize an isolated variant tree; returns its directory."""
    root = VEC / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)

    for f in ["emitter_v88.py", "crossko.py", "crossko_hurdle_v2.py", "PROTOCOL.md"]:
        shutil.copy(SNAP / f, root / f)

    code = (root / "emitter_v88.py").read_text()
    if axis != "frozen":
        old_t, new_t = ANCHORS[axis]
        assert code.count(old_t) == 1, (axis, code.count(old_t))
        code = code.replace(old_t, new_t.format(v=value))
    (root / "emitter_v88.py").write_text(code)

    # Evaluator with the same two frozen path substitutions as the baseline run.
    ev = (SNAP / "evaluate_source.py").read_text()
    ev = ev.replace(
        "R=Path('/workspace/shared/t3_v87_restored')",
        "R=Path('/home/huyudi/vework/rebuilt_model')",
    )
    ev = ev.replace(
        "'/workspace/shared/t3repo/third_party/veckit'",
        repr("/home/huyudi/014_virtualEmbryo/third_party/veckit"),
    )
    (root / "evaluate_source_local.py").write_text(ev)

    # Shared read-only inputs.
    (root / "source_panel").symlink_to("/home/huyudi/vework/prepared/source_panel")
    (root / "source_evaluation").mkdir()

    # Reuse the verified response cache; it is independent of the emitter variant.
    src = Path("/home/huyudi/vework/eval/baseline_reference")
    for f in ["embryo_responses.npz", "embryo_responses.json", "CACHE_INPUTS.json"]:
        shutil.copy(src / f, root / "source_evaluation" / f)

    receipt = {
        "variant": name,
        "axis": axis,
        "value": value,
        "original_emitter_sha256": hashlib.sha256((SNAP / "emitter_v88.py").read_bytes()).hexdigest(),
        "variant_emitter_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "response_cache": "reused from baseline; independent of emitter",
    }
    (root / "VARIANT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return root


def evaluate(root, arm="conditional"):
    proc = subprocess.run(
        [PY, str(root / "evaluate_source_local.py")],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    summary = root / "source_evaluation" / "summary.csv"
    if proc.returncode != 0 or not summary.exists():
        return None, proc.stderr[-1500:]

    import pandas as pd

    frame = pd.read_csv(summary)
    totals = {}
    for m in sorted(set(frame.model)):
        g = frame[frame.model == m]
        totals[m] = sum(g[k].mean() * w for k, w in WEIGHTS.items())
    g = frame[frame.model == arm]
    return {
        "arm": arm,
        "total": totals[arm],
        "all_arms": totals,
        "components": {k: float(g[k].mean()) for k in WEIGHTS},
    }, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True)
    ap.add_argument("--axis", default="frozen")
    ap.add_argument("--value", default="0")
    ap.add_argument("--arm", default="conditional")
    a = ap.parse_args()

    root = build_variant(a.name, a.axis, a.value)
    result, err = evaluate(root, a.arm)
    if result is None:
        print(json.dumps({"variant": a.name, "status": "metric-error", "error": err}))
        sys.exit(2)
    result["variant"] = a.name
    result["axis"] = a.axis
    result["value"] = a.value
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()