# Virtual Embryo Challenge — 第一批原子优化施工包

版本：2026-08-27

> 归档提示：Batch 1 已于 2026-08-29 关闭为 `CLOSED_FOR_REVIEW`。以下内容保留原始施工方案；当前无 active atom，重新激活任何 atom 都需要明确授权。综合结果见 `reports/PHASE_REPORT_BATCH1_20260829.md`。

## 一句话目标

只施工 4 个高价值原子/组合原子，并把 T2 的两个互补结果合成一次；每次施工都必须以通过官方文件契约、可立即提交测试的结果结束。每个已激活原子都固定产出 1+1 个最终 lane，B1-A4 覆盖三个 T2 board。

## 第一批顺序

| 顺序 | ID | 任务 | 优化对象 | 直接对应评分 | 结果 |
|---|---|---|---|---|---|
| 1 | B1-A1 | T2 | G1 组织尺度 | TSR；约占 T2 总分 8.33% | 2 条 lane × 3 个 T2 board，共 6 个最终候选，均人工提交并评分 |
| 2 | B1-A2 | T3 | C1 响应程序中的 E1+E2，并用 K2 保护 WT 背景 | DES 30% + DCS 25% | 2 条 signed sparse residual lane，共 2 个最终候选 |
| 3 | B1-A3 | T1 | P2 状态质量 + C7 均值-残差一致性 | 主要瞄准 MMD 30% 与 CSS 20% | mass-reweighted, covariance-preserving submission |
| 4 | B1-A4 | T2 | J1 表达-坐标局部生态位联合 | NFS 25% | 2 条 lane × 3 个 board，共 6 个 expression-coordinate re-paired candidates |
| 5 | B1-C1 | T2 | A1+A4 的无冲突组合 | TSR + NFS，合计直接覆盖约 33.33% | 仅在 A4 未继承选定 scale 时激活 |

## 为什么先做这批

1. **A1 与 A4 可近似正交。** 均匀缩放坐标改变 TSR，但不改变 15-NN 图；只重排表达与坐标的配对改变 NFS，但不改变表达边缘或点云边缘。因此二者可以独立施工，再直接组合。
2. **A2 瞄准 T3 最重要的缺口。** T3 的 55% 分数直接来自响应基因集合和方向；官方 floor 已经保护绝对表达，因此第一步应是小而有符号的 residual，而不是自由生成 KO。
3. **A3 购买三个任务都反复需要的能力。** 状态比例、状态内异质性和共变是 MMD/CSS 的核心，也是复杂模型最容易破坏的部分。第一版只在 T1 落地，以便形成单一、可评分的提交。
4. **暂不做高风险路线。** open-set 新生状态、G2/G3 全形态生成、T3 严重度专门校准、conditional flow、branch flow 和外部大规模先验放到下一批；它们依赖本批结果或需要更高不确定性的外部信息。

## 使用方法

1. 将整个目录放到现有项目中，例如 `docs/atomic_batch1/`。
2. 先把 `01_CODEX_CONTROLLER_PROMPT.md` 交给 Codex。
3. 第一次只激活 `config/active_atom.yaml` 中的 `B1-A1`。
4. 每完成一个原子，Codex 必须停止并交付结果集、各候选 `MANIFEST.json` 和提交文件；B1-A1/B1-A4 必须先冻结两条 lane 的 6 个候选，再等待人工上传和分数回填。人工决定是否进入下一个原子。
5. 不要一次性让 Codex 连跑全部原子。用户偏好是单步原子施工、完成后验收。

## 强制输出目录

```text
artifacts/atomic_batch1/<ATOM_ID>/
├── final/
│   ├── L1_FORMAL_LOG_RMS/<board>/prediction.h5ad
│   └── L2_ALL_STAGE_LOG_RMS_OLS/<board>/prediction.h5ad
├── exploration/
│   └── attempt-<nnn>/<board>/
├── metrics/
│   └── <lane>/<board>/
├── config_resolved.yaml
├── FINAL_SET_MANIFEST.json
├── RESULT.md
└── run.log
```

## 施工预算

每个原子默认只允许：

- 1 次小规模功能检查；
- 1 次完整候选生成；
- 1 次官方本地 scorer 或现有官方验证流程；
- 1 个固定随机种子；
- 0 次网格搜索；
- 0 次大范围重构；
- 0 次自动 leaderboard 提交。

若现有工作台已经有更简洁的验证入口，直接复用，不新建第二套框架。

## 双 lane 原子：探索与最终候选

- 最终 lane 固定为 `L1_FORMAL_LOG_RMS` 和 `L2_ALL_STAGE_LOG_RMS_OLS`；每条 lane 必须覆盖 embryo interp、heart interp、heart extrap 三个 board。
- 两条 lane 均属于最终候选，均需通过 contract、人工上传并获得服务器分数；本地 proxy 较差不能静默取消第二条 lane。
- 允许全局最多 4 次 source-only 临时尝试；一次尝试必须完整覆盖三个 board，只用于诊断，不进入 `submissions/INDEX.tsv`，不消耗线上评分配额。
- 临时尝试不得读取 hidden target、排行榜反馈或用于事后调节两条最终公式；最终终点始终是恰好 6 个候选。

## B1-A4

- 最终 lane 固定为 `L1_LATENT_KNN10` 和 `L2_STATE_HASH10`；每条 lane 必须覆盖三个 T2 board，共 6 个最终候选。
- 当前 per-board best 是 immediate parent；A4 同时记录 pre-A1 root，仅用于 B1-C1 重放，不重新应用已继承的 scale。
