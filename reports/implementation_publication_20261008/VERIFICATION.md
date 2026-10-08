# Publication verification

- T3 original-source snapshot hash inventory and synthetic suites passed; independent four-arm emission checks and exact cached v0087/v0088 inference (7449×500) passed
- T2 five synthetic tests passed; selected-model replay and refit have exact X/row/gene/geometry parity (maximum X difference 0); fresh endpoint extraction matches the recorded endpoint SHA
- Calibration 11 relocation/regression tests passed; default-bootstrap recomputation preserved all original scientific results, with donor means differing by at most 8.88e-16 floating-point roundoff
- Existing authoritative candidate identities, scores and registry files remain unchanged; the T2 v0036 legacy row schema inconsistency is not modified in this narrowed release
- No new model-selection experiments or competition submissions; bounded reproduction outputs only; existing coordination/AUDIT documents unchanged

Legacy regression spot-check: 35 passed, 1 failed after supplying the ignored official T3 gene-panel file. The failure is an existing `numpy.bool_ is True` identity assertion in tests/test_t2_controls.py, not modified by this release. A public clone without that ignored panel has four additional fixture failures (31 pass/5 fail); the untouched source-cache checkout reproduced the same five failures. Initial collection also required PYTHONPATH=.:docs/batch3/interfaces. No full historical test pass is claimed.

Command for the spot-check (from repository root, with authorized panel cache populated):

    PYTHONPATH=.:docs/batch3/interfaces python -m pytest -q tests/test_t2_baseline.py tests/test_t2_controls.py tests/test_t2_expression_model.py tests/test_t3_shift_transfer.py tests/test_t3_signed_response.py docs/batch3/interfaces/tests/test_contract_io.py docs/batch3/interfaces/tests/test_interface_contracts.py

No Actions workflows were present in the base checkout. Remote publication and exact-commit status are verified separately after the guarded ref update.

Frozen historical TSV/CSV/report bytes intentionally retain CRLF and terminal empty columns/spaces; broad git diff --check reports these as whitespace. Newly authored coordination/entrypoint/portable-wrapper paths pass the focused whitespace check. Historical bytes were not normalized because their recorded hashes must remain meaningful.
