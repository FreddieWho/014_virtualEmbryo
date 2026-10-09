# Server leaderboard score registry

导航：[`README.md`](README.md)、[`SYNTHESIS_T1.md`](SYNTHESIS_T1.md) / [`SYNTHESIS_T2.md`](SYNTHESIS_T2.md) / [`SYNTHESIS_T3.md`](SYNTHESIS_T3.md)。那三份不是分数账。

本文件只登记比赛服务器返回的分数。`local pseudo-score`、公开 target 上的
scorer smoke 和格式检查不得填入这里，也不得当作官方榜单分数。

提交文件的唯一索引是 [`submissions/INDEX.tsv`](../submissions/INDEX.tsv)；本文件
只负责分数、submission ID 和服务器证据，不重复维护文件清单。

## Scoring protocol

每次 scored submission 后，下一步模型迭代前必须补登记：

- 日期、submission ID、board/phase；
- 提交文件路径和 SHA-256；
- Total、T1、T2、T3 及各 task 子项分数；
- 相对上一次提交的差值；
- 成绩按用户或服务器回填登记；不额外要求截图、链接或 JSON。

如果新提交没有回填服务器分数，下一轮比较只能标记为 `score_pending`，不能宣称
模型进步。

## Registered submissions

### Baseline-001

| Field | Value |
|---|---|
| Record date | 2026-08-21 |
| Submission label | baseline (first scored submission) |
| Source | User-provided server result |
| Submission ID | pending |
| Board/phase | pending |
| Submission file / SHA-256 | pending |

| Score | Value |
|---|---:|
| **Total** | **145.7** |
| T1 | 47.0 |
| T2 | 53.4 |
| T3 | 45.3 |
| T1 · single-cell temporal | 47.0 |
| T2 · heart interpolation | 53.0 |
| T2 · heart extrapolation | 50.5 |
| T2 · embryo interpolation | 56.7 |
| T3 · Gata4 KO | 45.3 |

Consistency checks from the supplied values:

- `Total = T1 + T2 + T3 = 47.0 + 53.4 + 45.3 = 145.7`;
- `T2 = mean(53.0, 50.5, 56.7) = 53.4` after rounding to one decimal.

This is the baseline reference for future comparisons. No improvement claim is made
until a later server score is registered against this row.

### Submission-002

| Field | Value |
|---|---|
| Record date | 2026-08-22 |
| Submission label | T2 heart interpolation `v0002_expression_midpoint_norm` |
| Source | User-provided server result |
| Submission ID | pending |
| Board/phase | T2:heart:val_interp; aggregate table updated |
| Submission file | `submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad` |
| SHA-256 | `402b0a893672e9ce267af0a39bcdf8e00975cdf3dc7dca00fab80858ae2d08b4` |

| Score | Value | Delta vs Baseline-001 |
|---|---:|---:|
| **Total** | **145.9** | **+0.2** |
| T1 | 47.0 | 0.0 |
| T2 | 53.6 | +0.2 |
| T3 | 45.3 | 0.0 |
| T1 · single-cell temporal | 47.0 | 0.0 |
| T2 · heart interpolation | 53.6 | **+0.6** |
| T2 · heart extrapolation | 50.5 | 0.0 |
| T2 · embryo interpolation | 56.7 | 0.0 |
| T3 · Gata4 KO | 45.3 | 0.0 |

Consistency checks:

- `Total = 47.0 + 53.6 + 45.3 = 145.9`;
- `T2 = mean(53.6, 50.5, 56.7) = 53.6` after rounding to one decimal.

At the time of entry, this was the current best registered result. The candidate remains
the immutable parent for the B1-A1 heart interpolation comparison; its supplied score is
retained as the comparison baseline.

### Submission-003

| Field | Value |
|---|---|
| Record date | 2026-08-23 |
| Submission label | T1 validation `v0002_shrunk_pseudobulk_shift` |
| Source | User-provided server result |
| Submission ID | pending |
| Board/phase | T1:val |
| Submission file | `submissions/scored/submission-003/T1_val/submission.h5ad` |
| SHA-256 | `bef1d4654ee1723b7e27716b676dda97f229a5560f2295e144d78bd1334acb3d` |

| Score | Value | Delta vs Submission-002 |
|---|---:|---:|
| **Total** | not supplied | — |
| T1 | 45.9 | **-1.1** |
| T2 | not supplied (unchanged candidate set) | — |
| T3 | not supplied (unchanged candidate set) | — |
| T1 · single-cell temporal | 45.9 | **-1.1** |

Consistency checks:

- Only the T1 board score (45.9) was supplied with this result; T2/T3 were not
  re-submitted and their last registered values remain 53.6 / 45.3. If those stand,
  the implied aggregate would be `45.9 + 53.6 + 45.3 = 144.8` (-1.1 vs 145.9), to be
  confirmed against the server page on next upload.
- Delta is measured against the T1 current best (baseline-001 `copy_last`, 47.0).

Assessment: the T1 v0002 candidate (shrunk per-type shift + global fallback +
linear composition extrapolation) scored **below** the `copy_last` floor it was
meant to beat. It is rejected as an improvement; later T1 rows supersede it as
the current-best comparison. The scored artifact is kept immutable as the audit
snapshot; the supplied score is retained; submission ID is not used for the comparison.

### Submission-004 — T3 Gata4 comparison round

| Field | Value |
|---|---|
| Record date | 2026-08-24 |
| Submission label | T3 Gata4 `v0002_shift_transfer_norm` and `v0003_shift_transfer_shrunk` |
| Source | User-provided server result |
| Submission ID | pending |
| Board/phase | T3:gata4 |
| Submission files / SHA-256 | `v0002`: `submissions/candidates/T3_gata4/v0002_shift_transfer_norm/submission.h5ad` / `adfc109ef565e4813aed1f4dd60d0bdc62ef96ad4f1ac96dcfcf9dbf92a2ef5c`; `v0003`: `submissions/candidates/T3_gata4/v0003_shift_transfer_shrunk/submission.h5ad` / `7f0ecf27f6b453122842dc77c25d860b36f6166428f43a28f62651f52f05d50f` |

| Candidate | T3 · Gata4 KO | Delta vs T3 baseline `v0001` (45.3) | Decision |
|---|---:|---:|---|
| `v0002_shift_transfer_norm` | 45.2 | **-0.1** | rejected |
| `v0003_shift_transfer_shrunk` | 43.8 | **-1.5** | rejected |

| Score field | Value |
|---|---:|
| Total | not supplied (T3-only result) |
| T1 | not supplied; retained latest best 47.0 |
| T2 | not supplied; retained latest best 53.6 |
| T3 | retained latest best 45.3 (`wt_identity`) |

Consistency and decision: both candidates passed the local contract but scored below
the immutable T3 baseline, so neither is a leaderboard improvement. The retained
aggregate remains `47.0 + 53.6 + 45.3 = 145.9`. The supplied scores are retained;
the two scored artifacts stay immutable as audit snapshots.

### B1-A1 — T2 G1 dual-lane scoring round
| Record date | 2026-08-27 |
|---|---|
| Submission label | B1-A1: L1/L2 source-only uniform G1 scale |
| Board/phase | T2:embryo:val_interp; T2:heart:val_interp; T2:heart:val_extrap |
| Source | User-provided server results in score-return message |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs parent | Per-board decision |
|---|---|---|---:|---:|---|
| `B1-A1-L1-T2_embryo_val_interp` | `t2_emb_int_b1_a1_l1` | `submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad` / `392c470e4af35797ad27c100e773c1a7695c989baed95c911fceb0b5d7965fd4` | **60.1** | **+3.4** vs 56.7 | retain; board winner |
| `B1-A1-L2-T2_embryo_val_interp` | `t2_emb_int_b1_a1_l2` | `submissions/candidates/T2_embryo_val_interp/v0003_g1_all_stage_log_rms_ols/submission.h5ad` / `f06540293b9bb479e7090926825ec722420d266257455a85ca8f470ee565f668` | **59.9** | **+3.2** vs 56.7 | scored backup |
| `B1-A1-L1-T2_heart_val_interp` | `t2_hrt_int_b1_a1_l1` | `submissions/candidates/T2_heart_val_interp/v0003_g1_formal_log_rms/submission.h5ad` / `f8a4da854bf9e01e25503b59fddb70bae242c0382b38cc0f3984bf80cd751424` | **56.3** | **+2.7** vs 53.6 | retain; board winner |
| `B1-A1-L2-T2_heart_val_interp` | `t2_hrt_int_b1_a1_l2` | `submissions/candidates/T2_heart_val_interp/v0004_g1_all_stage_log_rms_ols/submission.h5ad` / `6239e6fa24fefb6a3f6ee76564a58f5e08a4463c24fc46747d9e59ee561d9538` | **55.3** | **+1.7** vs 53.6 | scored backup |
| `B1-A1-L1-T2_heart_val_extrap` | `t2_hrt_ext_b1_ba_l1` | `submissions/candidates/T2_heart_val_extrap/v0002_g1_formal_log_rms/submission.h5ad` / `8c76db9cdd5453422d4c392108fd459c4ca44b9c391dd9af4605017988164834` | **50.2** | **-0.3** vs 50.5 | retain; board winner but below parent |
| `B1-A1-L2-T2_heart_val_extrap` | `t2_hrt_ext_b1_ba_l2` | `submissions/candidates/T2_heart_val_extrap/v0003_g1_all_stage_log_rms_ols/submission.h5ad` / `a85b8207e50002068a3bdfd4d9dd6677fffd4f1177262e83a1fb0f271fb86a26` | **49.8** | **-0.7** vs 50.5 | scored backup; below parent |

Consistency and decision:
- L1 wins L2 on all three boards by 0.2, 1.0 and 0.4 points respectively.
- The leaderboard row at 13:13 labels the Model as an embryo-interpolation string, but its Board is T2 heart extrapolation and its 50.2 score is mapped to the canonical heart-extrapolation L1 artifact; the Model text is not used.
- Using L1 on all three boards, the derived T2 mean is `(60.1 + 56.3 + 50.2) / 3 = 55.5`; the derived aggregate is `47.0 + 55.5 + 45.3 = 147.8`.
- Using L2 on all three boards, the derived T2 mean is `55.0` and the derived aggregate is `147.3`.
- The server supplied board scores, not an aggregate Total; 147.8/147.3 are protocol-derived values and must be labeled as such.
- Decision: L1 wins within the B1-A1 lanes, but the current global board selection uses the higher baseline 50.5 for heart extrapolation; keep all six immutable artifacts and retain L2 as the scored second candidate/audit backup. No causal or universal extrapolation claim.
- User-provided values are registered as supplied server results.

### B1-A2 — T3 Gata4 signed-response scoring round

| Record date | 2026-08-28 |
|---|---|
| Submission label | B1-A2: L1/L2 WT-only signed-response candidates |
| Board/phase | T3:gata4 |
| Source | User-provided server results in score-return message |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs T3 baseline 45.3 | Decision |
|---|---|---|---:|---:|---|
| `B1-A2-L1-T3_gata4` | `t3_v0004` | `submissions/candidates/T3_gata4/v0004_b1_a2_cell_spearman/submission.h5ad` / `c6a09de79c8f29fb6096fabd36e2270e828a4c7d86da3966075babea3a0c5c8f` | **44.7** | **-0.6** | rejected; hold for failure diagnosis |
| `B1-A2-L2-T3_gata4` | `t3_v0005` | `submissions/candidates/T3_gata4/v0005_b1_a2_state_pb_spearman/submission.h5ad` / `a702805d24786308a90dfbe7c4db0a37fad626be2fef45e16a1cf76a9899b84d` | **44.0** | **-1.3** | rejected; hold for failure diagnosis |

Consistency and decision:
- The server returned T3 board scores only; no new Total/T1/T2 values were supplied, so the retained aggregate is unchanged.
- Both candidates passed local contract/invariant checks but scored below immutable `wt_identity` baseline `45.3`; v0004 remains the less-bad experimental lane, not a new best.
- User-provided values are registered as supplied. No additional screenshot, link, or JSON evidence is required.

### T1 historical validation rows — corrected from leaderboard
| Record date | 2026-08-24 |
|---|---|
| Submission label | Two unlabeled T1 validation submissions |
| Board/phase | T1:val |
| Source | User-provided leaderboard table |
| Mapping rule | Model field ignored; the 12:30 and 12:43 rows are mapped in chronological order to local candidates v0003 and v0004 respectively, consistent with candidate/version order |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs baseline 47.0 | Decision |
|---|---|---|---:|---:|---|
| `candidate/T1_val/v0003_no_comp_extrap` | not supplied | `submissions/candidates/T1_val/v0003_no_comp_extrap/submission.h5ad` / `a0d1ef28c30569a016fb5009a0da4fa68b8461c071b1a46a35416df2e8df0cda` | **46.2** | **-0.8** | rejected |
| `candidate/T1_val/v0004_strict_pseudobulk_shift` | not supplied | `submissions/candidates/T1_val/v0004_strict_pseudobulk_shift/submission.h5ad` / `1bc069d9aecd4b9b15f3ff91c328ef27a9773bfd0d3c890f36f5f1b6fb4f49bd` | **48.5** | **+1.5** | T1 best; retain immutable |

Consistency and decision:
- These two rows are now the missing T1 leaderboard entries; the Model text was not used to identify artifacts.
- The local v0003/v0004 files contain public pseudo-holdout metric vectors, not the leaderboard's one-dimensional score; those local values are not comparable to 46.2/48.5.
- The 48.5 row is higher than B1-A3 v0006=47.7, so the global T1 best is v0004, not B1-A3 v0006.
- No new Total/T2/T3 values were supplied. With the retained T1/T2/T3 selections, the derived aggregate is `48.5 + 55.5 + 45.3 = 149.3`; the server did not directly return Total.


- Decision: keep both immutable artifacts for diagnosis; do not enter B1-A3 or start another T3 route until the failure review is explicitly released.

### B1-A3 — T1 mass-residual dual-lane scoring round
| Record date | 2026-08-28 |
|---|---|
| Submission label | B1-A3: L1/L2 source-only mass residual |
| Board/phase | T1:val |
| Source | User-provided server results in score-return message |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs T1 baseline 47.0 | Decision |
|---|---|---|---:|---:|---|
| `B1-A3-L1_SHARED_UNRESOLVED-T1_val` | `t1_v0005` | `submissions/candidates/T1_val/v0005_b1_a3_shared_unresolved/submission.h5ad` / `88c3cb51245e19a100de0b0ad33766a6ee704c42f308b81141aeeeaed07e556a` | **47.5** | **+0.5** | scored backup; retain immutable |
| `B1-A3-L2_E95_EXPRESSION_PROBE-T1_val` | `t1_v0006` | `submissions/candidates/T1_val/v0006_b1_a3_e95_expression_probe/submission.h5ad` / `ba6b83cd4135968a3ce4f15ae4ca5dce01ed019cef268e5c01edf012a45bd4b4` | **47.7** | **+0.7** | B1-A3 lane winner; below T1 best v0004=48.5; retain immutable |

Consistency and decision:
- The server returned the T1 board score only; no new Total/T2/T3 values were supplied.
- Both B1-A3 candidates beat the immutable T1 baseline 47.0; L2 is higher than L1 by 0.2 points, but both are below the earlier v0004 score 48.5.
- This earlier B1-A3-derived aggregate is superseded by the current server snapshot below; do not use `48.5 + 55.5 + 45.3 = 149.3` as the current Total.
- User-provided values are registered as supplied. No additional screenshot, link, or JSON evidence is required.

### Current leaderboard snapshot — 2026-08-28
| Field | Server value | Basis |
|---|---:|---|
| Total | **149.5** | server-returned current leaderboard value |
| T1 | **48.5** | server-returned; `candidate/T1_val/v0004_strict_pseudobulk_shift` |
| T2 | **55.7** | server-returned task aggregate |
| T3 | **45.3** | server-returned; baseline `wt_identity` |
| T1 · single-cell temporal | **48.5** | server-returned |
| T2 · heart interpolation | **56.3** | server-returned; B1-A1 L1 |
| T2 · heart extrapolation | **50.5** | server-returned; baseline, higher than B1-A1 L1=50.2 |
| T2 · embryo interpolation | **60.1** | server-returned; B1-A1 L1 |
| T3 · Gata4 KO | **45.3** | server-returned; baseline |

Consistency note:
- The displayed T2 components average to `55.633...`, not exactly the displayed `55.7`; the local record does not expose the server's unrounded component values or aggregation precision. The server-returned T2/Total values are authoritative and must not be replaced by a hand-rounded local recomputation.
- The current aggregate is the server-returned **149.5**; the previous local derivation **149.3** was invalid because it selected 50.2 instead of the higher baseline 50.5 and was not a server Total.

### B1-A4 — T2 J1 hard expression-coordinate permutation scoring round
| Record date | 2026-08-28 |
|---|---|
| Submission label | B1-A4: L1/L2 source-only J1 permutation candidates |
| Board/phase | T2:embryo:val_interp; T2:heart:val_interp; T2:heart:val_extrap |
| Source | User-provided server results; portal Model filename used only for local candidate mapping |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs parent | Per-board decision |
|---|---|---|---:|---:|---|
| `B1-A4-L1_LATENT_KNN10-T2_embryo_val_interp` | not supplied | `submissions/candidates/T2_embryo_val_interp/v0004_b1_a4_latent_knn10/submission.h5ad` / `5bcc56b57ac021e608ba6b94e427e93accd03c780c9cf072c8767be8eb4a3645` | **59.3** | **-0.8** vs B1-A1 L1=60.1 | rejected; below current board best |
| `B1-A4-L2_STATE_HASH10-T2_embryo_val_interp` | not supplied | `submissions/candidates/T2_embryo_val_interp/v0005_b1_a4_state_hash10/submission.h5ad` / `85218c4edbf3430abe5cd7c670f2957dffb06c302d566372345479157b2977a2` | **59.2** | **-0.9** vs B1-A1 L1=60.1 | rejected; below current board best |
| `B1-A4-L1_LATENT_KNN10-T2_heart_val_interp` | not supplied | `submissions/candidates/T2_heart_val_interp/v0005_b1_a4_latent_knn10/submission.h5ad` / `d999bde5d118cb23ce5e16821592a0509b785ca78c47593f23223ab44fafacc1` | **56.3** | **0.0** vs B1-A1 L1=56.3 | tie; no promotion |
| `B1-A4-L2_STATE_HASH10-T2_heart_val_interp` | not supplied | `submissions/candidates/T2_heart_val_interp/v0006_b1_a4_state_hash10/submission.h5ad` / `cb91e88b0e2db0e2820d95d17aa9accecc203083b15c4241b11832a6646bd1ca` | **56.3** | **0.0** vs B1-A1 L1=56.3 | tie; no promotion |
| `B1-A4-L1_LATENT_KNN10-T2_heart_val_extrap` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0004_b1_a4_latent_knn10/submission.h5ad` / `3f1869bbb9fbc8f1f00ce4b7214c4ac8a8ec2a76336651c0060f69e5d067ad30` | **50.0** | **-0.5** vs baseline=50.5 | rejected; below parent |
| `B1-A4-L2_STATE_HASH10-T2_heart_val_extrap` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0005_b1_a4_state_hash10/submission.h5ad` / `bfec39b18a2e7d0b2a8c2a1d978550ff258728a4433aaec4ecf7dc65337325c8` | **49.9** | **-0.6** vs baseline=50.5 | rejected; below parent |

Consistency and decision:
- A4 L1/L2 tie on heart interpolation at 56.3, but neither exceeds the retained B1-A1 L1 board score.
- The current per-board selection remains B1-A1 L1 for embryo interpolation and heart interpolation, plus baseline for heart extrapolation: T2 **55.7**, Total **149.5**.
- A4 all-L1 would imply `(59.3 + 56.3 + 50.0) / 3 = 55.2` from board values; A4 all-L2 would imply `55.1`. These are protocol-derived comparisons, not new server Total values.
- Decision: retain all six scored artifacts as immutable records; reject A4 as a leaderboard improvement and do not start B1-C1 or another atom from this result.
- User-provided values are registered as supplied; no additional screenshot, link, or JSON evidence is required.

### T1-S2 — moscot coupling/decoder dual-lane scoring round
| Record date | 2026-09-03 |
|---|---|
| Submission label | T1-S2-MOSCOT-DECODER-20260902-v1: L1/L2 E10.5 extrapolation candidates |
| Board/phase | T1:val |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-02 19:55 and 2026-09-03 00:05; portal Model filename contains lane/version and is consistent with local mapping) |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs T1 best v0004=48.5 | Decision |
|---|---|---|---:|---:|---|
| `T1-S2 v0007 L1_EMPIRICAL_RESIDUAL` | not supplied | `submissions/candidates/T1_val/v0007_t1_s2_l1_moscot_empirical/submission.h5ad` / `4297f3fd344d4592eaf2176caa7f28b03148993aa1bbbcc52c6156f0b121d866` | **44.9** | **-3.6** | rejected; below T1 best and below T1 baseline 47.0 |
| `T1-S2 v0008 L2_MODULE_SCDESIGN3` | not supplied | `submissions/candidates/T1_val/v0008_t1_s2_l2_module_scdesign3/submission.h5ad` / `d664db404418fe8558dbe9a966352921c2498e74343318e0f8c9c08ff9774280` | **44.8** | **-3.7** | rejected; below T1 best and below T1 baseline 47.0 |

Consistency and decision:
- The server returned T1 board scores only; no new Total/T2/T3 values were supplied. The retained aggregate remains Total **149.5** (T1 48.5 / T2 55.7 / T3 45.3).
- Both candidates passed local contract/protected checks but scored well below the immutable T1 best `v0004_strict_pseudobulk_shift` (48.5) and even below the `copy_last` baseline (47.0). The moscot coupling + state-mass forecast + state-specific delta route is therefore **rejected as a leaderboard improvement on the E10.5 extrapolation board**, superseding the earlier local `HOLD_AS_COMPONENT` disposition: the server probe has now arbitrated the question that the source-only pseudo-holdout could not (whether structured extrapolation beats strict shift extension), and the answer is negative for both decoders.
- Both scored artifacts stay immutable as audit snapshots; no causal claim is made beyond this board. User-provided values are registered as supplied; no additional screenshot, link, or JSON evidence is required.

