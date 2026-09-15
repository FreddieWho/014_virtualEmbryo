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
- [x] commit + push 本批改动——已推送 `c7cb36b`（Total 153.7 确认、T2-R3 关闭、closeout 七报告；大文件按惯例留本地）

## 分支记录

- **当前执行分支**：无（batch4 已封板，2026-09-15）—— Total 153.7 已确认；T2-R3 按用户决定关闭不评分；判定 ARCHITECTURE_RESET_REQUIRED；新架构另行立项。
- **并行分支**：无。
- **暂缓分支**：
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
