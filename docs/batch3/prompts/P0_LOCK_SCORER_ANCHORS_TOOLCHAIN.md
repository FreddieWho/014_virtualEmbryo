# P0-LOCK · 锁定 scorer、parent、board 与工具链

## 唯一目标

在生成任何新候选前，把“比较基准到底是什么”变成不可歧义的机器可读锁。P0 不训练模型、不下载外部数据、不生成候选。

## 必须完成

### 1. 仓库发现

定位并记录：

- 当前 repo commit / dirty status；
- scorer、contract validator、submission builder；
- `reports/SERVER_SCORE_REGISTRY.md`；
- `submissions/INDEX.tsv`；
- Batch 1 phase report；
- 预计 T1/T2/T3 current parent；
- `docs/batch2_external/`、`artifacts/atomic_batch2/` 和 data audit；
- 当前 state label/latent、T1 full-panel scorer 入口。

运行 `scripts/repo_preflight.py`，结果写入当前 artifact。

### 2. Scorer lock

对每个 task 记录：

- scorer 文件路径与 SHA256；
- Python/R/容器版本；
- 完整命令行；
- 输入 contract；
- board/setting 参数；
- 输出字段和显示精度；
- 与官方当前 Evaluation 文案的差异。

至少对 current parent 完成一次可重复读取/评分。若无法评分，必须区分：缺 truth、缺依赖、contract 失败、版本不匹配。

### 3. Parent lock

从 `SERVER_SCORE_REGISTRY.md` 和 `INDEX.tsv` 解析 current selection，而不是只相信旧报告。对每个 board：

- candidate ID；
- canonical path；
- SHA256；
- contract status；
- scorer snapshot；
- server score（若登记）；
- 使用理由。

验证旧报告预期：T1 strict pseudobulk、T2 board-specific scale winner + extrapolation parent、T3 wt_identity。若不一致，以 registry 为准并记录差异。

### 4. T1 full-panel scorer

必须尝试一次：

- 使用 current T1 parent；
- 完整官方 gene order；
- 当前 scorer bundle；
- 输出完整 metrics 与日志。

若无法完成，P0 结论为 `BLOCKED_VALIDATION`。禁止后续 T1 正式候选。

### 5. Batch 2 复用审计

若已有 Batch 2：

- 读取 manifest；
- 校验 sanitized input 和中间产物 hash；
- 标记可复用的 `state_vocabulary/crosswalk/prior votes/evidence/operator`；
- 记录其 scorer/contract snapshot；
- 不重复下载。

### 6. Toolchain smoke inventory

只做检测和轻量 smoke，不进行重型安装：

- core：anndata/scanpy/numpy/scipy；
- T1：moscot/POT/WOT/scDesign3 是否存在；
- T2：pycpd/Spateo/POT/GeomLoss；
- T3：decoupler/CollecTRI/OmniPath/CellOracle/scTenifoldKnk/Pertpy。

对缺失工具写出隔离环境安装计划。P0 不因 Spateo/CellOracle 未安装而失败；但必须知道后续如何安装且不污染 core。

## 输出

```text
artifacts/tool_integration/P0-LOCK/
├── discovery/repo_inventory.tsv
├── discovery/preflight_report.json
├── locks/SCORER_LOCK.json
├── locks/PARENT_REGISTRY.yaml
├── locks/BOARD_REGISTRY.yaml
├── locks/TOOLCHAIN_LOCK.json
├── locks/BATCH2_REUSE_REGISTRY.tsv
├── metrics/parent_reproduction.json
├── metrics/t1_full_panel_score.json
├── BLOCKERS.md
├── config_resolved.yaml
├── MANIFEST.json
├── COMPLETION_REPORT.md
├── RESULT.md
└── run.log
```

## 通过条件

- scorer/contract 和 parent 均已 hash 锁定；
- board registry 可解析；
- T1 full-panel scorer 通过，或明确 `BLOCKED_VALIDATION`；
- Batch 2 复用项已登记；
- 工具环境计划已写出。

## 停止

写完 `RESULT.md` 后停止。不要自动启动 T3 或 T1。