### T2-S3 — shape-field geometry dual-board scoring round
| Record date | 2026-09-03 |
|---|---|
| Submission label | T2-S3-SHAPE-FIELD-20260903-v1: L1 pycpd non-rigid geometry candidates |
| Board/phase | T2:embryo:val_interp; T2:heart:val_interp |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-03 12:12 and 12:14; portal Model filenames `t2_emb_int__l1__v0006` / `t2_hrt_int__l1__v0007` match the fixed short-name rule and local versions exactly) |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs current board best | Decision |
|---|---|---|---:|---:|---|
| `T2-S3 embryo v0006 L1_PYCPD` | not supplied | `submissions/candidates/T2_embryo_val_interp/v0006_t2_s3_l1_pycpd/submission.h5ad` / `a46671bbd9f7c149c128a5f73f3f2cb479d5fdd468490bc18e245773476eff36` | **59.7** | **-0.4** vs B1-A1 L1=60.1 | rejected; board best unchanged |
| `T2-S3 heart_interp v0007 L1_PYCPD` | not supplied | `submissions/candidates/T2_heart_val_interp/v0007_t2_s3_l1_pycpd/submission.h5ad` / `0ca4f217915ed53dfa35370cc8026704531eefd5e701f63b976433b9ce4dd416` | **56.7** | **+0.4** vs B1-A1 L1=56.3 | **new board best; promote to current selection** |

Consistency and decision:
- The server returned the two board scores only; no new T2 aggregate or Total was supplied. The retained server values remain T2 **55.7** and Total **149.5** until the server page is re-read.
- Protocol-derived (not server-returned): if the server aggregates best-per-board with embryo 60.1 (B1-A1 L1), heart interpolation 56.7 (T2-S3 L1), heart extrapolation 50.5 (baseline), the derived T2 mean is `(60.1 + 56.7 + 50.5) / 3 = 55.77` and the derived Total is `48.5 + 55.77 + 45.3 = 149.6`; these derived values must be confirmed against the server page on the next read and must not be quoted as server values.
- The heart-interpolation improvement (+0.4) is consistent with the source-only holdout evidence (H2 full win) but the embryo decline (-0.4) despite H1 full win confirms the H3 caveat: narrow-window holdout gains do not guarantee board gains. No causal claim is made from leaderboard scores alone.
- The four non-uploaded T2-S3 candidates (L2 lanes and heart-extrap L1, all locally REJECTED) remain `score_pending`/immutable and will not be uploaded.
- Both scored artifacts stay immutable; user-provided values are registered as supplied.

### T2-J1 — FGW assignment heart-interp scoring round
| Record date | 2026-09-04 |
|---|---|
| Submission label | T2-J1-FGW-ASSIGNMENT-20260903-v1: heart_interp v0009 j1_fgw_assignment |
| Board/phase | T2:heart:val_interp |
| Source | User-provided server results in score-return message (leaderboard row 2026-09-03 19:51; portal Model filename `t2_hrt_int__j1fgw__v0009` matches the fixed short-name rule and local version exactly) |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs current board best | Decision |
|---|---|---|---:|---:|---|
| `T2-J1 heart_interp v0009 J1_FGW_ASSIGNMENT` | not supplied | `submissions/candidates/T2_heart_val_interp/v0009_j1_fgw_assignment/submission.h5ad` / `4f2e7552a4ff5a11191f8cf6f1e94393882d131aa76855e5da34faef3f43ac43` | **57.3** | **+0.6** vs T2-S3 L1=56.7 | **new board best; promote to current selection** |

Consistency and decision:
- The server returned the board score only; no new T2 aggregate or Total was supplied. The retained server values remain T2 **55.7** and Total **149.5** until the server page is re-read.
- Protocol-derived (not server-returned): with embryo 60.1 (B1-A1 L1), heart interpolation 57.3 (T2-J1 v0009), heart extrapolation 50.5 (baseline), the derived T2 mean is `(60.1 + 57.3 + 50.5) / 3 = 55.97` and the derived Total is `48.5 + 55.97 + 45.3 = 149.8`; these derived values must be confirmed against the server page on the next read and must not be quoted as server values.
- The +0.6 resolves the local mixed evidence in the positive direction: the same-target NFS-mirror improvement (0.0967→0.0747) was the pre-declared gate metric direction, while the same-target morans decline (0.7365→0.6743) did not dominate the board outcome. Consistent with J1-PROXY holdout evidence; no causal claim is made from leaderboard scores alone.
- embryo v0008 (`j1_fgw_assignment`, HOLD_AS_COMPONENT) was not uploaded and stays immutable/score_pending; the four non-uploaded T2-S3 candidates likewise remain untouched.
- The scored artifact stays immutable; user-provided value registered as supplied.

### B2-T3-A1 — T3 Gata4 signed-response dual-lane scoring round
| Record date | 2026-09-04 |
|---|---|
| Submission label | B2-T3-A1 L1_STRICT_WT_DIRECT / L2_GATA4_GATA6_CONDITION_AWARE（新命名规则包 `b2t3a1__t3__upload__20260904.zip`） |
| Board/phase | T3:gata4 |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-03 23:40 / 23:41; portal Model filenames `t3_gata4__l1__v0006` / `t3_gata4__l2__v0007` match the fixed short-name rule and local versions exactly) |
| Candidate | Submission ID | Submission file / SHA-256 | Server score | Delta vs current board best | Decision |
|---|---|---|---:|---:|---|
| `B2-T3-A1 v0006 L1_STRICT_WT_DIRECT` | not supplied | `submissions/candidates/T3_gata4/v0006_b2_t3_a1_l1/submission.h5ad` / `d3cc8adb6f46070f7dbfecbdff9c10e9df9184a417376fb0d4a4813b2517c175` | **45.5** | **+0.2** vs wt_identity 45.3 | **new board best (tied); promote to current selection** |
| `B2-T3-A1 v0007 L2_GATA4_GATA6_CONDITION_AWARE` | not supplied | `submissions/candidates/T3_gata4/v0007_b2_t3_a1_l2/submission.h5ad` / `012ac745c995f5f5ef0209c44250cf8aa1bb35ae1fe2355550e7ab16297cf900` | **45.5** | **+0.2** vs wt_identity 45.3 | **new board best (tied); promote to current selection** |

Consistency and decision:
- The server returned the two board scores only; no new T3 aggregate or Total was supplied. The retained server values remain T3 **45.3** and Total **149.5** until the server page is re-read.
- Protocol-derived (not server-returned): with a T3 board best of 45.5, the derived T3 task value is `45.5` and the derived Total is `48.5 + 55.7 + 45.5 = 149.7`; these derived values must be confirmed against the server page on the next read and must not be quoted as server values.
- First T3 candidates above the `wt_identity` 45.3 baseline after five rejected attempts (v0002 45.2, v0003 43.8, v0004 44.7, v0005 44.0); both lanes tie at 45.5, so the server probe cannot separate them. Both are promoted as tied board bests; no lane preference is claimed.
- The +0.2 does not constitute mechanistic or causal evidence: T3-S1 scientific gate remains CLOSED_AS_RESEARCH_COMPONENT (UNSATISFIABLE_UNDER_FIREWALL), `blocks_submission: false`; local leaderboard gains do not unlock the science gate.
- Both scored artifacts stay immutable; user-provided values registered as supplied.

### B4-P0 — exact-floor parity probe scoring round
| Record date | 2026-09-04 |
|---|---|
| Submission label | B4-P0-STATE-FLOOR-PARITY L0_EXACT_FLOOR（包 `b4p0__t1__upload__20260904.zip` / `b4p0__t3__upload__20260904.zip`；portal Model 列显示为 zip 包名） |
| Board/phase | T1:val; T3:gata4 |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-04 15:56 T1 / 14:17 T3) |
| Run | `B4-P0-STATE-FLOOR-PARITY-2026-09-04T110859.403071+0000`（artifacts/batch4/B4-P0-STATE-FLOOR-PARITY-20260904-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-P0 T1 v0009 L0_EXACT_FLOOR` | not supplied | `submissions/candidates/T1_val/v0009_b4p0_l0_exact_floor/submission.h5ad` / `38267746dfa4a5b2b3f44ee9dd3bbfb04d7674b5b68315e3477872d5bb81cd34` | **47.0** | baseline-001 copy_last 47.0; official floor defined as 50; T1 best v0004=48.5 | floor parity **UNRESOLVED**; stratification exonerated (identical score with different subset rule); no change to T1 selection |
| `B4-P0 T3 v0008 L0_EXACT_FLOOR` | not supplied | `submissions/candidates/T3_gata4/v0008_b4p0_l0_exact_floor/submission.h5ad` / `478786034343cc3ed1a604cd494ab2134751f4a1f4696204f9d105e404bdbef3` | **46.8** | baseline-001 wt_identity 45.3; v0006/v0007 45.5; official floor defined as 50 | **new board best (+1.3 vs 45.5); promote to current selection**; floor parity **UNRESOLVED** (below 50) |

Consistency and decision:
- The server returned the two board scores only; no new T1/T3 aggregates or Total was supplied.
- T1: two materially different 5,118-cell subsets (celltype-stratified seed 20260821 vs uniform seed 20260904, ~30% overlap) scored **identically 47.0**, so the -3.0 gap vs official floor=50 is not caused by celltype stratification; remaining hypotheses are prediction n_obs (contract max 5,118 vs scorer reference working copy 1,706) or other bundle-level differences not visible locally.
- T3: the no-change exact floor (uniform subset, original row order, float32 coords) scored 46.8, **above** both the old stratified wt_identity (45.3) and the signed-prior candidates v0006/v0007 (45.5). This is consistent with the Batch 4 premise that the old downstream residuals were harmful relative to no-change, and it makes the floor probe itself the T3 board best.
- Protocol-derived (not server-returned): with T3 board best 46.8, derived T3 task value is `46.8` and derived Total is `48.5 + 55.7 + 46.8 = 151.0`; these must be confirmed against the server page and must not be quoted as server values.
- Per Batch 4 execution rules, `FLOOR_PARITY_UNRESOLVED` is now open for T1 and T3; low-risk candidate generation (Wave 1) may proceed, but no complex candidate becomes a final parent while parity is unresolved. T3 Wave-1 comparisons must use 46.8 as the reference, not 45.3/45.5.
- The 45.5 tie of v0006/v0007 is superseded as board best; both artifacts stay immutable. The +1.3 floor gain is a construction/bundle effect, not mechanistic evidence; the T3-S1 scientific gate is unchanged.
- Both scored artifacts stay immutable; user-provided values registered as supplied.

### B4-P0 supplemental — T1 n=1,706 floor probe scoring round
| Record date | 2026-09-04 |
|---|---|
| Submission label | B4-P0 T1 L0_EXACT_FLOOR_N1706（包 `b4p0p2__t1__upload__20260904.zip`；portal Model 列显示为 zip 包名） |
| Board/phase | T1:val |
| Source | User-provided server results in score-return message (leaderboard row 2026-09-04 19:09) |
| Run | `B4-P0-STATE-FLOOR-PARITY-2026-09-04T164205.780061+0000`（artifacts/batch4/B4-P0-T1-FLOOR-PROBE2-20260904-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-P0 T1 v0010 L0_EXACT_FLOOR_N1706` | not supplied | `submissions/candidates/T1_val/v0010_b4p0_l0floor_n1706/submission.h5ad` / `6994a38e108a29ba6791f3d81bde6347f92cf92e8c9c28153e385b973ff54a18` | **46.8** | n=5118 v0009 47.0; official floor defined as 50; T1 best v0004=48.5 | n_obs hypothesis **EXCLUDED**; floor parity stays **UNRESOLVED**; no change to T1 selection |

Consistency and decision:
- The server returned the board score only; no new T1 aggregate or Total was supplied.
- n=1,706 scored **46.8** vs n=5,118 **47.0** (delta -0.2, wrong direction and far smaller than the ~3-point floor gap): the gap vs official floor=50 does not shrink with fewer cells, so prediction n_obs is excluded as its cause. The remaining explanation is bundle-level differences not visible locally (official floor construction unpublished; local truth unavailable for verification).
- Derived aggregates unchanged: T1 best remains v0004=48.5; derived Total stays ≈151.0 pending server page confirmation and must not be quoted as a server value.
- Per Batch 4 rules Wave 1 low-risk candidates may proceed as provisional scores while parity is unresolved; no complex candidate becomes a final parent.
- The scored artifact stays immutable; user-provided value registered as supplied.

### Current-best snapshot — Total 151.2 (server-returned) with per-metric skills
| Record date | 2026-09-04 |
|---|---|
| Source | User-provided server page read: Total **151.2** plus per-board precise scores and per-metric skill breakdowns for all five current-best boards |
| Selection | T1 v0004 + T2 embryo v0002 (B1-A1 L1) + T2 heart_interp v0009 (T2-J1) + T2 heart_extrap baseline v0001 + T3 v0008 (B4-P0 floor) |

| Board | Version / portal file | Precise board score | Per-metric skills |
|---|---|---:|---|
| T1:val | v0004 `shrunk_pseudobulk_shift_strict` / `t1_v0004.h5ad` (submitted 2026-08-24 12:43) | **48.47** | de_score 43.8 / de_direction 55.9 / mmd_u 51.5 / variogram 40.6 |
| T2:embryo:val_interp | v0002 `g1_formal_log_rms` / `t2_emb_val_int_b1_a1_l1.h5ad` (submitted 2026-08-27 13:07) | **60.15** | de_score 50.5 / de_direction 53.2 / mmd_u 60.9 / variogram 59.0 / d2_shape 52.8 / occupancy_dice 46.6 / scale_log_ratio 91.9 / neighborhood_mmd 64.8 |
| T2:heart:val_interp | v0009 `j1_fgw_assignment` / `t2_hrt_int__j1fgw__v0009.h5ad` (submitted 2026-09-03 19:51) | **57.25** | de_score 57.8 / de_direction 60.2 / mmd_u 53.9 / variogram 32.2 / d2_shape 62.0 / occupancy_dice 48.6 / scale_log_ratio 82.5 / neighborhood_mmd 60.4 |
| T2:heart:val_extrap | baseline v0001 `pseudobulk_shift` / `T2_heart_val_extrap_pseudobulk_shift.h5ad` (submitted 2026-08-21 13:07) | **50.53** | de_score 49.6 / de_direction 52.2 / mmd_u 49.9 / variogram 47.7 / d2_shape 46.2 / occupancy_dice 53.2 / scale_log_ratio 49.7 / neighborhood_mmd 52.4 |
| T3:gata4 | v0008 `b4p0_l0_exact_floor` / `t3_gata4__l0floor__v0008.h5ad` (submitted 2026-09-04 14:17) | **46.79** | de_score 38.8 / de_direction 49.7 / severity_slope 50.0 / mmd_u 51.3 / variogram 50.9 |

Machine-readable rows: `reports/SERVER_SUBMETRIC_REGISTRY.tsv` (one row per board x metric; standing rule: every future upload/score must append its per-metric skills there).

Consistency and decision:
- Arithmetic check: `(60.15 + 57.25 + 50.53) / 3 = 55.98` (T2 derived); `48.47 + 55.98 + 46.79 = 151.24`, server Total **151.2**. The 0.04 gap is server-side rounding at task/Total level; the server-returned Total is authoritative and must not be replaced by the hand recomputation.
- This supersedes all earlier derived Totals (149.3/149.6/149.7/149.8/151.0): the confirmed server Total is **151.2**.
- Per-metric read (diagnostic, not causal): T1's weakest anchored metric is variogram (40.6) vs de_direction 55.9; heart_interp's weakest is variogram (32.2) vs d2_shape 62.0; T3's weakest is de_score (38.8) with the other four near 50; embryo's standout is scale_log_ratio (91.9) vs occupancy_dice 46.6; heart_extrap is flat 46-53 across all eight metrics. No route decision is changed by these breakdowns alone.
- All five scored artifacts stay immutable; user-provided values registered as supplied.

### B4-T2-R1 — FGW assignment repair scoring round (TIE, no promotion)
| Record date | 2026-09-04 |
|---|---|
| Submission label | B4-T2-R1-FGW-ASSIGNMENT-REPAIR L1/L2 global matching（包 `b4t2r1__t2__upload__20260904.zip` / `b4t2r1b__t2__upload__20260904.zip`；portal Model 列显示为成员短名） |
| Board/phase | T2:heart:val_interp |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-04 19:52) |
| Run | `B4-T2-R1-FGW-ASSIGNMENT-REPAIR-2026-09-04T193416.762071+0000`（artifacts/batch4/B4-T2-R1-FGW-ASSIGNMENT-REPAIR-20260904-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-T2-R1 v0010 L1_EPS005_GLOBALMATCH` | not supplied | `submissions/candidates/T2_heart_val_interp/v0010_b4_t2_r1_l1_globalmatch/submission.h5ad` / `0f9d35db64f737bbe254e84c4df118df41282fd23509ce864254c468ef0aee25` | **57.3** | v0009 greedy 57.25 | **TIE (+0.05, within ±0.1 noise); no promotion** |
| `B4-T2-R1 v0011 L2_EPS002_GLOBALMATCH` | not supplied | `submissions/candidates/T2_heart_val_interp/v0011_b4_t2_r1_l2_globalmatch/submission.h5ad` / `7ed7aaba7229b4af3e92d20901a21b6766c05ccbcc62313acb8041d05bffed03` | **57.31** | v0009 greedy 57.25 | **TIE (+0.06, within ±0.1 noise); no promotion** |

Per-metric skills (server page; rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram | d2_shape | occupancy_dice | scale_log_ratio | neighborhood_mmd |
|---|---|---|---|---|---|---|---|---|
| v0010 L1 | 57.8 | 60.2 | 54.9 | 32.0 | 62.0 | 48.6 | 82.5 | 60.1 |
| v0011 L2 | 57.8 | 60.2 | 54.9 | 32.1 | 62.0 | 48.6 | 82.5 | 60.1 |

Consistency and decision:
- The server returned the two board scores only; no new T2 aggregate or Total was supplied. T2 selection and derived aggregates unchanged (heart_interp incumbent v0009=57.25 retained on tie; derived Total stays ≈151.2 pending page re-read and must not be quoted as a server value).
- Both lanes land within ±0.1 of greedy v0009 (57.25): the local wins (mass capture 0.718→0.796/0.873, NFS 0.0747→0.0733/0.0732, Moran 0.6743→0.6823/0.6833, hard objective 0.17168→0.17037) did **not** transfer to the board. Per the pre-declared stop rule, FGW discretization tuning is CLOSED: no further epsilon sweep.
- The two lanes are mutually indistinguishable on the server (delta 0.01; only variogram differs by 0.1): no lane preference is claimed, and eps=0.002 concentration shows no board benefit over eps=0.005.
- Both scored artifacts stay immutable; user-provided values registered as supplied.

### B4-T3-R1 — genotype-only ablation scoring round (new board best, tied lanes)
| Record date | 2026-09-05 |
|---|---|
| Submission label | B4-T3-R1-GENOTYPE-ONLY-ABLATION L1/L2（包 `b4t3r1a__t3__upload__20260905.zip` / `b4t3r1b__t3__upload__20260905.zip`） |
| Board/phase | T3:gata4 |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-05) |
| Run | `B4-T3-R1-GENOTYPE-ONLY-ABLATION-2026-09-05T010331.625263+0000`（artifacts/batch4/B4-T3-R1-GENOTYPE-ONLY-ABLATION-20260905-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-T3-R1 v0009 L1_GATA4_ZERO_ALL` | not supplied | `submissions/candidates/T3_gata4/v0009_b4_t3_r1_l1_gata4_zero_all/submission.h5ad` / `c6be65ec7d8c8a4b94bce936ff0cad985ac26f78c77ea3e4f68643f07076b088` | **46.95** | exact floor 46.8 | **new board best (+0.15); tied lanes** |
| `B4-T3-R1 v0010 L2_GATA4_ZERO_HARD_LINEAGE` | not supplied | `submissions/candidates/T3_gata4/v0010_b4_t3_r1_l2_gata4_zero_hard/submission.h5ad` / `6f789ae8cf841ca59289779682ddb7c52a0db5f2c54e368c6424f0d1f6ec38cb` | **46.95** | exact floor 46.8 | **new board best (+0.15); tied lanes** |

Per-metric skills (identical both lanes; rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):
de_score 39.2 / de_direction 49.7 / severity_slope 50.0 / mmd_u 51.5 / variogram 51.0.

Consistency and decision:
- Both lanes beat the exact floor (46.8) by +0.15: per the pre-declared branches, the old downstream residuals were very likely the main harm source. L2 == L1 exactly, so no lineage-encoding preference can be claimed at board level: the gain comes from removing the harmful residual, not from the Mesp1 gate.
- v0008 floor (46.8) is superseded as board best; all scored artifacts stay immutable. The gain is a construction effect, not mechanistic evidence; the T3-S1 scientific gate is unchanged.
- Protocol-derived (not server-returned): derived T3=46.95 and derived Total=`48.47 + 55.98 + 46.95 = 151.40`; must be confirmed against the server page and must not be quoted as server values.
- Both scored artifacts stay immutable; user-provided values registered as supplied.

