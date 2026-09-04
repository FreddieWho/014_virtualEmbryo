# TODO — 当前待办（用户与 agent 共读唯一入口）

按执行顺序排列，重要的在前。建立日期：2026-09-04。

- [x] 用户读服务器页面，提供最新 Total/T3 读数——服务器确认 Total=**151.2**，精确 board 48.47/60.15/57.25/50.53/46.79，33 个子项分数已入库
- [ ] 授权 commit + push 本轮改动（P0 产物、分数回填、coordinator 补丁）
- [x] 决定做 T1 n=1,706 探针——已生成候选 v0010（2026-09-04 夜，用户明确授权）
- [x] 用户手动上传 `deliveries/b4p0p2__t1__upload__20260904.zip` 并回填分数——v0010=46.8（2026-09-04 19:09 行）
- [ ] 授权 Wave 1：`B4-T2-R1-FGW-ASSIGNMENT-REPAIR`（服务器先验最强，优先）、`B4-T1-R1-CONSERVATIVE-FAMILY`、`B4-T3-R1-GENOTYPE-ONLY-ABLATION`（对比基准 46.8）

## 分支记录

- **当前执行分支**：batch4 P0（B4-P0-STATE-FLOOR-PARITY）已完成，等待 floor 探针分数；batch4 已由用户授权（2026-09-04）。
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
