# TODO — 当前待办（用户与 agent 共读唯一入口）

按执行顺序排列，重要的在前。建立日期：2026-09-04。

- [x] 用户读服务器页面，提供最新 Total/T3 读数——服务器确认 Total=**151.2**，精确 board 48.47/60.15/57.25/50.53/46.79，33 个子项分数已入库
- [x] 授权 commit + push 本轮改动——已推送 `951b50e`（P0 产物、Total 151.2 回填、子项登记制度；大文件按惯例留本地）
- [x] 决定做 T1 n=1,706 探针——已生成候选 v0010（2026-09-04 夜，用户明确授权）
- [x] 用户手动上传 `deliveries/b4p0p2__t1__upload__20260904.zip` 并回填分数——v0010=46.8（2026-09-04 19:09 行）
- [x] 授权 Wave 1（2026-09-04）——`B4-T2-R1-FGW-ASSIGNMENT-REPAIR` 已完成（v0010/v0011 待上传，L1 先传）
- [x] 用户手动上传 `deliveries/b4t2r1__t2__upload__20260904.zip`（L1）与 `deliveries/b4t2r1b__t2__upload__20260904.zip`（L2）并回填分数——v0010=57.3（+0.05）、v0011=57.31（+0.06），均 TIE 不晋级（2026-09-04 19:52 行）
- [x] 授权 Wave 1 其余（2026-09-04 用户确认开始）：`B4-T1-R1-CONSERVATIVE-FAMILY`、`B4-T3-R1-GENOTYPE-ONLY-ABLATION`（对比基准 46.8）——已完成并评分
- [x] 用户上传 T1-R1 四包与 T3-R1 两包并回填——T1 47.58/47.77/47.85/46.90（均未晋级，v0004 留任），T3 46.95/46.95（并列新 board best）
- [x] 读服务器页面确认 derived Total≈151.40——已替代：Wave 2 评分离散回填，derived Total≈153.71 待确认，见下
- [x] 授权 Wave 2（2026-09-11 用户确认开始，先做 TODO 规划）
- [x] B4-T1-R2 门控：单次短窗口核查完成 —— 无已登记 allowlist、无可用 late-program processed 对象 → **BLOCKED_DATA_NOT_READY**，任务停止（D-20260911-B4T1R2-001；数据停止位，非科学失败）
- [x] B4-T2-R2 表达桥——embryo 61.79/62.29（双晋级，v0010 新 best）、heart 62.04（+4.79 新 best）/56.27（淘汰）
- [x] B4-T3-R2 发育轴修复——46.45/46.47 双败 → T3 标 ARCHITECTURE_RESET_REQUIRED
- [x] B4-T2-R3 外推表达校准——v0008/v0009/v0010 已生成（L1 clip0/L2 clip21.6%/L3 clip2.4%），单包 `deliveries/b4t2r3__t2__upload__20260914.zip`（一批一包新规首用）
- [x] T2-R3 处置（2026-09-15 用户明确决定）：关闭不评分 —— v0008/v0009/v0010 保留 candidate/score_pending，INDEX 已标 closed_unscored，artifact 不变，可未来复用；不再追分
- [x] 服务器确认 Total=**153.7**（derived 153.71，差 0.01 为服务端舍入）
- [x] Batch 4 closeout（2026-09-15）：六报告 + ARCHITECTURE_RESET_BRIEF 落盘；判定 **ARCHITECTURE_RESET_REQUIRED**（T2 插值 parent 保留）；D-20260915-B4CLOSE-001
- [x] G0 15 轮独立建模（2026-09-16，用户立项，T1/T3 优先）：T1 收缩晋级（v0018-v0021，本地 0.9057/0.9071）、T3 五机制 bet（v0013-v0017，proxy 五连盲，防灾难全过）、T2-extrap 空间平滑晋级（v0012/v0015/v0016，本地 0.2603/0.4245）；交付包 deliveries/g0t1+g0t3+g0t2__*__upload__20260916.zip（18 候选全覆盖，成员校验通过）；本地分总表 G0_LOCAL_SCORE_TABLE.tsv、复现 G0_REPRO.md
- [x] G0-T3 五包回填——v0013=46.88/v0014=46.95/v0015=46.95/v0016=46.88/v0017=46.84（两持平三负，selection 不变；de 全钉 39.2；25 子项入库）；传播-剂量族关闭
- [x] G0-T2 六包回填——v0011=50.64（+0.11 新 board best）、v0012=50.26/v0013=50.32/v0014=50.26/v0015=50.28/v0016=50.25（空间族全负关闭）；selection 更新为 v0011；48 子项入库；本地/服务器方向反转已记
- [x] G0-T1 七包回填——v0015=48.51/v0019=48.54（TIE 带内，v0004 留任）、v0018/v0020=48.48（TIE）、v0016=48.14/v0017=47.46/v0021=48.34（REJECT）；收缩 sweep 关闭（C 弱旋钮）；T1 proxy 方向存活唯一正对照；28 子项入库（2026-09-17）
- [x] T3 D2 首轮构建——v0018（`a82b16e0…`，119 基因位移，contract PASS，恒等复现通过，本地盲无回归；心脏实占 20.75% 更正 52% 口径）；单包 `deliveries/g1t3r6__t3__upload__20260917.zip` 就绪（2026-09-17）
- [x] T3 统包余分回填——T3 R6–R8 分数回填完成：v0018=46.94（TIE）、v0019=46.95（exact TIE）、v0020=46.64（REJECT）；selection 保持 v0009/v0010=46.95。R6–R13 八候选均已评分，余分队列清零，后续轮次待决定。（2026-09-20，D-20260920-G0T3R6R8-001）
- [x] 用户上传 `deliveries/g1t1d3__t1__upload__20260917.zip`（T1 v0022，首适用上传仲裁政策）并回填分数＋子项——服务器 **45.3**（-3.17，低于 floor，REJECT；分项 de 43.7/dir 55.9/mmd 47.9/vario 30.2）；registry/INDEX/子项/TRACKING/DECISIONS 全套回填（D-20260917-T1D3-002）
- [x] T1-P0-1 开工门槛：reset brief §9–§12 重读＋contract E7.75 核对（D7 合法）——2026-09-17 完成，见 T1_TRACKING；CPU only
- [x] T1-P0-2 剩余检索-评估＋综合仲裁——2026-09-17 完成（D-20260917-T1P02-001）：OPT-A/D3/D5 代码 ✅，OPT-B 代码未定位（按论文实现），D4 数据齐，D7 数据 blocked；出场序 D4→D2→D3→D1→D6/D5→D7
- [ ] T1-P0-3 GPU 窗口确认——V100 已登录（双线均通，Tesla V100-SXM2-32GB，driver 550；密钥登录已生效、密码文件已销毁；磁盘 149G 空闲；torch 未装→后台装机中）；数据 1.2GB 已上传＋SHA 双验通过；待环境就绪即冒烟开训
- [x] T1-P1 D4 表达桥移植——2026-09-17 门 FAIL 关闭（G1 de 0.4151/dir 0.5869 双低于 G0 0.566/0.6127；D-20260917-T1D4-001）；组成雷区第四确认
- [ ] T1-P2 GPU 主攻（按仲裁顺序串行；每 lane 本地门→候选→统包→回填→保留/淘汰；上传限 8/task/day）
- [x] T3 D8——v0019 SPLIT（fallback=0，`4b6c5b45…`，R6 消融对照；本地盲无回归）
- [x] T3 D5——v0020 KNK（498 基因，`d8b50dd9…`，覆盖面最广；本地盲无回归）
- [x] T3 D3——v0022 GRAPH（PPR Top-150，`5423dc56…`，唯一 dir 为正；本地盲无回归）
- [x] T3 D6——v0023 SIGNMAX（直优不可行已证伪记诚实重构，一致性平方，`22340b14…`；mmd_u 最低；本地盲无回归）
- [x] T3 D4——v0021 HOP2（LLM/motif分级双不可行已记录；hop1＋hop2×0.5，`1bde8b96…`；首跑 bug 修后重跑；本地盲无回归）
- [x] T3 D1——v0024 DEBIAS（无 GPU 训练的诚实改编：R6＋偏移去偏，`b1a3c01d…`，dir≡baseline；本地盲无回归）
- [x] T3 D7——v0025 SPATIAL（R6＋k15 平滑，`4f64ce1e…`，lib-ratio 0.69 系 Jensen 效应已披露；本地盲无回归）
- [x] commit + push 本批改动——已推送 `c7cb36b`（Total 153.7 确认、T2-R3 关闭、closeout 七报告；大文件按惯例留本地）