### B4-T1-R1 — conservative family scoring round (no promotion; mass graft is family best)
| Record date | 2026-09-05 |
|---|---|
| Submission label | B4-T1-R1-CONSERVATIVE-FAMILY L1-L4（包 `b4t1r1{a,b,c,d}__t1__upload__20260904.zip`） |
| Board/phase | T1:val |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-05) |
| Run | `B4-T1-R1-CONSERVATIVE-FAMILY-2026-09-04T195835.729374+0000`（artifacts/batch4/B4-T1-R1-CONSERVATIVE-FAMILY-20260904-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-T1-R1 v0011 L1_DAMP050` | not supplied | `submissions/candidates/T1_val/v0011_b4_t1_r1_l1_damp050/submission.h5ad` / `d67bf5dbcbf7b69c22bdfd0269b0af7527fd75257344e1f7b3c227587b147628` | **47.58** | best 48.47 | REJECT as improvement (-0.89) |
| `B4-T1-R1 v0012 L2_POPMIX050` | not supplied | `submissions/candidates/T1_val/v0012_b4_t1_r1_l2_popmix050/submission.h5ad` / `8090413532275f6fed3acc1d36f0cb4c6ae257b64a51ad7a293596249e918a1d` | **47.77** | best 48.47 | REJECT as improvement (-0.70) |
| `B4-T1-R1 v0013 L3_MASSGRAFT025` | not supplied | `submissions/candidates/T1_val/v0013_b4_t1_r1_l3_massgraft025/submission.h5ad` / `8ac4f7cff702da7766fc6e9035ba4e6555de7e85740b6c67e82ac75d7f0b7fbb` | **47.85** | best 48.47 | family best but REJECT (-0.62) |
| `B4-T1-R1 v0014 L4_MASSGRAFT050` | not supplied | `submissions/candidates/T1_val/v0014_b4_t1_r1_l4_massgraft050/submission.h5ad` / `561a5421b11c8ba540cc5f60688fb638f0a2bd09981444e593ff3d67b0521bc8` | **46.90** | floor 47.0 | REJECT, below floor (-1.57) |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram |
|---|---|---|---|---|
| v0011 L1 | 41.0 | 54.7 | 50.0 | 43.3 |
| v0012 L2 | 40.3 | 54.2 | 50.5 | 45.0 |
| v0013 L3 | 43.0 | 55.0 | 51.2 | 40.0 |
| v0014 L4 | 42.7 | 54.1 | 49.8 | 38.8 |

Consistency and decision:
- All four lanes below best 48.47; v0014 even below the 47.0 floor. The family ranking (L3 > L2 > L1 > L4) shows 25% mass graft helps vs damp/popmix but 50% graft overshoots: the moscot mass signal is real but weak, and only at conservative dose.
- v0004 stays incumbent. Per stop rules the T1 conservative family is closed as a promotion route; whether a follow-up micro-run is justified depends on Wave 2 authorization, not on re-tuning these lanes.
- All scored artifacts stay immutable; user-provided values registered as supplied.

### B4-T3-R2 — developmental-axis repair scoring round (both below floor)
| Record date | 2026-09-14 |
|---|---|
| Submission label | B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR L1/L2（单批次包，按一批一包规则） |
| Board/phase | T3:gata4 |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-14) |
| Run | `B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR-2026-09-11T201916.227503+0000`（artifacts/batch4/B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR-20260911-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-T3-R2 v0011 L1_DELAY025` | not supplied | `submissions/candidates/T3_gata4/v0011_b4_t3_r2_l1_delay025/submission.h5ad` / `248910d4770edd207a00e2665b2cdd80e0a9411beba284744a98274a35ce2fea` | **46.45** | floor 46.8; R1 best 46.95 | REJECT (-0.35 vs floor) |
| `B4-T3-R2 v0012 L2_DELAY050` | not supplied | `submissions/candidates/T3_gata4/v0012_b4_t3_r2_l2_delay050/submission.h5ad` / `270f9afcd2ae2fefbb2b7b1e44b46d873224d25fa30f33ca18ecce1cea025511` | **46.47** | floor 46.8; R1 best 46.95 | REJECT (-0.33 vs floor) |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---|---|---|---|---|
| v0011 L1 | 38.1 | 49.4 | 50.0 | 51.2 | 50.3 |
| v0012 L2 | 38.5 | 49.3 | 50.0 | 51.0 | 49.9 |

Consistency and decision:
- Both lanes below the exact floor (46.8): per the pre-declared branch, T3 is marked **`ARCHITECTURE_RESET_REQUIRED`** — no reverse direction, no third alpha, no old-prior recombination within Batch 4.
- Delay adds nothing over the genotype-only R1 best (46.95): de_score stays the weakest metric (38.1/38.5 vs 38.8 for the floor probe), i.e. the developmental-delay hypothesis does not move differential-expression magnitude.
- T3 selection stays v0009/v0010 (46.95). All scored artifacts stay immutable; user-provided values registered as supplied.

### B4-T2-R2 — interpolation expression bridge scoring round (3 promotions)
| Record date | 2026-09-14 |
|---|---|
| Submission label | B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE（单批次包，按一批一包规则） |
| Board/phase | T2:embryo:val_interp; T2:heart:val_interp |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-14) |
| Run | `B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE-2026-09-11T201037.603176+0000`（artifacts/batch4/B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE-20260911-v1/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `B4-T2-R2 embryo v0009 L1_MEAN_BRIDGE` | not supplied | `submissions/candidates/T2_embryo_val_interp/v0009_b4_t2_r2_l1_mean_bridge/submission.h5ad` / `0fb2dc40718ac2cbbe421fceb5a93ce5c61cd1addd35a5a3a70f423f7c9e11f2` | **61.79** | best 60.15 | **promote (+1.64)** |
| `B4-T2-R2 embryo v0010 L2_MEAN_MASS_BRIDGE` | not supplied | `submissions/candidates/T2_embryo_val_interp/v0010_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad` / `34caae70aff220b6a754dedea54bd27a5c4d0962305341994dd239f60f14364e` | **62.29** | best 60.15 | **new board best (+2.14)** |
| `B4-T2-R2 heart v0012 L1_MEAN_BRIDGE` | not supplied | `submissions/candidates/T2_heart_val_interp/v0012_b4_t2_r2_l1_mean_bridge/submission.h5ad` / `94e2b018b5a90712a3a815128fb2a25e891a06d3359923ec3cc9b9a0d3c60029` | **56.27** | best 57.25 | REJECT (-0.98) |
| `B4-T2-R2 heart v0013 L2_MEAN_MASS_BRIDGE` | not supplied | `submissions/candidates/T2_heart_val_interp/v0013_b4_t2_r2_l2_mean_mass_bridge/submission.h5ad` / `9080cfc3adbed773ad57a601548e15427b25696461b68d083a45c522b85daf08` | **62.04** | best 57.25 | **new board best (+4.79)** |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram | d2_shape | occupancy_dice | scale_log_ratio | neighborhood_mmd |
|---|---|---|---|---|---|---|---|---|
| embryo v0009 L1 | 55.8 | 70.1 | 60.0 | 52.9 | 52.8 | 46.6 | 91.9 | 63.3 |
| embryo v0010 L2 | 54.1 | 67.5 | 60.2 | 52.0 | 54.6 | 51.2 | 90.8 | 65.9 |
| heart v0012 L1 | 55.3 | 59.1 | 54.0 | 29.8 | 62.0 | 48.6 | 82.5 | 59.2 |
| heart v0013 L2 | 60.6 | 65.8 | 62.5 | 28.4 | 65.4 | 47.8 | 97.9 | 65.8 |

Consistency and decision:
- Embryo: both lanes promote; L2 (mean+mass, 62.29) is the new board best, +2.14. L2 beats L1 by +0.50 with occupancy_dice 51.2 vs 46.6 — composition resampling is the incremental gain on top of the mean bridge.
- Heart: L2 (62.04, +4.79) is the new board best and the largest single-lane gain of Batch 4; L1 (56.27, -0.98) is rejected. The mean-shift-only lane fails while mean+mass succeeds — same pattern as embryo (L2 > L1 on both boards). Notably the 60%-clip concern did not materialize as damage: heart L2 leads on de_score (60.6), mmd_u (62.5), d2_shape (65.4), scale (97.9).
- Variogram stays the weakest submetric on heart (28.4–29.8) while everything else rises — spatial autocorrelation remains the headroom.
- Protocol-derived (not server-returned): derived T2 = `(62.29 + 62.04 + 50.53) / 3 = 58.29` and derived Total = `48.47 + 58.29 + 46.95 = 153.71`; must be confirmed against the server page and must not be quoted as server values.
- All scored artifacts stay immutable; user-provided values registered as supplied.

### Current-best snapshot — Total 153.7 (server-returned) with per-metric skills
| Record date | 2026-09-15 |
|---|---|
| Source | User-provided server page read: Total **153.7** plus per-board precise scores (T2-R3 unscored per user closeout decision, see below) |
| Selection | T1 v0004 (48.47) + T2 embryo v0010 (62.29) + T2 heart_interp v0013 (62.04) + T2 heart_extrap baseline v0001 (50.53) + T3 v0009/v0010 (46.95) |

| Board | Score |
|---|---:|
| T1:val (v0004) | 48.47 |
| T2:embryo:val_interp (v0010) | 62.29 |
| T2:heart:val_interp (v0013) | 62.04 |
| T2:heart:val_extrap (baseline v0001) | 50.53 |
| T3:gata4 (v0009/v0010 tied) | 46.95 |
| **Total (server)** | **153.7** |

Consistency and decision:
- Arithmetic check: `(62.29 + 62.04 + 50.53) / 3 = 58.29` (T2 derived); `48.47 + 58.29 + 46.95 = 153.71`, server Total **153.7**. The 0.01 gap is server-side rounding; the server-returned Total is authoritative.
- This supersedes the 151.2 snapshot: the confirmed server Total is **153.7** (+2.5 vs 151.2, all of it from T2-R2).
- T2-R3 (heart_extrap v0008/v0009/v0010) was closed unscored by explicit user decision on 2026-09-15 (see D-20260915-B4CLOSE-001); heart_extrap selection stays baseline v0001 (50.53). No score is fabricated for unsubmitted lanes.

### G1-T3 — 15-round goal T3 lanes scoring round (all below best; selection unchanged)
| Record date | 2026-09-16 |
|---|---|
| Submission label | G1 15-round goal T3 lanes（包 `g0t3__t3__upload__20260916.zip`，成员 `t3_gata4__r1prop__v0013.h5ad` 等 5 个） |
| Board/phase | T3:gata4 |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-16) |
| Run | `G1-T3-R1-DIRECTPROP-20260916-v1` / `G1-T3-R2-GRADEDDOSE-20260916-v1` / `G1-T3-R3-LINEAGEDOSE-20260916-v1` / `G1-T3-R4-COMBO-20260916-v1` / `G1-T3-R5-AMP2-20260916-v1`（artifacts/g0/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `G1-T3-R1 v0013 L_A_DIRECTPROP` | not supplied | `submissions/candidates/T3_gata4/v0013_g0_t3_r1_directprop/submission.h5ad` / `b8467cc07880f7f5ca73986738cd99cd26dfd502acecfcf21b0e6ff89b36e789` | **46.88** | best 46.95 | REJECT as improvement (-0.07) |
| `G1-T3-R2 v0014 L_B_GRADEDDOSE` | not supplied | `submissions/candidates/T3_gata4/v0014_g0_t3_r2_gradeddose/submission.h5ad` / `b3406e154e7bb6e791dddc8f815967bab9eede705c408fcd942eebd030ced552` | **46.95** | best 46.95 | TIE, v0009/v0010 stay (0.00) |
| `G1-T3-R3 v0015 L_C_LINEAGEDOSE` | not supplied | `submissions/candidates/T3_gata4/v0015_g0_t3_r3_lineagedose/submission.h5ad` / `86c12e4901e8ff14dc98d74ab257f07d050adf033d77f2d3cc37e44833ddafa3` | **46.95** | best 46.95 | TIE, v0009/v0010 stay (0.00) |
| `G1-T3-R4 v0016 L_D_COMBO` | not supplied | `submissions/candidates/T3_gata4/v0016_g0_t3_r4_combo/submission.h5ad` / `28caf0e473e4b72aba6ecc0ea1f2b7a3d6394eed8a7a6ce21b84df5fe66d9846` | **46.88** | best 46.95 | REJECT as improvement (-0.07) |
| `G1-T3-R5 v0017 L_E_AMP2X` | not supplied | `submissions/candidates/T3_gata4/v0017_g0_t3_r5_amp2/submission.h5ad` / `9e05be511b6c56271bf7313af28b0ec74afdd0d358ca25527ae664bc3c41131c` | **46.84** | best 46.95 | REJECT as improvement (-0.11) |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---|---|---|---|---|
| v0013 L_A | 39.2 | 49.6 | 50.0 | 51.5 | 50.4 |
| v0014 L_B | 39.2 | 49.7 | 50.0 | 51.5 | 51.0 |
| v0015 L_C | 39.2 | 49.7 | 50.0 | 51.5 | 51.0 |
| v0016 L_D | 39.2 | 49.6 | 50.0 | 51.5 | 50.4 |
| v0017 L_E | 39.2 | 49.6 | 50.0 | 51.4 | 50.0 |

Consistency and decision:
- No lane beats best 46.95; two TIE (v0014/v0015 = 46.95), three below (v0013/v0016 = 46.88, v0017 = 46.84). Selection stays v0009/v0010 (46.95 tied).
- de_score is pinned at 39.2 across all five lanes — the weakest submetric does not move under any Gata4-axis mechanism, consistent with the pre-registered local-kit blindness diagnosis (proxy de 0.1739 ×5 identical). Direction/slope/mmd_u/variogram move only ±0.1–1.0.
- T3 propagation-dose family is CLOSED as a promotion route (mirrors the B4-T3-R2 architecture-reset call, now with five more server points): no further hand-built lanes on this axis without a new mechanism.
- All scored artifacts stay immutable; user-provided values registered as supplied.

