# T3 六新路线（2026-10-06）

父本 v0048 `n2hurdle`（47.93）。设计与依据：[DESIGN.md](DESIGN.md)。
源侧冻结 LOPO 协议沿用既有批准的 GSE261783 OP2 + 锁定 retained model +
官方 core_metrics 五分项；未读 Gata4 目标 truth。

## 源侧开发 LOPO 选中参数（历史 test 仅诊断）

| 路线 | 类型 | 选中 | 均值加权秩（该方法=保留值） |
|---|---|---|---|
| o1_dual_form | 结合（v0070×v0071） | sm0.25_sa0.5 | 见 SELECTION.json |
| o2_gate_mult | 结合（v0048门×v0071） | s0.5 | 见 SELECTION.json |
| o3_shrunk_beta | 优化 v0071 | k2.0 | 见 SELECTION.json |
| n1_nmf_ablation | 新机制 | s0.25 | 见 SELECTION.json |
| n2_marker_gate | 新机制 | s2.0 | 见 SELECTION.json |
| n3_switch_emit | 新机制 | s0.5 | 见 SELECTION.json |

候选：v0075（o1）、v0076（o2）、v0077（o3）、v0078（n1）、v0079（n2）、v0080（n3）。
v0073/v0074 是 aborted deliver 重试的 O1 同参数副本，score_status 置
invalidated_unsubmitted、artifact 保留不动。所有 6 个候选 contract PASS、
`score_pending`、未提交、`blocks_submission:false`。

## 机制差异的诚实限定

- O2 的源侧选择用密度 proxy 门（ctrl 阳性率），交付用 v0048 锁定
  Hurdle probability 作为门；源-胚胎门不等价，已在 DESIGN 声明。
- N3 的交付开关率用最 GO 相似供体条件（Gata4 不在来源条件表中），
  声明在 `n3_donor.json`。
- 本地源侧指标不等于服务器分；本候选未回分不得宣称晋级。

## 复现

`scripts/t3_six/evaluate.py`（源侧 LOPO，ProcessPoolExecutor×8，约 1.5h）+
`scripts/t3_six/deliver.py`（交付/契约/INDEX）；中间产物在
`reports/t3_six_routes_20261006/<route>/` 与 `artifacts/t3_six_routes_20261006/`。

## 交付包（2026-10-07 打包）

[ZIP](../../deliveries/t3six__t3__upload__20261006.zip)：6 个成员（短名 o1dual/o2gate/o3shrink/n1nmf/n2marker/n3switch）+ MANIFEST/UPLOAD_MANIFEST/RUN_ID_MAP/EVIDENCE 四表；回执 `deliveries/t3six__t3__upload__20261006.zip.receipt.json`，状态 READY_NOT_SUBMITTED。身份核验以 INDEX.tsv SHA256 为准；v0073/v0074 副本不在包内。

## 服务器回分（2026-10-07）

v0075=46.73、v0076=47.31、v0077=47.43、v0078=47.93、v0079=47.40、v0080=46.82。对照现役 v0048=47.93：v0078（N1 NMF 程序消融）同分，平局带内现役留下；其余 5 个 NOT_PROMOTED。六路线无一晋级，全部关闭；原样五分项与子项登记见 [SERVER_SCORE_REGISTRY.md#t3-six-score-return-20261007](../SERVER_SCORE_REGISTRY.md#t3-six-score-return-20261007)。D-20261007-T3SIXSCORE-001。