## T3 后续修复与数据收集（2026-09-20 用户授权）

- [ ] 路线 3 优化修复：保留完整 WT/356 节点和零干预恒等条件，检查产生负值的节点、细胞类型及传播层；比较天然非负的输出参数化与受约束的响应强度。不得直接放宽 1% 裁剪门槛；新版本须重新报告完整输出和线性/非线性对照。
- [ ] 路线 4 优化修复：按细胞类型定位遮蔽基因误差，检查跨平台归一化、基因映射和供体匹配；在独立留出上检验新映射，须优于类型均值且覆盖率达标后才继续反事实模型。不得用验证基因挑选映射参数后再作为独立结果。
- [x] 路线 5/6 首轮数据收集：已取得 GSE261783 两个原始矩阵并过滤为 5,454×32,287（26 个候选扰动、500/500 panel），以及 R5 关系表和 37 张引用卡片；全部隔离，未训练。详见 `reports/t3_data_intake_20260920/REPORT.md`。
- [ ] 路线 5 准入：补齐可审计 receptor–target 链，解决 ConnectomeDB/CellPhoneDB 数据许可和逐条来源/同源映射；现有资料不可直接当训练 prior。
- [ ] 路线 6 准入：26 个候选扰动仍需逐基因 phenocopy 审查；闭合通用 Perturb-seq 响应形状用途及书面许可边界，不能直接启动带符号预测训练。数据归一化、WT/ontology-only 图输入亦未完成。