### G1-T2 — 15-round goal heart_extrap lanes scoring round (1 promotion: v0011 shrink)
| Record date | 2026-09-16 |
|---|---|
| Submission label | G1 15-round goal T2-extrap lanes（包 `g0t2__t2__upload__20260916.zip`，成员 `t2_hrt_ext__r2shr__v0011.h5ad` 等 6 个） |
| Board/phase | T2:heart:val_extrap |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-16) |
| Run | `G1-T2-R1-EXTRAP-GATE-20260916-v1`（门控） / `G1-T2-R2-SHRINK-20260916-v1` / `G1-T2-R3-SPATIAL-20260916-v1` / `G1-T2-R4-KSWEEP-20260916-v1` / `G1-T2-R5-K60-20260916-v1`（artifacts/g0/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `G1-T2-R2 v0011 L1_SHRINK` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0011_g0_t2_r2_shrink/submission.h5ad` / `38edc52e3a9af7cdf87085c0f87d12d630dcfec8d5bb55735b383e62017d44e9` | **50.64** | baseline 50.53 | **promote (+0.11), new board best** |
| `G1-T2-R3 v0012 L1_SPATIAL_K15` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0012_g0_t2_r3_spatial/submission.h5ad` / `4456cc7568a237093d9e944f36a5877d4d0bb465342f40df7ee50c04b0c00873` | **50.26** | baseline 50.53 | REJECT (-0.27) |
| `G1-T2-R4 v0013 L1_K07` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0013_g0_t2_r4_k07/submission.h5ad` / `451837a8d9b69f2cf87c1147e2401866baad1165fe837bc9cbc09516d8f6cd0b` | **50.32** | baseline 50.53 | REJECT (-0.21) |
| `G1-T2-R4 v0014 L2_K15` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0014_g0_t2_r4_k15/submission.h5ad` / `d7583979c33ca686143a270e7f195e3daf4dfe9f7e459db658c7735b804cec99` | **50.26** | baseline 50.53 | REJECT (-0.27) |
| `G1-T2-R4 v0015 L3_K30` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0015_g0_t2_r4_k30/submission.h5ad` / `04e360c51dbf01295a9c2a6eaf22061d68bea9a7f1118260ccfb1256f6c134fa` | **50.28** | baseline 50.53 | REJECT (-0.25) |
| `G1-T2-R5 v0016 L1_K60` | not supplied | `submissions/candidates/T2_heart_val_extrap/v0016_g0_t2_r5_k60/submission.h5ad` / `1f02c2f2605217644852443baab7d04222c3490cb5f248223bad4bf4f087026d` | **50.25** | baseline 50.53 | REJECT (-0.28) |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram | d2_shape | occupancy_dice | scale_log_ratio | neighborhood_mmd |
|---|---|---|---|---|---|---|---|---|
| v0011 L1 shrink | 50.0 | 51.9 | 49.9 | 48.5 | 46.2 | 53.2 | 49.7 | 52.5 |
| v0012 k15 | 49.2 | 52.2 | 49.9 | 45.3 | 46.2 | 53.2 | 49.7 | 52.5 |
| v0013 k07 | 49.2 | 52.3 | 50.0 | 45.9 | 46.2 | 53.2 | 49.7 | 52.5 |
| v0014 k15 | 49.2 | 52.2 | 49.9 | 45.3 | 46.2 | 53.2 | 49.7 | 52.5 |
| v0015 k30 | 49.6 | 52.1 | 49.9 | 45.0 | 46.2 | 53.2 | 49.7 | 52.6 |
| v0016 k60 | 49.6 | 52.1 | 49.8 | 44.6 | 46.2 | 53.2 | 49.7 | 52.7 |

Consistency and decision:
- v0011 (t-shrink C=2) = **50.64 (+0.11)** → **new heart_extrap board best** (displaces baseline v0001 50.53). The T1-winning mechanism DID port to extrap at server level even though the local gate called it pinned-negative (local 0.2466/0.4183 vs baseline 0.2466/0.4221). Local proxy direction was inverted on this family — recorded as a proxy-lesson update.
- All five spatial-smoothing lanes (k07–k60) score BELOW baseline (-0.21 to -0.28) despite winning locally (local 0.2603 > 0.2466). The local extrap proxy is ADVERSARIAL on the spatial family: local win → server loss. Spatial-smoothing family is CLOSED as a promotion route on heart_extrap.
- Net effect: heart_extrap 50.53 → 50.64 (+0.11); selection updates to v0011. New weakest board is now T3 (46.95).
- All scored artifacts stay immutable; user-provided values registered as supplied.

### G1-T1 — 15-round goal lanes scoring round (no promotion; best stays v0004)
| Record date | 2026-09-17 |
|---|---|
| Submission label | G1 15-round goal T1 lanes（包 `g0t1__t1__upload__20260916.zip`，成员 `t1_val__r1node__v0015.h5ad` 等 7 个） |
| Board/phase | T1:val |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-17) |
| Run | `G1-T1-R1-NEURAL-ODE-20260916-v1` / `G1-T1-R2-SUBSTATE-20260916-v1` / `G1-T1-R3-MATURITY-20260916-v1` / `G1-T1-R4-SHRINK-20260916-v1` / `G1-T1-R5-SHRINKSWEEP-20260916-v1`（artifacts/g0/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `G1-T1-R1 v0015 L1_NODE` | not supplied | `submissions/candidates/T1_val/v0015_g0_t1_r1_neural_ode/submission.h5ad` / `a2ca6bd555e3e01b16026c15144063d733916b6204180aec163c1edc894d4273` | **48.51** | best 48.47 | TIE (+0.04, within ±0.1), v0004 stays |
| `G1-T1-R2 v0016 L1_SUB` | not supplied | `submissions/candidates/T1_val/v0016_g0_t1_r2_substate/submission.h5ad` / `889f87bbf2f3c327d304856532ea6902569f6a13f874319e589fef216126d2c1` | **48.14** | best 48.47 | REJECT (-0.33) |
| `G1-T1-R3 v0017 L1_MAT` | not supplied | `submissions/candidates/T1_val/v0017_g0_t1_r3_maturity/submission.h5ad` / `594db45fc5be4a024e3ab0842b7e90461d42a8adda1d9f5d8292b899b774c1fb` | **47.46** | best 48.47 | REJECT (-1.01) |
| `G1-T1-R4 v0018 L1_C2` | not supplied | `submissions/candidates/T1_val/v0018_g0_t1_r4_shrink/submission.h5ad` / `8dbcabcc096082aaec75fbd54a797628f1eda49edf2c527d643fb94de050cc6d` | **48.48** | best 48.47 | TIE (+0.01), v0004 stays |
| `G1-T1-R5 v0019 L1_C1` | not supplied | `submissions/candidates/T1_val/v0019_g0_t1_r5_c1/submission.h5ad` / `617cdd3db1362054856333e935c9ea77d813a4d3ec786ef2f4ffda844a115c7e` | **48.54** | best 48.47 | TIE (+0.07, within ±0.1), v0004 stays |
| `G1-T1-R5 v0020 L2_C2` | not supplied | `submissions/candidates/T1_val/v0020_g0_t1_r5_c2/submission.h5ad` / `6ec62b099fc0802b8cddc127423bda825101e2560ec1dba530bc3f865c0ab07f` | **48.48** | best 48.47 | TIE (+0.01), v0004 stays |
| `G1-T1-R5 v0021 L3_C4` | not supplied | `submissions/candidates/T1_val/v0021_g0_t1_r5_c4/submission.h5ad` / `ab44c7036088141c24cd5cb523537e2c9d9a04fda1d43a64e588116b23df0698` | **48.34** | best 48.47 | REJECT (-0.13) |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram |
|---|---|---|---|---|
| v0015 node | 43.8 | 55.8 | 51.6 | 40.6 |
| v0016 substate | 43.8 | 55.8 | 51.1 | 39.5 |
| v0017 maturity | 43.9 | 55.1 | 50.3 | 38.0 |
| v0018 shrink C2 | 43.2 | 55.1 | 51.1 | 42.9 |
| v0019 shrink C1 | 43.6 | 55.4 | 51.2 | 42.1 |
| v0020 shrink C2 | 43.2 | 55.1 | 51.1 | 42.9 |
| v0021 shrink C4 | 42.6 | 54.7 | 50.8 | 44.0 |

Consistency and decision:
- No promotion: best stays v0004 (48.47). v0019 (+0.07) and v0015 (+0.04) fall inside the standing ±0.1 TIE band → incumbent stays per rule (same rule as B4-T2-R1).
- Shrink sweep ordering C1 (48.54) > C2 (48.48) = R4 (48.48) > C4 (48.34): monotone preference for lighter shrinkage, but the full sweep spans only 0.20 — C is a weak knob.
- Proxy lesson (positive control): the T1 local proxy RANKED correctly — locally-PROMOTED shrink lanes all scored ≥48.34 on server (all within 0.13 of best), locally-rejected lanes (node/substate/maturity) all scored below. T1 proxy is the only one of three tasks whose gate direction survived contact with the server (T2-extrap inverted, T3 blind).
- Submetric note: shrink lanes trade de_score (43.2–43.6 < best 43.8) for variogram (42.1–44.0 > 40.6); v0021/C4 pushes variogram highest (44.0) but loses de most (42.6) → net negative. The T1 ceiling is a de↔variogram trade, not a single weak term.
- All scored artifacts stay immutable; user-provided values registered as supplied.

### G1-T3-R9..R13 — 30-round plan lanes scoring round (one exact tie, one catastrophe; selection unchanged)
| Record date | 2026-09-17 |
|---|---|
| Submission label | G1-T3 30 轮计划 R9–R13（包 `g1t3__t3__upload__20260917.zip`，成员 `t3_gata4__r9hop2__v0021.h5ad` 等 5 个；同包 R6–R8 v0018–v0020 已上传仍待评分） |
| Board/phase | T3:gata4 |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-17) |
| Run | `G1-T3-R9-HOP2` / `R10-GRAPH` / `R11-SIGNMAX` / `R12-DEBIAS` / `R13-SPATIAL`（artifacts/g0/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `G1-T3-R9 v0021 L_A_HOP2` | not supplied | `submissions/candidates/T3_gata4/v0021_g0_t3_r9_hop2/submission.h5ad` / `1bde8b96a0e8263e579abb8bab666fa98c29dafe18347dbccf47d902af7be5c0` | **46.88** | best 46.95 | TIE (-0.07, within ±0.1), v0009/v0010 stay |
| `G1-T3-R10 v0022 L_A_GRAPH` | not supplied | `submissions/candidates/T3_gata4/v0022_g0_t3_r10_graph/submission.h5ad` / `5423dc569723ef87c1af4d06d7826df2708e45f87bb1dbc491a96116735821d6` | **46.93** | best 46.95 | TIE (-0.02, within ±0.1), v0009/v0010 stay |
| `G1-T3-R11 v0023 L_A_SIGNMAX` | not supplied | `submissions/candidates/T3_gata4/v0023_g0_t3_r11_signmax/submission.h5ad` / `22340b14d9139c1dff044371043170398358f3d995784aea8f543ed5374bfbc4` | **46.95** | best 46.95 | exact TIE (0.00), v0009/v0010 stay |
| `G1-T3-R12 v0024 L_A_DEBIAS` | not supplied | `submissions/candidates/T3_gata4/v0024_g0_t3_r12_debias/submission.h5ad` / `b1a3c01d9379624dd67a1fb06fd244c5e2039061bed34c281fa7b2efbfbb46d3` | **46.90** | best 46.95 | TIE (-0.05, within ±0.1), v0009/v0010 stay |
| `G1-T3-R13 v0025 L_A_SPATIAL` | not supplied | `submissions/candidates/T3_gata4/v0025_g0_t3_r13_spatial/submission.h5ad` / `4f64ce1e19e8507cf691f5024cbb86ec9a03f4117b27f3984a62655a8b62a93c` | **43.30** | best 46.95 | **CATASTROPHIC REJECT (-3.65)** |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---|---|---|---|---|
| v0021 hop2 | 39.2 | 49.6 | 50.0 | 51.5 | 50.4 |
| v0022 graph | 39.6 | 49.8 | 50.0 | 51.6 | 49.0 |
| v0023 signmax | 39.6 | 49.7 | 50.0 | 51.5 | 49.6 |
| v0024 debias | 39.2 | 49.7 | 50.0 | 51.5 | 50.5 |
| v0025 spatial | 38.1 | 49.3 | 50.0 | 42.1 | 25.0 |

Consistency and decision:
- Selection stays v0009/v0010 (46.95 tied). v0023 is an exact tie → incumbent stays per the standing ±0.1 TIE rule (same rule as B4-T2-R1, G1-T1, G1-T3-R2/R3); v0021/v0022/v0024 also fall inside the band. No co-promotion for late ties (precedent: G1-T3-R2/R3 v0014/v0015).
- de_score moves for the first time: v0022/v0023 = **39.6 (+0.4)** vs the pinned 39.2 across all ten previous G1/B4 lanes — the weakest submetric finally moves under graph/signmax mechanisms. But variogram gives it back (49.0/49.6 vs 51.0): the T3 ceiling is now a de↔variogram trade, same shape as T1's. v0024 debias reproduces baseline direction to 4 decimals locally yet scores -0.05: offset-debias adds nothing.
- R13 spatial is a catastrophe (mmd_u -9.4, variogram -26.0, total -3.65), mirroring the T2-extrap spatial family (local PROMOTED → server -0.21…-0.28, family closed D-20260916-G0T2-001). The local spatial proxy is adversarial on T3 as well: spatial smoothing is CLOSED as a promotion route on T3; the disclosed lib-ratio/Jensen note did not save it.
- R6/R7/R8 (v0018/v0019/v0020, same pack) remain score_pending; no claim until return. Server Total stays **153.7** (no new Total supplied; T3 best unchanged so derived aggregates unchanged).
- All scored artifacts stay immutable; user-provided values registered as supplied.

### G1-T1-D3 — OT-CFM field-forecast lane scoring round (REJECT; first T1-proxy false positive)
| Record date | 2026-09-17 |
|---|---|
| Submission label | G1-T1-D3 单包 `g1t1d3__t1__upload__20260917.zip`（成员 `t1_val__d3otcfm__v0022.h5ad`；首适用 D-20260917-T1UPLOAD-001 上传仲裁政策） |
| Board/phase | T1:val |
| Source | User-provided server results in score-return message (leaderboard rows 2026-09-17) |
| Run | `G1-T1-D3-FLOW-20260917-v1` + `scripts/g0/t1_d3_build.py`（artifacts/g0/） |

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `G1-T1-D3 v0022 L1_OTCFM` | not supplied | `submissions/candidates/T1_val/v0022_g0_t1_d3_otcfm/submission.h5ad` / `269dbfd64f97aadec1cf309dcb1ae89c61b2b9a2c89fa0c78d3d9292823cd687` | **45.3** | best 48.47; floor 47.0 | **REJECT (-3.17, below floor)** |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram |
|---|---|---|---|---|
| v0022 otcfm | 43.7 | 55.9 | 47.9 | 30.2 |

Consistency and decision:
- Arithmetic check with T1 weights (0.25/0.25/0.30/0.20): 0.25×43.7+0.25×55.9+0.30×47.9+0.20×30.2 = 45.31 → 45.3 ✓. Deltas vs best (43.8/55.9/51.5/40.6): de -0.1, dir 0.0, mmd -3.6, variogram **-10.4**. The entire loss sits in distribution/covariation.
- Proxy lesson (honest revision): first T1-proxy false positive. Local de 0.9623 (best-ever local) transferred as server de 43.7 (≈par with best 43.8) — de decoupled via variogram collapse. BUT the local distribution-side flag warned correctly: field energy 0.486 vs baseline 0.434. Refined doctrine: local de/dir alone insufficient; distribution-side local metrics (energy/variogram) carry veto signal. The G0 ranking claim stands for the lanes it covered; v0022 bounds its scope.
- Selection stays v0004 (48.47). Server Total stays **153.7** (T1 best unchanged). D3 remains CLOSED; upload-arbitration policy (D-20260917-T1UPLOAD-001) worked as designed — arbitration returned REJECT, no promotion claimed.
- All scored artifacts stay immutable; user-provided values registered as supplied.

### G1-T3-R6..R8 — remaining unified-pack scores (TIE / TIE / REJECT)

| Record date | 2026-09-20 |
|---|---|
| Board/phase | T3:gata4 |
| Source | User-provided server results in this score-return message; submission IDs and submission timestamps not supplied |
| Package | `deliveries/g1t3__t3__upload__20260917.zip`; member identity mapped via UPLOAD_MANIFEST.tsv and INDEX SHA256 |

The supplied R6 label omitted `.h5ad`; mapped to the exact package member `t3_gata4__r6cipher__v0018.h5ad`. No artifact was renamed.

| Candidate / portal file | Submission ID | Submission file / SHA256 | Server score | Decision vs incumbent 46.95 |
|---|---|---|---:|---|
| `G1-T3-R6 / t3_gata4__r6cipher__v0018.h5ad` | not supplied | `submissions/candidates/T3_gata4/v0018_g0_t3_r6_cipher/submission.h5ad` / `a82b16e008eb9158097b356322db455604117fee0edd7fbd13112768765aab3f` | **46.94** | TIE (-0.01); no promotion |
| `G1-T3-R7 / t3_gata4__r7split__v0019.h5ad` | not supplied | `submissions/candidates/T3_gata4/v0019_g0_t3_r7_split/submission.h5ad` / `4b6c5b4541219d3726d8f85100aedd16b6e5cb02a4e2bb4c7c5a4a2c0b0e133d` | **46.95** | exact TIE (0.00); no promotion |
| `G1-T3-R8 / t3_gata4__r8knk__v0020.h5ad` | not supplied | `submissions/candidates/T3_gata4/v0020_g0_t3_r8_knk/submission.h5ad` / `d8b50dd9721ca3a9a821401d9603d7ce1ecec4408a73f03bbbe49246aeb2f717` | **46.64** | REJECT (-0.31); no promotion |

Per-metric skills (user values preserved; also registered in SERVER_SUBMETRIC_REGISTRY.tsv):

| Lane | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---|---|---|---|---|
| v0018 r6cipher | 39.2 | 49.7 | 50.0 | 51.5 | 50.8 |
| v0019 r7split | 39.2 | 49.7 | 50.0 | 51.5 | 50.9 |
| v0020 r8knk | 39.2 | 50.3 | 50.0 | 51.5 | 45.2 |

Decision and limits:
- R6 is within the standing ±0.1 TIE band; R7 is an exact tie; R8 is rejected. Selection stays v0009/v0010 (46.95); no late-tie co-promotion.
- All three de_score values remain 39.2. R8 improves de_direction by 0.6 relative to R7 but loses 5.7 variogram points; its board score is lower by 0.31. These are observed score differences, not causal-mechanism evidence.
- All eight candidates R6–R13 in this package now have registered scores. This closes the score-return queue, not a claim that all planned 30 research rounds were executed. Further rounds require a separate decision; no automatic run or upload.
- No new server Total was supplied; the last confirmed Total remains 153.7. Published rounded skills are stored as supplied rather than used to replace the reported board scores.
- Canonical artifact SHA256 checks passed for these three files; scored artifacts remain immutable. Scientific gate unchanged; blocks_submission: false.
- Decision: D-20260920-G0T3R6R8-001.

<a id="t3-next-r1r2-score-return-20260920"></a>
## T3 NEXT R1/R2 score return — 2026-09-20

Source / raw evidence: user transcribed the following portal model names, board totals and five skills in the current conversation. Submission IDs, timestamps and screenshots were not supplied; no independent portal query was performed. Values below preserve supplied precision; no total was reconstructed from rounded skills. All four local artifact SHA256 values match submissions/INDEX.tsv. Artifacts remain immutable.

| Portal model | Board score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|---:|
| t3_gata4__r1graph__v0026.h5ad | 46.93 | 39.6 | 49.8 | 50.0 | 51.6 | 49.0 |
| t3_gata4__r1sign__v0027.h5ad | 46.95 | 39.6 | 49.7 | 50.0 | 51.5 | 49.6 |
| t3_gata4__r2adapt__v0030.h5ad | 46.6 | 38.1 | 49.7 | 50.0 | 51.4 | 51.1 |
| t3_gata4__r2random__v0031.h5ad | 46.12 | 37.4 | 49.0 | 50.0 | 51.1 | 50.3 |

Decisions:
- v0026: 46.93, exact tie with parent v0022; -0.02 versus incumbent. TIE under existing ±0.1 band; not promoted.
- v0027: 46.95, exact tie with parent v0023 and incumbent; not co-promoted.
- v0030: 46.6, -0.35 versus parent v0009/incumbent; REJECT.
- v0031: 46.12, -0.83 versus parent v0009/incumbent; REJECT.
- Adaptive replacement beats matched random replacement by 0.48 on this returned score, but both underperform the parent. This is one ablation comparison, not evidence of statistical significance or causal validity.
- R1 rank reconstruction shows no board-total improvement over either parent. R2 current candidates are not retained as best. Selection remains v0009/v0010 (46.95). R5 v0032/v0033 remain unsubmitted/unscored.
- No new overall server Total supplied. No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260920-T3NEXTSCORE-001. Candidate identities, parents, paths and SHA256 remain authoritative in submissions/INDEX.tsv.

<a id="t3-next-r5-score-return-20260921"></a>
## T3 NEXT R5 score return — 2026-09-21

Source / raw evidence: user transcribed these exact portal names, board totals and five skills in the current conversation. Submission IDs, timestamps and screenshots were not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Both local artifact SHA256 values match submissions/INDEX.tsv; artifacts remain immutable. Identities, parent v0009 and contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|---:|
| t3_gata4__r5off__v0032.h5ad | 46.95 | 39.2 | 49.7 | 50.0 | 51.5 | 51.0 |
| t3_gata4__r5on__v0033.h5ad | 46.95 | 39.2 | 49.7 | 50.0 | 51.5 | 51.0 |

Decision and limits:
- Both totals exactly tie parent v0009 and incumbent 46.95 (delta 0.00); no promotion, selection v0009/v0010 unchanged.
- Signal-on versus signal-off totals and all five displayed skills are identical. This tested minimal SIGNOR implementation shows no gain at the reported precision; this is not proof that cell communication is biologically irrelevant or that the artifacts are identical.
- R5 score-return queue closed; lane SHIPPED (scored, no gain). R6 remains FAILED_DISASTER with no candidate; no new training or submission in this registration task.
- No overall server Total supplied. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260921-T3R5SCORE-001.

## T2 H-N2 LOWAMP score return — 2026-09-28

Source / raw evidence: user transcribed the two portal board totals and their eight
per-metric skills in the current conversation. Submission IDs and timestamps were not
supplied; no independent portal query was performed. Values are recorded exactly as
supplied and are not reconstructed from the rounded skills.

| Candidate | Submission ID | Submission file / SHA-256 | Server score | Reference points | Decision |
|---|---|---|---:|---|---|
| `T2-H-N2-LOWAMP v0014 L1_SHARED` | not supplied | `submissions/candidates/T2_heart_val_interp/v0014_h_n2_lowamp_shared/submission.h5ad` / `23a0488260abf799...` | **61.52** | vs incumbent v0013 62.04 | **not promoted** (-0.52) |
| `T2-H-N2-LOWAMP v0015 L2_PERSTAGE` | not supplied | `submissions/candidates/T2_heart_val_interp/v0015_h_n2_lowamp_perstage/submission.h5ad` / `203bbcb68712e247...` | **61.52** | vs incumbent v0013 62.04 | **not promoted** (-0.52) |

Per-metric skills (rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`):

| Lane | de_score | de_direction | mmd_u | variogram | d2_shape | occupancy_dice | scale_log_ratio | neighborhood_mmd | board |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| incumbent v0013 (B4-T2-R2 L2) | 60.6 | 65.8 | 62.5 | 28.4 | 65.4 | 47.8 | 97.9 | 65.8 | **62.04** |
| `H-N2-LOWAMP v0014 L1` | 61.2 | 66.0 | 62.6 | **25.4** | 65.4 | 47.8 | 97.9 | **64.5** | **61.52** |
| `H-N2-LOWAMP v0015 L2` | 60.6 | 66.0 | 62.6 | **25.4** | 65.4 | 47.8 | 97.9 | **64.7** | **61.52** |
| delta v0014 | +0.6 | +0.2 | +0.1 | **-3.0** | 0.0 | 0.0 | 0.0 | **-1.3** | **-0.52** |
| delta v0015 | 0.0 | +0.2 | +0.1 | **-3.0** | 0.0 | 0.0 | 0.0 | **-1.1** | **-0.52** |

Decision and limits:
- **Selection UNCHANGED.** Both lanes score 61.52, below the incumbent 62.04 by 0.52,
  which is well outside the standing +/-0.1 TIE band. `T2:heart:val_interp` stays on
  v0013. **No Total changes as a result of this scoring round** (the Total is the sum
  over the registered per-board selection, which is untouched).
- **The three geometry submetrics are bit-identical to the incumbent**
  (d2_shape 65.4, occupancy_dice 47.8, scale_log_ratio 97.9). This is a **positive
  control** confirming the byte-identity claim: the submission really differs from
  v0013 only in the expression matrix.
- **The whole loss is on the expression side**, and `variogram` (-3.0) is the single
  largest contributor, followed by `neighborhood_mmd` (-1.3 / -1.1).
- **L1 and L2 are exactly tied at 61.52 with 6 of 8 submetrics identical.** The
  cross-stage coefficient-sharing constraint -- the route's core hypothesis and the
  reason the second arm existed -- is **empirically null**.
- Both artifacts stay immutable and are retained as evidence. No new candidate.

<a id="t1-next-r1-score-return-20260926"></a>
## T1 NEXT R1 score return — 2026-09-26

Source / raw evidence: user transcribed the portal Model name, board total and four skills in the current conversation. Submission ID, timestamp and screenshots were not supplied; no independent portal query was performed. Values preserve supplied precision; reported total is not reconstructed from rounded skills (weights-check 0.25/0.25/0.30/0.20 over supplied 1-decimal skills = 50.84 vs reported 50.82; difference is rounding). Local artifact SHA256 matches submissions/INDEX.tsv; artifact immutable. Parent v0004, contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|
| t1_val__r1qshape__v0023.h5ad | 50.82 | 44.0 | 57.4 | 53.1 | 47.8 |

Decision and limits:
- v0023 50.82 vs incumbent v0004 48.47: +2.35, far outside the ±0.1 TIE band. PROMOTED: new T1 selection and highest observed (also above v0019 48.54). Server Total updates 153.7 → 156.06 (50.82 + 58.29 + 46.95; T2/T3 components unchanged).
- Skill-level read (descriptive, not causal): all four returned skills beat v0004's recorded submetrics (de 43.8→44.0, dir 55.9→57.4, mmd 51.5→53.1, vario 40.6→47.8; largest move on variogram +7.2). The report-scenario prediction (B uniform gains incl. variogram −69%) is consistent in direction with the server outcome, but local-proxy insufficiency stands: this is one arbitration success, not proof the proxy ranks reliably.
- R1 lane SHIPPED (scored, promoted). R1 second-candidate slot stays in reserve. R5/R3/R4 proceed against the new v0023 baseline; strict-shift remains a secondary control, not the bar.
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260926-T1V23SCORE-001.

<a id="t3-five-repair-score-return-20260927"></a>
## T3 FIVE + repairs score return — 2026-09-27

Source / raw evidence: user transcribed eight portal Model names, board totals and five skills each in the current conversation. Submission IDs, timestamps and screenshots were not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Local artifact SHA256 values match submissions/INDEX.tsv; artifacts immutable. Parent v0009, contract PASS remain in that index. v0037/v0040/v0041 still score_pending (not in this return).

| Portal model | Board score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|---:|
| t3_gata4__n1quant__v0042.h5ad | 46.95 | 39.2 | 49.7 | 50.0 | 51.5 | 51.0 |
| t3_gata4__n3latent__v0044.h5ad | 47.47 | 40.8 | 49.5 | 50.0 | 52.1 | 51.2 |
| t3_gata4__o2shrink__v0046.h5ad | 47.65 | 41.2 | 49.7 | 50.0 | 52.1 | 51.3 |
| t3_gata4__o1stable__v0047.h5ad | 46.97 | 39.2 | 49.8 | 50.0 | 51.5 | 51.0 |
| t3_gata4__n2hurdle__v0048.h5ad | 47.93 | 42.6 | 50.0 | 50.0 | 51.8 | 49.3 |
| t3_gata4__r6meanfix__v0034.h5ad | 47.53 | 40.8 | 49.7 | 50.0 | 52.2 | 51.3 |
| t3_gata4__r6graphfix__v0035.h5ad | 47.03 | 40.0 | 49.2 | 50.0 | 51.3 | 50.8 |
| t3_gata4__r3linfix__v0036.h5ad | 46.98 | 39.2 | 49.8 | 50.0 | 51.5 | 51.0 |

Decision and limits:
- v0048 47.93 vs incumbent 46.95: +0.98, far outside the ±0.1 TIE band. PROMOTED: new T3 selection and highest observed. Server Total updates 156.06 → 157.04 (50.82 + 58.29 + 47.93; T1/T2 components unchanged; T2 heart_extrap 50.64-vs-50.53 OPEN item unaffected).
- v0046 (+0.70), v0034 (+0.58), v0044 (+0.52) all beat the old incumbent but trail the new best; recorded as scored backups. v0035 (+0.08), v0036 (+0.03), v0047 (+0.02) TIE; v0042 exact tie.
- Skill-level read (descriptive, not causal): v0048's gain concentrates in de_score (39.2→42.6, +3.4) with direction at 50.0; its variogram (49.3) trails v0046/v0034 (51.3). severity_slope reads 50.0 on all eight returns — floor-anchored, carries no discriminative signal in this batch.
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260927-T3SCORE-001.

<a id="t1-five-score-return-20260928"></a>
## T1 FIVE score return — 2026-09-28

Source / raw evidence: user transcribed five portal Model names, board totals and four skills each in the current conversation. Submission IDs, timestamps and screenshots were not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills (T1 weights 0.25/0.25/0.30/0.20 give 51.93/51.21/50.455/51.41/49.215 versus reported 51.92/51.23/50.44/51.38/49.19; differences are rounding). Local artifact identities match submissions/INDEX.tsv; artifacts immutable. Parent v0023 and contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|
| t1_val__n1density__v0024.h5ad | 51.92 | 45.5 | 58.5 | 54.3 | 48.2 |
| t1_val__n2param__v0025.h5ad | 51.23 | 44.4 | 57.0 | 53.6 | 48.9 |
| t1_val__n3borrow__v0026.h5ad | 50.44 | 43.9 | 56.8 | 53.0 | 46.9 |
| t1_val__o1mass__v0027.h5ad | 51.38 | 44.0 | 57.6 | 53.7 | 49.5 |
| t1_val__o2rate__v0028.h5ad | 49.19 | 42.1 | 55.2 | 50.7 | 48.4 |

