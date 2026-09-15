# Batch 4 Phase Report — 2026-09-15 (closeout)

## 1. 实际上传与回填

| Task | Lanes scored | Server scores | Disposition |
|---|---|---|---|
| P0 floors | T1 v0009 47.0; T3 v0008 46.8 | 47.0 / 46.8 | baselines, no promotion |
| T1-R1 | v0011–v0014 | 47.58 / 47.77 / 47.85 / 46.90 | all REJECT, v0004 stays |
| T1-R2 | — | — | BLOCKED_DATA_NOT_READY (no scored H5AD by design) |
| T2-R1 | v0010/v0011 | 57.3 / 57.31 | TIE, v0009 stays, micro-tuning closed |
| T2-R2 | embryo v0009/v0010; heart v0012/v0013 | 61.79 / 62.29 / 56.27 / 62.04 | 3 promotions |
| T2-R3 | v0008/v0009/v0010 | — | closed_unscored per user 2026-09-15 |
| T3-R1 | v0009/v0010 | 46.95 / 46.95 | tied best |
| T3-R2 | v0011/v0012 | 46.45 / 46.47 | REJECT, reset trigger |

## 2. Current best (server aggregate first)

| Board | Best | Version |
|---|---|---|
| T1:val | 48.47 | v0004 (unchanged all batch) |
| T2 embryo | 62.29 | B4-T2-R2 v0010 |
| T2 heart_interp | 62.04 | B4-T2-R2 v0013 |
| T2 heart_extrap | 50.53 | baseline v0001 (unchanged) |
| T3:gata4 | 46.95 | B4-T3-R1 v0009/v0010 tied |
| **Total (server)** | **153.7** | confirmed 2026-09-15 |

## 3. 成功分级判定

- S0 审计成功：达成（registry/INDEX/TRACKING 一致；floor builder 差异逐项列出；全部 run 有 lock）。
- S1 基线修复：未达成（floor parity 未解决；T1 47.0 / T3 46.8 均未到 50±0.2，且未能证明参赛者不可复制）。
- S2 有效追赶：达成（T2 +2.31 ≥ 1.0；与第十名差距缩小，见 SCORE_GAP）。
- S3 理想结果：未达成（T2 58.29 < 59；T1/T3 远未及）。

## 4. 架构决策

**`ARCHITECTURE_RESET_REQUIRED`**（触发器见 SCORE_GAP §4；brief 见 ARCHITECTURE_RESET_BRIEF.md）。
T2 插值 parent（v0010/v0013）作为可保留增量资产；T1/T3 需要新架构能力（见 brief §能力缺口）。
T2-R3 closed_unscored：用户明确关闭本批，不再追分；heart_extrap 仍是全项目最弱 board。

## 5. 证据链

- `reports/SERVER_SCORE_REGISTRY.md`（全部回填节）+ `reports/SERVER_SUBMETRIC_REGISTRY.tsv`
- `submissions/INDEX.tsv`（T2-R3 三行已标 closed_unscored，artifact 不变）
- `docs/coordination/DECISIONS.md`（D-20260915-B4CLOSE-001 本次封板）
- 各 run `artifacts/batch4/*/RESULT.md` + RUN_LOCK