## 分支记录

- **当前执行分支**：T3 R1/R2回分登记完成；R5最小SIGNOR链已跑通，v0032/v0033待上传回分；R3/R4修复待办保留；R6规则评审建议修改额外限制（未生效），来源仍隔离。GPU保持关机。
- **并行分支**：无。
- **暂缓分支**：
  - T1-P2 D2 调参挂起（用户特批，2026-09-17）：dz=20 加 patience/调参；触发条件：D3/D1 双败后或用户另行指示。当前 D2 状态：dz20 稳定（410 步无 NaN）但挂门（de 0.8113/dir 0.8652），v0022 未注册；复活时从 `scripts/g0/t1_d2_cellmnn.py --dz` 起步。
  - T1-D7 E7.75 对齐：CLOSED（2026-09-17）。官网实抓：E7.75 not released，不向任何任务分发，前提不存在；此前 PARKED 及下载触发条件一并作废。
  - T3 路线五/六：BLOCKED_PROVENANCE / BLOCKED_DATA_NOT_READY；代码入口已完成，需合规信号边/多扰动输入，正式计算 NOT_RUN。路线三/四本次门槛失败，无候选；后续不自动放宽门槛。
  - T2 embryo_interp v0008 `j1_fgw_assignment`：HOLD_AS_COMPONENT（缺同靶 parent scorer 参照，见 LEADS L-001）
  - T2-S3 L2 spateo v0007/v0008 与 heart_extrap v0006/v0007：本地 REJECT，不可变保留不上传
  - B2-T3-A1 v0006/v0007 条目已移除：二者已评分 45.5/45.5 并列 board best 并晋级当前 selection，不再属于暂缓（原"score_pending"记录过时）
- **停止分支（已关闭，不可变存档）**：
  - T1-S2 moscot decoder（服务器 44.9/44.8 REJECT）
  - HX MIOFlow 增长/死亡动力学（kill test REJECT）
  - T3-S1 prior 链（UNSATISFIABLE_UNDER_FIREWALL 收口）
  - B1-A2/A3/A4、T1 v0002/v0003/v0005/v0006 等历史淘汰候选（见 submissions/INDEX.tsv）

## 变更记录