Decision and limits:
- v0024 51.92 vs parent/incumbent v0023 50.82: +1.10, outside the ±0.1 TIE band. PROMOTED: new T1 selection and highest observed. Server Total updates 157.04 → 158.14 (51.92 + 58.29 + 47.93; T2/T3 components unchanged; heart_extrap 50.64-vs-50.53 OPEN item unaffected).
- v0027 +0.56 and v0025 +0.41 also beat v0023 but trail v0024; scored backups, not co-promoted. v0026 −0.38 and v0028 −1.63 REJECT versus the parent.
- Skill-level read versus v0023 (44.0/57.4/53.1/47.8), descriptive not causal: v0024 improves all four skills, largest on de_score +1.5. v0027's gain is mostly variogram +1.7 with de unchanged. v0028 loses de/dir/mmd and only variogram rises. This does not identify a biological mechanism.
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260928-T1FIVESCORE-001.

<a id="t3-repair-r3r4-score-return-20260928"></a>
## T3 REPAIR R3/R4 remaining lanes score return — 2026-09-28

Source / raw evidence: user transcribed three portal Model names, board totals and five skills each in the current conversation. Submission IDs, timestamps and screenshots were not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Local artifact SHA256 values match submissions/INDEX.tsv (v0037 `9b82a600…`, v0040 `7bc782fb…`, v0041 `879acc88…`); artifacts immutable. Parent v0009, contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|---:|
| t3_gata4__r3splfix__v0037.h5ad | 46.98 | 39.2 | 49.8 | 50.0 | 51.5 | 51.0 |
| t3_gata4__r4panelfix__v0040.h5ad | 47.08 | 39.6 | 49.7 | 50.0 | 51.5 | 51.0 |
| t3_gata4__r4medfix__v0041.h5ad | 47.09 | 39.6 | 49.8 | 50.0 | 51.5 | 51.0 |

Decision and limits:
- v0037 46.98 vs parent v0009 46.95: +0.03, inside the ±0.1 TIE band; vs incumbent v0048 47.93: -0.95 REJECT as improvement. Five skills identical to sibling v0036 (39.2/49.8/50.0/51.5/51.0) to the supplied precision.
- v0040 47.08 vs parent 46.95: +0.13, outside TIE as a parent comparison; vs incumbent 47.93: -0.85 REJECT as improvement. de_score 39.6 (+0.4 vs pinned 39.2) matches the graph/signmax level seen on v0022/v0023, but variogram stays 51.0 with no net gain.
- v0041 47.09 vs parent 46.95: +0.14; vs incumbent 47.93: -0.84 REJECT as improvement. Differs from v0040 only on de_direction (+0.1) at the supplied precision.
- Selection stays v0048 (47.93). No new Total supplied; last confirmed Total remains 158.14 as derived (51.92 + 58.29 + 47.93; T2 heart_extrap 50.64-vs-50.53 OPEN item unaffected). severity_slope reads 50.0 on all three returns — floor-anchored, carries no discriminative signal, consistent with all prior T3 returns.
- Repair queue is now closed on scores: v0034/v0035/v0036/v0037/v0040/v0041 all scored; v0038/v0039 stay invalidated_unsubmitted (withdrawn). No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260928-T3REPAIR2-001.

<a id="t1-round2-score-return-20260928"></a>
## T1 ROUND2 score return — 2026-09-28

Source / raw evidence: user transcribed five portal Model names, board totals and four skills each in the current conversation. Submission IDs, timestamps and screenshots were not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills (T1 weights 0.25/0.25/0.30/0.20 give 52.485/52.485/50.485/51.94/51.065 versus reported 52.5/52.49/50.51/51.97/51.10; differences are rounding). Local artifact SHA256 values match submissions/INDEX.tsv; artifacts immutable. Parent v0024 and contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|
| t1_val__n1stack__v0029.h5ad | 52.5 | 45.8 | 58.5 | 54.9 | 49.7 |
| t1_val__n2composition__v0030.h5ad | 52.49 | 45.6 | 59.5 | 54.7 | 49.0 |
| t1_val__n3states__v0031.h5ad | 50.51 | 43.7 | 57.0 | 52.7 | 47.5 |
| t1_val__o1caldensity__v0032.h5ad | 51.97 | 45.7 | 58.3 | 54.4 | 48.1 |
| t1_val__o2shrinkmass__v0033.h5ad | 51.10 | 43.5 | 57.4 | 53.2 | 49.4 |

Decision and limits:
- v0029 52.5 vs parent/incumbent v0024 51.92: +0.58, outside the ±0.1 TIE band. PROMOTED: new T1 selection and highest observed. Server Total updates 158.14 → 158.72 (52.5 + 58.29 + 47.93; T2/T3 components unchanged; heart_extrap 50.64-vs-50.53 OPEN item unaffected).
- v0030 52.49 (+0.57 vs old best) trails the new best by 0.01 → TIE with v0029; incumbent v0029 stays per the standing no-co-promotion rule. Scored backup, not co-promoted.
- v0032 51.97 (+0.05 vs old best, inside TIE) trails the new best by 0.53 → REJECT as improvement.
- v0031 −1.41 and v0033 −0.82 vs parent → REJECT.
- Skill-level read versus v0024 (45.5/58.5/54.3/48.2), descriptive not causal: v0029 improves de/mmd/vario (+0.3/+0.6/+1.5) with dir flat; v0030 trades de for direction (+1.0 dir, +0.8 vario). The two leaders are 0.01 apart with mirrored profiles — direction carries v0030, distribution carries v0029. v0033 loses de/dir/mmd (−2.0/−1.1/−1.1) while variogram rises (+1.2); v0031 loses on all four. Local rank partially inverted at the top (report scenario preferred v0030 over v0029); this bounds the T1 proxy rather than validating it. This does not identify a biological mechanism.
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260928-T1R2SCORE-001.

<a id="t3-round2-score-return-20260929"></a>
## T3 ROUND2 score return — 2026-09-29

Source / raw evidence: user-supplied score table (datetimes 2026-09-28 07:30–07:33, board, portal filenames, file sizes 35 MB, board totals and five skills). Submission IDs not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Local artifact SHA256 values match submissions/INDEX.tsv (v0049 `19094705…`, v0050 `4a0ca825…`, v0051 `bc88b624…`, v0052 `652d3b0a…`, v0053 `ed4e82fe…`); artifacts immutable. Parent v0048, contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|---:|
| t3_gata4__n1stack__v0049.h5ad | 47.86 | 41.7 | 50.4 | 50.0 | 52.3 | 49.8 |
| t3_gata4__n2orth__v0050.h5ad | 47.40 | 40.8 | 49.9 | 50.0 | 51.8 | 49.4 |
| t3_gata4__n3occup__v0051.h5ad | 46.07 | 37.4 | 48.5 | 50.0 | 51.4 | 50.7 |
| t3_gata4__o1logit__v0052.h5ad | 47.62 | 41.7 | 50.1 | 50.0 | 51.8 | 48.6 |
| t3_gata4__o2geneshrink__v0053.h5ad | 47.66 | 41.2 | 49.7 | 50.0 | 52.1 | 51.3 |

Decision and limits:
- v0049 47.86 vs parent/incumbent v0048 47.93: −0.07, inside the ±0.1 TIE band. Not promoted; recorded as scored TIE backup. The high-score stack (v0048+v0046) does not beat v0048 alone.
- v0053 −0.27, v0052 −0.31, v0050 −0.53, v0051 −1.86 vs incumbent → REJECT as improvement.
- Selection stays v0048 (47.93). severity_slope reads 50.0 on all five returns — floor-anchored, carries no discriminative signal, consistent with all prior T3 returns.
- No new Total supplied with this batch. No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260929-T3R2SCORE-001.

<a id="t1-three-score-return-20260929"></a>
## T1 THREE score return — 2026-09-29

Source / raw evidence: user-supplied score table (datetimes 2026-09-28 18:57–19:08, portal filenames, file sizes 632 MB, board totals and four skills). Submission IDs not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills (T1 weights 0.25/0.25/0.30/0.20 give 53.23/53.445/53.35 versus reported 53.24/53.43/53.36; differences are rounding). Local artifact SHA256 values match submissions/INDEX.tsv (v0034 `dbe266bd…`, v0035 `d5cce857…`, v0036 `89891ef9…`); artifacts immutable. Parent v0029 and contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|
| t1_val__r1compose__v0034.h5ad | 53.24 | 46.0 | 60.0 | 55.4 | 50.6 |
| t1_val__r2joint__v0035.h5ad | 53.43 | 46.8 | 60.2 | 55.1 | 50.8 |
| t1_val__r3mix__v0036.h5ad | 53.36 | 47.0 | 59.5 | 55.1 | 51.0 |

Decision and limits:
- v0035 53.43 vs parent/incumbent v0029 52.5: +0.93, far outside the ±0.1 TIE band. PROMOTED: new T1 selection and highest observed.
- v0036 53.36 trails the new best by 0.07 → TIE with v0035; incumbent v0035 stays per the standing no-co-promotion rule. Scored backup, not co-promoted.
- v0034 53.24 trails the new best by 0.19 → outside TIE → REJECT as improvement (still +0.74 vs old best; recorded as scored above the old line).
- Skill-level read versus v0029 (45.8/58.5/54.9/49.7), descriptive not causal: all three improve de/dir/mmd/vario together; the largest move is direction (+1.0 to +1.7). v0036 carries de (47.0) but gives back direction versus v0035. This does not identify a biological mechanism.
- No new Total supplied with this batch. No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260929-T1THREESCORE-001.

<a id="t2-round2-score-return-20260929"></a>
## T2 ROUND2 score return — 2026-09-29

Source / raw evidence: user-supplied score table (datetimes 2026-09-28 19:05–19:08 and 2026-09-29 04:36–04:39 / 07:33–07:35, portal filenames, file sizes 21/29/113 MB, board totals and eight skills per lane, plus one board-mismatch rejection note). Submission IDs not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Local artifact SHA256 values match submissions/INDEX.tsv for all 14 scored files; artifacts immutable. Parents (embryo v0010, interp v0013, extrap v0001) and contract states remain in that index.

Embryo interp (incumbent v0010 62.29):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_emb_int__e_n1_qbridge__v0011.h5ad | 61.31 | 53.5 | 61.0 | 56.5 | 62.0 | 54.6 | 51.2 | 90.8 | 63.7 |
| t2_emb_int__e_n2_trend3__v0012.h5ad | 60.51 | 54.1 | 66.0 | 59.6 | 47.3 | 55.7 | 44.3 | 88.5 | 64.5 |
| t2_emb_int__e_n3_substate2__v0013.h5ad | 61.66 | 51.5 | 66.0 | 59.4 | 59.6 | 52.2 | 48.5 | 87.5 | 65.6 |
| t2_emb_int__e_o1_shrinkmerge__v0014.h5ad | 62.89 | 55.2 | 67.4 | 60.3 | 56.0 | 54.6 | 51.2 | 90.8 | 66.1 |
| t2_emb_int__e_o2_scalemass__v0015.h5ad | 62.38 | 54.1 | 67.5 | 60.2 | 52.0 | 54.6 | 51.2 | 91.9 | 65.9 |

Heart interp (incumbent v0013 62.04):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_hrt_int__h_n1_qbridge__v0016.h5ad | 62.35 | 60.0 | 67.4 | 50.8 | 56.2 | 65.4 | 47.8 | 97.9 | 62.4 |
| t2_hrt_int__h_n2_curve95__v0017.h5ad | 61.81 | 60.0 | 65.1 | 62.3 | 27.0 | 68.7 | 47.1 | 97.5 | 65.4 |
| t2_hrt_int__h_n3_cmjoin__v0018.h5ad | 62.14 | 60.6 | 66.2 | 62.7 | 28.3 | 66.0 | 45.1 | 98.4 | 66.4 |
| t2_hrt_int__h_o1_shrinkmerge__v0019.h5ad | 62.36 | 61.2 | 66.1 | 61.9 | 30.0 | 65.4 | 47.8 | 97.9 | 66.3 |
| t2_hrt_int__h_o2_libnorm__v0020.h5ad | 57.74 | 61.8 | 66.8 | 36.8 | 38.6 | 65.4 | 47.8 | 97.9 | 58.8 |

Heart extrap (aggregate uses baseline 50.53; board-best v0011 50.64):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_hrt_ext__x_n2_trend3__v0018.h5ad | 48.40 | 47.4 | 50.0 | 48.1 | 40.6 | 46.2 | 53.2 | 49.7 | 50.1 |
| t2_hrt_ext__x_n3_compmix__v0019.h5ad | 50.38 | 48.9 | 51.7 | 50.1 | 47.4 | 45.2 | 54.3 | 49.5 | 52.5 |
| t2_hrt_ext__x_o1_trendshrink__v0020.h5ad | 48.59 | 47.4 | 49.9 | 48.4 | 41.5 | 46.2 | 53.2 | 49.7 | 50.3 |
| t2_hrt_ext__x_o2_shrinkcomp__v0021.h5ad | 50.52 | 49.2 | 51.6 | 50.2 | 48.2 | 45.2 | 54.3 | 49.5 | 52.6 |

Board-mismatch attempt (recorded, not a score): at 2026-09-29 04:40 the extrap file `t2_hrt_ext__x_o1_trendshrink__v0020.h5ad` (25179 cells) was submitted to the embryo board and rejected — that board accepts 583–5000 cells. No INDEX change for this event; the file's extrap-board score (48.59) stands as registered above.

Decision and limits:
- Embryo: v0014 62.89 vs incumbent 62.29: +0.60, outside TIE. PROMOTED: new embryo board best. v0015 62.38 (+0.09 vs old best) trails the new best by 0.51 → REJECT as improvement. v0013/v0011/v0012 below the old best → REJECT.
- Heart interp: v0019 62.36 was returned first (19:05) vs incumbent 62.04: +0.32 → PROMOTED: new board best. v0016 62.35 trails the new best by 0.01 → TIE; incumbent v0019 stays per the standing no-co-promotion rule. v0018 (+0.10 vs old best) trails the new best by 0.22 → REJECT. v0017 REJECT. v0020 57.74 (−4.30) → REJECT; library rank remap collapses mmd_u (36.8) and variogram (38.6) while geometry stays fixed — a clean expression-side disaster on this board.
- Extrap: v0019 50.38 (−0.15 vs baseline 50.53; −0.26 vs board-best 50.64), v0021 50.52 (−0.01 vs baseline, inside TIE; −0.12 vs board-best) → neither enters the aggregate or takes the board best. v0020/v0018 REJECT. Extrap selection and the 50.64-vs-50.53 OPEN item are unchanged.
- New derived Total: 159.95 (53.43 + 58.59 + 47.93, with T2 = (62.89+62.36+50.53)/3 = 58.59). Derived only — the last portal-confirmed Total remains 156.06 until re-read.
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260929-T2R2SCORE-001.

<a id="t3-pending-score-return-20260929"></a>
## T3 THREE + FIVE-SELECT score return — 2026-09-29

Source / raw evidence: user-supplied score table (portal filenames, board totals and five skills each; per-lane datetimes not supplied). Submission IDs not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Local artifact SHA256 values match submissions/INDEX.tsv (v0054 `dd4ff51f…`, v0055 `11076fed…`, v0056 `586fad56…`, v0057 `06a7dc29…`, v0058 `b671f35b…`, v0059 `914054b8…`); artifacts immutable. Parent v0048, contract PASS remain in that index.

| Portal model | Board score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|---:|
| t3_gata4__r1agree__v0054.h5ad | 47.75 | 42.1 | 49.8 | 50.0 | 51.8 | 49.4 |
| t3_gata4__r2damp__v0055.h5ad | 47.25 | 40.4 | 49.9 | 50.0 | 51.6 | 49.4 |
| t3_gata4__r3diffuse__v0056.h5ad | 47.93 | 42.6 | 50.0 | 50.0 | 51.8 | 49.3 |
| t3_gata4__r2gene__v0057.h5ad | 47.37 | 40.8 | 49.7 | 50.0 | 52.0 | 49.5 |
| t3_gata4__r4spline__v0058.h5ad | 47.95 | 42.6 | 50.0 | 50.0 | 51.8 | 49.5 |
| t3_gata4__r3bag__v0059.h5ad | 47.93 | 42.6 | 50.0 | 50.0 | 51.8 | 49.3 |

Decision and limits:
- v0058 47.95 vs incumbent v0048 47.93: +0.02, inside the ±0.1 TIE band. Not promoted; recorded as scored TIE backup per the standing no-co-promotion rule.
- v0056 and v0059 both 47.93, exact tie with the incumbent; not co-promoted. Their five skills match v0048 (42.6/50.0/50.0/51.8/49.3) to the supplied precision — same readout from different constructions, descriptive only.
- v0054 −0.18, v0057 −0.56, v0055 −0.68 vs incumbent → REJECT as improvement. The damped/gene arms lose on de_score (40.4/40.8 vs 42.6).
- Selection stays v0048 (47.93). T3 score queue is now closed: no score_pending T3 candidate remains. severity_slope reads 50.0 on all six returns — floor-anchored, carries no discriminative signal, consistent with all prior T3 returns.
- No new Total supplied with this batch; T3 component unchanged so the derived Total stays 159.95. No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260929-T3SCORE-002.

<a id="t1-seven-pbmean-score-return-20260930"></a>
## T1 seven routes and mean extrapolation score return — 2026-09-30

Source / raw evidence: user-supplied filenames, 11 board scores and all 44 submetric skills in this conversation on 2026-09-30. Submission IDs, upload timestamps and portal Total were not supplied; no independent portal query was performed. Preserve supplied totals; do not reconstruct them from rounded skills. All 11 local artifact SHA256 values were checked against submissions/INDEX.tsv; all indexed contracts are pass. Files remain immutable.

| Portal model | Board score | de_score | de_direction | mmd_u | variogram |
|---|---:|---:|---:|---:|---:|
| t1_val__n1moment__v0037.h5ad | 52.65 | 45.0 | 59.6 | 54.6 | 50.7 |
| t1_val__n2covot__v0038.h5ad | 53.55 | 46.5 | 60.3 | 55.7 | 50.8 |
| t1_val__n3graph__v0039.h5ad | 53.23 | 46.4 | 60.0 | 55.1 | 50.6 |
| t1_val__f1soft__v0040.h5ad | 53.02 | 46.0 | 59.9 | 54.8 | 50.6 |
| t1_val__s1growth__v0041.h5ad | 52.91 | 45.7 | 59.6 | 55.3 | 49.9 |
| t1_val__f2stable__v0042.h5ad | 53.31 | 46.5 | 60.1 | 55.0 | 50.7 |
| t1_val__s2mix__v0043.h5ad | 53.55 | 46.5 | 59.7 | 56.0 | 50.9 |
| t1_val__pba05__v0044.h5ad | 48.75 | 42.3 | 58.2 | 52.4 | 39.4 |
| t1_val__pba10__v0045.h5ad | 47.92 | 43.5 | 58.1 | 52.2 | 34.4 |
| t1_val__pbb05__v0046.h5ad | 49.10 | 41.2 | 58.8 | 52.5 | 41.8 |
| t1_val__pbb10__v0047.h5ad | 49.97 | 43.5 | 58.8 | 53.2 | 42.1 |

Decision and limits:
- v0038 and v0043 both score 53.55, +0.12 versus incumbent v0035=53.43, outside the standing ±0.1 tie band. Register v0038 as selection and v0043 as exact-score backup. This administrative tie-break follows the order of this single user-supplied list, NOT an inferred upload/score timestamp; no co-promotion or claim that v0038 is scientifically better.
- Top 3 by reported score: v0038=53.55, v0043=53.55, v0035=53.43. v0035 is retained as a historical reference, outside the new head's ±0.1 band.
- v0037/v0039/v0040/v0041/v0042 do not improve the old incumbent; all are below the new selection. v0044–v0047 mean-shift candidates lose 3.46–5.51 versus their v0035 parent; reject this submitted family as an improvement, no further alpha sweep in this score-registration task.
- Versus v0035 skills 46.8/60.2/55.1/50.8, v0038 changes are −0.3/+0.1/+0.6/0.0; v0043 changes are −0.3/−0.5/+0.9/+0.1. Shared gain is distribution skill; different submetric tradeoffs, not uniform improvement or mechanism identification.
- Mean-shift variogram skills fall by 11.4/16.4/9.0/8.7 respectively; de, direction and MMD also fall in every arm. Global alpha 1 is worse than 0.5; type-based alpha 1 is better than 0.5 but still far below parent. Do not generalize a universal monotone amplitude rule.
- T1 pending queue is empty after these 11 returns. New derived sum 53.55+58.59+47.93=160.07 uses current local selection bookkeeping only; it is NOT a newly returned portal Total. Last recorded portal Total remains 156.06 and the heart_extrap 50.64/50.53 discrepancy stays open.
- No new training, candidate, portal selection operation or scientific validation was performed. Decision: D-20260930-T1SCORE-001. Review: reports/t1_score_review_20260930/REPORT.md. blocks_submission: false.

<a id="t2-xn1-score-return-20260930"></a>
## T2 x_n1_lineage score return — 2026-09-30

Source / raw evidence: user-supplied board total and eight skills in this conversation on 2026-09-30 (portal model `t2_hrt_ext__x_n1_lineage__v0017.h5ad`). Submission ID, upload timestamp and portal Total not supplied; no independent portal query was performed. Local artifact SHA256 `7ffd3053…` matches submissions/INDEX.tsv; artifact immutable. Parent v0001, contract PASS remain in that index.

Heart extrap (aggregate uses baseline 50.53; board-best v0011 50.64):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_hrt_ext__x_n1_lineage__v0017.h5ad | 48.17 | 50.8 | 52.5 | 45.9 | 33.3 | 46.2 | 53.2 | 49.7 | 50.5 |

Decision and limits:
- v0017 48.17 (−2.36 vs baseline 50.53; −2.47 vs board-best 50.64) → REJECT as improvement. Lineage-mapped deltas for the 17 zero-shift types do not move the extrap board; variogram 33.3 is the weakest skill, consistent with the extrap-board pattern that spatial autocorrelation is the headroom.
- Extrap selection unchanged (aggregate still baseline 50.53; 50.64-vs-50.53 OPEN item unchanged). T2-ROUND2 score queue is now closed: 15/15 returned.
- No new Total supplied; derived figures unchanged (160.07 stays a local derivation, NOT a portal Total; last portal-confirmed Total 156.06).
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260930-T2XN1SCORE-001.

