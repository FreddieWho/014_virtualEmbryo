# Server leaderboard score registry

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