- 2026-09-04：建立本文件（batch3 收口后）。初始内容：3 条待办 + 分支记录；此前待办散见于各 TRACKING 文档"下一步"节，现以本文件为唯一入口。
- 2026-09-04：新增"用户读服务器页面确认 derived 149.8 / 授权 push / 决定 batch4 或封板"三条为当前待办（由 batch3 收尾事件产生）；同日落盘 `reports/PHASE_REPORT_BATCH3_20260904.md` 与 `reports/RELEASE_CHANGELOG_BATCH3_20260904.md`，分支记录不变。
- 2026-09-04：T3 评分事件（v0006/v0007 双双 45.5 并列晋级 board best，首次超过 wt_identity）回填完毕，登记于 registry/INDEX/TRACKING/STATUS/DECISIONS；待办清单不变（"读服务器页面确认"条目推算值由 149.8 变为 149.7，语义不变）。
- 2026-09-04（晚）：floor 探针评分回填——T1 v0009=47.0（与分层版完全相同，分层被排除）、T3 v0008=46.8（新 board best）；登记于 registry/INDEX/TRACKING/STATUS/DECISIONS（D-20260904-B4P0-001/002）；INDEX.tsv 已回填 6 行 B1-A1 缺分。待办变化：移除"上传 floor 探针""应用 P0 补丁""授权 Wave 1（旧表述）"，新增"T1 n_obs=1,706 探针决定"与"Wave 1 授权（T2-R1 优先，T3 基准 46.8）"；route_status.yaml 冲突项保留待用户在 Wave 1 授权时一并裁决。
- 2026-09-04（夜）：用户授权执行 T1 n=1,706 探针；新 locked run 完成候选 v0010（sha `6994a38e…`，检查全 PASS，重跑字节一致，INDEX 已登记 candidate/score_pending），交付包 `deliveries/b4p0p2__t1__upload__20260904.zip` 就绪。待办变化：“探针决定”完成勾选，新增“手动上传并回填分数”。
- 2026-09-04（夜）：v0010 评分回填——46.8（-0.2 vs v0009=47.0），n_obs 假设被排除，FLOOR_PARITY_UNRESOLVED 维持；登记于 registry（§B4-P0 supplemental）/INDEX/DECISIONS（D-20260904-B4P0-003）/T1_TRACKING/双层 STATUS。待办变化：“上传并回填”完成勾选；剩余待办为 Total 确认、push 授权与 Wave 1 授权。
- 2026-09-04（夜）：服务器确认 Total=**151.2**，五 board 精确分与 33 个 per-metric skill 回填 `reports/SERVER_SUBMETRIC_REGISTRY.tsv`（新建）并在 registry 立快照节（D-20260904-TOTAL-001）；INDEX 五行备注精确分；双层 STATUS 更新至 151.2。待办变化：“Total 确认”完成勾选；即日起每次上传/评分必须登记子项分数（规则见 submissions/README.md）。
- 2026-09-04（夜）：B4-T2-R1 双 lane 评分回填——v0010=57.3（+0.05）、v0011=57.31（+0.06），均与 v0009 打平 → TIE 不晋级，v0009 留任，关闭 FGW 离散化微调；登记于 registry（§B4-T2-R1）/INDEX/DECISIONS（D-20260904-B4T2R1-001）/T2_TRACKING/双层 STATUS，16 子项已入库。待办变化：“上传 R1 双包并回填”完成勾选；剩余 Wave 1（T1-R1/T3-R1）授权与 push。
- 2026-09-05：Wave 1 剩余评分回填——T3-R1 v0009/v0010 双双 46.95（+0.15 vs floor，并列新 board best；L2==L1 不声称 lineage 偏好），T1-R1 v0011–v0014 为 47.58/47.77/47.85/46.90（均低于 best 48.47，排序 L3>L2>L1>L4；v0004 留任，保守族关闭）；登记于 registry（§B4-T3-R1 / §B4-T1-R1）/INDEX/DECISIONS（D-20260905-WAVE1-001）/T1+T3_TRACKING/双层 STATUS，26 子项已入库。待办变化：Wave 1 全部完成；新增“确认 derived Total≈151.40”与“Wave 2 / 封板授权（含 push）”。
- 2026-09-14：Wave 2 评分回填——T2-R2 embryo v0009=61.79（+1.64）晋级、v0010=62.29（+2.14）新 best，heart v0013=62.04（+4.79）新 best、v0012=56.27（-0.98）淘汰，两 board 均 L2>L1；T3-R2 v0011=46.45/v0012=46.47 双败 → T3 标 ARCHITECTURE_RESET_REQUIRED；登记于 registry（§B4-T2-R2 / §B4-T3-R2）/INDEX/DECISIONS（D-20260914-WAVE2-001）/T2+T3_TRACKING/双层 STATUS，42 子项已入库。待办变化：Wave 2 部分完成；新增“确认 derived T2=58.29/Total≈153.71”与“T2-R3（独立 UTC 日）授权”。
- 2026-09-15：Batch 4 closeout —— 服务器确认 Total=**153.7**（registry 确认节）；T2-R3 v0008/v0009/v0010 按用户明确决定关闭不评分（INDEX 标 closed_unscored，artifact 不变）；六报告（PHASE_REPORT/SCORE_GAP/ERROR_SIGNATURES/COMPONENT_LEDGER/PROXY_VS_SERVER/RESET_BRIEF/INPUT_READINESS）落盘；判定 ARCHITECTURE_RESET_REQUIRED（D-20260915-B4CLOSE-001）；双层 STATUS 与分支记录同步封板。待办变化：Wave 2/closeout 全勾选；仅剩“commit + push（需授权）”。
- 2026-09-16：G0 交付 —— 15 轮（T1×5/T3×5/T2×5）全部完成：T1 四晋级（C=4 最优）、T3 零本地胜（机制 bet×5）、T2-extrap 三晋级（k=60 最优）；三包交付（审计后补全 18/18）、INDEX 18 行 G1候选（T1×7/T3×5/T2×6；T2-R1 为门控轮无新候选，R5/R4 扫参一轮多 lane）、本地分总表与复现文档落盘。待办变化：新增“用户统一上传并回填分数”。
- 2026-09-16：G0-T3 评分回填——五 lane 无晋级（v0014/v0015 持平 46.95，v0013/v0016 -0.07，v0017 -0.11）；登记于 registry（§G1-T3）/INDEX/DECISIONS（D-20260916-G0T3-001）/T3_TRACKING，25 子项已入库。待办变化：T3 回填完成勾选；剩余 T1/T2 两包待用户上传。
- 2026-09-16：G0-T2 评分回填——一晋级五负（v0011 收缩 +0.11 新 best，空间族 k07–k60 全低于 baseline）；登记于 registry（§G1-T2）/INDEX/DECISIONS（D-20260916-G0T2-001）/T2_TRACKING，48 子项已入库。待办变化：T2 回填完成勾选；仅剩 T1 一包待用户上传。
- 2026-09-17：T3 30 轮调研转执行（reports/G1_T3_30ROUND_RESEARCH.md D1–D8）——按 D2(2)→D8(2)→D5(3)→D3(4)→D6(4)→D4(3)→D1(8)→D7(4)=30 顺序推进，每 5 轮仲裁（de 未动砍分支）；用户明确"写入然后开始工作"。待办变化：新增 D2–D7 八项；当前执行分支更新为 T3-D2。
- 2026-09-17：D2 首轮完成——v0018 构建＋RESULT.md＋INDEX 登记（score_pending）＋单包交付＋T3_TRACKING；待办变化：D2 构建勾选，新增 D2 服务器仲裁轮。
- 2026-09-17：D8/D5/D4/D3/D6/D1/D7 七 lane 全收——7 候选构建＋RESULT.md＋INDEX 登记（score_pending）＋8 成员统包交付＋T3_TRACKING；待办变化：七项勾选，D2 次轮升级为 8 包统一仲裁轮。
- 2026-09-17：G0-T1 评分回填——三 TIE 两持平两负，无晋级；登记于 registry（§G1-T1）/INDEX/DECISIONS（D-20260917-G0T1-001）/T1_TRACKING，28 子项已入库。待办变化：g0t1 勾选；G0 三包全清；仅剩 T3 统包待用户统一提交。
- 2026-09-17：T1 调研转执行开工（reports/G1_T1_30ROUND_RESEARCH.md D1–D7）——P0-1 完成：reset brief §9–§12 已重读（覆盖映射：D5/D6/D3/OPT-A→§12(2)非自主分支生成，D7＋OPT-A(c)→§12(1)开放集多锚点；缺口：“外部时序预训练”无直接对应 lane、全转录组 decoder 待代码评估单列，记入 P0-2 仲裁；§10 四禁令 D 系均遵守，§11 floor 门延续）；contract 核对 T1 background=[E7.75]（D7 合法）。待办变化：T3 统包待办更新为余分 3 行；新增 T1-P0/P1/P2 五项；当前执行分支切为 T1-P0，T3 余分转暂缓。
- 2026-09-17：T1 P0-2 仲裁落盘（D-20260917-T1P02-001）——出场序 D4→D2→D3→D1→D6/D5→D7；D7 数据 blocked（E7.75 本地无，911MB 登录下载）转用户下载项；P0-3 转 CPU-first（租赁押后到 D1/D5）。待办变化：P0-2 勾选；P1 拆为 D4 执行中＋D7 blocked；新增用户下载项。
- 2026-09-17：撤回 E7.75 下载要求（D-20260917-T1D7-001）——用户质疑成立：E7.75 的 holdout 身份属 T2-embryo（absolute holdout＋外部数据禁区），T1-background 用途虽合规但 D7 排仲裁末位、即时需求不明确，911MB 登录下载现在不值得。待办变化：删除用户下载项与 P1-D7 行，D7 转暂缓分支 PARKED，触发条件为 D4→D5 均败。
- 2026-09-17：T1-D5 回报门 FAIL 关闭（D-20260917-T1D5-001）——energy 差 8 倍，JSD 腿空转（设计债）；v0024 空号保留；P2 进 D6。待办变化：当前执行分支切为 T1-P2 D6。
- 2026-09-17：T1-D1 回报门 FAIL 关闭（D-20260917-T1D1-001）——de 0.3585/dir 0.6243 双远低，坍缩签名，停建 E10.5；P2 剩 D5/D6（GPU 级，需新设计）；GPU 机闲置待命。待办变化：当前执行分支切为 T1-P2 待命。
- 2026-09-17：T1-D3 v0022 服务器仲裁回填（D-20260917-T1D3-002）——45.3 REJECT（低于 floor）；proxy 教训修正（T1 首个假阳性，energy 旗预警正确，doctrine 细化为须分布侧连署）。待办变化：上传项勾选关闭。
- 2026-09-17：T1-D3 v0022 上传交付（D-20260917-T1UPLOAD-001 首适用）——构建数 de 0.9623/dir 0.8889，contract PASS，INDEX 登记 score_pending；单包已交付待用户上传。待办变化：新增用户上传项。
- 2026-09-17：T1-D3 全基因门 FAIL 关闭（D-20260917-T1D3-001）——energy 差于基线，cosine 虽优但门要双指标；v0022 未建；P2 进 D1（待 GPU 批）。待办变化：当前执行分支切为 T1-P2 D1（pending GPU）；P0-3 请用户批租赁。
- 2026-09-17：T1-D4 门 FAIL 关闭（D-20260917-T1D4-001）——G1 双低于 G0，不建候选；P2 进 D2。待办变化：P1-D4 勾选关闭；当前执行分支切为 T1-P2 D2。
- 2026-09-17：V100 沿用获批＋D1 上机准备（D-20260917-T1GPU-001）——用户批 V100 沿用链路；OPT-A(c) 修订（去 E7.75 锚点，回两点 DOT，原因 D7 CLOSED）；设计稿＋训练脚本＋CPU 冒烟＋上机清单本地备齐待登录。待办变化：P0-3 改已批待登录；分支切 D1 上机准备中。
- 2026-09-17：V100 上机（双线 SSH 均通，V100-SXM2-32GB；密钥替换密码登录；裸机无 torch→后台装 cu121＋依赖；数据 1.2GB 上传＋SHA 对账通过）。待办变化：P0-3 改登录就绪、环境装机中。
- 2026-09-17：E7.75 缓存订正＋D7 关闭（D-20260917-T1D7-002）——重抓官网 Data 页：E7.75 为 unused / not released（held out as T2-embryo test，不向任何任务分发），此前“已发布/911MB/登录下载”缓存作废，SYNC §2/§7 与 INVENTORY §3 已订正（来源与日期已记）；T1-D7 前提出不存在，由 PARKED 转 CLOSED，下载触发条件作废；禁从第三方镜像补齐。待办变化：暂缓分支 D7 改 CLOSED。
- 2026-09-17：T1-D2 调参挂起＋D3 开工（D-20260917-T1P23-001）——用户裁决：D2（dz20 挂门）不关闭，转调参挂起（触发条件 D3/D1 双败或另行指示）；执行分支切为 T1-P2 D3。待办变化：暂缓分支新增 D2 调参项。
- 2026-09-17：T1-D5/D6 全开＋费用纪律（D-20260917-T1GPU-002）——用户指令全开快开、完工即关机；D5 先行 D6 排队；wall 单 lane 4h 上限。待办变化：当前执行分支切为 T1-P2 D5；新增 D5/D6 会话任务（#9 执行中/#10 待命）。
- 2026-09-17：T1-D6 回报门 FAIL 关闭＋GPU 关机（D-20260917-T1D6-001）——de 恰等门线不算过；GPU 已 OS halt 待控制台确认释放；D2 调参触发条件已满足（D3/D1 双败），待用户定夺。待办变化：当前执行分支切为 T1-P2 待定。
- 2026-09-17：本轮独立复核（D-20260917-T1AUDIT-001）——D1/D6/D4/D2/v0022 全确认；D5 测试无效（理由订正，CLOSE 维持）；重名目录改名；SHA/台账全对。待办变化：无（分支仍为 T1-P2 待定；D2 调参＋D5b 立项均待用户定夺）。
- 2026-09-17：D5b 立项开工（D-20260917-T1D5B-001）——用户令修复重跑且 CPU 先行；DESIGN 定稿（三修复＋坍缩 veto＋v0026）；码已写，本地冒烟→CPU 全量→建门，GPU 保持关机零花费。待办变化：当前执行分支切为 T1-P2 D5b。
- 2026-09-17：T1-D5b 回报门 FAIL 关闭（D-20260917-T1D5B-002）——基线精确复现（可比成立）；场 7.23 差基线 27×，欠拟合发散（library 4.3×/方差 2.2×）；D5c 长训（约 10× 量）属新假设待立项。待办变化：当前执行分支切回 T1-P2 待定。
- 2026-09-20：项目结构整理开工（方案 v2，用户批 A 全执行）——P1：AGENTS 路径修复＋维护规则、LANE_VERDICTS 31 行、generate_audit.py＋AUDIT.md、立牌不搬家、根 DECISIONS 补齐到 09-17。待办变化：当前执行分支切为结构整理 P1。
- 2026-09-20：结构整理 P2 执行完——删 S1A v1–v6（留 v7，P0-LOCK intact）、outputs/t2_*、27 个 g0 重复副本（SHA 双验一致才删）、7 训练件、6 回报探针、v0002 孤儿副本；g0 12G→1.3G，outputs 5.2G→80K；门检查全过（INDEX 零 artifacts 引用、JSON 零 truthy、D2 豁免）；ENV_SNAPSHOT＋DELETION_MANIFEST（54 行）入库；quarantine 保留注记。待办变化：当前执行分支切为结构整理 P3。
- 2026-09-20：结构整理 P3 执行完——AST 逆依赖确认 24 死脚本，但 18 个用 parents[1] 定位根，搬家必炸，改立牌（scripts/ARCHIVED.md）不搬家；t3_s1_prior 有 incoming 剔除；包装/契约入口豁免。待办变化：整理收工，当前执行分支切回 T1-P2 待定。
- 2026-09-20：T3 R6–R8 分数回填完成：v0018=46.94（TIE）、v0019=46.95（exact TIE）、v0020=46.64（REJECT）；selection 保持 v0009/v0010=46.95。R6–R13 八候选均已评分，余分队列清零，后续轮次待决定。15 子项入库，LANE_VERDICTS 三行转 SHIPPED（已评分无增益），审计入口重生成；T1-P2 待定不变。