<a id="t2-r3-score-return-20260930"></a>
## B4-T2-R3 score return — 2026-09-30

Source / raw evidence: user-supplied board totals and eight skills per lane in this conversation on 2026-09-30 (portal models `t2_hrt_ext__l1damp050__v0008.h5ad`, `t2_hrt_ext__l2time1333__v0009.h5ad`, `t2_hrt_ext__l3popmix050__v0010.h5ad`; pack `deliveries/b4t2r3__t2__upload__20260914.zip`, no receipt — packed 2026-09-14, closed_unscored 2026-09-15 per D-20260915-B4CLOSE-001, scored now). Submission IDs, upload timestamps and portal Total not supplied; no independent portal query was performed. Local artifact SHA256 values match submissions/INDEX.tsv (v0008 `a58896c9…`, v0009 `f692fd8f…`, v0010 `4475b233…`); artifacts immutable. Parent baseline-001 v0001, contract PASS remain in that index.

Heart extrap (aggregate uses baseline 50.53; board-best v0011 50.64):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_hrt_ext__l1damp050__v0008.h5ad | 48.40 | 42.5 | 51.1 | 48.4 | 41.6 | 46.2 | 53.2 | 49.7 | 51.4 |
| t2_hrt_ext__l2time1333__v0009.h5ad | 50.51 | 50.4 | 52.5 | 49.9 | 47.1 | 46.2 | 53.2 | 49.7 | 52.1 |
| t2_hrt_ext__l3popmix050__v0010.h5ad | 48.87 | 43.6 | 52.6 | 48.1 | 43.6 | 46.2 | 53.2 | 49.7 | 51.3 |

Decision and limits:
- v0009 50.51 (−0.02 vs baseline 50.53, inside ±0.1 TIE; −0.13 vs board-best 50.64) → TIE with baseline, no promotion. Time-normalized 1.333×Delta extrapolation matches the no-change baseline but does not beat the shrink lane; notably its de_score 50.4 is the strongest differential-expression readout among extrap attempts (baseline 49.6), yet the Total does not move — descriptive only.
- v0008 48.40 (−2.13) and v0010 48.87 (−1.66) → REJECT. Damping toward E9.5 and half-copy-last grafting both lose on de_score (42.5/43.6 vs 49.6) and variogram (41.6/43.6 vs 47.7).
- Extrap selection unchanged (aggregate still baseline 50.53; 50.64-vs-50.53 OPEN item unchanged). The B4-T2-R3 closed_unscored state is now resolved as scored; no future-batch scoring left for this run.
- No new Total supplied; derived figures unchanged (160.07 stays a local derivation, NOT a portal Total; last portal-confirmed Total 156.06).
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20260930-T2R3SCORE-001.

<a id="t3-priority-six-score-return-20261001"></a>
## T3 priority six score return — 2026-10-01

Evidence: user-transcribed six totals and all 30 displayed submetrics, preserved in `reports/t3_score_review_20261001/USER_SCORE_REPORT.md`; identities matched the uploaded `deliveries/t3six__t3__upload__20261001.zip`, member manifest, current INDEX and actual candidate bytes. No independent portal query. Submission IDs and actual submitted timestamps NOT_PROVIDED; record date is receipt date. Original member H5AD files unchanged.

| Version / model | Total | Δ vs selection v0048 | de_score | de_direction | severity_slope | mmd_u | variogram (portal label) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v0060 t3_gata4__r1_celloracle__v0060.h5ad | 46.91 | -1.02 | 39.2 | 49.6 | 50.0 | 51.5 | 50.8 | REJECT |
| v0061 t3_gata4__r3_activity__v0061.h5ad | 45.51 | -2.42 | 39.6 | 51.2 | 50.0 | 42.6 | 40.0 | REJECT |
| v0062 t3_gata4__r4_functional__v0062.h5ad | 44.42 | -3.51 | 39.2 | 48.7 | 50.0 | 42.6 | 35.8 | REJECT |
| v0063 t3_gata4__r4_bilinear__v0063.h5ad | 44.27 | -3.66 | 38.8 | 48.7 | 50.0 | 42.7 | 35.4 | REJECT |
| v0064 t3_gata4__r5_scouter__v0064.h5ad | 44.14 | -3.79 | 41.7 | 50.3 | 50.0 | 36.8 | 26.8 | REJECT |
| v0065 t3_gata4__r6_gears__v0065.h5ad | 42.38 | -5.55 | 38.1 | 48.7 | 50.0 | 34.4 | 26.8 | REJECT |

All six are more than 0.1 below selection 47.93: no promotion, selection v0048 and tie backup v0058 unchanged. The exact-native CellOracle+decoder variant 46.91 is also within ±0.1 of the old CellOracle-derived v0018 46.94; broader cell/gene changes did not create a server gain. State-mass null route has no registered candidate and no returned score.

No new aggregate Total supplied; last portal-confirmed 156.06 and locally derived 160.07 remain separate. T3 new pending count becomes zero. Old execution/package receipts are immutable historical records of READY_NOT_SUBMITTED at creation; current submission status is the canonical INDEX and this score section. User-provided totals remain authoritative: rounded submetric weighted sums are diagnostic, not replacements for totals. Scientific mechanisms remain unvalidated; blocks_submission: false. Decision D-20261001-T3SIXSCORE-001. Review: reports/t3_score_review_20261001/REPORT.md.

<a id="t2-goal-score-return-20261001"></a>
## T2 GOAL score return — 2026-10-01

Source / raw evidence: user-supplied board totals and eight skills per lane in this conversation on 2026-10-01 (portal models `t2_hrt_ext__x_n1_lineage__v0017.h5ad`, `t2_hrt_ext__x_o2_shrinkcomp__v0021.h5ad`, `t1_val__pbb05__v0046.h5ad`, `t1_val__pba10__v0045.h5ad`, `t1_val__pba05__v0044.h5ad`, `t2_hrt_int__h_r2shrinkc1__v0022.h5ad`, `t2_hrt_int__h_r1compotrend__v0021.h5ad`, `t2_hrt_ext__x_r2shrinkc1__v0023.h5ad`, `t2_hrt_ext__x_r1lateref__v0022.h5ad`, `t2_emb_int__e_r2shrinkc1__v0017.h5ad`, `t2_emb_int__e_r1compotrend__v0016.h5ad`). Of these 11, five were already registered with identical values (x_n1_lineage v0017 48.17 in §t2-xn1-score-return-20260930; x_o2_shrinkcomp v0021 50.52 in §t2-round2-score-return-20260929; T1 v0044 48.75 / v0045 47.92 / v0046 49.10 in §t1-seven-pbmean-score-return-20260930) and are NOT re-registered here. This section registers only the six new T2-GOAL returns below. Submission IDs, upload timestamps and portal Total not supplied; no independent portal query was performed. Values preserve supplied precision; reported totals are not reconstructed from rounded skills. Local artifact SHA256 values match submissions/INDEX.tsv (e_r1 v0016 `c3250e9d…`, e_r2 v0017 `7f85be3c…`, h_r1 v0021 `e11aa83b…`, h_r2 v0022 `f94649df…`, x_r1 v0022 `f5cc7c59…`, x_r2 v0023 `c2d5063d…`); artifacts immutable. Parents (embryo v0014, interp v0019, extrap v0001) and contract states remain in that index. Per-metric rows also in `reports/SERVER_SUBMETRIC_REGISTRY.tsv`.

Embryo interp (incumbent v0014 62.89):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_emb_int__e_r1compotrend__v0016.h5ad | 61.65 | 54.6 | 64.8 | 60.3 | 56.3 | 54.7 | 40.4 | 87.1 | 67.4 |
| t2_emb_int__e_r2shrinkc1__v0017.h5ad | 62.55 | 54.1 | 67.4 | 60.3 | 54.5 | 54.6 | 51.2 | 90.8 | 66.0 |

Heart interp (incumbent v0019 62.36):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_hrt_int__h_r1compotrend__v0021.h5ad | 62.22 | 58.3 | 65.3 | 63.4 | 29.6 | 67.7 | 47.1 | 98.0 | 66.3 |
| t2_hrt_int__h_r2shrinkc1__v0022.h5ad | 62.21 | 60.6 | 66.0 | 62.2 | 29.5 | 65.4 | 47.8 | 97.9 | 66.1 |

Heart extrap (aggregate uses baseline 50.53; prior board-best v0011 50.64):

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t2_hrt_ext__x_r1lateref__v0022.h5ad | 50.74 | 53.7 | 53.8 | 48.7 | 47.7 | 46.2 | 53.2 | 49.7 | 51.1 |
| t2_hrt_ext__x_r2shrinkc1__v0023.h5ad | 50.03 | 50.4 | 52.5 | 48.9 | 46.3 | 46.2 | 53.2 | 49.7 | 51.0 |

Decision and limits:
- Embryo: e_r2 62.55 (−0.34 vs 62.89) REJECT; e_r1 61.65 (−1.24) REJECT. Trend-share resample + incumbent expression does not beat the shrinkmerge incumbent; e_r1 additionally collapses occupancy_dice (40.4 vs 51.2).
- Heart interp: h_r1 62.22 (−0.14 vs 62.36) and h_r2 62.21 (−0.15) both REJECT (outside the ±0.1 TIE band). Same pattern as embryo: neither the trend-share combo nor the C=1 shrink moves the board past the shrinkmerge incumbent. Variogram stays the weakest skill (29.5–29.6).
- Extrap: x_r2 50.03 (−0.50 vs baseline 50.53; −0.61 vs prior best 50.64) REJECT. x_r1 50.74 (+0.21 vs baseline 50.53; +0.10 vs prior board-best v0011 50.64) lands exactly on the ±0.1 TIE boundary → recorded as TIE-highest-numeric backup, NO promotion per the standing no-co-promotion rule; incumbent v0011 stays. x_r1 is the numerically highest extrap return to date; its de_score 53.7 is also the strongest extrap de readout to date (baseline 49.6), yet the selection/aggregate rule keeps it out of the Total until a portal re-read promotes it — descriptive only.
- Selections unchanged on all three T2 boards (embryo v0014 62.89 / interp v0019 62.36 / aggregate extrap 50.53). The extrap OPEN item is now 50.74-vs-50.53 (was 50.64-vs-50.53); still needs a portal re-read before any promotion claim.
- T2-GOAL score queue is now closed: 6/6 returned. No new Total supplied; derived figures unchanged (160.07 stays a local derivation, NOT a portal Total; last portal-confirmed Total 156.06).
- No new model fit or candidate generation in this score-registration task. Scientific status unchanged; blocks_submission: false.
- Decision: D-20261001-T2GOALSCORE-001.

<a id="t3-architecture-two-score-return-20261001"></a>
## T3 architecture two score return — 2026-10-01

Evidence: user-transcribed two totals and ten displayed submetrics; raw evidence reports/t3_arch_two_score_review_20261001/USER_SCORE_REPORT.md. Model filenames matched deliveries/arch2__t3__upload__20261001.zip, member manifest, canonical artifacts and INDEX SHA256. No independent portal query; submission IDs, actual submitted timestamps and new portal Total NOT_PROVIDED. All scored artifact bytes unchanged.

| Version / model | Total | Δ vs selected v0048 | de_score | de_direction | severity_slope | mmd_u | variogram | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v0066 t3_gata4__a_flow__v0066.h5ad | 43.21 | -4.72 | 37.0 | 53.5 | 50.0 | 41.3 | 15.7 | REJECT |
| v0068 t3_gata4__b_fate__v0068.h5ad | 46.37 | -1.56 | 38.8 | 49.9 | 50.0 | 50.1 | 46.9 | REJECT |

Both are >0.1 below selection: no promotion; v0048=47.93 and v0058=47.95 tie backup unchanged. A direction53.5 is the highest displayed T3 direction among registered submetrics so far (prior max51.2), descriptive only; DE and distribution losses dominate. B is also0.58 below its Gata4-zero carrier v0009=46.95; current composition prediction did not provide a server gain. v0067 remains withdrawn/unsubmitted with no score. T3 pending count becomes zero; this batch is closed.

User totals are retained exactly, not replaced with rounded-submetric weighted estimates. No new aggregate Total: last portal-confirmed156.06 and local derived160.07 remain separate and unchanged. Historical creation-time READY_NOT_SUBMITTED receipts remain immutable; current status is INDEX and this score section. Scientific mechanisms remain unvalidated, blocks_submission:false. Decision D-20261001-T3ARCHSCORE-001; review reports/t3_arch_two_score_review_20261001/REPORT.md.

## Route C extrap score return — 2026-10-02

User-reported portal returns for the five Route C candidates (`deliveries/arcqte__t2__upload__20261002.zip`,
run `AR-ROUTE-C-20261002-v1`). Submitted field is the user's return date; no portal Total was supplied.

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd | local composite |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `t2_hrt_ext__qte_tc_s929__v0024.h5ad` | 50.09 | 46.8 | 52.1 | 50.1 | 50.1 | 45.2 | 54.3 | 49.5 | 51.1 | +3.913 |
| `t2_hrt_ext__qte_compmix__v0025.h5ad` | 50.17 | 45.8 | 51.2 | 50.9 | 49.7 | 49.5 | 52.1 | 50.0 | 51.2 | +3.464 |
| `t2_hrt_ext__qte_time__v0026.h5ad` | 50.03 | 46.4 | 52.4 | 49.8 | 50.1 | 46.2 | 53.2 | 49.7 | 51.1 | +2.608 |
| `t2_hrt_ext__sharetrend_qte__v0027.h5ad` | 39.60 | 47.1 | 52.9 | 37.3 | 42.2 | 23.6 | 47.9 | 54.4 | 37.6 | +0.855 |
| `t2_hrt_ext__qte_tc_s008__v0028.h5ad` | 50.08 | 46.1 | 51.6 | 50.7 | 49.5 | 49.5 | 52.1 | 50.0 | 50.7 | +3.606 |

Reference points: incumbent/aggregate baseline v0001 = **50.53**; board-best v0011 = **50.64**;
numeric-high v0022 (unpromoted TIE-highest) = **50.74**.

Deltas (vs 50.53 / vs 50.64 / vs 50.74):
- v0024 **−0.44 / −0.55 / −0.65** → REJECT
- v0025 **−0.36 / −0.47 / −0.57** → REJECT (best of the five)
- v0026 **−0.50 / −0.61 / −0.71** → REJECT
- v0027 **−10.93 / −11.04 / −11.14** → REJECT (catastrophic, as its local guardrail failure predicted)
- v0028 **−0.45 / −0.56 / −0.66** → REJECT

Decision and limits:
- **No promotion.** All five sit below the incumbent; heart-extrap selection and the aggregate stay on baseline
  50.53, and the 50.74-vs-50.53 OPEN item is unchanged (still needs a portal re-read).
- **The frozen 8-channel local composite was falsified as a predictor for new designs.** It ranked these five
  at +0.9…+3.9 (champion +3.913) and they all scored at-or-below baseline; over the full 17-lane set
  Spearman(composite, board) is now **0.122** (it was 0.539 over the 12 pre-Route-C lanes only — the
  correlation does not survive out-of-family candidates). The composite must not be used to justify a
  submission again without a server-anchored calibration set that includes the candidate's own family.
- **First confirmed channel transfer.** The Route C designs improved the `variogram` skill to **49.5–50.1**,
  i.e. the best vario values on this board (previous lanes 47.4–48.5); this matches the (corrected,
  lower-is-better) local variogram ordering, so the variogram channel is a genuine, transferable lever.
- **The DE channel inverted.** Route C lanes score **45.8–46.8** on `de_score` versus 48.9–50.0 for the older
  compmix/shrink lanes, despite *higher* local `de_score`. Optimising the local DE readout actively costs
  server DE on this board.
- **Server-side row-luck is negligible, unlike the local proxy.** v0024 and v0028 are the same design with
  different resample rows: server 50.09 vs 50.08 (Δ0.01) while the local composite differed by 0.31 (8.5%
  relative). The local 3-seed spread is therefore a proxy artifact, not model variance — the standing
  3-seed-median rule is conservative rather than necessary for server purposes.
- v0027's collapse (d2 23.6, mmd_u 37.3, nmmd 37.6) reproduces its known local defect (library_size_ratio
  11.98, variance_ratio 1.74); the local guardrails were the only component that fired correctly.
- No new Total supplied; derived figures unchanged. Submission IDs, timestamps and portal Total were not
  supplied; no independent portal query was performed. Artifacts immutable; submetrics registered above.

<a id="t1-armix-score-return-20261002"></a>
## T1 AR-MIX score return — 2026-10-02

User-transcribed portal returns for the three AR-MIX lanes
(`deliveries/art1mix__t1__upload__20261002.DRAFT-PENDING-INDEX.zip`, run
`AR-T1-MIX-20261002-v1`; staged sha `4d5bb215…` / `6e8d89f7…` / `9615510f…`,
pack integrity verified at packing time). Submission IDs, upload timestamps and
portal Total NOT supplied; no independent portal query. Values preserve supplied
precision; reported totals are not reconstructed from rounded skills (T1 weights
0.25/0.25/0.30/0.20 give 53.70/53.315/53.93 versus reported 53.72/53.32/53.92;
differences are rounding). Versions v0049–v0051 are PROPOSED (v0048 skipped: touched
by closed D2R3, never registered); INDEX rows + canonical placement pending coordinator.

| Version / portal model | Total | de | dir | mmd_u | vario | Verdict |
|---|---:|---:|---:|---:|---:|---|
| v0049 `t1_val__mix35x38a__v0049.h5ad` (70/30 v0035×v0038, seed 20260921) | 53.72 | 46.7 | 59.9 | 56.3 | 50.8 | HIGH BACKUP (see below) |
| v0050 `t1_val__mix35x38b__v0050.h5ad` (70/30 v0035×v0038, seed 20261023) | 53.32 | 47.0 | 59.9 | 55.1 | 50.3 | REJECT |
| v0051 `t1_val__mix36x38a__v0051.h5ad` (70/30 v0036×v0038, seed 20260921) | 53.92 | 47.2 | 60.0 | 56.7 | 50.6 | PROMOTED new T1 best |

Deltas vs prior best v0038/v0043 = 53.55: v0049 **+0.17**, v0050 **−0.23**, v0051 **+0.37**.
v0051 is outside the ±0.1 TIE band → new T1 selection and highest observed; v0049 beats
the old best but trails the new best by 0.20 → high backup, no co-promotion (standing
precedent); v0050 below old best → REJECT. New derived sum 53.92+58.59+47.93=**160.44**
(derived only, NOT a portal Total; last portal-confirmed Total remains 156.06).

Submetric read vs v0038 (46.5/60.3/55.7/50.8), descriptive not causal: v0051 gains de
(+0.7) and mmd (+1.0) with dir −0.3 and vario flat — the second-ever server DE move on
T1 (after v0035 46.8 / v0036 47.0) and the top mmd skill on this board (56.7 > 56.0).
v0049 is the same profile smaller (+0.2/+0.6/−0.4/flat). v0050 gains de (+0.5) but loses
mmd (−0.6) and vario (−0.5).

Seed-luck finding (headline): L1 and L2 are the SAME design with different mixture seeds
yet score 53.72 vs 53.32 (Δ0.40) — server-side row selection matters on T1, the opposite
of the same-day T2-extrap result (identical-design reseed 50.09 vs 50.08, Δ0.01). The
report-level quantum lottery replicates on the server. Consequence: future T1 lanes should
either ship 2 seeds of a mix design or prefer deterministic (seed-insensitive) constructions;
single-seed server reads of resampling designs are lottery tickets.

T1 pending queue is empty after these 3 returns. Decision: D-20261002-T1MIXSCORE-001.
blocks_submission: false. Pending coordinator: INDEX rows (v0049–v0051, staged paths +
SHAs in the AR-T1-MIX handoff), T1_TRACKING line, DECISIONS entry, STATUS/TODO sync.

## T2 scale09 score return — 2026-10-03

Source / raw evidence: user transcribed `t2_hrt_ext__ar_scale09__v0029.h5ad:49.40` followed by the eight values below in this conversation. Evidence class: SERVER_SCORED_USER_REPORTED. Portal submission ID and submission timestamp were not supplied; no independent portal lookup. Date is the score-recording date, not an inferred submission date. The canonical artifact SHA and ZIP-member SHA match the v0029 INDEX row; no artifact was modified.

| Portal model | Board score | de_score | de_direction | mmd_u | variogram | d2_shape | occupancy_dice | scale_log_ratio | neighborhood_mmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `t2_hrt_ext__ar_scale09__v0029.h5ad` | 49.40 | 46.8 | 52.1 | 50.1 | 50.1 | 45.2 | 54.3 | 41.3 | 51.1 |

Decision: **REJECT**, no promotion. Delta vs direct parent v0024 50.09: **−0.69**; vs incumbent baseline 50.53: **−1.13**; vs unpromoted numeric-high v0022 50.74: **−1.34**. Selection and aggregate remain unchanged; the old 50.74-vs-50.53 portal-selection OPEN item is unaffected. The reported board score is authoritative, not recomputed from rounded skill values.

All seven non-scale skill values equal the parent v0024 values. Only scale skill changes: **49.5→41.3 (−8.2)**. The same coordinate shrink gave the opposite local conclusion (raw absolute scale error 0.2131→0.1078; frozen three-seed median composite 3.912955→7.523743, all improvement from this channel). Thus the local development objective succeeded while this submitted configuration failed transfer. The composite is not a calibrated prediction of official score.

