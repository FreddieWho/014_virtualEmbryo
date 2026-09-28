# TODO — 当前待办（用户与 agent 共读唯一入口）

按执行顺序排列，重要的在前。建立日期：2026-09-04。

## T3 后续修复与数据收集（2026-09-20 用户授权）

- [ ] 路线 5 准入：补齐可审计 receptor–target 链，解决 ConnectomeDB/CellPhoneDB 数据许可和逐条来源/同源映射；现有资料不可直接当训练 prior。

### T2 线索闭环（2026-09-27，用户授权执行）

- [x] LEADS L-001：embryo v0008 同靶 parent 参照 —— 对 parent v0002 跑锁定 scorer（同 pseudo-target E7.25／同 reference E6.75／同 seed 20260830），`neighborhood_mmd` 0.03124→0.03445、`morans_I_agreement` 0.9722→0.9555 **两个独立耦合指标同向变差**；排除"度量偏袒 parent"，v0008 由 `HOLD_AS_COMPONENT` 升级为**确证拒绝**。附带：J1 的 NFS 镜像在 parent 臂上与官方 scorer 逐位吻合（0.03124 vs 0.031240），代理当时无偏差。证据 `artifacts/tool_integration/T2-L001-EMBRYO-PARENT-REF-20260927-v1/RESULT.md`
- [x] LEADS L-002：FGW ε 两值敏感性（**非网格搜索**，ε∈{0.005 冻结, 0.002}，其余逐位复用冻结 J1-PROXY）—— 分散度大幅下降（有效来源数 64.15→11.46、59.84→12.20，冲突率 0.610→0.395、0.620→0.409）**Q1 成立**；但 NFS-like 只 H2 变好、H1 反向，**Q2/Q3 未在两 holdout 同时成立**，预声明升级判据未达成 → **L-002 关闭为已放弃，不再扫 ε**。附带：objective 在两 holdout 都更低而 NFS 只 H2 降，**冻结 objective 与官方度量在 ε 方向不对齐**。证据 `artifacts/tool_integration/T2-L002-FGW-EPS-SENSITIVITY-20260927-v1/RESULT.md`
- [x] T2 收口报告 + 决策 + tracking + verdicts + LEADS 状态回填（D-20260927-T2LEADS-001）；脚本 `scripts/t2_l2_eps_sensitivity.py` 与测试 `tests/test_t2_l2_eps_sensitivity.py`；**零候选、零评分、零上传，INDEX 未改**
- **T2 现无未跑的已规划路线。** 唯一未闭合的账：heart_extrap v0011 已评分 50.64 但未反映在 Total 156.06 的组合里（差 0.11），需重读门户页面。

### T2 九路线（2026-09-27 用户授权，M0 已冻结）

- [x] **M0** 前置冻结：3 个 board 父版本 SHA 实核、board 契约、5% 三分类判据、重复测量离散度定义、设计先于训练检查、已耗尽轴清单、替补预算上限。证据 `reports/T2_NINE_ROUTES_20260927_M0_FREEZE.md`（D-20260927-T2M0FREEZE-001）
- [ ] **M1** researcher 检索 6 条新路线 + 我定稿 3 条迭代路线 + 独立审稿；9 个槽位填满并冻结设计文档
    - [ ] researcher 检索：embryo 2 新 + 1 迭代候选（含出处、距已耗尽轴距离）
    - [ ] researcher 检索：heart_interp 2 新 + 1 迭代候选
    - [ ] researcher 检索：extrap 2 新 + 1 迭代候选（extrap 另需先建 pseudo_holdout proxy）
    - [ ] 9 份设计文档落盘（每条：出处、机制、pseudo-target、2 臂、预期失败模式）
    - [ ] researcher 对 9 份定稿设计做独立审稿，意见逐条回应并落盘
- [ ] **M2** embryo 三条 lane 实现与完整运行（串行，子项可并行否→否）
- [ ] **M3** heart_interp 三条 lane 实现与完整运行（须 M2 完成后开始，单写者约束）
- [ ] **M4** heart_extrap 三条 lane 实现与完整运行（须 M3 完成后开始）
- [ ] **M5** 9 候选 contract、INDEX 登记、三方 SHA、命名合规、打包（须 M2–M4 全完成）
- [ ] **M6** 收口报告 + 文档回填（须 M5 完成）

