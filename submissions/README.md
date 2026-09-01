# Submission artifact layout

`submissions/INDEX.tsv` is the canonical lookup table. Do not place `.h5ad` files
directly under `submissions/` and do not overwrite an existing version.

## Lifecycle

```text
submissions/
├── scored/<submission-id>/<board>/submission.h5ad
├── candidates/<board>/v000N_<method>/submission.h5ad
├── INDEX.tsv
└── README.md
```

- `scored/` contains immutable snapshots associated with a server submission or
  registered score. `baseline-001` is the first score package; its portal submission
  ID and exact upload mapping are still pending.
- `candidates/` contains generated, unscored or format-checked versions. Each method
  or material parameter change gets a new monotonically increasing version within its
  board directory.
- Every artifact is named `submission.h5ad`; method, board, version, SHA-256 and score
  status live in `INDEX.tsv`, not in an increasingly long filename.

## Operating rules

1. Generate a new candidate in its own `candidates/<board>/v000N_<method>/` directory.
2. Run the minimum contract check and record the SHA-256 in `INDEX.tsv`.
3. After upload, record the portal submission ID and returned score. Do not rename or
   overwrite the uploaded artifact.
4. When a candidate is scored, move it to `scored/<submission-id>/<board>/` only if
   the move preserves its recorded SHA-256; otherwise keep it in place and update the
   index with the server ID.
5. `reports/SERVER_SCORE_REGISTRY.md` records scores; this directory records files.

Board directory names are stable slugs: `T1_val`, `T2_embryo_val_interp`,
`T2_heart_val_extrap`, `T2_heart_val_interp`, and `T3_gata4`.