### T3 R5/R6 补充准备（2026-09-20）

- [x] 第二轮隔离过滤、500基因唯一映射、逐条件处置表、signed/shape用途门、书面确认草稿。
- [ ] R5逐边补全target链和物种/实验背景/数据许可审查；当前批准链0。
- [ ] R6剩23扰动完整背景审查、主办方来源用途书面确认；草稿NOT_SENT。
- [ ] 获批后集成shape-only完整分支，构建许可内标准化矩阵/WT或ontology图与embedding，再做gene holdout。当前全部训练NOT_RUN，禁止降低20扰动门。
- 证据：`reports/t3_r56_readiness_20260920/REPORT.md`。R3/R4已有修复TODO保留。

### T3 R5 本轮补齐结果

- [x] 最小链4条SIGNOR关系的来源/许可/同源映射审核，建立1条LRT及hash绑定manifest，官方WT实际运行，v0032/v0033 contract PASS。原37条不宣称全部补齐。
- [ ] 用户上传 `deliveries/r5sig__t3__upload__20260920.zip` 并提供服务器总分/子分/证据；既有v0026/v0027/v0030/v0031已回填，R1无总分增益，R2当前两候选淘汰。
- [ ] R6其余背景审查与内部要求确认继续保留；官网和内部要求区别见 `reports/t3_r5_completion_20260920/R6_RULE_EXPLANATION.md`。

- [x] 2026-09-20：登记R1/R2四组服务器总分及20个子分，核对artifact SHA；best不变。
- [ ] 按 `reports/T3_INTERNAL_RULE_REVIEW_20260920.md` 修订内部额外约束与R6用途门，并重新审查数据；当前为建议，未变更有效规则。
