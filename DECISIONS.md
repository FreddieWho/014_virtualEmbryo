# DECISIONS — 项目级决策入口

**权威详细存档：[`docs/coordination/DECISIONS.md`](docs/coordination/DECISIONS.md)**（只追加事件日志，含全部 evidence/boundary/next_action）。
本文件按 `~/AGENTS.md` 规范收录影响后续路线的选择摘要：选择、当时理由、复查触发条件。只追加，不覆盖。同一决策不双写——全文以 coordination 存档为准，此处只留索引式摘要。

## 已登记决策摘要

- **D-20260829-005｜batch1 收尾冻结**：4 atom 16 候选全部评分，B1-A1 局部有效，B1-C1 按条件不执行。理由：边际收益递减，转 batch2/3。复查：新数据或新假设出现时。
- **D-20260902-T3-S1C-001｜T3-S1 链收口**：UNSATISFIABLE_UNDER_FIREWALL，gate 结构性不可达。理由：matched 证据公开不可得 + leakage firewall。复查：官方新数据/organizer 书面许可。
- **D-20260903-T2-S3-001｜heart_interp 56.7 晋级**：位移场几何方向首个服务器验证的改善。复查：服务器聚合复核。
- **D-20260903-NAME-001｜上传命名规则固化**：成员名 ≤50 字符短码规则，防止长名不可读。复查：portal 约束变更时。
- **D-20260904-T2-J1-001｜heart_interp 57.3 晋级、embryo HOLD**：FGW 配对方向服务器验证 +0.6；embryo 本地证据不足不消耗提交。复查：embryo 补同靶 parent 参照后（LEADS L-001）。
- **D-20260904-HX-001｜增长/死亡动力学方向关闭**：kill test 预声明阈值未达成（0.7475 vs 0.6645）。复查：独立证据表明 T1 残差由 mass 漂移主导时。
- **D-20260904-T3-001｜T3 并列新 board best 45.5**：B2-T3-A1 v0006/v0007 双双 +0.2，首次超过 wt_identity；服务器无法区分 lane。复查：服务器聚合复核；科学 gate 不受影响。
- **D-20260904-B4P0-001｜Batch 4 启动与 P0 完成**：human team 启动 B4，P0 基线就绪。复查：P0 分数回填时。
- **D-20260904-B4P0-002｜exact-floor 探针 T1 47.0/T3 46.8**：floor parity 正式 UNRESOLVED。复查：新 floor 证据出现时。
- **D-20260904-B4P0-003｜T1 floor 探针 n_obs 假设排除**：n=1,706 得 46.8，规模解释不成立。复查：同上。
- **D-20260904-TOTAL-001｜服务器确认 Total 151.2**：子项分数入库并立 per-metric 登记规。复查：新评分回填时。
- **D-20260904-B4T2R1-001｜T2-R1 双 lane 打平关闭**：57.3/57.31 均与 v0009 打平，FGW 离散化微调关闭。复查：新配对证据出现时。
- **D-20260905-WAVE1-001｜Wave 1 评分**：T3 双 lane 46.95 新 best（打平），T1 四 lane 未晋级。复查：聚合复核。
- **D-20260911-B4T1R2-001｜T1-R2 数据门控 BLOCKED**：数据未就绪即停，不烧提交。复查：数据就绪后。
- **D-20260914-WAVE2-001｜Wave 2 评分**：T2-R2 三晋级（含 heart +4.79），T3-R2 双败触发架构重置。复查：重置后新 lane。
- **D-20260915-B4CLOSE-001｜Batch 4 关账**：Total 153.7 服务器确认；ARCHITECTURE_RESET_REQUIRED。复查：G0 新架构结果。
- **D-20260916-G0T3-001｜G0 T3 五 lane 无晋级**：两持平三负，传播-剂量族关闭。复查：30 轮新 lane。
- **D-20260916-G0T2-001｜G0 T2-extrap 一晋级**：v0011 收缩 +0.11；空间族关闭。复查：同上。
- **D-20260917-G0T1-001｜G0 T1 七 lane 无晋级**：v0004 留任；收缩族 C1 最优但落 TIE 带。复查：P2 新架构。
- **D-20260917-G0T3R9R13-001｜R9–R13 评分**：一持平（v0023 46.95）＋一灾难（v0025 43.30），selection 不变，空间族关闭。复查：R6–R8 分数回填时。
- **D-20260917-T1P02-001｜T1 P0-2 仲裁**：D4→D2→D3→D1→D6/D5→D7，廉价数据优先。复查：节点完成或路径调整。
- **D-20260917-T1D7-001/002｜D7 关闭**：E7.75 官方未发布（not released），PARKED 转 CLOSED。复查：官方发布 E7.75 后。
- **D-20260917-T1P23-001｜D2 调参挂起＋D3 开工**：用户特批挂起（破例非先例），门阈值不变。复查：D3/D1 双败触发条件已满足，用户定夺。
- **D-20260917-T1D3-001｜D3 门 FAIL 关闭**：panel 成功未传导全基因。复查：新流模型证据。
- **D-20260917-T1GPU-001｜V100 沿用获批**：OPT-A(c) 去 E7.75 锚点。复查：完工即关机（已执行）。
- **D-20260917-T1D1-001｜D1 门 FAIL 关闭**：VAE+SDE 塌向均值（var 0.086）。复查：重加权属新 lane。
- **D-20260917-T1GPU-002｜D5/D6 全开＋费用纪律**：完工即关机，单 lane 4h 上限。复查：已执行关机。
- **D-20260917-T1D5-001｜D5 门 FAIL 关闭**：回报分布崩 8×；JSD 腿空转设计债（后被审计升级为测试无效）。复查：D5b。
- **D-20260917-T1UPLOAD-001｜上传仲裁政策**：本地门降格为上传筛选器；v0022 首战 REJECT 即证伪流程有效。复查：持续适用。
- **D-20260917-T1D3-002｜v0022 服务器 45.3 REJECT**：proxy 误报首例，教训修正为需分布侧会签。复查：持续适用。
- **D-20260917-T1D4-001｜D4 门 FAIL 关闭**：组成锚定无回报信号（第四次确认组成是雷区）。复查：新组成机制证据。
- **D-20260917-T1D2-000/001｜D2 首跑 VOID**：step-41 发散按 intent 不判晋级；warmup 后重跑。复查：dz20 结果（已出：门 FAIL，调参挂起）。
- **D-20260917-T1D6-001｜D6 门 FAIL 关闭＋GPU 关机**：de 恰等门线不算过；实例已 halt。复查：D2 调参或新架构。
- **D-20260917-T1AUDIT-001｜独立复核**：D5 测试无效（死条件＋不可满足门），其余 verdict 确认；D2 重名去雷。复查：D5b 结果。
- **D-20260917-T1D5B-001/002｜D5b 立项＋门 FAIL 关闭**：审计修复后暴露严重欠拟合（27×）；CPU 零花费；D5c 长训属新假设待立项。复查：用户定 D5c/D2/封存。

