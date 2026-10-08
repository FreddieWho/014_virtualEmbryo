# Publication verification, 2026-10-08

## Result

PASS. Lightweight audit reproduction is self-contained in this directory.
This package was prepared without modifying the integration checkout and without
training, inference, new scorer calls, network use, or submissions.

## Environment and commands actually exercised

- Python 3.12.14
- NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0 (already installed; no setup mutations)
- Full `analyze.py` run with the default 10,000 bootstrap resamples and fixed seed
- Both task-specific entry points, including T3 regeneration after final report
  sanitization so published source hashes identify the actual published bytes
- `python -m unittest discover -s tests -v`: all 11 tests PASS
- Final SHA256 verification: `python verify_manifest.py`

The tests make a temporary, relocated copy and recompute everything from an
unrelated working directory with no access to original runtime cache paths.
Generated JSON numeric comparisons allow 1e-12 floating-point tolerance; this is
roundoff tolerance, not scientific uncertainty. All generated CSVs also match the
frozen publication tables. Tests confirm missing T2 receipts fail visibly and
output cannot overwrite the evidence directory.

## Original-value preservation

`provenance/VERIFICATION_RESULTS.json` records the machine-readable comparisons.

- T2 `statistics.json`: every value exactly equals the original audit in this run
- T3 summary: every original key/value exactly equals the original audit; a new
  `n_published_inventory=26` field distinguishes focused publication inventory
- T2 17 historical rows, 36 inclusion rows and 966 raw metric rows: unchanged values
- T3 106 paired records, six dominance records and 28 top-K records: unchanged
  scientific values; source IDs and source hashes reflect published evidence
- T3 156 central raw rows: unchanged values
- T3 12 central summary rows: recomputed from the full 390-row evidence, maximum
  absolute difference from original 8.881784197001252e-16 (serialization/roundoff)
- Frozen-donor source-code hash matches the unchanged frozen protocol

## Inventory, privacy and size policy

Only allowlisted small research receipts, reports and provenance code are included.
Full multi-board registries, duplicate stdout, raw execution logs, private notes,
large matrices, trained models and upload packages are excluded. The source
inventory preserves the SHA256 of each original and its final published counterpart.
Account-scoped portal links and one unrelated personal workstation path were removed.
No credentials, signed URLs or personal account details were found in the final
text scan. No data/model binaries are included.

The original frozen-donor script intentionally retains research cache paths for
byte-identical protocol verification. It is an archival evidence file, not one of
the runnable portable analysis entry points. This exception is documented in the
README. Primary entry points contain no workstation-specific paths.

## Narrowed publication scope

Six historical Markdown evidence copies were removed. Only original repository
links and previously recorded original hashes remain in EXCLUDED_SOURCE_RECEIPTS.
No omitted text was extracted or repackaged. Their existing audited numerical
values remain unchanged. Reproduction covers recorded calculations, not renewed
verification of omitted report content. Unknown missing source files still fail.

## Interpretation and unrun work

The audit does not establish a universal local-score cutoff, an overall false-
negative rate, or a local/server point correction. The observed T3 2.10-point
ranking regret concerns one method pair across overlapping source strata. All
related original submissions already existed; this publication creates none.

Full reconstruction of biological predictions and source scorer outputs was
NOT_RUN and is not included in the lightweight verification claim. It requires
separate original data/artifact caches and environments; some historical original
artifact bytes are unavailable. Snapshot hashes do not remove that limitation.