关键约束（详见 M0 冻结文件）：主指标 `neighborhood_mmd` 算 5%；结构性失败一票否决；边界从宽按轻微处理；每 lane 须报 `disp%`；extrap 迭代父版本用 v0011（50.64）但不改 selection；不重提 FGW ε、extrap 空间平滑、extrap 位移幅度族。

## T1 五路线交付（2026-09-27）

- [x] 三条新路线与R1/R2两条优化完整实现、全量拟合/预测与五个完整panel官方scorer；五候选v0024–v0028，contract/独立重放PASS，9测试PASS。
- [ ] 五候选按 reports/t1_five_20260927/REPORT.md 进行服务器仲裁并回填分数；未提交/未评分，selection v0023不变。

## 分支记录

- **当前执行分支**：T2 九路线 M0 已冻结（5% 判据 + 父版本 SHA 实核 + 已耗尽轴清单），M1 researcher 检索与设计定稿待启动；T3 八分回填完（v0048 47.93 新 best，Total 157.04；v0037/v0040/v0041 仍待分）；T1 selection 改为 v0024 51.92（2026-09-28 五路线回填；v0025/v0027 超旧线但未晋级，v0026/v0028 低于父版本）。分支详情见“T2 九路线”节与 DECISIONS D-20260927-T2M0FREEZE-001。
- **并行分支**：无。
- **暂缓分支**：
  - T1-P2 D2 调参挂起（用户特批，2026-09-17）：dz=20 加 patience/调参；触发条件：D3/D1 双败后或用户另行指示。当前 D2 状态：dz20 稳定（410 步无 NaN）但挂门（de 0.8113/dir 0.8652），v0022 未注册；复活时从 `scripts/g0/t1_d2_cellmnn.py --dz` 起步。
  - T1-D7 E7.75 对齐：CLOSED（2026-09-17）。官网实抓：E7.75 not released，不向任何任务分发，前提不存在；此前 PARKED 及下载触发条件一并作废。
  - T3 路线五/六：路线六（R6 signed）准入与数据已就绪，首次执行输出负值门槛失败；非负修复见 2026-09-21 已完成项。路线五（R5）最小信号链 4 条已审核并生成 v0032/v0033（已回分，与父同分），**扩链未执行**，当前批准链仍为最小集；需 ConnectomeDB/CellPhoneDB 许可与逐条同源映射方可推进
  - T3 2026-09-27 五路线已完整实现与运行，五个最终候选待服务器仲裁；11测试、contract与模型逐值重放PASS，v0043/v0045撤回保留。见 reports/t3_five_20260927/REPORT.md；旧六修复候选仍待回分。
  - T2-S3 L2 spateo v0007/v0008 与 heart_extrap v0006/v0007：本地 REJECT，不可变保留不上传
  - B2-T3-A1 v0006/v0007 条目已移除：二者已评分 45.5/45.5 并列 board best 并晋级当前 selection，不再属于暂缓（原"score_pending"记录过时）
- **停止分支（已关闭，不可变存档）**：
  - T1-S2 moscot decoder（服务器 44.9/44.8 REJECT）
  - T2 embryo_interp v0008 `j1_fgw_assignment`：2026-09-27 由暂缓转**确证拒绝**（LEADS L-001 已跑同靶 parent scorer 参照，两个独立耦合指标同向变差；见 `reports/T2_LEADS_CLOSURE_20260927.md`）；保留为不可变研究组件，不删不改名不上传
  - HX MIOFlow 增长/死亡动力学（kill test REJECT）
  - T3-S1 prior 链（UNSATISFIABLE_UNDER_FIREWALL 收口）
  - B1-A2/A3/A4、T1 v0002/v0003/v0005/v0006 等历史淘汰候选（见 submissions/INDEX.tsv）
  - T1-P0-3/P2 GPU 主攻链（2026-09-27 清理移入）：D1/D5/D6/D5b 全关＋GPU 已 halt，09-17 仲裁顺序执行完毕；复活需新 lane 立项

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

