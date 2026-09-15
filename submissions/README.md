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
6. Every upload/score MUST register per-metric skills (standing rule, fixed 2026-09-04): append one row per board x metric to `reports/SERVER_SUBMETRIC_REGISTRY.tsv` (record_date, board, version, method, portal_file, submitted, precise board_score, metric, skill), add/update the snapshot section in `reports/SERVER_SCORE_REGISTRY.md`, and point the INDEX.tsv notes of the scored rows at the TSV. A score without its submetric breakdown is not a complete registration.

Board directory names are stable slugs: `T1_val`, `T2_embryo_val_interp`,
`T2_heart_val_extrap`, `T2_heart_val_interp`, and `T3_gata4`.

## Manual-upload naming rule (fixed 2026-09-03, mandatory)

Portal `Model` 名来自上传文件名，因此交付 zip 的成员名必须短且稳定：

- 成员名（= portal Model 名）：`<task>_<board>__<lane>__v<NNNN>.h5ad`，全小写，
  **总长 ≤50 字符（含扩展名）**。
  - `task` ∈ `t1` / `t2` / `t3`
  - `board` 短码：t1 `val`；t2 `emb_int` / `hrt_int` / `hrt_ext`；t3 `gata4`；
    新 board 按同风格追加并在本文件登记
  - `lane`：如 `l1` / `l2` / `base`
  - `v<NNNN>` 必须与 `INDEX.tsv` 的 version 完全一致（board 内唯一锚点）
- zip 包名：`<atom短码>__<task>__upload__<YYYYMMDD>.zip`，≤50 字符；
  atom 短码如 `b1a4` / `b2t3a1` / `t1s2` / `t2s3`
- 包内必须附 `MANIFEST.tsv`（`filename / bytes / sha256`），身份核验以 SHA256 为准，
  短名不承载语义完整性
- 2026-09-03 之前已上传/已评分的长名 artifact 不回溯改名（历史记录不变）

## Batch packaging rule (fixed 2026-09-11, mandatory, going forward)

一个批次（一次 locked run / 一个 task 及其全部 lane）的产出打成**一份 zip**，不再按 lane 分包：

- 包内含该批次全部成员 h5ad（成员命名仍遵守上面的短名规则，`v<NNNN>` 与 INDEX.tsv 一致）；
- 包内必须附 `MANIFEST.tsv`（全体成员的 `filename / bytes / sha256`）+ `UPLOAD_MANIFEST.tsv`（全体成员的 board/version/canonical 路径映射）+ `RUN_ID_MAP.tsv` + `EVIDENCE_MANIFEST_POINTERS.tsv`；
- zip 包名沿用 `<atom短码>__<task>__upload__<YYYYMMDD>.zip`（≤50 字符），一批次一包；
- 已产生的历史分包（2026-09-11 及以前）不回溯重打，不影响已登记的 SHA256 身份核验。

