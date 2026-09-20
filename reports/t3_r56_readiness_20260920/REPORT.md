# T3 路线 5/6 开工准备（2026-09-20）

状态：PREPARATION_PARTIAL_QUARANTINE；尚不能宣称两路线已具备真实训练资格。无候选、未提交、未评分。科学阻塞 blocks_submission: false，不影响其他已合规路线。

## 本次完成

- 对原始隔离数据完成第二轮即时过滤：5454 → 4998 个细胞；移除 Chd4/Smarca4/Yy1 共456个细胞，剩23个扰动和220个明确NTC。全500基因唯一Ensembl映射已生成，保留全部32287基因原始计数。旧文件未覆盖。
- 过滤前落盘逐细胞计划，过滤后检查结构、排除条件及输入输出SHA256。详见 PREPARATION_RECEIPT.json、R6_CELL_FILTER_PLAN.tsv、R6_PANEL_MAPPING.tsv。
- Chd4: https://pmc.ncbi.nlm.nih.gov/articles/PMC9067406/；Smarca4: https://pmc.ncbi.nlm.nih.gov/articles/PMC3096875/；Yy1: https://pmc.ncbi.nlm.nih.gov/articles/PMC6048588/。三项属于基于原始研究的保守风险排除，不声称与目标完全同表型。这些论文仅用于排除审查，不进入训练或提供目标响应方向。
- R6_CONDITION_REVIEW.tsv覆盖全部26个扰动及对照的当前处置。其余23项为 HOLD_FULL_CONTEXT_REVIEW，不是已通过审查。没有把查不到证据等同于安全。
- 原R6学习有符号响应，与当前shape-only许可边界不相容。新增用途门，在打开外部矩阵前检查任务、来源、用途、人工核对的书面确认及原始确认文件哈希。普通APPROVED_SANITIZED标签不再足以放行原R6。此门不鉴定信件真伪，须由人工核对来源；禁止自行把草稿改成批准。
- 新增形状目标转换函数及独立符号/幅度不变性测试；这是后继设计的基础组件，尚未集成完整训练、推理流程。4项针对性测试通过，包括原R6在矩阵读取前拒绝shape-only许可。

## 路线五：仍缺什么

已下载的37条panel内LR记录未提供完整可用target链，批准完整链仍为0；不能把受体当靶基因，也不能把TF活性当作TF表达改变。逐行缺口在 R5_EDGE_ADMISSION.tsv。ConnectomeDB的软件MIT与数据库条款不同；CellPhoneDB的软件许可亦不能代替数据许可。保持原隔离许可。

下一批优先审查SIGNOR的逐边原始文献及Reactome事件，二者分别公开CC-BY4.0和CC0数据条款，但本次未下载它们的网络，也未批准任何边。许可较明确不等于不存在target/phenocopy污染。每条链必须核对物种/实验背景/受体特异性、排除受保护证据、覆盖panel并提供可追溯引用。完成后才可执行现有WT拟合、signal-on/off及sender permutation。

## 路线六：仍缺什么

1. 23个剩余扰动逐项完成背景审查并获得来源用途确认，重新过滤后仍需≥20个扰动且每个≥20细胞，不能降低原门槛。
2. 采用 R6_SHAPE_DESIGN.md 的显式新分支；现有有符号R6不可直接运行。完整shape训练与推理集成仍NOT_RUN/NOT_IMPLEMENTED。
3. 获批后才能标准化、建立不含响应信息的图和embedding，并生成新任务许可及hash绑定manifest。当前只有raw隔离矩阵，尚无可用expression/embedding/adjacency训练三件套。
4. 单基因完整留出；比较无改变、ridge和GCN。来源holdout通过亦不证明成人成纤维细胞向E8.75胚胎迁移有效。

## 外部确认边界

本地控制文档 docs/batch2/03_COMPLIANCE_RULES_SNAPSHOT_20260829.md:84-88 明确要求书面确认通用Perturb-seq严格blacklist后的使用、聚合网络target-specific边来源边界和外部measured data范围。ORGANIZER_QUERY_DRAFT.md已写好，状态NOT_SENT；未代用户联系主办方。没有书面确认时保留隔离，不能以用户允许准备工作代替比赛方批准。
