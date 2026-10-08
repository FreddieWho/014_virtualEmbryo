# T3 第二波六新路线（2026-10-07）

父本 v0048 `n2hurdle`（47.93）。设计与依据：[DESIGN.md](DESIGN.md)。
源侧冻结 LOPO 协议沿用第一波（GSE261783 OP2 + 锁定 retained model +
官方 core_metrics 五分项）；未读 Gata4 目标 truth。

## 路线与结果

| 路线 | 类型 | 结果 |
|---|---|---|
| o1_hnmf | 结合（现役 v0048 ⊕ v0078 NMF，等权平均） | 交付 v0081（LOPO 仅诊断） |
| o2_pnmf | 结合（v0076 hurdle 门 × v0078 NMF） | 交付 v0082（LOPO 仅诊断） |
| o3_psb | 结合（o2 门 × o3 收缩 × v0071 乘法） | 交付 v0083（LOPO 仅诊断） |
| n1_qtl | 新机制（分位数形状迁移） | 交付 v0084，LOPO 选中 q0.25 |
| n2_dsign | 新机制（供体符号一致性门） | 交付 v0085，LOPO 选中 g0.5 |
| n3_pswap | 新机制（程序置换/质量再分配） | **源侧关闭**：identity 秩最优（2.28），三强度单调更差（2.39/2.56/2.76），无正信号，不交付候选 |

N3 关闭记录：`n3_pswap/SOURCE_CLOSED.json`；与 dir6 阶段二关闭同先例
（源侧无增量即关，不建候选）。

## 诚实限定

- O1/O2/O3 参数全部沿用第一波冻结选中值（0.5/0.5、s=0.25、s=0.5+k=2.0），
  无网格重扫；其 LOPO 行只是源侧近似诊断（O1 的源侧“现役类似物”是加性
  发射，hurdle 模型不可迁移到源侧，已声明）。
- N1/N2 供体选择规则与第一波 n3_donor 相同（GO 嵌入 argmax），
  记录在 `donor.json`。
- 本地源侧指标不等于服务器分；5 个候选 `score_pending`、未提交、
  `blocks_submission:false`；晋级门槛 > 48.03（±0.1 平局带外）。

## 复现与交付

`scripts/t3_six2/evaluate.py`（源侧 LOPO，ProcessPoolExecutor×8）+
`scripts/t3_six2/deliver.py`（交付/契约/INDEX）+ `scripts/t3_six2/package.py`
（打包）。交付包：`deliveries/t3six2__t3__upload__20261007.zip`
（5 成员：hnmf/pnmf/psb/qtl/dsign + 四表）。
