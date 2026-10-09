"""Path-only adapter for the frozen v0088 four-arm source evaluator.

Substitutes three local roots into the immutable archived evaluate_source.py so
the frozen composite local score can be computed against the rebuilt model.
No scientific parameter, weight or gate is touched.

Same minimal substitution set the archived run_source_from_pack.py performs.
"""
from pathlib import Path

ARCHIVED = Path(
    "/home/huyudi/014_virtualEmbryo/research/t3_20261008/snapshots/v0088/evaluate_source.py"
)
OUT = Path("/home/huyudi/vework/eval/evaluate_source_local.py")

REBUILD = "/home/huyudi/vework/rebuilt_model"
VECKIT = "/home/huyudi/014_virtualEmbryo/third_party/veckit"

SUBS = {
    "R=Path('/workspace/shared/t3_v87_restored')": f"R=Path('{REBUILD}')",
    "'/workspace/shared/t3repo/third_party/veckit'": repr(VECKIT),
}

code = ARCHIVED.read_text()
changes = []
for before, after in SUBS.items():
    n = code.count(before)
    assert n == 1, (before, n)
    code = code.replace(before, after)
    changes.append({"from": before, "to": after, "occurrences": n})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(code)
compile(code, str(OUT), "exec")

import hashlib
import json

(OUT.parent / "EVALUATOR_PATH_ADAPTER.json").write_text(
    json.dumps(
        {
            "scope": "Only model root and scorer import paths rebound; frozen evaluator file otherwise unchanged",
            "original_code_sha256": hashlib.sha256(ARCHIVED.read_bytes()).hexdigest(),
            "executed_code_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "path_only_substitutions": changes,
        },
        indent=2,
    )
    + "\n"
)
print("path_only_substitutions:", changes)
print("wrote", OUT)