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

- D-20260921-T3REPAIR-001：T3首批修复完成，六候选待评分；R6图优势未成立，R3/R4 WT评估通过；R4旧未提交对撤回并以校准一致的v2替换。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260921-T1NEXT-001：T1六路线方案准备完成，全部未执行；订正D5b旧滞后状态，selection不变。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2LEADS-001：T2 两条未完成线索（L-001/L-002）执行收口；embryo v0008 确证拒绝、FGW ε 轴耗尽，T2 无未跑已规划路线；零候选零评分。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260926-T1V23SCORE-001：T1-v0023 服务器 50.82（+2.35）晋级新 best，Total 156.06；R1 SHIPPED，R2 诊断关闭，R6 PARKED。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T3FIVE-001：T3 三新+两优化全量完成，五候选未提交/未评分，两个首跑撤回；contract/重放/11测试通过，best不变。见 [统一报告](reports/t3_five_20260927/REPORT.md)、[协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2M0FREEZE-001：T2 九路线 M0 冻结——父版本 SHA 实核、5% 三分类判据（主指标 neighborhood_mmd，结构性失败一票否决、边界从宽）、disp% 必报、设计先于训练、替补上限每 board 1 条、5 条已耗尽轴不得重提；extrap 迭代父用 v0011(50.64) 但不动 selection，0.11 差异 OPEN。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2UNATTENDED-001：无人值守窗口决策边界——模糊选择由 coordinator 自行决定并记名待追认；改动已评分 artifact／目标泄漏／放宽 contract／伪造分数／复活已关闭路线仍然硬停；「失败不消耗预算」= 淘汰不占名额，替补上限后转入新路线轮，每 board 累计超 5 条 lane 即停等用户。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2GATES-001：M1 闸门判决——官方 `variogram` 经三臂对照确认为**坐标无关的基因间协方差**（行置换不可分辨、基因置乱 4.35×），`morans_I_agreement` 为 CONSTRAINT 非分数，几何冻结使四个纯坐标子分恒定；探针 C 实测现役表达桥把协方差**弄坏**（embryo 2.49×、heart 1.44× 于基线），噪声标定 `neighborhood_mmd` 零噪声而 `variogram` 4.18%。据此把三条空间变异函数路线降级为备选，腾出槽位给新增 GJC 族（**无文献先例的自研方向，用户可整族撤销**）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2LEADS-003：L-002 atom B 程序性修复＋机制更正——复现门由绝对 1e-9 改为**跑前声明**的相对 1e-4 并通过；atom B **非独立复现**（与 v1 数字逐位相同）；新诊断测得两 ε 臂落点仅 46% 重合，故"落到相同行"被否证，正确机制是**冻结 FGW 目标面在 ε 方向近退化**（两解不同但 objective 分不出高下），据此判定「把同一目标解得更好」这条轴在 T2 为死路。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2M0APPX-001：T2 九路线 M0 §7 关闭依据的证据更新（**追加附录 A，不回改 §7**）——FGW ε 轴真实理由为**目标面近退化**（落点差 54% 而 objective 仅差 2.4e-03/4.6e-03），后果扩展为「把同一目标解得更好」在 T2 均无望；embryo 配对轴补「只换参考可能不够，须同时换目标」的前置约束。已核对 9 条 lane 均不触碰该约束。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2PROBED-001：T2 探针 D（只读）——表达桥的基因间协方差损失**归因于 mean bridge 本身**而非 mass 臂（embryo 父→L1 已 2.440×；L2 vs L1 差在 4.2% 噪声内不可分辨），并**部分推翻探针 C 的「免费拿回」建议**（破坏最重的两臂恰是服务器 board best）；另发现 `mmd_u` 在 B4-T2-R2 族**与服务器反向**，构成第三个本地门失效族，对 M0 §3.2 会签规则有影响（建议追加新决策，未回改 M0）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T3SCORE-001：T3 八分回填，v0048 47.93（+0.98）晋级新 best，Total 157.04；FIVE＋R6 转 SHIPPED，R3 部分回填。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2VALIDATE-001：T2 验证 V1（只读，31 条已评分候选）——**本地判据逐板方向不同**：`neighborhood_mmd` 在 heart_interp（−0.559）与 extrap（−0.627）有预测力，但在 **embryo 强反向（+0.833）**，M0 的 5% 规则把板最佳 v0010（62.29）判成 DEGRADE；另发现 embryo 板「表达字节相同、仅坐标 ×1.305 膨胀、服务器 +3.4 分而本地七项指标全零」的输入对，证明**服务器几何子分对绝对尺度敏感而本地镜像看不见**；`d2_shape` 在两个插值板均反向。原设计的「方向一致率」统计量无效已作废。M0 需追加决策（未回改）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T1FIVE-001：T1三新+两优化全量完成，v0024–v0028待服务器仲裁；五contract/模型重放与9测试通过，best v0023不变。见 [报告](reports/t1_five_20260927/REPORT.md) 与 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2M0APPXB-001：T2 M0 附录 B（追加，未回改 §3/§4）——**逐板校准主指标**：`neighborhood_mmd`+5% 在 heart_interp/extrap 维持，**embryo 停用 5% 三分类**（Spearman +0.833 反向，M0 规则把板最佳 v0010 判成 DEGRADE），该板改服务器仲裁优先、本地只记录不否决；`mmd_u` 会签在 embryo 零信号且族内成对反向；**`d2_shape` 不得单独作失败签名**（两插值板均反向）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2M1VERDICT-001：T2 九路线 M1 逐条裁决（追加，不回改 §1/§2）——**执行** `E-N1 SBL`（前提未证伪、锚点须标自拟）、`E-I1 TCI`、`H-N2 A2C`；**条件执行** `X-N2`（须重定义占据度）；**待澄清** `X-I1`；**保留为验证实验但本轮不执行** `E-N2`+`H-I1`（其原始目的已被 V1 在 31 条候选上完成，且两者被预测量均已证伪）；**否决** `H-N1`、`X-N1`。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2EN1-002：T2 `E-N1 SBL` **执行失败、路线立即关闭**（预声明否定判据触发）——两臂 `neighborhood_mmd` 0.396/0.325 对基线 0.031，差 10–13 倍。根因：**全局水平与场项之间无幅度控制**，回归在 z-score 化表达上做导致场项带标准差量级动态范围，把总质量抬高 53%+，分布整体推高。两项自我订正（`log1p(expm1)` 恒等而非 softplus，我的首次诊断因此有误；设计 τ=0.5 与目标 stage E7.5 算术不一致，正确为 0.6）均非结果导向调参。复活须作新 lane 预声明幅度控制。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2EXTRAPAGG-001：T2 heart_extrap 的 0.11 聚合差异**定案**——服务器 Total 按**已登记的 per-board 选集**聚合，不是每板历史最高之和。决定性证据是第二个 Total **157.04**（09-27，距 v0011 评分已 11 天）T2 仍为 58.29 ⇒ extrap=50.53，据此排除舍入／最新提交／自动取最高三种解释。`registry` 中「selection updates to v0011」不成立（已订正、不追溯改写）；**`INDEX.tsv` 无需改**，此前判为矛盾是误读。剩余两项待用户：换选集、TIE 边界口径裁决。（初稿所称「v0011 子项未回填」经实测**不成立、已撤回**：该板 v0011 有完整 8 行；真正缺子项的是 32 条 2026-09-04 规则固化**之前**的历史候选。）见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2DESIGN-001：T2 `E-I1 TCI` 与 `H-N2 A2C` 设计冻结落盘（训练前）。**训练前 bracket 核对抓出一处会导致 target 泄漏的设计错误**——检索简报写「E8.5/E8.75 中点」，而 `BOARD_REGISTRY.yaml`、`t2_s3_shape_field.py`、`t2_j1_pairing.py` 三处一致显示 bracket 为 **[E8.25, E8.75]**、目标为 E8.5，原设计会拿目标 stage 当源阶段；已修正并新增泄漏断言。`E-I1` 所在 embryo 板 5% 规则已停用（只记录不否决），`H-N2` 所在 heart_interp 维持 5%（三档判定）。**待用户裁决**：`PLAN.md` 写「heart 插值 E9.0」与三处权威来源的 E8.5 冲突。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T1FIVESCORE-001：T1 五分回填，v0024 51.92（+1.10）晋级新 best，Total 158.14；v0026/v0028 低于父版本。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2CITE-002：T2 第二批承重引用核验（原文级，arXiv + Europe PMC `resultType=core`）——`E-I1` 的 **CPD 核心锚点成立**（概率软对应 + EM + 非刚性位移场均在原文），但「正反一致性自诊断」子主张**不成立**、已改标为本项目自定；`H-N2` 的 Aviñó-Esteban 2025 *Development* 152(4):dev204313 **核心思想成立但锚点降级**——该文是 **limb/2D/ISH**，与本路线 heart/3D/MERFISH **三项均不匹配**，不得声称其支撑 3D 心脏构造。累计 5 条已核验（3 撑不住 / 1 部分不成立 / 1 核心成立）。两条路线均不阻塞执行。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T3R2-001：T3三新+两优化完整交付，含高分v0048+v0046叠加，v0049–v0053未评分；13测试及五模型独立重放PASS，科学不确定，best不变。见 [报告](reports/t3_round2_20260928/REPORT.md)、[协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2ROUTES-EXEC-001：T2 `E-I1 TCI` 与 `H-N2 A2C` 均已执行并**失败，裁决不提交、本轮不产生上传包**（几何/行序/组成重采样逐字节复现现役版本,恶化全在表达项；相对现役分别劣化 +78~97% 与 +2379~2568%,四个分布侧指标同向变差）。**三次尝试收敛到同一失败模式**：给已被服务器验证的低空间方差均值场叠加"学出来的空间对比度"会摧毁分布,且劣化幅度与对比度幅度同向；`SBL` 事前把定标改成层内 sd **也没用**——sd=1 这个定标本身是病灶。**T2 九路线的共同前提已被三重独立证据否定**,新增 LEADS **L-008** 作为前置问题（对比度幅度须由数据决定）,未执行。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260927-T2L008-001：T2 **L-008 前置探针**——幅度是唯一被扫的变量。损伤随幅度单调递增，**两板可接受带均只到 `a ≤ 0.05`**（首个出带 `a = 0.10`），而**真值自身空间对比度幅度为 1.20 / 1.55，比上限大 24–31 倍** ⇒ **「均值场 + 加性空间对比度」机制族关闭**，L-008 改判已放弃。**定量交叉验证**：曲线在 `a = 1.0` 的 heart 劣化 +79.9%，与 `H-N2 A2C`（`ALPHA = 1.0`）实测 +77.8~96.9% 几乎重合 ⇒ 前三次失败**幅度驱动而非内容驱动**。T2 搜索空间收窄到**唯一方向：作用在边际分布上的机制**（与 +4.79 组成重采样、+0.11 收缩两个服务器正例一致）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T1R2-001：T1三新两优化完整执行，v0029–v0033未提交/未评分；含v0024+v0027实际组合，优先v0030本地信号，best不变。详见 docs/coordination/DECISIONS.md 与 reports/t1_round2_20260928/REPORT.md。

- D-20260927-T2MARGINAL-001：T2 **边际分布响应面探针**（只读）——现役版本在 `composition-intensity` 与 `shrinkage` **两条阶梯上均为局部最优**：从现役单调向外，服务器已确认有效的子分全部变差（heart `de_score` −32%、`de_direction` −17%、`neighborhood_mmd` +55%、`mmd_u` +55%），而唯一变好的 `occupancy_dice`/`d2_shape` 恰是**已证实与服务器反向**的那两个。**`B4-T2-R2` 的 +4.79 是「回到现役」而非「继续往前」，该方向已走完一次。** 附带机制事实：**收缩对 DE 类指标完全无感**（`de_score`/`de_direction` 恒定），因收缩只改型内幅度、每型均值不变 ⇒ 想不动 DE 而改分布必须改**每型均值**。另：`de_score` 在 embryo pseudo-target 上恒 `UNDEF`，该板本地不可用作筛选判据。LEADS 新增 **L-009** 记录唯一剩余入口，**不授权任何新 lane**。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T3REPAIR2-001：T3修复剩余三 lane 回分，v0037 46.98（TIE 父版本）、v0040 47.08、v0041 47.09（均低于现 best 47.93，不晋级）；修复队列分数关闭。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T1R2SCORE-001：T1第二轮五 lane 回分，v0029 52.5（+0.58）晋级新 best，Total 158.72；v0030 52.49 距新 best -0.01 不并列晋级；v0031/v0032/v0033 不晋级。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T2LOWAMP-001：T2 **低幅度可提交包已产出**（`deliveries/t2hn2lo__t2__upload__20260928.zip`，heart_interp v0014/v0015）——采纳用户「小幅劣化可试提交、可能存在反转」的判断：该判断有先例支持（`G1-T2-R2` 本地 NOT promoted 而服务器 +0.11 成板最佳；`neighborhood_mmd` 在 embryo 与服务器强反向 +0.833），但**幅度决定其是否可迁移**：`ALPHA=1.0` 的候选劣化 +78~97% 不属「小幅」，而 **L-008 预声明的独立幅度探针**给出 `a=0.05` 时损伤仅 +3.2~3.7%，故取 `ALPHA=0.05`（**幅度由独立测量决定，非从本路线结果倒推**）。结果：nmmd **+1.08% / +0.99%**、mmd_u **优于现役**、几何与行序 **byte-identity**、contract 全 PASS。**如实标注：这是探针候选不是提分候选**，预期持平或略降。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260928-T2LOWAMP-002：T2 低幅度两条**均已评分 61.52（现役 62.04，−0.52）→ 不晋级，selection 与 Total 不变**。子项分解极干净：`d2_shape`/`occupancy_dice`/`scale_log_ratio` **三项与现役逐位相同**（byte-identity 正面对照），损失全在表达侧且 **`variogram` −3.0 为最大单项**、`neighborhood_mmd` −1.3/−1.1。**两条结论**：① 用户「小幅劣化或可反转」的假设在此板此族**被实证否定**（本地 +1.0% → 服务器 −0.52，方向一致约 1:1）；② **L1/L2 完全并列、8 项中 6 项相同 ⇒ 跨阶段系数共享约束经验为 null**，H-N2 设第二臂的理由被证伪。`H-N2 A2C` 核心假设**由服务器证伪**（不再只是本地）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260929-T3THREE-001：T3三路线v0054–v0056实际执行并独立验收，交付3个短名h5ad与单ZIP；未提交/未评分，best不变。详见docs/coordination/DECISIONS.md及reports/t3_three_20260929/REPORT.md。

- D-20260929-T1THREE-001：T1三路线v0034–v0036完整执行并通过独立验收，单ZIP含三个h5ad；优先v0035本地信号，未提交/未评分，best保持。详见docs/coordination/DECISIONS.md及reports/t1_three_20260929/REPORT.md。

- D-20260929-T2ROUND2-001：T2三新两优化×三board共15候选（v0011–v0015/v0016–v0020/v0017–v0021）实际执行并通过全部本地检查，单ZIP含15个短名h5ad；未提交/未评分，三board best不变。详见docs/coordination/DECISIONS.md及reports/t2_round2_20260929/REPORT.md。

- D-20260929-T3FIVESELECT-001：T3五路线全量执行，事前开发规则选v0057–v0059三个h5ad入单包；另两条保留研究输出。6测试/14项独立进程验收通过，未提交/未评分。详见docs/coordination/DECISIONS.md及reports/t3_five_select_20260929/REPORT.md。

- D-20260929-T3R2SCORE-001：T3第二轮五 lane 回分，v0049 47.86（−0.07）平局不晋级，其余不晋级；selection v0048 不变。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260929-T1THREESCORE-001：T1三路线回分，v0035 53.43（+0.93）晋级新 best；v0036 平局备份；v0034 不晋级。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260929-T2R2SCORE-001：T2第二轮回分，胚胎 v0014 62.89（+0.60）与心脏插值 v0019 62.36（+0.32）双双晋级；外推不动；另记一次误投胚胎榜拒收。推导合计 159.95（待门户确认）。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260929-T3SCORE-002：T3最后六 lane 回分，v0058 47.95（+0.02）平局不晋级；v0056/v0059 精确打平；其余不晋级。selection v0048 不变，T3 队列关闭。见 [协调决策](docs/coordination/DECISIONS.md)。

- D-20260930-T1SEVEN-001：T1按3新/2失败优化/2成功优化完成七路线全量计算，七次完整panel评分与独立验收通过，候选v0037、v0038、v0039、v0040、v0042、v0041、v0043未提交/未评分；best保持。详见docs/coordination/DECISIONS.md及reports/t1_seven_20260930/REPORT.md。

- D-20260930-T1SCORE-001：T1十一条回分；v0038/v0043同为53.55（+0.12），按本批列表顺序v0038晋级、v0043备份；平均数平移四臂均失败，T1待分清零。详见docs/coordination/DECISIONS.md及reports/t1_score_review_20260930/REPORT.md。

- D-20260930-T2XN1SCORE-001：T2第二轮收尾，x_n1_lineage v0017回分48.17（-2.36），REJECT；外推选择不变，15/15回分完毕队列关闭。详见docs/coordination/DECISIONS.md及reports/SERVER_SCORE_REGISTRY.md#t2-xn1-score-return-20260930。

- D-20260930-T2R3SCORE-001：B4-T2-R3三条迟到回分；v0009 50.51（-0.02）判TIE但不及board-best，不晋级；v0008/v0010 REJECT；外推选择不变，closed_unscored结清。详见docs/coordination/DECISIONS.md及reports/SERVER_SCORE_REGISTRY.md#t2-r3-score-return-20260930。

- D-20260930-T3SIX-001：L-010 登记 T3 审计报告完整八方向计划；按用户授权执行六项优先路线，原工具/全推断/整扰动留出，不自动上传，旧评分产物只读。详见 docs/coordination/DECISIONS.md。

- D-20261001-T3SIX-002：T3六项核心实跑完成，v0060–v0065合为一包、contract PASS、未提交/未评分；状态质量零效应不登记；源侧神经网络未胜强基线，保留变体与跨域限制。详见docs/coordination/DECISIONS.md及reports/t3_priority_six_20260930/REPORT.md。

- D-20261001-T2GOAL-001：T2三board×两轮建成（R1新路线v0016/v0021/v0022 + R2旧优化v0017/v0022/v0023），6/6重放一致，合打一包t2goal__t2__upload__20261001.zip待上传回分。详见docs/coordination/DECISIONS.md及reports/t2_goal_20261001/REPORT.md。

- D-20261001-T3SIXSCORE-001：T3 v0060–v0065六件回分全部REJECT，现役不变/待分清零；复盘定位count/log评分空间与近零来源ratio风险，保留具体实现边界，不改已评分文件。详见docs/coordination/DECISIONS.md及reports/t3_score_review_20261001/REPORT.md。

- D-20261001-T2GOALSCORE-001：T2-GOAL六件回分，五REJECT + 外推x_r1 50.74记TIE最高数备份不晋级；三榜选择不变，待分清零，推导合计160.07不变。详见docs/coordination/DECISIONS.md及reports/SERVER_SCORE_REGISTRY.md#t2-goal-score-return-20261001。

- D-20261001-T1D2R3-001：D2 调参 R3 单轮启动（用户授权）：dz=20 冻结，max_checks 40→120 单参单轮，门不变（de>0.8868/dir>0.8895），过则建 v0048 不过则关 D2。详见 docs/coordination/DECISIONS.md。

- D-20261001-T1D2R3-002：D2-R3 1210 步足额仍挂门（de/dir 与 R2 逐位相同），按预声明关闭 D2，patience 轴判死路；v0048 不进 INDEX。详见 docs/coordination/DECISIONS.md。

- D-20261001-T3ARCH-001：T3剩余两次额度建议分给WT锚定条件残差flow与发育分支/相对群体份额模型；研究设计完成，两条NOT_RUN、未生成候选/未提交/未评分；L-012及reports/t3_two_architectures_20261001/REPORT.md。

- D-20261001-T3ARCH-002：用户授权顺序完整执行两架构，A先行/B后行，每项一件、统一包、不自动上传；配置artifacts/t3_arch_two_20261001/CONFIG.json。

- D-20261001-T3ARCH-003：v0067未上传初版撤回；同一B模型/状态配额下修复整簇重抽噪声，最大保留WT原有行，新候选另登记；两次预算用于A和修正版B。

- D-20261001-T3ARCH-004：两架构顺序实跑/完整目标/验收完成，最终v0066、v0068统一包，未提交/未评分；来源/WT基线未胜，保留科学负结果，现役不变；见reports/t3_arch_two_execution_20261001/REPORT.md。

- D-20261001-T3ARCHSCORE-001：v0066/v0068回分与10子项入库，两件REJECT、配置关闭、T3待分清零；A方向显示值最高但整体退步，B组成未获收益，现役不变；reports/t3_arch_two_score_review_20261001/REPORT.md。

- D-20261001-SCALE-001：Scaling 四条路线程序建立（用户授权逐个完成）：①T1-D5c ②T3 方向四 ③T3 方向六 ④T1 外部预训练，一次一条，跑前冻结、触发停止即停。详见 docs/coordination/DECISIONS.md。

- D-20261001-T1D5C-001：D5c 200 epochs 足额仍挂门（14.7×/7.9×），按冻结关闭，扩散线三振出局，不提 D5d。详见 docs/coordination/DECISIONS.md。

- D-20261002-ARROUTEC-001：T2 外推板 Route C 自动研究轮打包 5 候选（v0024-v0028）待服务器仲裁；本地综合分冠军 3.913（时间归一化分位数边缘外推 × 组成重采样），并把 variogram 方向纠正与 Route B keep 撤回一并记录。详见 docs/coordination/DECISIONS.md。

- D-20261002-T3DIR4-001：T3 方向四全量双挂（留出 0.552 vs 0.518、谱系 0.612 vs 0.80），按冻结关闭，跨模态映射轴判死路。详见 docs/coordination/DECISIONS.md。

- D-20261002-ARROUTCESCORE-001：T2 外推 Route C 五件回分全部 REJECT（最好 50.17 vs 基线 50.53），外推选择与合计不变；本地综合分被证伪（17 条 ρ=0.122），但 variogram 通道确证可迁移（49.5–50.1 为该榜最好），服务器侧换种子方差仅 0.01。详见 docs/coordination/DECISIONS.md。
- D-20261002-T3AR-001：T3本地48次实验完成20.3112%开发MSE降低目标；末次来源test降低6.1245%但区间跨零，保留模块，不晋级服务器、无新候选。详见 reports/t3_autoresearch_20261002/REPORT.md。

- 2026-10-03 `D-20261003-T2LOCAL-001`：T2 heart外推本地中位数3.913→7.524达到目标；仅尺度项改善、v0029 HOLD_LOCAL_ONLY、服务器不晋级；[报告](reports/t2_autoresearch_20261003/REPORT.md)。
- D-20261003-T3ARDEL-001：补齐T3 autoresearch H5AD v0070，7449×500、contract PASS，上传包就绪，未提交/未评分；初始v0069参考元数据失败草稿保留，修复后X不变。详见 reports/t3_autoresearch_delivery_20261003/REPORT.md。

- D-20261002-T3DIR6-001：T3 方向六放行（用户授权）：GSE261783 26 扰动 0/26 黑名单命中，许可转 RELEASED_BY_OWNER_20261002（仅此集）；Smarca4/Rest/Yy1 复核提示保留，organizer 答复缺席。详见 docs/coordination/DECISIONS.md。

- 2026-10-03 `D-20261003-T2SCALE-SCORE-001`：T2 v0029回分REJECT，当前scale0.9配置关闭；本地尺度收益与服务器相反，现役不变；[复盘](reports/t2_scale_score_review_20261003/REPORT.md)。

- D-20261003-T3ARSCORE-001：v0070回分REJECT、现役不变；来源均值目标与全细胞残差转换脱节，当前配置关闭；详见 reports/t3_autoresearch_score_review_20261003/REPORT.md。

- D-20261003-T3SPARSE-001：v0071以现役v0048为母本，采用来源完整矩阵筛选的有界强度转换；保留零结构、contract PASS、未提交/未评分；详见 reports/t3_sparse_response_20261003/REPORT.md。

- D-20261002-T3DIR6SRC-001：方向六 source v1 冻结为 GSE261783（26 扰动）；GSE92872 屏蔽过但暂缓集成，GSE157977 基因表未取到记 PENDING，Axin 系排除。详见 docs/coordination/DECISIONS.md。

- D-20261003-T3HALF-001：v0071回分不晋级，现役保持；预设减半响应生成v0072，contract PASS、未提交/未评分；来源诊断不支持本地晋级。详见 reports/t3_halfstep_20261003/REPORT.md。

- D-20261003-T3HALFSCORE-001：v0072回分REJECT，现役保持；分布改善不足以抵消DE损失，关闭半步试验、不继续倍率扫描；详见 reports/t3_halfstep_20261003/SCORE_REVIEW.md。

- D-20261003-T3DIR6CLOSE-001：方向六 GEARS 5 折 mse 0.05747，双挂 no-change/ridge 双 bar，升级关闭；附 cosine 口径 bug 修（MSE/verdict 不变）。详见 docs/coordination/DECISIONS.md。

- D-20261003-T2H10SCORE-001：v0030 51.12 晋级新外推 board best（+0.59 vs 基线），v0031 49.91 REJECT、crosswalk 轴关闭；dev–server 方向一致但刻度差远，dev 目标未达成 reserve 仍 NOT_RUN；详见 reports/t2_holdout10_score_review_20261003/REPORT.md。

- D-20261003-T2H10X567SCORE-001：v0032 51.14 TIE 不晋级、v0033 50.89 REJECT、v0034 51.02 TIE 不晋级，现役 v0030=51.12 不变；服务器 de 剂量响应单调确认最优 0.9、同族 dev↔服务器排序完全复现；详见 reports/t2_holdout10_score_review_20261003/REPORT.md。

- D-20261003-T1EXTPRE-001：T1 外部预训练 G-return 挂门（de 0.0189/dir 0.1412），按冻结关闭，不建 v0052。详见 docs/coordination/DECISIONS.md。
- D-20261003-T1MIX2SCORE-001：T1 AR-MIX2 五 lane 回分——v0054 53.98（+0.06）落 ±0.1 TIE 带不晋级、v0051=53.92 留任；v0052/v0056 scored backup、v0053 REJECT、v0055 marginal backup；种子彩票第三次复现（Δ0.31）、36 系配对受控比较第三次领先（+0.31）、权重轴死、三池=稀释、混合族饱和 ~53.7。详见 docs/coordination/DECISIONS.md。

- D-20261005-STRUCT-001：结构整理。已评分 deliveries 包删除（正本仍在 submissions/candidates，见 reports/DELETION_MANIFEST.tsv）；reports/submissions/docs/batch3 不搬动。新入口 docs/00_START_HERE.md、docs/ATOM_MAP.md、reports/README.md。INDEX 回填 T3 v0026/v0027/v0030–v0033 空白 server_score。
- 2026-10-06 `D-20261006-T3SIX-001`：T3 六新路线实现并交付 v0075–v0080；源侧 LOPO 选择，未提交/未评分；[报告](reports/t3_six_routes_20261006/REPORT.md)。
- 2026-10-07 `D-20261007-T3SIXSCORE-001`：T3 六新路线回分，v0075–v0080 全部登记，v0078=47.93 同分现役留下，其余 NOT_PROMOTED，现役 v0048 不变；[registry](reports/SERVER_SCORE_REGISTRY.md#t3-six-score-return-20261007)。
- 2026-10-07 `D-20261007-T3SIX2-001`：T3 第二波六新路线，v0081–v0085 交付、n3_pswap 源侧关闭；未提交/未评分；[报告](reports/t3_six_routes_20261007/REPORT.md)。
- 2026-10-07 `D-20261007-T1SIX-001`：T1 六新路线（3 优化/结合＋3 全新），v0057–v0062 交付、score_pending，未提交/未评分；POT ot.emd 修订+环境修复内嵌；[报告](reports/t1_six_20261007/REPORT.md)。
- 2026-10-07 `D-20261007-T2GEOM-001`：T2 几何新机制冻结为 RMS 锁定的各向异性插值，先诊断不建候选；[冻结](reports/T2_GEOM_ANISO_FREEZE_20261007.md)。
- 2026-10-07 `D-20261007-T2GEOM-002`：各向异性诊断 HEART_ONLY_CONTINUE；胚胎线性族关闭；无候选。详见 artifacts/t2_geom_aniso_20261007-v1/RESULT.md。
- 2026-10-07 `D-20261007-T2GEOM4-001`：T2 四件几何包交付、未评分；[报告](reports/t2_geom4_20261007/REPORT.md)。
- 2026-10-07 `D-20261007-T2GEOM4SCORE-001`：v0023＝62.48 晋级心脏插值；其余三件 REJECT。分位数搬运和外推生长关闭。详见 reports/t2_geom4_20261007/SCORE_REVIEW.md。
- 2026-10-07 `D-20261007-T1SIXSCORE-001`：T1-SIX 六路线回分，v0057–v0062 全部登记，v0058=53.85 带内 TIE 不晋级，其余五件 REJECT，现役 v0051=53.92 不变，T1 待分清零；[registry](reports/SERVER_SCORE_REGISTRY.md#t1-six-score-return-20261007)。
- 2026-10-09 `D-20261009-NAV-001`：导航按 2026-10-08/09 回分刷新。现役 T1 v0092=58.89、T2 胚胎 v0021=63.0047 / 心插 62.48 / 外推 51.12（均分 58.87）、T3 v0088=53.69；推导合计 171.45，门户观测仍 171.4（2026-10-08T11:58Z，rank 61）需重读。两处缺口显式记录：门户 per-task 与现役和对不上（仅 T3 吻合）、AUDIT.md 因 score_status 字段不一致低估数值最高。T3 提交额度标 OPEN/UNVERIFIED。
- 2026-10-09 `D-20261009-T3REBUILD-001`：T3 v0088 从公开代码完整复现（表达式哈希与三个推理产物逐位相同，GO embedding 逐字节相同，基线复合分与归档差 0.0）；发射器成分轴 14 次迭代判定饱和（最好 +0.0034，de_skill 全变体零变化），不建议提交变体，本地源侧指标不再是有效目标。
- 2026-10-09 `D-20261009-T2EMBRYO-SUPPORT-001`：T2 胚胎 v0021 scRNA copula = 63.0047 晋级（官方公开 API 高精度，+0.1117 vs v0014 62.8930）；v0019/v0020/v0022 REJECT，三轴关闭。
- 2026-10-09 `D-20261009-T1LATEANCHOR-001`：T1 late-anchor/OT 五 lane 回分，v0092 ot_gen_v51 = 58.89 晋级为新 board best。
- 2026-10-08 `D-20261008-T3BACKLOG-001`：T3 v0081–v0085 回分，v0084 q0.25 重建=49.55 晋级，v0083/v0085 同 ID 重建 REJECT，不追认历史原始字节。
- 2026-10-08 `D-20261008-T3ARANK-001`：T3 v0086 arank r2=49.34 REJECT（−0.21），源侧代理改善未转化，配置级负结果。
- 2026-10-08 `D-20261008-T3EMBHURDLE-001`：T3 v0087 七 KO 通用胚胎状态响应 hurdle v2=53.42 晋级（+3.87），带 DE/分布权衡。
- 2026-10-08 `D-20261008-T3CONDHURDLE-001`：T3 v0088 conditional hurdle=53.69 晋级为现役（+0.27），消耗最后一次授权尝试预算，当日用量 8/8。
- 2026-10-09 `D-20261009-T2EMBRYO-CLOSE-003`：T2 胚胎 campaign 以 v0021 晋级、v0022 REJECT 收口；外推 existing-route 预算 2/2 已用尽。
- 2026-10-09 `D-20261009-PORTALTOTAL-001`：采纳用户确认的门户 Total **172.9**、per-task T1 58.9 / T2 60.3 / T3 53.7（rank 71/187）；选集相加 172.857 与之一致，全部导航改用该基准。**per-task 对账关闭**——此前对不上是选集滞后所致，非门户口径未知。门户 T2 用各榜数值最高 60.2879，与选集 60.2770 的 0.011 差额来自 ±0.1 带内保留。
- 2026-10-09 `D-20261009-T2OPTRANSFER-001`：T2 算子迁移三件回分。心插 v0025 = 66.7064 晋级并易主（+4.23，相对字节精确 H1 父 65.0260 为 +1.6804）；胚胎 v0023 = 63.0185 带内不换人，保留 v0021；外推 v0037 = 48.86 REJECT。现役 = v0021 / v0025 / v0030，T2 均分 60.277。