## 最近一条

D-20260917-T1D5B-002（2026-09-17）：D5b 27× 落败关闭；T1-P2 七死一悬（D2 调参＋D5c 待定夺）；GPU 保持关机。

- **D-20260920-G0T3R6R8-001｜T3 R6–R8 评分闭环**：两 TIE、一 REJECT，原 selection 留任；统包八候选全部已评分，后续轮次待决定。详见 docs/coordination/DECISIONS.md。

- **D-20260920-T3NEXT-001｜T3 六路线实现收口**：四候选待上传，R3/R4 门槛失败，R5/R6 输入阻塞；修复 R2 对照并作废未提交旧对，selection 不变。见 docs/coordination/DECISIONS.md。

- **D-20260920-T3DATA-001｜T3 R5/R6 数据收集**：GSE261783 静息组隔离过滤 5,454 细胞/26 候选扰动，R5 资料与引用落盘；全为 model_input=false。R3/R4 修复加入 TODO。见 docs/coordination/DECISIONS.md。

- D-20260920-T3R56PREP-001：T3 R5/R6第二轮隔离准备、signed/shape用途门和确认草稿；真实训练仍未获准。详见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260920-T3R5SOURCE-001：R5最小SIGNOR来源闭环并生成v0032/v0033（未提交/未评分）；订正R6官方与内部规则归因。详见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260920-T3NEXTSCORE-001：T3 R1/R2四组回分已登记，best不变；内部额外约束评审建议修改但尚未生效。详见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260921-T3POLICY-LAUNCH-001：内部规则修改生效，R6来源重审及三件套准备完成（训练NOT_RUN），R5保留现有两候选待评分。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260921-T3R6RUN-001：R6实际训练及推断完成，留出通过但两个输出负值门槛失败，0候选，后继非负修复待办。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260921-T3R5SCORE-001：R5 v0032/v0033回分登记，均与父版本总分相同，on/off全部回报指标一致，不晋级。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260921-T3REVIEW-001：T3全路线复核，补充R6零值/平均响应及R5差分证据，整合四项后继建议；未执行新分支，selection不变。见 [协调决策](docs/coordination/DECISIONS.md)。
