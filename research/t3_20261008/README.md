# T3 2026-10-08 implementation — incremental code release

This first commit publishes the available original Python implementations for v0083–v0088 reconstruction, source intake, rejected v0086, seven-KO state-response v0087, conditional activation v0088, independent checks, and portable cached-asset replay. Reports, aggregate provenance, manifests and license review follow in the next commit.

No large datasets, models or prediction binaries are included. Cell-level membership/filter tables are also excluded from the public release. The portable entrypoint is `python research/t3_20261008/portable/replay.py --help`; exact replay requires separately supplied hash-verified cached assets. Fresh training from a public clone is NOT yet a verified turnkey workflow. Historical scripts retain their original paths and must not be mistaken for portable fresh-clone commands.

The full-package synthetic checks and exact cached-array v0087/v0088 replay have passed locally and independently. This code-only intermediate commit omits the snapshot inventory consumed by `portable/test_lightweight.py`; run that aggregate test after the evidence follow-up is published. No new training or competition submission was made.

Scored identities remain in `submissions/INDEX.tsv`; official score records remain in `reports/SERVER_SCORE_REGISTRY.md`. v0088 is selected, v0086 is rejected, and no historical prediction is replaced.