- [ ] R5逐边补全target链和物种/实验背景/数据许可审查；当前批准链0。
- 已替代（2026-09-21）：旧的普遍书面确认与shape-only要求取消；本次26个条件按实际来源上下文重新审查通过。未取得确认函，也不伪称已取得。
- 可选方法：shape-only后继不再是准入前提；当前准备启动原signed R6，shape版完整集成未执行。
- 证据：`reports/t3_r56_readiness_20260920/REPORT.md`。R3/R4已有修复TODO保留。

### T3 R5 本轮补齐结果

- 已替代（2026-09-21）：旧的普遍书面确认与shape-only要求取消；本次26个条件按实际来源上下文重新审查通过。未取得确认函，也不伪称已取得。



### T3全路线复核后的整合建议（2026-09-21，未执行新分支）

- [ ] P2 整合R1结构保护、R5有效信号链及旧图/rank先验；不原样重跑R2整细胞替换或全表达平滑。

- [x] 上传 `deliveries/r634fix__t3__upload__20260921.zip` 六个修复候选（用户已上传；2026-09-27 回填 v0034/v0035/v0036，v0037/v0040/v0041 仍 score_pending）并回填总分/五子分；R5旧分数已登记。

### T1新六路线（2026-09-21 提案，R1–R5 已执行收口，R6 PARKED）

- [x] R2：残差保留decoder——2026-09-21 诊断关闭（decoder 失真确认但只追平 strict，无候选）。
- [x] R1：分布零率/阳性分位数外推——v0023 服务器 **50.82** 晋级新 T1 best；尺度扫描 1x 为峰，不建 v0025，第二候选位保留。
- [x] R5：固定逐基因边际——2026-09-27 诊断关闭（重排破坏内聚，学习方向差于置乱，无候选）。
- [x] R3：稳定有界仿射动力学——2026-09-27 诊断关闭（对角持平 strict，低秩更差，无候选）。
- [x] R4：模块运输代价——2026-09-27 诊断关闭（energy 6.79＋library 对半＋A/B 四位一致，无候选）。
- [x] R6 数据源审查——2026-09-21 只读审查完成（单研究谱系；E7.75 窗口 14,493 细胞）；2026-09-27 用户裁决 E7.75 相关进 LEADS L-007；剩余 barcode 去重＋第二来源待排期。R6 PARKED，非关闭。

