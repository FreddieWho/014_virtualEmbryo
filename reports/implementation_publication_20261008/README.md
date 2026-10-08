# 2026-10-08 implementation publication

## Included

- [T3 implementation and evidence](../../research/t3_20261008/README.md): v0083–v0085 reconstruction/source intake, rejected v0086, seven-KO embryonic state-response v0087, conditional-activation v0088; frozen original source, portable cached-array replay, tests, provenance, permissions and original/published hashes
- [T2 E14.5 endpoint work](../../scripts/t2_heart_extra_20261008/README.md): v0036 endpoint-rank implementation, failed flow/graph/Hermite controls, 42 historical scorer reports, exact replay/refit and endpoint extraction checks; [portable code](../../scripts/t2_heart_extra_20261008/)
- [Local/server calibration audit](../../research/20261008/calibration/README.md): self-contained small research evidence, focused dated candidate receipts, portable recomputation, dependencies, 11 relocation/regression tests and explicit uncertainty
- Source acquisition/provenance additions in [SOURCE_INDEX_ADDITIONS.tsv](SOURCE_INDEX_ADDITIONS.tsv); existing coordination history, root summaries and registries are left unchanged by this release

The first incremental commit published 69 T3 Python files and an explicit code-only README. This follow-up adds the aggregate evidence and the remaining T2/calibration work. Refer to each package's inventory and exclusion manifest for exact coverage, not old full-packet inventories preserved as historical evidence.

## Preserved outcomes and identities

The authoritative candidate identity/hash store is [submissions/INDEX.tsv](../../submissions/INDEX.tsv); server outcomes are [reports/SERVER_SCORE_REGISTRY.md](../SERVER_SCORE_REGISTRY.md). No existing candidate hash or scientific score was changed. The existing T2 v0036 row schema inconsistency (kind=scored, score_status=registered) is disclosed but not changed by this narrowed release. T3 v0088 remains selected; rejected v0086 and T2 v0036 remain negative results. T2 v0030 remains incumbent and v0032 the numeric-high tie backup. No new competition submissions or training experiments were performed.

## Reproduction boundaries and exclusions

- Large public datasets, model binaries, frozen arrays and prediction H5ADs are excluded. Public source URLs, SHA256, permits and documented rebuild/acquisition steps are supplied where available; authenticated official challenge inputs remain the user's responsibility
- Cell-level membership/filter/row-ledger payloads are excluded, with original hashes retained; they must be regenerated from authorized source data or supplied separately. No denied payload was republished in a different format
- T3 exact cached-asset inference was verified, but a complete public fresh-training reconstruction was not verified. The missing/omitted inputs and unverified end-to-end fitting/GO steps are explicit in the T3 reproduction guide
- T2 selected-model refit and replay reproduce expression, row/gene identities and geometry exactly; H5AD container bytes are not claimed identical. Historical v0030 is a recipe reconstruction, not the unavailable original artifact
- Calibration is retrospective/adaptive and cross-domain. Seeds/overlapping strata are not independent server trials; no universal false-negative rate or local-to-server correction is claimed
- Private notes, internal messages, accounts/credentials, signed URLs, caches and raw internal execution logs are not part of this publication

## Verification

See [verification report](VERIFICATION.md), per-package test receipts, inventories and original/final hash mappings. These focused tests are not a claim that the complete historical repository test suite passes from a public clone.