Submetrics: `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, eight rows. Review: `reports/t2_scale_score_review_20261003/REPORT.md`. Decision `D-20261003-T2SCALE-SCORE-001` closes current scale0.9 configuration; this proxy cannot justify promotion. No new candidate/training/scorer change; blocks_submission:false.


<a id="t3-autoresearch-score-return-20261003"></a>
## T3 autoresearch v0070 回分（2026-10-03）

证据：用户本轮原文；文件名绑定本地交付与 INDEX SHA256，二者实测一致。未独立查询门户；submission ID、上传时间、截图未提供，不推断。

```text
登记分数，t3_gata4__ar_complex__v0070.h5ad :45.80
de_score 38.1
de_direction 50.5
severity_slope 50.0
mmd_u 50.7
variogram 39.6
```

| board | version | portal file | reported total | decision |
|---|---|---|---:|---|
| T3:gata4 | v0070 | t3_gata4__ar_complex__v0070.h5ad | 45.80 | REJECT；较现役 v0048 低2.13，较母本 v0009 低1.15 |

五项显示值已原样写入 SERVER_SUBMETRIC_REGISTRY.tsv；不由四舍五入子项重算/替换总分。现役 v0048 不变，当前配置关闭。复盘：`reports/t3_autoresearch_score_review_20261003/REPORT.md`；D-20261003-T3ARSCORE-001。候选身份/contract以 INDEX 为准；blocks_submission:false。


<a id="t3-sparse-scale-score-return-20261003"></a>
## T3 v0071 回分（2026-10-03）

来源：用户本轮直接提供；canonical与交付文件SHA匹配INDEX。未查询门户，submission ID/上传时间/截图未提供。

```text
t3_gata4__sparse_scale__v0071.h5ad：47.85
de_score 41.7
de_direction 51.4
severity_slope 50.0
mmd_u 51.0
variogram 48.4
```

原样登记总分47.85及五项；较现役v0048低0.08，较v0070高2.05。NOT_PROMOTED，现役不变；差距很小且无重复评分，不能宣称显著差异。有效权重下相对现役贡献约DE −0.270、方向+0.350、severity 0、MMD −0.096、variogram −0.072，净−0.088；不替换用户总分。用户已授权进一步优化，下一分叉固定只减半新增响应。D-20261003-T3HALF-001；reports/t3_halfstep_20261003/REPORT.md。


<a id="t3-half-scale-score-return-20261003"></a>
## T3 v0072 回分（2026-10-03）

用户原文如下。canonical与交付H5AD的SHA均匹配INDEX；未查询门户，submission ID/上传时间/截图未提供，不推断。

```text
t3_gata4__half_scale__v0072.h5ad :47.51
de_score 40.4
de_direction 51.2
severity_slope 50.0
mmd_u 51.5
variogram 48.8
```

总分47.51和五项显示值原样登记，较v0071低0.34、较现役v0048低0.42。REJECT，现役保持。分布小幅回升未抵消DE退步，减半响应未获总分收益，关闭当前强度减半试验、不继续细分步长。无重复评分，不主张统计显著性或机制结论。详见 reports/t3_halfstep_20261003/SCORE_REVIEW.md；D-20261003-T3HALFSCORE-001。blocks_submission:false。


<a id="t2-holdout10-xr3xr4-score-return-20261003"></a>
## T2 HOLDOUT10 x_r3/x_r4 score return — 2026-10-03

Source / raw evidence: user-transcribed portal returns in this conversation for the two
HOLDOUT10 board lanes (`deliveries/t2h10__t2__upload__20261003.zip`,
`deliveries/t2h10x4__t2__upload__20261003.zip`; run `T2-HOLDOUT10-20261003-v1`).
Evidence class: SERVER_SCORED_USER_REPORTED. No independent portal lookup; portal
submission ID and submission timestamp were not supplied; no Total was returned.
Candidate identity verified by ZIP-member filename bound to INDEX SHA256
(v0030 `71f587ed…`, v0031 `86fec27f…`); no artifact was modified.
Date is the score-recording date, not an inferred submission date.

```text
t2_hrt_ext__x_r3medlib09__v0030.h5ad: 51.12
de_score 52.0 / de_direction 50.9 / mmd_u 49.4 / variogram 50.4
(metric, value) pairs per user text: d2_shape 46.2 / occupancy_dice 53.2 /
scale_log_ratio 49.7 / neighborhood_mmd 53.5

t2_hrt_ext__x_r4xwalk09__v0031.h5ad: 49.91
de_score 52.4 / de_direction 51.8 / mmd_u 44.3 / variogram 49.0
d2_shape 46.2 / occupancy_dice 53.2 / scale_log_ratio 49.7
neighborhood_mmd 51.6
```

Skill mapping (per user text: each metric name followed by its value; total first).
Values recorded exactly as transcribed.

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `t2_hrt_ext__x_r3medlib09__v0030.h5ad` | 51.12 | 52.0 | 50.9 | 49.4 | 50.4 | 46.2 | 53.2 | 49.7 | 53.5 |
| `t2_hrt_ext__x_r4xwalk09__v0031.h5ad` | 49.91 | 52.4 | 51.8 | 44.3 | 49.0 | 46.2 | 53.2 | 49.7 | 51.6 |

Baseline board (v0001): 50.53 (49.6/52.2/49.9/47.7/46.2/53.2/49.7/52.4).
Board-best reference: v0011 50.64; unpromoted numeric-high v0022 50.74.

Deltas:
- v0030 **+0.59 vs baseline 50.53; +0.48 vs board-best 50.64; +0.38 vs 50.74** → **PROMOTED new board best**.
- v0031 **−0.62 vs baseline 50.53** → REJECT.

Decision and limits:
- **v0030 PROMOTED to heart-extrap selection** (first board-best change on this board
  since v0011 2026-09-16). Per-metric drivers vs baseline v0001 (49.6/52.2/49.9/47.7/
  46.2/53.2/49.7/52.4): de 52.0 (+2.4) and vario 50.4 (+2.7) and nmmd 53.5 (+1.1)
  are the gains; dir 50.9 (−1.3) and mmd 49.4 (−0.5) give back; d2/occ/scale are
  flat at the pinned 46.2/53.2/49.7. The de gain mirrors the holdout finding
  (library preservation unblocked the DE channel); nmmd 53.5 is the highest nmmd
  on this board. No causal claim beyond this board.
- **v0031 REJECT.** Broad crosswalk coverage (67% rows) lost to the narrow shared-state
  lane: mmd_u collapses to 44.3 (−5.6 vs baseline) and nmmd to 51.6 (−0.8), wiping out
  even better de 52.4 (+2.8) and dir 51.8. Coverage expansion moved mass in the wrong
  distributional direction; the crosswalk axis is closed (no threshold retuning — the
  thresholds were frozen pre-build and the mmd failure is structural).
- Derived (not server-returned): T2 = (62.89 + 62.36 + 51.12)/3 = 58.79; derived sum
  with T1/T3 selections = 53.55 + 58.79 + 47.93 = 160.27 (derived only, NOT a portal
  Total; last portal-confirmed Total remains 156.06).
- blocks_submission: false.

Submetrics: `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, sixteen rows. Review:
`reports/t2_holdout10_score_review_20261003/REPORT.md`. Decision D-20261003-T2H10SCORE-001.


<a id="t2-holdout10-x567-score-return-20261003"></a>
## T2 HOLDOUT10 x_r5/x_r6/x_r7 score return — 2026-10-03

Source / raw evidence: user-transcribed portal returns in this conversation for the three
HOLDOUT10 board lanes (`deliveries/t2h10x5__t2__upload__20261003.zip`,
`deliveries/t2h10x67__t2__upload__20261003.zip`; run `T2-HOLDOUT10-20261003-v1`).
Evidence class: SERVER_SCORED_USER_REPORTED. No independent portal lookup; portal
submission ID and timestamp not supplied; no Total returned. Candidate identity verified
by ZIP-member filename bound to INDEX SHA256 (v0032 `079cc775…`, v0033 `32b3fd6e…`,
v0034 `bcc90053…`); no artifact was modified. Date is the score-recording date.

```text
t2_hrt_ext__x_r5tshk09__v0032.h5ad:   51.12 -> 51.14 (de 52.0 / dir 51.2 / mmd 49.8 / vario 49.8 / d2 46.2 / occ 53.2 / scale 49.7 / nmmd 53.4)
t2_hrt_ext__x_r6medlib05__v0033.h5ad: 50.89 (de 50.8 / dir 51.3 / mmd 50.0 / vario 49.1 / d2 46.2 / occ 53.2 / scale 49.7 / nmmd 53.2)
t2_hrt_ext__x_r7typeadapt__v0034.h5ad: 51.02 (de 51.6 / dir 51.1 / mmd 49.9 / vario 49.5 / d2 46.2 / occ 53.2 / scale 49.7 / nmmd 53.3)
```

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `t2_hrt_ext__x_r5tshk09__v0032.h5ad` | 51.14 | 52.0 | 51.2 | 49.8 | 49.8 | 46.2 | 53.2 | 49.7 | 53.4 | **TIE (+0.02 vs 51.12, within ±0.1 band); no promotion; tied numeric-high backup** |
| `t2_hrt_ext__x_r6medlib05__v0033.h5ad` | 50.89 | 50.8 | 51.3 | 50.0 | 49.1 | 46.2 | 53.2 | 49.7 | 53.2 | REJECT (−0.23) |
| `t2_hrt_ext__x_r7typeadapt__v0034.h5ad` | 51.02 | 51.6 | 51.1 | 49.9 | 49.5 | 46.2 | 53.2 | 49.7 | 53.3 | TIE (−0.10, band edge); no promotion |

Incumbent: v0030 = **51.12** (52.0/50.9/49.4/50.4/46.2/53.2/49.7/53.5). Baseline v0001 = 50.53.

Decision and limits:
- **No promotion; v0030 stays the heart-extrap selection.** v0032's +0.02 is inside the
  pre-declared ±0.1 TIE band (B4-T2-R1 precedent); its per-metric read vs v0030
  (dir +0.3, mmd +0.4, vario −0.6, nmmd −0.1) is a wash. v0034 sits at the band edge.
  Derived values unchanged: T2 = (62.89+62.36+51.12)/3 = 58.79; derived sum 160.27
  (both derived only; portal-confirmed Total remains 156.06).
- **Server-side dose-response on de, monotone**: damp 0.5 → de 50.8 (v0033);
  per-type adaptive ≈0.73 mean dose → 51.6 (v0034); damp 0.9 (±t-shrink) → 52.0
  (v0030, v0032). The dev dose bracket (optimum 0.9) reproduces on the server; the
  dose axis is CLOSED with a server-consistent optimum at 0.9. The dev "purest DE
  direction" read on the half-dose lane did NOT transfer (50.8 < 52.0).
- **Within-family dev ranking reproduced perfectly.** dev medians 0.9194 / 0.9347 /
  0.9376 (run18 / run09 / run04 recipes) map to server 51.14 / 51.02 / 50.89 —
  Spearman 1.0 across the three-lane family. The Route-C-era "local DE readout is
  broken on this board" conclusion is family-specific: within one recipe family the
  frozen dev evaluator is a reliable ranker; cross-family transfer is where it fails.
- **d2/occ/scale pinned at 46.2/53.2/49.7 across all three lanes** (as in v0030/v0031):
  expected — parent-anchored expression-only construction cannot move the
  geometry/occupancy/scale channels.
- blocks_submission: false.

Submetrics: `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, 24 rows. Review:
`reports/t2_holdout10_score_review_20261003/REPORT.md`. Decision D-20261003-T2H10X567SCORE-001.

<a id="t1-ar-mix2-score-return-20261003"></a>
## T1 AR-MIX2 score return — 2026-10-03

User-transcribed portal returns for the five AR-MIX2 lanes
(`deliveries/art1mix2__t1__upload__20261003.zip`, run `AR-T1-MIX2-20261003-v1`;
zip sha `e8b60cd8d87172db…`; staged member shas verified at packing time).
Submission IDs, upload timestamps and portal Total NOT supplied; no independent
portal query. Values preserve supplied precision. Versions v0052–v0056 are
PROPOSED (INDEX rows pending coordinator). Version-number note: the closed
T1-EXTPRE lane referenced "v0052" as a would-have-been number ("不建 v0052",
no artifact was ever built); this batch's v0052 is the mix3538even member below —
no artifact conflict, identity is bound by SHA256.

| Version / portal model | Total | de | dir | mmd_u | vario | Verdict |
|---|---:|---:|---:|---:|---:|---|
| v0052 `t1_val__mix3538even__v0052.h5ad` (50/50 v0035×v0038, seed 20260921) | 53.67 | 46.9 | 60.0 | 56.1 | 50.5 | scored backup (−0.25 vs v0051; beats both parents 53.43/53.55) |
| v0053 `t1_val__mix3538evenb__v0053.h5ad` (50/50 v0035×v0038, seed 20261023) | 53.36 | 46.7 | 59.9 | 55.4 | 50.4 | REJECT (−0.56 vs v0051; below both parents) |
| v0054 `t1_val__mix3638even__v0054.h5ad` (50/50 v0036×v0038, seed 20260921) | 53.98 | 47.0 | 60.4 | 56.5 | 51.0 | TIE (+0.06 vs v0051 53.92, inside ±0.1 band; no promotion; tied numeric-high backup) |
| v0055 `t1_val__mix3way__v0055.h5ad` (equal thirds v0035/36/38, seed 20260921) | 53.48 | 46.4 | 59.4 | 56.3 | 50.7 | scored backup, marginal (−0.44 vs v0051; beats v0035 53.43 / v0036 53.36, trails v0038 53.55) |
| v0056 `t1_val__mix3538f030__v0056.h5ad` (30/70 v0035×v0038, seed 20260921) | 53.76 | 46.9 | 60.3 | 56.1 | 50.6 | scored backup (−0.16 vs v0051; beats both parents) |

Incumbent: v0051 = 53.92 (47.2/60.0/56.7/50.6). No promotion: v0054's +0.06 is
inside the pre-declared ±0.1 TIE band (precedent D-20260917-G0T1-001; tie goes to
the incumbent); v0051 stays the T1 selection and v0054 is the tied numeric-high
backup. Derived sum unchanged at 160.44 (counting v0054 instead would give 160.50 —
derived only, NOT a portal Total; last portal-confirmed Total remains 156.06).
Submetric read vs v0051, descriptive not causal: v0054 trades de (−0.2) and mmd
(−0.2) for dir (+0.4) and vario (+0.4) — a textbook TIE-band swap.

Headline findings:
1. **Seed-pair luck replicates a third time**: v0052 vs v0053 = 53.67 vs 53.36
   (Δ0.31) for the identical 50/50 35×38 design with different draws (batch-1
   Δ0.40). T1 mix server row-luck is ±0.3–0.4 — larger than the ±0.1 TIE band.
   "Ship 2 seeds or go deterministic" stands; single-seed reads of resampling
   designs are lottery tickets.
2. **Pair axis confirmed by controlled comparison**: v0054 (36×38 even) 53.98 vs
   v0052 (35×38 even) 53.67 = +0.31 at the SAME weight and seed (20260921).
   36-containing mixes lead for the third time (36×38@70/30 53.92 → 36×38@50/50
   53.98); the 35×38 pair plateaus at 53.36–53.76 regardless of weight.
3. **Weight axis is dead for 35×38**: f0.3 53.76 ≈ f0.5 53.67 ≈ f0.7 53.72/53.32 —
   all inside row-luck. No server dose-response on the fraction knob.
4. **Three pools do not stack**: v0055 (53.48) lands below both of its pair-mix
   components (53.67 / 53.98) — dilution, not synergy. Three-pool mixing is closed
   as a promotion axis on T1.
5. **The mix family looks saturated**: all eight scored mix lanes sit in
   53.32–53.98 (plateau mean ≈ 53.7); incremental movement is now in ±0.1 lottery
   units. The next real move needs a new mechanism family, not more winner-pair
   arithmetic.

Submetrics: `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, +20 rows. Decision:
D-20261003-T1MIX2SCORE-001. blocks_submission: false.
Pending coordinator: INDEX rows (v0052–v0056; staged paths + SHAs in
`artifacts/autoresearch/t1-20261003-v1/stage_art1mix2/UPLOAD_MANIFEST.tsv`),
T1_TRACKING line, STATUS/TODO sync. (Still pending from 2026-10-02: INDEX rows
v0049–v0051 — that batch's submetric rows and LANE_VERDICTS rows were also never
added.)

<a id="t3-six-score-return-20261007"></a>
## T3 六新路线回分（2026-10-07）

来源：用户本轮直接提供；canonical与交付文件SHA匹配INDEX（zip `deliveries/t3six__t3__upload__20261006.zip`，6 成员）。未查询门户，submission ID/上传时间/截图未提供。

```text
t3_gata4__o1dual__v0075.h5ad：46.73
de_score 40.0
de_direction 50.9
severity_slope 50.0
mmd_u 51.2
variogram 42.1

t3_gata4__o2gate__v0076.h5ad：47.31
de_score 40.4
de_direction 50.3
severity_slope 50.0
mmd_u 51.6
variogram 49.0

t3_gata4__o3shrink__v0077.h5ad：47.43
de_score 40.8
de_direction 50.3
severity_slope 50.0
mmd_u 51.6
variogram 48.9

t3_gata4__n1nmf__v0078.h5ad：47.93
de_score 42.6
de_direction 49.8
severity_slope 50.0
mmd_u 51.9
variogram 49.9

t3_gata4__n2marker__v0079.h5ad：47.4
de_score 40.0
de_direction 51.2
severity_slope 50.0
mmd_u 51.5
variogram 48.9

t3_gata4__n3switch__v0080.h5ad：46.82
de_score 40.4
de_direction 49.3
severity_slope 50.0
mmd_u 51.9
variogram 45.7
```

总分与五项原样登记。对照现役 v0048=47.93：v0078（N1 NMF 程序消融）47.93 同分，按 ±0.1 平局带规则现役留下、不换人；其余 5 个（o1_dual 46.73、o2_gate 47.31、o3_shrunk 47.43、n2_marker 47.4、n3_switch 46.82）均低于现役，NOT_PROMOTED。六条源侧变换路线一次回分无一晋级：hurdle 概率门、可靠性收缩、marker 门与开关发射都没有把 DE 或分布子分抬过现役；v0078 的 DE 42.6 是六候选最高、variogram 49.9 也接近现役，但未构成晋级，不能据此宣称 NMF 机制优于现役。同分不换人与单次评分的无重复性照旧。D-20261007-T3SIXSCORE-001；reports/t3_six_routes_20261006/REPORT.md。blocks_submission:false。

<a id="t2-geom4-score-return-20261007"></a>
## T2 GEOM4 score return — 2026-10-07

Source / raw evidence: user-transcribed portal returns in this conversation for the four
geometry lanes (`deliveries/t2geom__t2__upload__20261007.zip`, sha `f864af37…`; run
`T2-GEOM4-20261007-v1`). Evidence class: SERVER_SCORED_USER_REPORTED. No independent
portal lookup; portal submission ID and timestamp not supplied; no Total returned.
Candidate identity verified by ZIP-member filename bound to INDEX SHA256
(v0023 `049c48f0…`, v0024 `b553bd9c…`, v0035 `3cfb0791…`, v0018 `66f4674b…`);
no artifact was modified. Date is the score-recording date.

```text
t2_hrt_int__h_aniso50__v0023.h5ad: 62.48
t2_hrt_int__h_qaxis__v0024.h5ad: 60.61
t2_hrt_ext__x_grows__v0035.h5ad: 49.06
t2_emb_int__e_qaxis__v0018.h5ad: 62.50
```

| Portal model | Board score | de | dir | mmd_u | vario | d2 | occ | scale | nmmd | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `t2_hrt_int__h_aniso50__v0023.h5ad` | 62.48 | 61.2 | 66.1 | 61.9 | 30.0 | 69.5 | 45.2 | 97.9 | 66.3 | **PROMOTED (+0.12 vs v0019 62.36; outside ±0.1)** |
| `t2_hrt_int__h_qaxis__v0024.h5ad` | 60.61 | 61.2 | 66.1 | 61.9 | 30.0 | 37.9 | 53.5 | 97.9 | 66.6 | REJECT (−1.75) |
| `t2_hrt_ext__x_grows__v0035.h5ad` | 49.06 | 52.0 | 50.9 | 49.4 | 50.4 | 33.3 | 50.4 | 40.7 | 53.5 | REJECT (−2.06 vs v0030 51.12) |
| `t2_emb_int__e_qaxis__v0018.h5ad` | 62.50 | 55.2 | 67.4 | 60.3 | 56.0 | 51.9 | 48.9 | 90.8 | 66.2 | REJECT (−0.39 vs v0014 62.89) |

Decision and limits:
- **Heart interpolation selection moves to v0023 = 62.48.** +0.12 is outside the
  standing ±0.1 TIE band (the band edge, used for v0034 −0.10, stays inside and
  does not promote). Expression metrics and scale are identical to v0019. The
  whole gain is d2 65.4→69.5, paid for by occupancy 47.8→45.2. Promotion is real.
  It does not mean the occupancy hole was repaired.
- **Quantile transport is closed.** v0024 raised occupancy to 53.5 and collapsed
  d2 to 37.9. Embryo v0018 lost both geometry skills. Do not retune the quantile.
- **Growth extrapolation is closed.** v0035 left expression identical to v0030 and
  made scale 49.7→40.7 and d2 46.2→33.3. The formula factor 0.890 was read by the
  server as a worse size, same direction as the closed ×0.9 knob. Do not try
  another factor.
- Derived only: T2 = (62.89+62.48+51.12)/3 = 58.83; derived sum
  53.92+58.83+47.93 = 160.68. Portal-confirmed Total remains 156.06.
- blocks_submission: false.