D5b已按最终RESULT失败关闭，不以旧追踪“建门中”状态重启；上述条目均为待实施方案，不预占候选号、不恢复旧训练。
- 2026-09-27：**T2 九路线立项，M0 冻结（用户授权）**——用户授权 T2 三个 board 各 2 新 + 1 迭代共 9 条 lane，裁定 5% 为量化阈值。M0 完成：父版本 SHA 实核（embryo v0010 62.29 / heart v0013 62.04 / extrap 迭代父 v0011 50.64，selection 不动）、board 契约核对、5% 三分类判据（主指标 `neighborhood_mmd`，结构性失败一票否决，边界从宽）、重复测量离散度定义（3 seed，disp%）、设计先于训练可核查规则、5 条已耗尽轴清单、替补预算上限（每 board 1 条）。决策 `D-20260927-T2M0FREEZE-001`。待办变化：新增“T2 九路线”节共 6 条（M0 已勾选，M1 含 5 个子项）；当前执行分支切为 T2 九路线 M1。⚠️ 随附反证已写入冻结文件：extrap 迭代父版本 v0011 当年本地门判 NOT promoted 而服务器给 50.64（board 最高）——若机械套用 5% 会误杀这条最高分路线，故 5% 只能当筛选器。
- 2026-09-27：**T2 未完成路线执行收口（用户授权）**——LEADS L-001 与 L-002 两条线索全部执行完毕，零候选零评分零上传。分支变化：T2 embryo v0008 `j1_fgw_assignment` 由**暂缓分支移入停止分支**（HOLD_AS_COMPONENT → 确证拒绝，依据同靶 parent scorer 参照）；FGW ε 离散化轴确认耗尽，不再新增该方向待办。LEADS 状态：L-001 改「已并入主线（N12）」、L-002 改「已放弃（2026-09-27）」、新增 L-006（embryo 若再做行-点配对，先修 M 参考构建——纯文档评审，不占 TODO）。决策 `D-20260927-T2LEADS-001`（coordination 与根索引同批追加），收口报告 `reports/T2_LEADS_CLOSURE_20260927.md`，LANE_VERDICTS 追加 2 行 GATE_ONLY。待办变化：新增"T2 线索闭环"四条（全部勾选完成）；**T2 自此无未跑的已规划路线**。
- 2026-09-27：**文档一致性修复（用户指令）**——根 STATUS.md 从 09-21 滞后状态追到 09-26 事实（Total 153.7→156.06、T1 best v0004 48.47→v0023 50.82、Top3 三任务重写、下一步总览重写、活跃节点改为 N11）；ROADMAP.md 从 7/8 节点补到 10/12，新增 N9（G0 15 轮）、N10（T1-P2 D1–D8）、N11（T1-NEXT/T3-NEXT）、N12（T2 线索闭环）四个节点及“路径偏离”段；coordination/STATUS.md 的 leaderboard 与 T1/T2/T3 next_action 同步。
  待办变化：① **注销重复项**——第 45/46 行“T3 路线 3/4 优化修复”实为 09-21 已执行内容（v0034/v0035、v0036/v0037、v0040/v0041）却未勾选，已改为已完成条目并标注“新优化 o1stable/o2shrink 不等于它们”；② 暂缓分支中“T3 路线三/四本次门槛失败，无候选”已过时，同步改写；③ 新增 STATUS 偏离段的 **PLAN H1 冲突**（PLAN 写“T1 停留在 strict-shift 48.5、重启需全新假设”，R1 +2.35 已推翻；按规则不改 PLAN，只报告）。
  未决：heart_extrap 已评分最高 v0011=50.64，但服务器确认的 156.06 用的仍是 baseline 50.53，差 0.11 未解释，已在两层 STATUS 与 registry basis 标为 OPEN，需重读门户页面。
- 2026-09-26：T1-v0023 服务器回填 50.82（de 44.0/dir 57.4/mmd 53.1/vario 47.8，用户转录，ID/时间戳未提供）——+2.35 晋级新 T1 best，Total 153.7→156.06；INDEX scored、registry 快照、submetrics＋4、verdicts R1 SHIPPED/R2 FAIL/R6 PARKED、AUDIT 重生成、D-20260926-T1V23SCORE-001。待办变化：R1/R2 关闭（#28/#29 完成）；当前执行分支切为 T1-v0023 新基线＋R5 开工。
- 2026-09-27：**L-002 atom B 程序性修复 + 机制更正（`D-20260927-T2LEADS-003`）**——首次执行的复现门（绝对 1e-9）未通过，按用户指示立 atom B，把容差改为**跑前声明**的相对 1e-4 并通过；atom B 与首次执行数字逐位相同（差值 0.000e+00），**非独立复现**，引用须成对。新增落点诊断测得两 ε 臂仅 46.05%/45.80% 位置重合，**推翻「两 ε 落到相同行」的原解读**；正确机制为**冻结 FGW 目标面在 ε 方向近退化**（两解不同、hard objective 仅差 2.4e-03/4.6e-03），这是 `B4-T2-R1` heart 双 TIE（57.3/57.31）的成因。待办变化：L-002 关闭结论不变（已放弃、不再扫 ε），但**理由升级**——「把同一目标解得更好」（ε/max_iter/tol 一类）在 T2 判为死路；新增两条**未验证线索**（非 ε 依赖 tie-break / 换更敏感的目标 / 官方 metric 可微代理），按 LEADS 纪律只登记不执行。已回填：coordination DECISIONS + 根 DECISIONS 索引、LEADS 补正（追加式）、T2_TRACKING、LANE_VERDICTS 新增一行、收口报告 atom B 补正节、atom B RESULT.md。零候选零上传，INDEX 未改。
  过程记录：本轮在共享工作树中执行，同时段另一持租约会话（T3 五路线 → T1-NEXT R3/R4 → T2 M1 闸门）在同一目录写入，并在我首次执行后改写过本任务产出脚本。教训已记入 DECISIONS 的 process_note：**共享工作树下的 gate 容差不得由后到会话顺手修正，须以新 atom 事前声明**。
