# B2-T1-C1 · 状态支持与时间动力学机械组合

## 激活条件

- B2-T1-A1 与 B2-T1-A2 均完成；
- 至少一个 atom 在主分项或服务器分数上有正信号；
- 两者 candidate、config、hash 已冻结。

## 唯一目标

检验 A1 的 state support 与 A2 的 expression operator 是否能在不重新训练的情况下兼容。C1 不下载数据、不重新拟合、不调参。

## 组合规则

1. state vocabulary、admission、mass plan 来自 A1 选定 lane；
2. matched existing states 的 program delta 来自 A2 选定 lane；
3. late/open-set state 使用 A1 prototype，再应用 A2 同 lineage 的有限 delta；
4. residual bank 与 full-panel background仍来自官方 parent；
5. shrinkage 取 A1/A2 已冻结值中更保守者；
6. 不重复叠加相同 delta；
7. cell count、gene order 与 parent contract 保持。

## 输出

一个：

```text
artifacts/atomic_batch2/B2-T1-C1/submissions/T1_val/L1_MECHANICAL_COMPOSE/prediction.h5ad
```

附 `composition_trace.tsv`，逐模块说明每个 cell/gene 修改来自 A1 还是 A2。

## 停止

一次生成、一次 local score后停止。即使组合不如单组件，也不重新权重。
