# Local/server calibration audit, 2026-10-08

Publication destination: `research/20261008/calibration/`.

This is a frozen research audit of existing T2/T3 results. No training, inference,
new scoring, portal operations, or submissions are needed or performed. The audit
supports local-score **prioritization**, not a universal rejection threshold or a
constant local-to-server correction. See [Chinese summary](README_中文.md),
[T2 report](t2/REPORT.md), [T3 report](t3/REPORT.md), and
[independent review](INDEPENDENT_REVIEW.md).

## Recompute using only this directory

Tested with Python 3.12.14 and the pinned dependencies in `requirements.txt`.
Install dependencies in your preferred isolated Python environment, then run:

```bash
python -m pip install -r requirements.txt
python analyze.py
python -m unittest discover -s tests -v
python verify_manifest.py
```

`python analyze.py` writes to `recomputed/t2/` and `recomputed/t3/`. It does not
replace the frozen `t2/` and `t3/` publication outputs. Run from any working directory
by supplying the absolute path to `analyze.py`. No network access is used by the
analysis or tests; dependency installation is a separate setup step.

```bash
python /path/to/calibration/analyze.py --output-dir /tmp/calibration-results
python analyze.py --task t3
python t2/analyze.py --evidence-dir /path/to/evidence --output-dir /tmp/t2-audit
```

The shared `config.json` controls evidence/output paths, bootstrap count (10,000)
and random seed (20261008). Config-relative paths are resolved against the config
file, while explicit CLI paths are resolved against the calling directory.
Changing bootstrap settings changes the descriptive bootstrap intervals.
The bootstrap/binomial intervals are nominal sensitivities on dependent selected
candidates, not calibrated future prediction guarantees.

## What is reproducible from recorded results here

- T2: all historical 17-row statistics and threshold counterfactuals; the complete
  36-row heart-extrapolation inclusion audit; expansion of 42 frozen score JSONs
  into 966 metric records (33 development calls, nine reserve calls)
- T3: 106 source-local/server records; all rank/dominance counterfactuals; current
  v88/v87 deltas; independent aggregation of all 390 frozen-donor rows; original
  frozen-donor source-code hash check
- Relocation test: copies the package to a new directory, runs from an unrelated
  working directory, and checks every generated CSV and summary against the
  publication outputs

Historical candidate identity and score joins use focused, static projections in
`evidence/registries/`. These are input receipts for this dated audit, **not a new
registry**. Candidate identities remain authoritative at repository-root
`submissions/INDEX.tsv`; official server results remain authoritative at
`reports/SERVER_SCORE_REGISTRY.md` and `reports/SERVER_SUBMETRIC_REGISTRY.tsv`.

T3 publishes only the 26 candidate/parent rows needed by the 106 audit records.
Historical 87-candidate/78-scored coverage totals are retained as metadata; the
complete T3 score history is not duplicated. T2's 36 heart-extrapolation rows are
needed for the all-candidate inclusion/exclusion audit; unrelated boards are
excluded except eight embryo-v2 submetric rows supporting the scale example.

## What requires the original source cache

This package recomputes **audit tables from recorded evidence**, not biological
predictions or the original scorer outputs. Exact historical artifact rescoring
would additionally require the original candidate H5AD bytes, released expression
and spatial data, source/target partitions, fixed scorer code and its environment.
Some original historical artifact bytes were already unavailable during the audit.
There is no claim that copying those caches would recover every missing original.

`evidence/t3repo/.auto/` contains a narrow allowlist of historical composite
research outputs, formula/configuration and provenance scripts, never execution
logs. `calibrate_composite.py` is an archival recipe, not a supported standalone
entry point, and it retains historical assumptions. The frozen-donor
`recheck_frozen_donors.py` is byte-identical archival code so its hash can be checked
against the protocol; it retains original cache paths and imports. Do not run these
archival recipes as part of lightweight reproduction. The supported portable
entry points are the three `analyze.py` files.

Related source reconstruction packages are repository-root
`research/t3_20261008/` and `scripts/t2_heart_extra_20261008/`, with T2 reports under
`reports/t2_heart_extra_20261008/`. Their presence does not make unavailable original
artifact bytes available and is not required for this audit.

## Omitted historical report text

All six historical Markdown reports previously copied under `evidence/` are
excluded. `provenance/EXCLUDED_SOURCE_RECEIPTS.json` retains their original
repository links and recorded original SHA256 values, without any report excerpts.
For these sources, T3 uses numerical values already present in the independently
audited analysis and frozen outputs. It recomputes their downstream calculations;
it does not re-extract, read or verify absent report text. Receipt hashes identify
original evidence and are explicitly not hashes recomputed from bundled bytes.
All JSON/TSV/CSV inputs required for the numerical calculations remain bundled.

## Provenance and exclusions

- `provenance/ORIGINAL_PACKAGE_SHA256.json`: original audit-package paths, sizes
  and hashes, including originals that were deliberately not republished
- `provenance/SOURCE_INVENTORY.json`: each source's logical origin, original hash,
  published file hash, scope and transformation; reports may have workstation paths
  normalized and account-scoped or unrelated personal-path references removed
- `provenance/EXCLUSIONS.json`: redundant registry/output omissions and excluded
  classes of material
- `provenance/FINAL_MANIFEST_SHA256.json`: every final publication file's hash;
  excludes itself, generated `recomputed/`, and Python bytecode caches
- `RUN_REPORT.md`: actual verification, original-value equivalence and limitations

Original hashes are retained even when publication text has been sanitized.
Bundled source IDs are evidence-relative, with published-byte hashes. Omitted historical reports use original repository URLs and recorded original hashes. Use the
source inventory to map those back to original-byte hashes. Frozen protocol hashes
are unchanged. The small original source summaries are recorded evidence; they do
not imply independent held-out biological validation.
