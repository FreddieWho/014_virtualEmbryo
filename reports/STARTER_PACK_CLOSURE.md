# Starter Pack closure report

更新时间：2026-08-22

## 结论

`CLOSED_FOR_COMPETITION_BASELINE`

`OPEN_FOR_RESEARCH_EXTENSION`

starter_pack 的主要职责是搭建可合规生成、检查和提交首轮榜单候选的基本环境。该目标已经完成：官方数据/面板/scorer 已落盘，T1/T2/T3 的提交路径已建立，官方或等价 baseline 已生成，本地 scorer smoke 已通过，并且已经取得首个服务器评分。

科学 promotion 仍为 `BLOCKED_FOR_SCIENTIFIC_PROMOTION_ONLY`，且 `blocks_submission: false`。这表示科学证据不足以支持更强的生物学结论，但不阻断后续合法的 leaderboard 迭代。

## 关闭依据

| 最低关闭要求 | 当前证据 | 状态 |
|---|---|---|
| 官方规则、任务、面板和 scorer 已锁定 | `reports/OFFICIAL_SYNC.md`；`third_party/veckit` commit `46d41e63f42a9aab815db20b742feeccd249cb17` | PASS |
| challenge 数据和官方 panel 可读、结构已核对 | `data/MANIFEST.tsv`、`infra/bioinf-data-index/INDEX.tsv` | PASS |
| T1/T2/T3 合法 submission 路径已建立 | `scripts/prepare_t1_t3_submission.py`、`scripts/prepare_t2_submission.py`、`reports/SUBMISSION_READINESS.md` | PASS |
| 官方/等价 baseline 已生成并可提交 | `submissions/scored/baseline-001/`、`submissions/INDEX.tsv` | PASS |
| 本地 scorer / pseudo-holdout 至少可用于基本筛选 | `reports/T2_CONTROLS_AUDIT.md`、`outputs/t2_controls/` | PASS（筛选用途） |
| 首次服务器评分已取得 | `reports/FIRST_CYCLE_REPORT.md`、`reports/SERVER_SCORE_REGISTRY.md`；Total `145.9` | PASS |
| 外部来源和辅助数据边界已登记 | `docs/starter_pack/compliance/external_sources.tsv`、`data/external/INDEX.tsv` | PASS |

## 原 Gate 的关闭解释

原 starter_pack 把完整 research evidence ladder 当作 first-cycle 关闭条件。结合项目级约束和已经完成的首次 scored submission，本项目改为以下解释：

| 原 Gate | 竞赛基线关闭状态 | 后续科研扩展状态 | 影响 |
|---|---|---|---|
| Gate 0：官方同步 | CLOSED | 可随官网变化重新审计 | 不阻断提交 |
| Gate 1：统一 validator | CLOSED_FOR_SUBMISSION_PATH | 完整通用 validator 测试仍开放 | 每次候选仍必须通过 board-aware contract |
| Gate 2：baseline 与独立复现 | CLOSED_FOR_COMPETITION | T1/T3 更完整的独立复现仍可补 | 首轮提交已经发生 |
| Gate 3：pseudo-holdout | CLOSED_FOR_BASIC_SCREENING | target-blind、重复实验和稳定性上限仍开放 | local proxy 不得冒充服务器预测 |
| Gate 4：对抗性 controls | CLOSED_FOR_CURRENT_T2_AUDIT | 全套 C1–C5 和 hidden-target 证据仍开放 | 只用于风险审计，不是提交门槛 |
| Gate 5：T2-B1/B2 多 seed 改进 | NOT_REQUIRED_FOR_CLOSURE | OPEN_FOR_RESEARCH_EXTENSION | 不得阻断高分候选生成 |

因此，原文中的严格 Gate、3-seed 结论、完整 T1/T3 独立复现和科学 promotion 要求保留为研究扩展清单，不再被解释为“starter_pack 尚未关闭”。

## 尚未完成但不阻断竞赛的事项

- 完整覆盖 T1/T2/T3 的统一 validator 回归测试；当前提交脚本的 board-aware 检查可用。
- T1 pseudobulk baseline 和 T3 shift-transfer 的逐项独立复现报告。
- 完整 C1–C5 controls、target-blind 内部验证和 B1/B2 多 seed 研究。
- 首次提交的服务器 submission ID 和原始回执仍待用户补录。
- 仓库尚无 initial Git commit；现有 registry 中的 `git_commit=UNCOMMITTED` 是可追溯性缺口，不改变已取得的服务器分数。

这些事项应在后续任务 agent 的 handoff 中按需推进，不得把它们重新包装成首轮竞赛启动阻塞点。

## 后续执行规则

后续候选只需满足：官方 board contract、格式/数值/空间字段检查、外部来源边界、候选哈希和提交登记。服务器返回分数后再更新 `reports/SERVER_SCORE_REGISTRY.md`，并提醒用户提供 submission ID 或原始证据。