- 2026-09-27：**TODO 清理＋E7.75 进 LEADS（用户指令）**——① 移除 09-27 之前完成的全部 52 条 [x] 待办（分支记录与变更记录保留；空了的旧节标题一并移除）；② T1 新六路线六个 stale [ ] 按 TRACKING/verdicts 实际收口改 [x]（R1 shipped 50.82、R2/R3/R4/R5 诊断关闭、R6 审查完成转 PARKED）；③ E7.75 相关（D7 前提＋R6 外部 E7.75 窗口 14,493 细胞）记入 LEADS L-007（待挖掘，触发条件为官方发布/放行）；④ T1-P0-3/P2 GPU 僵尸待办移入停止分支（D 系全关＋GPU 已 halt）；⑤ 当前执行分支同步为 T1-NEXT 全收口。待办变化：共读入口只剩当前可执行项（T3 准入/M1–M6/上传/P2 四项、T2 M1–M6 六项）。
- 2026-09-27：**T3 八分回填（用户转录）**——FIVE 五件 v0042 46.95（exact tie）/v0044 47.47（+0.52）/v0046 47.65（+0.70）/v0047 46.97（TIE）/v0048 47.93（+0.98 **PROMOTED 新 T3 best**）＋修复三件 v0034 47.53（+0.58）/v0035 47.03（TIE）/v0036 46.98（TIE）；Total 156.06→**157.04**；INDEX 八行 scored、submetrics＋40、verdicts FIVE×5＋R6/R3、AUDIT 重生成、D-20260927-T3SCORE-001。待办变化：r634fix 上传项勾选（3/6 回填，v0037/v0040/v0041 仍待分）；T3-FIVE 五件由“待回分”转已回分；当前执行分支同步。
- 2026-09-27：**已评分路线综述**——新建 `reviews/2026-09-27_submitted-route-synthesis/`（正文、三张图、可复核表）。只读 INDEX 与子项台账，不改候选、不改分数、不改 selection。待办变化：无新执行项；综合评估以后追加到 `reviews/`，不另建平行清单。
- 2026-09-27：**T2 九路线裁决 + M0 附录 B + `E-N1 SBL` 执行关闭（用户授权「yes and move on」）**——① 追加 `D-20260927-T2M0APPXB-001`（M0 附录 B，逐板校准主指标）：`neighborhood_mmd`+5% 在 heart_interp/extrap 维持，**embryo 停用 5% 三分类**（Spearman +0.833 反向），该板改服务器仲裁优先、本地只记录不否决；`mmd_u` 会签在 embryo 零信号且族内成对反向；`d2_shape` 不得单独作失败签名。**未回改 M0 §3/§4 任何原有条款。** ② 追加 `D-20260927-T2M1VERDICT-001`：9 条逐条裁决（追加 M1 §7）——执行 `E-N1 SBL`/`E-I1 TCI`/`H-N2 A2C`，条件执行 `X-N2`（须重定义占据度），待澄清 `X-I1`，保留不执行 `E-N2`+`H-I1`（其原始目的已被 V1 达成），否决 `H-N1`/`X-N1`。③ `D-20260927-T2EN1-002`：**`E-N1 SBL` 执行失败、路线立即关闭**——两臂 `nmmd` 0.396/0.325 对基线 0.031（差 10.4–12.7 倍），根因是**全局水平与场项间无幅度控制**（z-score 回归致场项带标准差量级动态范围，总质量抬高 53%+）。两项自我订正如实记录（`log1p(expm1)` 恒等而非 softplus，**我首次诊断因此错误**；设计 τ=0.5 与目标 stage E7.5 算术不一致，正确 0.6），均非结果导向调参。**不补救**，复活须作新 lane 预声明幅度控制。④ 新增 `tests/test_t2_gates_and_sbl.py`（10 项），**全量 231 passed**。
  待办变化：新增两条待执行 lane（`E-I1 TCI`、`H-N2 A2C`，须先写设计冻结文档）；`X-N2`/`X-I1` 留待条件满足；T2 侧**无待执行的本地裁决项**（embryo 本地门已停用）。全程零候选零上传，`submissions/` 0 改动。