Submetrics: `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, 32 rows. Review:
`reports/t2_geom4_20261007/SCORE_REVIEW.md`. Decision D-20261007-T2GEOM4SCORE-001.

<a id="t1-six-score-return-20261007"></a>
## T1 SIX score return — 2026-10-07

Source / raw evidence: user-transcribed portal returns in this conversation for the six
T1-SIX lanes (`deliveries/t1six__t1__upload__20261007.zip`, zip sha `22e99637…`; run
`T1-SIX-20261007-v1`). Evidence class: SERVER_SCORED_USER_REPORTED. No independent
portal lookup; portal submission ID and timestamp not supplied; no Total returned.
Candidate identity verified by ZIP-member filename bound to INDEX SHA256
(v0057 `d8e0b178…`, v0058 `7e0ff6c6…`, v0059 `0d58989a…`, v0060 `52bf8c7b…`,
v0061 `e8cc3acd…`, v0062 `cd8c1501…`); no artifact was modified. Date is the
score-recording date.

```text
t1_val__osoftcov__v0057.h5ad: 49.28
t1_val__ostabmix__v0058.h5ad: 53.85
t1_val__nconf__v0059.h5ad: 51.13
t1_val__nbidir__v0060.h5ad: 52.07
t1_val__ocovstab__v0061.h5ad: 49.42
t1_val__nwasser__v0062.h5ad: 51.02
```

| Portal model | Board score | de | dir | mmd_u | vario | Verdict |
|---|---:|---:|---:|---:|---:|---|
| `t1_val__osoftcov__v0057.h5ad` | 49.28 | 42.6 | 55.7 | 51.9 | 45.7 | REJECT (−4.64 vs v0051 53.92) |
| `t1_val__ostabmix__v0058.h5ad` | 53.85 | 46.7 | 60.4 | 56.1 | 51.2 | **TIE 带内（−0.07; ±0.1 内不换人）NOT_PROMOTED** |
| `t1_val__nconf__v0059.h5ad` | 51.13 | 45.0 | 56.3 | 53.6 | 48.6 | REJECT (−2.79) |
| `t1_val__nbidir__v0060.h5ad` | 52.07 | 44.2 | 59.1 | 53.8 | 50.4 | REJECT (−1.85) |
| `t1_val__ocovstab__v0061.h5ad` | 49.42 | 43.0 | 55.3 | 51.3 | 47.3 | REJECT (−4.50) |
| `t1_val__nwasser__v0062.h5ad` | 51.02 | 44.8 | 56.2 | 53.6 | 48.5 | REJECT (−2.90) |

Decision and limits:
- **v0051 = 53.92 留任**。v0058（ostabmix，本地 de 冠军 0.6111 = +0.0185）服务器
  53.85 落在 ±0.1 平局带内不晋级——本地 de 信号再次未转化为服务器收益，与 T1 phase
  预承诺的 proxy 有效性警告一致（本地 de 不选拔服务器冠军）。
- v0058 的 dir 60.4（与 v0054 并列已知最高）与 vario 51.2（已知最高）是板面强项，
  但被 de 46.7（−0.5 vs 47.2）与 mmd 56.1（−0.6 vs 56.7）抵消。不据此宣称
  ostabmix 机制优于现役，不重启混合族调参。
- 其余五件全部 REJECT：conformal 校准（v0059）、前向/后向一致性权重（v0060，本地
  dir/Energy/Vario 改善未兑现）、cov-OT 升级（v0061）、精确 OT 位移场（v0062）、
  soft-cov（v0057）均无晋级信号。
- 六条一次回分无一晋级：混合/结合族饱和再确认（v0058 又一个 ~53.8）；全新机制
  三件（nconf/nwasser/nbidir）也未越过现役。本波关闭。
- Derived only: T1 53.92 不变；derived sum 160.68 不变。Portal-confirmed Total
  remains 156.06。
- blocks_submission: false.

Submetrics: `reports/SERVER_SUBMETRIC_REGISTRY.tsv`, 24 rows. Review:
`reports/t1_six_20261007/REPORT.md`. Decision D-20261007-T1SIXSCORE-001.

<a id="t3-backlog-score-return-20261008"></a>
## T3 backlog reproduction and score return — 2026-10-08

Evidence class: SERVER_SCORED_PORTAL_VERIFIED. Direct authenticated browser observation of official submission detail pages. Scores below retain detail-page precision; list-page rounded values are separate. Submitted timestamps are copied from the page, whose timezone is not labelled; UTC observation times do not reinterpret submitted timestamps. No account email or other private account details are published.

User requested original candidate IDs v0083–v0085. These three are explicitly labelled same-ID reconstructed revisions, not original-byte restorations; historical and uploaded SHA256 bindings are preserved in INDEX. Original frozen parameters unchanged. v0081/v0082 are existing submissions, not resubmitted by this run. Their mapping uses exact portal filenames; portal did not expose artifact hashes, so their historical INDEX SHA values have not been independently binary-verified. v0081/v0082 remain within the prior v0048 tie band; neither is promoted.

| Candidate | Portal file | Submission ID / evidence | Submitted (timezone unlabelled) | Observed UTC | Detail score | List score | de_score | de_direction | severity_slope | mmd_u | variogram |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| v0081 | `t3_gata4__hnmf__v0081.h5ad` | [62c624e98c1e4c218e20688ba15e2b24](https://virtualembryo.ai/challenge/account/submissions/62c624e98c1e4c218e20688ba15e2b24) | 2026-10-07 11:07 | 2026-10-08T06:44:40Z | 47.92 | 47.9 | 42.6 | 49.9 | 50.0 | 51.8 | 49.5 |
| v0082 | `t3_gata4__pnmf__v0082.h5ad` | [e1e3ddd0cac241d391cf3f7bba27c54f](https://virtualembryo.ai/challenge/account/submissions/e1e3ddd0cac241d391cf3f7bba27c54f) | 2026-10-07 11:07 | 2026-10-08T06:45:22Z | 47.94 | 47.9 | 42.6 | 49.9 | 50.0 | 51.8 | 49.6 |
| v0083 | `t3_gata4__repropsb__v0083.h5ad` | [d22593c4f14041be9824552910220129](https://virtualembryo.ai/challenge/account/submissions/d22593c4f14041be9824552910220129) | 2026-10-08 06:36 | 2026-10-08T06:38:25Z | 47.51 | 47.5 | 41.2 | 50.0 | 50.0 | 51.7 | 49.2 |
| v0084 | `t3_gata4__reproqtl__v0084.h5ad` | [d11defa589b64fcd90bfb76d83328707](https://virtualembryo.ai/challenge/account/submissions/d11defa589b64fcd90bfb76d83328707) | 2026-10-08 06:40 | 2026-10-08T06:41:15Z | 49.55 | 49.6 | 47.1 | 48.4 | 50.0 | 54.8 | 53.4 |
| v0085 | `t3_gata4__reprodsign__v0085.h5ad` | [1e1a1d550e66460fbe61a59647d19117](https://virtualembryo.ai/challenge/account/submissions/1e1a1d550e66460fbe61a59647d19117) | 2026-10-08 06:42 | 2026-10-08T06:43:37Z | 47.45 | NOT_RECORDED | 40.8 | 50.1 | 50.0 | 51.9 | 49.2 |

All five submetrics are the portal SKILL values, not locally computed scores. v0084 reconstructed q0.25 revision is promoted at 49.55 (+1.62 versus previous incumbent v0048 47.93), beyond the strict >48.03 promotion threshold. Same-ID reconstruction does not retroactively score the unavailable historical bytes. No other board selection or portal Total is changed by this registration. blocks_submission:false.

Identity/reconstruction: reports/t3_backlog_20261008/RECONSTRUCTION_RECEIPT.json and REPORT.md. Decision reports/SERVER_SCORE_REGISTRY.md#t3-backlog-score-return-20261008.

Portal leaderboard observation at 2026-10-08T06:46:14Z: displayed Total 163.2, Human rank 83, task values T1 54.0 / T2 59.7 / T3 49.6. Before these three uploads the observed Total was 161.6, rank 85. The independent T2 heart-interpolation 65.0 submission was not produced by this run; no T1/T2 candidate identities or selections are reassigned here. These are rounded page displays, not inferred precise totals.

<a id="t3-arank-v0086-score-return-20261008"></a>
## T3 v0086 arank revision 2 score return — 2026-10-08

Evidence class: SERVER_SCORED_PORTAL_VERIFIED. Official detail page observed
2026-10-08T08:55:06Z. Submitted display is `2026-10-08 08:54`; its timezone is not
labelled. Submission [7e5a259d47d84ce086ddc7c5e8bc9b0a](https://virtualembryo.ai/challenge/account/submissions/7e5a259d47d84ce086ddc7c5e8bc9b0a),
file `t3_gata4__arank__v0086.h5ad`. Exact uploaded SHA256 is in INDEX; only revision 2
was submitted. Earlier pre-submit drafts and unused temporary version labels are
not registered as candidates or charged as submissions here.

| Candidate | Detail score | de_score | de_direction | severity_slope | mmd_u | variogram | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| v0086 arank r2 | 49.34 | 46.5 | 48.4 | 50.0 | 54.5 | 53.1 | REJECT; -0.21 vs v0084 49.55 |

The five submetrics are displayed SKILL values; raw metric values were not exposed
and are not inferred. Current selection remains v0084's 2026-10-08 reconstructed
q0.25 revision, score 49.55; this attempt does not cross the ±0.1 incumbent band.

Algorithm and limits: domain-anchored response-rank transport, using pooled-control
source-range correction and equally weighted sample-matched positive-quantile
changes indexed by embryo positive ranks. Parent is v0084. Inputs remain the
existing approved GSE261783 OP2/26 source and GO information, without target KO
truth. Final zero mask, global positive-rank order, composed 0.5–2.0 carrier bounds,
7449×500 contract and artifact/hash checks passed. The source-side evidence is
historical and adaptively reused, not a pristine validation set. Source-proxy
improvement did not transfer to the embryo leaderboard for this configuration;
this negative result does not establish a causal mechanism or invalidate all
possible domain-transfer methods. No parameter sweep or another submission is
implied by this record.

One of the user's two newly authorized attempts has been used; one remains
reserved. Portal Total/rank observed at 2026-10-08T08:55:56Z remained 163.2/83
(rounded display); other-board identities and selections are unchanged.
blocks_submission:false. Five metric rows appended to SERVER_SUBMETRIC_REGISTRY.tsv.

<a id="t3-embhurdle-v0087-score-return-20261008"></a>
## T3 v0087 embryonic hurdle-v2 score return — 2026-10-08

Evidence class: SERVER_SCORED_PORTAL_VERIFIED. Official detail page observed
2026-10-08T10:48:14Z. Submitted display is `2026-10-08 10:47`; timezone is unlabelled.
Submission [592546488d2543d5bfcf42394d5de414](https://virtualembryo.ai/challenge/account/submissions/592546488d2543d5bfcf42394d5de414),
file `t3_gata4__embhurdle__v0087.h5ad`. The exact uploaded SHA256 is in INDEX;
original v0084/v0086 artifacts, scores and hashes are preserved.

| Candidate | Detail score | de_score | de_direction | severity_slope | mmd_u | variogram | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| v0087 embhurdle v2 | 53.42 | 41.7 | 51.2 | 75.0 | 49.7 | 42.3 | PROMOTED; +3.87 vs v0084 49.55 |

**Current T3 selection: v0087, 53.42.** The gain exceeds the ±0.1 incumbent band;
v0084's 2026-10-08 reconstructed q0.25 revision remains a historical fallback.
The five submetrics are displayed SKILL values; raw metrics were not exposed and
are not inferred. Compared with v0084, direction rises 48.4→51.2 and severity
50.0→75.0, while DE falls 47.1→41.7, MMD 54.8→49.7 and variogram 53.4→42.3.
This is a total-score improvement with substantial distribution/DE tradeoffs,
not uniform improvement across metrics.

Method/source boundary: a generic seven-KO embryonic state-response model with
composition resampling and separate detection-fraction/positive-quantile hurdle-v2
emission. Selected source conditions are E8.5 Dnmt1, Dnmt3a, Dnmt3b, Ehmt2/G9a,
Kdm2b, Kmt2a and Kmt2b interventions from GSE137337, with GSE122187 E8.5 WT and
ontology information. These replace the previous adult-fibroblast response source;
there are seven source KOs, not adult OP2/26 in this model. GO identity models were
compared but the final generic response is not determined by GO identity.
Condition-scoped permits, attribution and full source provenance are embedded in
the uploaded artifact. No hidden Gata4 truth, same-target KO signatures or forbidden
phenocopy data were used. WT-only states, sex-matched controls and equal embryo
weighting do not eliminate cohort, chemistry, sex and developmental-context
confounding; development was adaptive, not a pristine independent confirmation.
This is a generic developmental perturbation prior, not proof of a Gata4-specific
causal mechanism.

Final 7449×500 contract, source review, frozen expression equality, parent v0084
geometry and independent hash/array checks passed before submission. Expression
carrier is official E8.75 WT; v0084 is the selected parent/geometry reference.
The two newly authorized attempts are now exhausted: v0086 and v0087. No further
submission is implied. Other-board identities and selections are unchanged.
blocks_submission:false. Five metric rows appended to SERVER_SUBMETRIC_REGISTRY.tsv.

Portal leaderboard observation at 2026-10-08T10:49:25Z: displayed Total 167.1, Human rank 72, T1 54.0 / T2 59.7 / T3 53.4. These are rounded page displays; the submission detail provides the exact T3 score 53.42. No precise aggregate is inferred, and unrelated board candidate identities are not reassigned.

<a id="t3-condhurdle-v0088-score-return-20261008"></a>
## T3 v0088 conditional hurdle score return — 2026-10-08

Evidence class: SERVER_SCORED_PORTAL_VERIFIED. Official detail page observed
2026-10-08T11:57:10Z. Submitted display is `2026-10-08 11:56`; timezone is unlabelled.
Submission [67faa8da3e0049d4a26a6fa64c2984b0](https://virtualembryo.ai/challenge/account/submissions/67faa8da3e0049d4a26a6fa64c2984b0),
file `t3_gata4__condhurdle__v0088.h5ad`. Exact uploaded SHA256 is in INDEX.
All previous candidate rows, artifacts, scores and hashes are preserved.

| Candidate | Detail score | de_score | de_direction | severity_slope | mmd_u | variogram | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| v0088 condhurdle | 53.69 | 41.7 | 51.2 | 75.2 | 51.1 | 43.1 | PROMOTED; +0.27 vs v0087 53.42 |

**Current T3 selection: v0088, 53.69.** The +0.27 gain is beyond the ±0.1 incumbent
band; v0087 remains a historical fallback. Five submetrics are exact displayed
SKILL values, not raw metrics. Raw metric values were not displayed and are not
inferred. DE/direction are unchanged at displayed precision; severity improves
+0.2, MMD +1.4 and variogram +0.8 versus v0087. The improvement is concentrated in
distribution/emission behavior; it does not establish a new target-specific causal
response or imply that unchanged rounded submetrics are numerically identical.

Method boundary: same seven-KO generic embryonic state-response hurdle as v0087,
replacing random zero-activation ties with WT-only state-conditioned activation
propensity. This arm was selected through the frozen four-family source comparison;
no post-portal retuning is represented by this record. Sources remain the admitted
GSE137337 embryonic KO conditions, GSE122187 WT and ontology information; no new
source scope or hidden target outcomes. The source development remains adaptive,
and cohort/chemistry/developmental confounding is not resolved by this score gain.
Full condition-level source/implementation provenance is in the uploaded artifact.
Final frozen-array, source/code, parent protected metadata/geometry and 7449×500
contract checks independently passed before submission.

This consumes the user's separately authorized final one-attempt budget. No further
attempt remains authorized; the portal displayed daily T3 usage 8/8 after acceptance.
Other-board candidate identities and selections are unchanged. blocks_submission:false.
Five rows appended to SERVER_SUBMETRIC_REGISTRY.tsv.

Portal leaderboard observed at 2026-10-08T11:58:09Z: displayed Total 171.4, Human
rank 61, T1 58.0 / T2 59.7 / T3 53.7. Immediately before this final attempt the
observed Total/rank was 171.1/62. These are rounded displays; only the detail-page
T3 score is recorded precisely as 53.69. The separate T1 improvement is not credited
to this T3 attempt, and no precise aggregate is inferred.

<a id="t2-heart-extrap-endpoint-rank-v0036-score-return-20261008"></a>
## T2 heart extrapolation v0036 endpoint-rank score return — 2026-10-08

Evidence class: SERVER_SCORED_PORTAL_VERIFIED. Official detail page observed
2026-10-08T12:45:01Z. Submitted display is `2026-10-08 12:44`; timezone is unlabelled.
Submission [4ccbf06d9ca247a191e3d7cefb242a7c](https://virtualembryo.ai/challenge/account/submissions/4ccbf06d9ca247a191e3d7cefb242a7c),
file `t2_hrt_ext__x_endrank__v0036.h5ad`, 15,353,761 bytes.
Exact uploaded SHA256: `0b89c69adff3b5cb3d86f0d8b0dbfe667f289343b0d7ac8908ca9c70ed33fc03`.

| Candidate | Detail score | de_score | de_direction | mmd_u | variogram | d2_shape | occupancy_dice | scale_log_ratio | neighborhood_mmd | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| v0036 x_endpoint_rank | 50.47 | 52.4 | 52.6 | 44.8 | 52.3 | 46.2 | 53.2 | 49.7 | 51.8 | REJECT for promotion; -0.65 vs incumbent v0030 51.12 |

**Heart-extrap selection remains v0030, 51.12.** Numeric-high backup v0032 remains
51.14 under the existing ±0.1 tie/no-co-promotion rule; v0036 is 0.67 below it.
All eight submetrics are displayed SKILL values, not raw metrics. Raw values were
not exposed and are not inferred. Relative to incumbent v0030, displayed
DE/direction/variogram rise +0.4/+1.7/+1.9, while MMD falls -4.6 and neighborhood
MMD -1.7; d2/occupancy/scale are unchanged. Source-proxy gains did not transfer
to total server score in this submission. This is a configuration-level negative
result, not proof that every external-endpoint method fails.

Method/source boundary: fixed-drift cardiomyocyte endpoint-rank residual using
official released stages and clean raw MOSTA STDS0000058 E14.5_E1S3 Heart bins
(Chen et al., Cell 2022, DOI 10.1016/j.cell.2022.04.003). The fixed terminal-rank
correction used 483 measured genes, 7,633 eligible cardiomyocyte rows and weight
0.104, with 17 unmeasured genes and non-cardiomyocyte rows left at the reconstructed
recipe. No external E9.5 or hidden E10.5/E12.5 outcomes were used. Full source
attribution and provenance are embedded in the submitted artifact. Historical
v0030 is a recipe reference; its exact artifact was unavailable and byte-identical
parent reconstruction is NOT claimed. The local development was adaptive and
reused E9.5; the held-row check is not an independent biological validation.
A single far-stage, mixed-bin external section limits the transfer evidence.

Final 25179×500 contract, frozen-array/hash and independent replay checks passed
before submission. This record registers the scored artifact without uploading
its binary or broad audit files to the repository. All previous candidate rows,
hashes, scores and other-board selections are preserved. The single authorized
T2 attempt is consumed; portal daily usage is 8/8. No further submission is
implied. Eight rows appended to SERVER_SUBMETRIC_REGISTRY.tsv.

<a id="t1-late-anchor-ot-score-return-20261009"></a>
# T1 late-anchor OT score return 20261009

## T1 late-anchor LA1–LA3 and OT generative A/B score return — 2026-10-09

**Renumber note:** mistaken labels v0063–v0067 from earlier side-file drafts are retired.
Those IDs already belong to T3:gata4. Global high-water was v0088; assigned
**v0089–v0093**. SHA-256 values unchanged.

Evidence class: SERVER_SCORED_PORTAL_VERIFIED for LA3 and round-3 A/B (detail pages / board
readbacks confirmed 2026-10-09 CST). LA1/LA2 totals are SERVER_SCORED_USER_REPORTED from
the same late-anchor campaign (2026-10-08); their four skill columns were not re-captured
in this write-up and are left blank rather than inferred. Human Team track. Artifacts
remain local (`*.h5ad` gitignored); SHA-256 values match
`reports/t1_late_anchor_20261008/MANIFEST.tsv`. Code published under `scripts/vework/`
and `scripts/vework/t1ext/`. External scope: GEO GSE230531 per-sample files only
(E8.5 GSM7226268/69, E14.5 GSM7226272/73, E16.5 GSM7226274/76 for warp check);
banned-window E10.5/E12.5 never downloaded. No pre-trained models.

| Candidate | Detail score | de_score | de_direction | mmd_u | variogram | Verdict |
|---|---:|---:|---:|---:|---:|---|
| v0089 LA1 late_anchor_x1 | 53.14 | — | — | — | — | REJECT (−0.78 vs incumbent v0051 53.92) |
| v0090 LA2 late_anchor_x2_comphalf | 53.43 | — | — | — | — | REJECT (−0.49 vs v0051) |
| v0091 LA3 v51_anchor_auto | 57.99 | 51.6 | 64.0 | 61.7 | 52.8 | PROMOTED vs v0051 (+4.07); later superseded by v0092 |
| v0092 ot-gen-A ot_gen_v51 | **58.89** | 49.7 | 65.9 | 65.2 | 52.3 | **PROMOTED current T1 best** (+0.90 vs LA3) |
| v0093 pergroup-B v51_anchor_pergroup | 58.22 | 51.4 | 64.2 | 62.4 | 53.0 | scored backup (−0.67 vs A; +0.23 vs LA3) |

Portal detail IDs:
- A: https://virtualembryo.ai/challenge/account/submissions/39e6870fb90549e09067e7c3cff92333
- B: https://virtualembryo.ai/challenge/account/submissions/455eb227ed4a407382c2f18a4d2ab920

Exact uploaded SHA256:
- LA1 `f876b1ef0983c635833fe7ca8713034712b777b091413196923fac5282d84282`
- LA2 `7dbc0eb05f5ab578fffe3590158bbb5b33cd1230acb26522759a1db5e217fa09`
- LA3 `79af479a577c53a182b5c74aeba5066c8b9a553e1a9570ccf4b9a15c540052d2`
- A `35fae3a797acdf44b4c6d141e1a0db65b44744ea218f96218c7909e34eda5dc1`
- B `04d73c5d2c9daab7c9fc9db3ba9543c295639f9e4415ca312511c0147adf7fe6`

**Current T1 selection: v0092 ot-gen-A, 58.89.** See also `reports/t1_late_anchor_20261008/SCORE_RETURN.md`
and `reports/t1_late_anchor_20261008/INDEX_ROWS.tsv`. Local backtests remain a
proxy-faithfulness bound, recorded in `reports/t1_late_anchor_20261008/backtests/` and
PROGRESS_T1_round3.md. This does not establish a developmental mechanism claim.

Twelve skill rows (LA3 + A + B × four metrics) appended to SERVER_SUBMETRIC_REGISTRY.tsv.
INDEX rows v0089–v0093 appended (old mistaken v0063–v0067 labels retired). Test-phase plan
(no official submission authorized by this commit): `reports/TEST_PHASE_PLAN.md`.
blocks_submission:false for further val work; ask before any official test-phase portal upload.
