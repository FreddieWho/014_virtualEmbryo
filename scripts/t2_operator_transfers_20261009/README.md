# Source snapshots for this run

These files mirror the executed code; execute the packaged run-tree originals rather than these relocated snapshots. The reproducibility archive preserves `embryo/`, `heart_interp/`, `heart_extra/`, `repo/scripts/vework/`, `repo/third_party/veckit/`, and the hash-locked candidate/control artifacts. The original cloud run root is `/workspace/shared/t2_operator_transfers_20261009`.

- Embryo: `embryo/build.py --out NEW_DIRECTORY` and `--holdout` for released-stage evaluation; set `T2_TRANSFER_REPO` and `T2_EMBRYO_DATA` for relocation
- Heart interp: `heart_interp/run_transfer.py --data DATA --mode parent|holdout|final --outdir NEW_DIRECTORY`; final requires the exact parent path and hash listed in handoff
- Heart extra: `heart_extra/code/run.sh`; inspect its documented explicit data/root locations before relocating

Numerical libraries are single-thread. Match requirements.freeze.txt, verify input hashes, and retain the same downloaded panel order. Original training files are not included in the small archive; retrieve released official files and verify the recorded SHA256. No protected target is needed or allowed. All outputs are immutable: use new output directories for replay.
