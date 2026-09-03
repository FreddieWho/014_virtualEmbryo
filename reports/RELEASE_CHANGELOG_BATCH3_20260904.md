# Batch 3 收尾与发布变更日志

发布日期：2026-09-04  
配套评审报告：`reports/PHASE_REPORT_BATCH3_20260904.md`（范围、方法与结论以该报告为准；本文件只记发布面的审计与变更）。

## 1. 发布范围

Batch 3（`docs/batch3/`，执行窗口 2026-08-30 至 2026-09-04）全部计划任务收尾：T3-S1 链（PRIOR/S1A/S1B/S1C/S1D/可满足性审计/收口）、T1-PRE-HARMONIZE、T1-S2-MOSCOT-DECODER、T2-S3-SHAPE-FIELD、T2-J1-PROXY、T2-J1-FGW-ASSIGNMENT、HX-DYNAMICS-KILLTEST。

## 2. 已完成更新

- 服务器评分回填三轮：T1-S2（v0007=44.9、v0008=44.8）、T2-S3（embryo 59.7、heart_interp 56.7）、T2-J1（heart_interp v0009=57.3）；均登记 `reports/SERVER_SCORE_REGISTRY.md` 与 `submissions/INDEX.tsv`，登记前后候选 SHA256 不变。
- 当前 selection 变更两处：heart_interp 56.3 → 56.7（T2-S3 L1）→ 57.3（T2-J1 v0009 `j1_fgw_assignment`）。
- 上传命名规则固化：成员名 ≤50 字符短码规则 + 包内 MANIFEST.tsv；写入 `AGENTS.md` 与 `submissions/README.md`；三个人工上传包均按规则（T1-S2 包为规则前旧长名，保留不重打）。
- 新增隔离环境两个并审计：`.venvs/ve-t1-ot`（moscot 0.5.2 等）、`.venvs/ve-hx-mioflow`（mioflow 0.1.14，torch 2.2.2+cpu，**Yale 非商业许可**已披露；wheel/sdist SHA256 核验、56 包依赖快照）。
- 文档体系建立（2026-09-04）：根目录 `PLAN.md`、`ROADMAP.md`、`TODO.md`、`LEADS.md`、`DECISIONS.md`（薄入口，权威存档仍为 `docs/coordination/DECISIONS.md`）；根 `STATUS.md` 增加"给人读的进展 + 偏离评估 + agent 接手信息"两部分结构。
- `docs/coordination/DECISIONS.md` 只追加补齐本批决策：D-20260903-T2-S3-001、D-20260903-NAME-001、D-20260904-T2-J1-001、D-20260904-HX-001。

## 3. 审计结果

- 各 atom stable manifest 自校验全部 PASS（T1-PRE 15、T1-S2 44、T2-S3 157、J1-PROXY 46、J1-FGW 40、HX 18 文件；T3 链各版本此前已核验）。
- 测试基线：103 → 148 → 162 → **174 passed**（2026-09-04 全量复跑，`PYTHONPATH=docs/batch3/interfaces`）。
- 候选完整性：INDEX 登记 SHA256 与磁盘文件一致（本批新候选 v0006–v0009 抽查匹配；上传包成员 SHA 与 INDEX 一致）。
- 无泄漏声明复核：本批全部候选 `target_used=false`；HX 部署后计算阶段网络关闭；E8.5–E9.0 窗口数据未用于任何候选生成。

## 4. 当前冻结决定

- 关闭路线（不再投入）：T1-S2 moscot 外推、HX MIOFlow 增长/死亡、T2-S3 L2 spateo、T2 heart_extrap 位移场、T3-S1 链（重开条件见 `artifacts/tool_integration/T3-S1-CLOSURE-20260902-v1/CLOSURE_REPORT.md` §6）。
- 保留待授权：LEADS L-001（embryo v0008 同靶参照闭环）、L-002（FGW ε 敏感性，batch4 首选）。
- 已评分 artifact 全部不可变；HOLD/REJECT 候选原路径保留作失败诊断。

## 5. 保留的验证缺口

- 服务器页面自单 board 提交后未重读：derived T2≈55.97 / Total≈149.8 未确认，任何文档不得引用为服务器值。
- embryo v0008 缺同靶 parent scorer 参照（L-001 未执行）。
- J1-FGW 的高 conflict 率（72–73%）未做敏感性分析（L-002 未授权）。

## 6. 收尾后的唯一入口

- 项目状态：`STATUS.md`；待办：`TODO.md`；探索线索：`LEADS.md`。
- 候选/分数权威：`submissions/INDEX.tsv`、`reports/SERVER_SCORE_REGISTRY.md`。
- 决策日志：`docs/coordination/DECISIONS.md`；任务级追踪：`docs/coordination/T{1,2,3}_TRACKING.md`。
