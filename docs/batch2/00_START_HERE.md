# Virtual Embryo Challenge · Batch 2 外部数据驱动原子优化包

版本：2026-08-29  
适用阶段：Batch 1 已关闭、第一次服务器反馈已取得、进入 P2 多路线优化  
默认入口：`01_CODEX_CONTROLLER_PROMPT.md` + `config/active_atom.yaml`

## 一句话结论

Batch 1 的主要问题不是代码链路，也不是模型容量不足，而是 **T1 与 T3 缺少决定隐藏答案的外部信息**：

- T1 仅凭官方 E8.5、E9.5，无法可靠知道 E10.5/E12.5 将出现哪些状态与发育程序；
- T3 仅凭 Mab21l2 KO，无法可靠推出 Gata4 或 β-catenin KO 的基因特异方向；
- 因此 Batch 2 不再优先更换网络骨干，而是先建设可审计的外部信息层，再把信息以低自由度方式写入可提交分布。

## 这批实际施工什么

| 顺序 | Atom | 核心信息缺口 | 最终产物 | 状态 |
|---|---|---|---|---|
| 1 | `B2-T3-A1` | Gata4/Gata6 的有符号、谱系特异响应 | 1–2 个 T3 Gata4 可提交 `.h5ad` | READY，默认激活 |
| 2 | `B2-T1-A1` | 统一状态词表与允许的晚期发育程序 | 2 个 T1 E10.5 可提交 `.h5ad` | READY |
| 3 | `B2-T1-A2` | 允许数据上的稠密时间转移规律 | 2 个 T1 E10.5 可提交 `.h5ad` | READY，依赖 A1 |
| 4 | `B2-T3-A2` | 扰动响应的稀疏度、幅度与异质性 | 1–2 个 T3 可提交 `.h5ad` | CONDITIONAL |
| 5 | `B2-T1-C1` | 状态支持与时间动力学的组合 | 1 个 T1 可提交 `.h5ad` | CONDITIONAL |
| — | `B2-T2-X1` | 外部空间形态先验 | T2 可提交 `.h5ad` | BLOCKED，需书面澄清 |

`P0_DATA_AUDIT_AND_INGEST` 是一次性合规前置步骤，不是评分 atom。控制器在执行第一个 atom 前自动完成 P0；P0 本身不占用一个优化循环。

## 交给 Codex 的方式

把本目录放入项目仓库，例如：

```text
docs/batch2_external/
```

然后给 Codex：

1. `01_CODEX_CONTROLLER_PROMPT.md`
2. `config/active_atom.yaml`

默认配置会：

1. 检查现有仓库与 Batch 1 canonical parent；
2. 仅下载并净化 `B2-T3-A1` 必需的数据；
3. 施工 `B2-T3-A1`；
4. 生成可人工上传的预测文件；
5. 写完结果后停止，不自动上传服务器。

## 不可违背的边界

- 外部源必须登记在 `compliance/external_sources.tsv`，并且对当前 task 状态为 `ALLOW` 或 `ALLOW_FILTERED`。
- 含保护阶段/基因型的数据集必须在任何训练、embedding、统计汇总之前完成样本/细胞过滤。
- 未知训练语料的基础模型默认禁止使用。
- 不得把 T1 允许的数据自动复用于 T2；许可是 **task-scoped**，不是 dataset-scoped。
- 不得用服务器分数反推目标属性；服务器只用于候选选择。
- 每个 atom 只允许一次小型功能检查、每 lane 一次完整生成、每 lane 一次最终本地 scorer。
- 不做网格搜索，不重搭工作台，不重写已经存在的 validator、scorer、registry 和 submission builder。

## 每个 atom 的固定结束面

```text
artifacts/atomic_batch2/<ATOM_ID>/
├── submissions/<board>/<lane>/prediction.h5ad
├── metrics/local_score.json
├── metrics/protected_checks.json
├── DATA_SOURCES_USED.tsv
├── METHOD_DISCLOSURE.md
├── config_resolved.yaml
├── MANIFEST.json
├── RESULT.md
└── run.log
```

只允许四种结论：

- `READY_FOR_MANUAL_SUBMISSION`
- `HOLD_AS_COMPONENT`
- `REJECT`
- `BLOCKED_COMPLIANCE`

只要形成了满足 contract 的候选，无论本地结果好坏，本 atom 即结束。不要继续“顺手再调一点”。
