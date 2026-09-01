# P0 · 外部数据审计与净化（一次性前置，不是评分 atom）

## 目标

只为当前 active atom 准备合规、task-scoped、可复现的 sanitized sources。完成后控制器直接继续 active atom。

## 输入

- `compliance/external_sources.tsv`
- `compliance/protected_windows.yaml`
- `compliance/target_leakage_blacklist.tsv`
- `compliance/DATA_FIREWALL_SPEC.md`
- `config/active_atom.yaml`
- `config/batch2_manifest.yaml`

## 施工

1. 解析 active atom 的 `required_sources` 与 `optional_sources`。
2. 检查已有 sanitized snapshot；hash、规则版本与过滤脚本完全匹配则复用。
3. 对缺失 source 执行 metadata-first：先获取 accession metadata、file list、license、stage/genotype/condition。
4. 生成 planned keep/remove tables；任何 ambiguous stage/genotype 先移入 remove。
5. 下载最小必要数据：
   - 优先 processed count/matrix 与 metadata；
   - 不下载与 active atom 无关的 100GB 级单细胞文件；
   - knowledge resource 冻结 release/commit；
   - software 冻结 package version/commit。
6. 混合 processed object 只允许立即 subset；在 sanitized object 写出前不计算表示或统计。
7. 运行一次 forbidden-count audit，必须为 0。
8. 输出：

```text
infra/external_data/
├── sanitized/<task>/<source_id>/...
├── manifests/<source_id>/source_manifest.json
├── reports/<source_id>__DATA_AUDIT_REPORT.md
└── AUDIT_COMPLETE.json
```

## Active atom B2-T3-A1 的最低数据

- E-MTAB-6967：WT atlas only；
- E-MTAB-11763：WT E8.5–E9.5 only；
- GSE52123：E12.5 WT heart GATA4 ChIP replicates + matched input only；
- Reactome / GO release；
- CellOracle / scTenifoldKnk code version；
- CollecTRI / OmniPath 仅在 edge/resource provenance 规则通过时准备。

## 验收

- 每个 required source 为 `PASS` 或有 prompt 指定的安全 fallback；
- forbidden records remaining = 0；
- task permit PASS；
- license 与 disclosure 字段非空；
- sanitized hash 存在；
- 不训练模型，不生成 submission。

完成后继续 active atom。只有没有安全 fallback 的硬阻塞才停止。
