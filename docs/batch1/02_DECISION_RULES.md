# 第一批结果决策规则

## 通用

- **SUBMIT**：主指标按预期改善，受保护指标没有无法解释的实质回退，文件契约通过。
- **HOLD**：主指标有改善但被其他重要指标抵消，或结果依赖弱先验；保留为后续 ensemble 成员。
- **REJECT**：预定主指标没有改善，或违反了原子隔离假设；不因总分偶然上升而保留。

## B1-A1：双 lane 决策

B1-A1 覆盖三个独立 board，每个 board 固定有两个最终候选：

- `L1_FORMAL_LOG_RMS`：严格按观测阶段的 `log(RMS)` 分段插值或末段外推；
- `L2_ALL_STAGE_LOG_RMS_OLS`：对该组织全部训练阶段的 `log(RMS)` 做等权 OLS 趋势外推。

两条 lane 都必须完成 contract、局部不变量检查和人工服务器评分。局部 proxy 较差不构成取消第二 lane 的理由；只有硬性 contract/invariant 失败才可阻止上传。

最多 4 次全局临时 source-only 尝试仅用于诊断，每次覆盖三个 board，不得成为第三条最终 lane，也不得使用 hidden target、排行榜反馈或服务器分数调参。

主要看原始 scorer key `scale_log_ratio` 的 `abs`（报告别名 `TSR`）；不得手工构造 composite score。
uniform scaling 后 `SDD/ODS/NFS` 理应基本不变；若明显改变，优先视为实现错误，而不是生物现象。

服务器分数回填后按 board 独立比较 L1 与 L2：`L1_BETTER`、`L2_BETTER`、`TIE/NO_PROMOTION` 或 `INVALID`。一条 board 的结果不得覆盖另一条 board。

六个 artifact 均必须使用相同 scorer 版本和固定 score input；服务器 ID 和用户回填分数只写入 `reports/SERVER_SCORE_REGISTRY.md`，不额外要求截图、链接或 JSON 原始证据。分数未回填前状态为 `score_pending`，不得宣称改善。

## B1-A2

- 先看 DES/DCS，再看 PSS；Mab21l2 self-check 只用于诊断方向规则，不是服务器结果。
- 只要两条 lane 都通过 contract 和硬性 invariant，两条都必须交给用户人工上传并分别获得服务器分数；弱 prior 或 self-check 偏弱不能取消第二条最终候选。
- 服务器分数回填前，两条均保持 `score_pending`，不得宣称 leaderboard 改善；回填后按 `L1_BETTER`、`L2_BETTER`、`TIE/NO_PROMOTION` 或 `INVALID` 比较。
- MMD/CSS 若明显坏于 wt_identity，记录为风险并为未来批次提供 shrinkage 方向，不在本原子现场调参或追加第三条 lane。

## B1-A3

- 主要看 MMD/CSS；DES/DCS 是次要观察。
- 若状态比例变化改善 MMD 但 CSS 明显恶化，说明 residual 处理失败，应 REJECT。
- 若 MMD 改善但总分小幅下降，可 HOLD 作为群体模块或 ensemble 成员。

## B1-A4

- 两条 lane × 三个 board 都必须完成 contract、排列不变量和一次固定 public scorer；不得因 local proxy 较差取消第二条 lane。
- 主要看 NFS 是否改善；其他全量表达统计和 geometry 应保持不变。
- 当前 scorer 的 `mmd_u`、energy、variogram 会按行索引抽样；行置换后同一 seed 的轻微 raw 波动不单独判为失败。表达 permutation、所有表达层/`raw`/`obs` 的同步重排、坐标 hash 和 15-NN hash 才是硬不变量。
- 若 MMD/CSS 或 geometry 的结构性结果改变，说明并非纯行置换或 scorer 输入发生错误；local NFS 不改善时仍保留并提交两条 contract-valid 候选，按 `HOLD/REJECT` 记录科学结果。

## B1-C1

- 只接受近似“继承 A1 的 TSR + 继承 A4 的 NFS”的结果。
- 不允许为了组合分数再次训练或改参数。
- 若 A4 直接父本已经是当前 per-board 选定的 A1 scale（本轮 embryo/heart interpolation）或 identity scale（heart extrapolation），不得再次应用 scale；该 board 记为 `NOT_NEEDED_PRECOMPOSED`，不生成重复候选。
