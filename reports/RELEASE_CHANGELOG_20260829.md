# Batch 1 收尾与发布变更日志

日期：2026-08-29  
发布状态：`CLOSED_FOR_REVIEW`  
范围：Batch 1 结果对齐、外部评审交付和下阶段入口冻结

## 1. 发布范围

本次收尾覆盖 B1-A1、B1-A2、B1-A3、B1-A4 的最终候选、服务器评分登记、当前选择、阶段状态和评审文档。没有重新生成表达矩阵、坐标、候选 H5AD 或服务器分数。

## 2. 已完成更新

### 2.1 结果和状态对齐

- B1-A2 `RESULT.md` 从 `SCORE_PENDING` 对齐为 `SCORED`；两条候选标记为已评分但不晋级，保留诊断。
- B1-A2 `FINAL_SET_MANIFEST.json` 从 `score_pending` 对齐为 `complete`，并补充 `server_score_count=2` 和 `server_score_status=complete`。
- B1-A1、B1-A3 的最终集清单补充服务器评分完成计数；没有写入具体服务器分数或 ID，避免复制权威 registry。
- `docs/batch1/config/active_atom.yaml` 清除 active atom，设为 `CLOSED_FOR_REVIEW`，防止无授权重启 B1-A4。
- `docs/batch1/04_FILE_INVENTORY.md` 修正过期的“当前为 B1-A2”说明。

### 2.2 新增交付文档

- `reports/PHASE_REPORT_BATCH1_20260829.md`：面向外部评审的综合过程、结果、失败线索和后续方案报告；不含外部引用。
- `reports/RELEASE_CHANGELOG_20260829.md`：本次审计、修正和冻结动作记录。

## 3. 审计结果

- Batch 1 正式候选数：16；A1/A2/A3/A4 分别为 6/2/2/6。
- 服务器评分登记：16/16。
- `submissions/INDEX.tsv` 中 B1-A1 至 B1-A4 的 16 个 canonical 文件 SHA256：16/16 匹配。
- 四份 `FINAL_SET_MANIFEST.json`：全部可解析；最终候选数量与计划一致。
- 已评分 artifact：未覆盖、未重命名、未静默替换。
- 新增外部生信数据：无，因此不触发 `infra/bioinf-data-index/` 更新。

## 4. 当前冻结决定

- 当前 aggregate 保持服务器返回的 149.5；T1/T2/T3 保持 48.5/55.7/45.3。
- T2 继续使用 B1-A1 L1 的两个 interpolation board 与 baseline heart extrapolation 的 per-board selection。
- B1-A2 两条候选不晋级；B1-A3 两条候选不替换 T1 v0004；B1-A4 六条候选不晋级。
- B1-C1 不执行，因为 A4 的 immediate parent 已携带 A1 scale 或 identity scale，重复组合不增加独立候选。
- 无 active atom；新 atom、下一批或任何新服务器提交均需用户明确授权。

## 5. 保留的验证缺口

- A3 locked full-panel local scorer 曾超时/中断，未使用替代 scorer；其服务器成绩可用于竞争决策，但本地证据不完整。
- 部分上传记录缺少用户提供的 submission ID；未推测或伪造。A4 成绩按人工上传包文件名映射。
- 仓库尚无 initial Git commit，完整复现缺少统一 commit anchor。
- 科学 promotion 仍为开放但受限状态；Batch 1 分数不构成因果或生物学机制证据。

## 6. 收尾后的唯一入口

外部评审先读 `reports/PHASE_REPORT_BATCH1_20260829.md`，再按其中的内部证据定位审查 `reports/SERVER_SCORE_REGISTRY.md`、`submissions/INDEX.tsv` 和四个 atom 结果目录。除非获得新授权，不再从 `docs/batch1/config/active_atom.yaml` 激活 atom。
