# 外部数据防火墙规范

## 1. 目录

```text
infra/external_data/
├── registry/
│   ├── external_sources.tsv
│   ├── protected_windows.yaml
│   └── target_leakage_blacklist.tsv
├── quarantine/<source_id>/
├── sanitized/<task>/<source_id>/
├── manifests/<source_id>/
├── reports/
└── AUDIT_COMPLETE.json
```

`quarantine/` 中的文件不得被训练、embedding、聚类、pseudobulk、marker 或任何统计模型读取；它只允许 metadata inspection 与立即过滤。

## 2. Metadata-first

每个 source 先下载：

- accession/series metadata；
- sample/cell metadata；
- file list、size、checksum；
- license/terms；
- publication与 stage/genotype 描述。

在大矩阵下载前生成 `planned_keep_samples.tsv` 与 `planned_remove_samples.tsv`。

## 3. Task-scoped permit

实现一个单一入口：

```text
permit(source_id, task, board=None)
```

它必须验证：

- source 状态；
- allowed_tasks；
- task/board stage window；
- genotype/perturbation blacklist；
- organizer clearance（若 status=CONDITIONAL）；
- license。

同一 sanitized 文件不得用软链接绕过 task 许可。每个 task 写独立 manifest。

## 4. 阶段过滤

- 将 `E8.75`、somite stage、Theiler stage 转成统一浮点 embryonic day；
- 原始文本和转换值同时保存；
- 落在边界或转换区间跨越边界时，状态为 `AMBIGUOUS_BLOCKED`；
- T1 严格执行：`stage <= 9.5 OR stage > 13.5`；
- GSE193346 只允许 `9.5` 与 `>=14.5`，不因为缺少某个 exact day 而放宽；
- 不从连续 trajectory/embedding 中“删除标签但保留已经看过保护细胞的模型”。任何表示必须在 sanitized data 上重训。

## 5. 基因型与 perturbation 过滤

- 明确 WT 才可进入 T1/T3 context data；
- chimera、mutant、drug、CRISPR、KO、KD、OE 等条件默认不进入，除非 source 在当前 atom 中明确允许；
- generic Perturb-seq 必须先运行 `target_leakage_blacklist.tsv`；
- 任何可能 phenocopy 的 perturbation 由人工可审计规则删除，而不是交给模型自行判断；
- 不使用 Gata4/Gata6/Ctnnb1/Mesp1 及 conservative pathway/family blacklist。

## 6. Processed object 含混合阶段时

允许的唯一处理：

1. 读取 metadata；
2. 立即构造布尔 mask；
3. 在同一进程中只写出允许 cells/features；
4. 不计算 PCA、neighbors、normalisation statistics、HVG 或 marker；
5. 写出 sanitized object；
6. 后续所有模型只读取 sanitized object。

保存：

- raw object hash；
- mask 逻辑；
- kept/removed count by stage/genotype；
- sanitized hash；
- script hash。

## 7. Knowledge graph 与 ChIP

- ChIP peak 只提供 directness，不提供调控符号；
- 聚合 GRN edge 必须记录 upstream resource；
- strict lane 排除无法证明不来自 target perturbation/phenocopy 的 edge；
- Reactome/GO 可用于 pathway/module membership，不可被包装成 context-specific effect truth；
- OmniPath/CollecTRI 使用 academic-license filter，并冻结 snapshot。

## 8. 预训练模型

每个 checkpoint 必须有：

- corpus manifest；
- stage/genotype metadata；
- protected sample removal proof；
- license；
- checkpoint hash。

缺任意一项即禁止。模型名称或论文声明“trained on public data”不构成证明。

## 9. 最小审计

每个 sanitized source 只运行一次：

- cells/samples by stage；
- cells/samples by genotype/condition；
- forbidden count 必须为 0；
- allowed gene overlap；
- file hash。

不做冗余 QC 图或完整生物学分析。

## 10. 完成标志

`AUDIT_COMPLETE.json` 至少含：

```json
{
  "rules_snapshot": "2026-08-29",
  "task": "T3",
  "active_atom": "B2-T3-A1",
  "sources": {
    "GSE52123": {"status": "PASS", "sanitized_sha256": "..."}
  },
  "forbidden_records_remaining": 0
}
```