- 2026-09-27：**T2 验证 V1 完成（`D-20260927-T2VALIDATE-001`）**——全历史 31 条已评分候选的本地指标 vs 服务器分排名相关已实测。**结论：本地判据逐板方向不同**。`neighborhood_mmd` 在 heart_interp（−0.559）与 extrap（−0.627）有预测力，在 **embryo 强反向（+0.833）**，M0 的 5% 规则把板最佳 v0010（62.29）判成 DEGRADE。另查出 embryo 板「表达矩阵字节相同、obs 顺序与组成相同、仅 3D 坐标整体 ×1.305 膨胀、服务器 56.70→60.10（+3.4）而本地七项指标全零」的输入对——**服务器几何子分对绝对尺度敏感，本地镜像看不见**。`d2_shape` 在两个插值板均反向。原设计的「方向一致率」统计量**无效已作废**（一个板只有一条能等于最佳，必然低报）。
  待办变化：新增「heart_extrap 50.64 vs 50.53 门户复核」（已在 M0 §1 标 OPEN，需用户读门户页面，非本 agent 可完成）。
- 2026-09-27：**三项全部开工完成（用户指令「三项都开始工作」）**——① **heart_extrap 50.64/50.53 定案**（`D-20260927-T2EXTRAPAGG-001`）：决定性证据是第二个服务器 Total **157.04**（09-27，距 v0011 评分已 11 天）T2 仍为 58.29 ⇒ extrap=50.53，据此排除**舍入／最新提交／自动取最高**三种解释，结论为**服务器按已登记 per-board 选集聚合**。`registry` 的「selection updates to v0011」不成立（已订正不追溯改写）；**`INDEX.tsv` 无需改**，此前判为矛盾是误读。剩余三项待用户：换选集、TIE 边界口径、v0011 子项 skills 补齐。② **PLAN H2 修订完成**（用户授权）：假设陈述改为「失效方向与幅度逐板而异，必须逐板实测校准后方可作筛选器」，现状改为部分支持并附三项实测（Spearman 逐板、embryo 判反、3.4 分尺度杠杆），新增修订记录节。③ **`E-I1 TCI` / `H-N2 A2C` 设计冻结落盘**（`D-20260927-T2DESIGN-001`），**训练前 bracket 核对抓出一处会导致 target 泄漏的设计错误**（简报写 E8.5/E8.75 中点，三处权威来源一致显示 bracket 为 [E8.25, E8.75]、目标为 E8.5）→ 已修正并新增泄漏断言。**新发现待用户裁决**：`PLAN.md` 科学问题节写「heart 插值 E9.0」与 `BOARD_REGISTRY.yaml`/`t2_s3_shape_field.py`/`t2_j1_pairing.py` 的 **E8.5** 冲突。
  待办变化：两条 lane 由「待写设计冻结」转为「设计已冻结，待锚点核验 + 可执行」；新增一项待用户裁决（PLAN 的 heart 插值 stage 事实性订正）。

## T1 第二轮三新两优化（2026-09-28）

- [x] v0029–v0033完整实施/拟合或冻结组件复用/推断，五次完整panel官方本地scorer、16测试、五模型独立重放、包校验。reports/t1_round2_20260928/REPORT.md。
- [ ] 用户按需上传单包并回分；优先v0030，其次v0029。新五项未提交/未评分，best v0024=51.92保持，未来真值验证NOT_RUN。

## T3 三候选（2026-09-29）

- [x] v0054–v0056三路线完整执行，12测试、独立模型/contract校验、三个短名h5ad和单ZIP交付。reports/t3_three_20260929/REPORT.md。
- [ ] 按需上传回分；此前v0049–v0053仍待分，提交前核对上传状态。best v0048=47.93保持，匹配KO官方评分NOT_RUN。

## T1 三候选提交包（2026-09-29）

- [x] v0034–v0036三路线完整实现/推断、三次全panel官方scorer、13测试、独立重放与单ZIP校验。reports/t1_three_20260929/REPORT.md。
- [ ] 按需上传并回分，优先v0035；三个未提交/未评分，best保持v0029=52.50，未来真值验证NOT_RUN。
