# B2-T2-X1 · 外部空间形态预训练（默认禁止）

## 状态

`BLOCKED_PENDING_ORGANIZER`。没有书面许可不得运行、下载或预处理 MOSTA 等外部 spatial data。

## 激活后唯一目标

在保留 Batch 1 board-specific G1 scale winner 的前提下，仅改善：

- G2：占据形状 / ODS；
- G3：内部距离几何 / SDD。

不重新做通用 expression-coordinate pairing，不以外部数据优化 NFS。

## 数据

- 只使用组织者书面明确允许的 stage；
- 默认 source 为 MOSTA；
- 所有保护 stage 在任何表示学习前删除；
- 2D sagittal sections 与 3D MERFISH 的 modality gap 必须显式建模；
- 不从有限切片重建或逼近 held-out embryo/heart truth。

## 方法

1. 从允许 stage 提取 scale-normalized tissue/heart mask 与 pairwise-distance statistics；
2. 学习低维 shape basis，而不是 absolute coordinates；
3. 将 basis 作为 current T2 parent 的小幅 shape residual；
4. uniform scale 保持当前 winner；
5. translation/rotation irrelevant；
6. 一次 board-specific candidate。

## 输出

每个获准 board 一个 submit-ready `.h5ad`，并附 organizer clearance 原文。

## 停止

一次生成与评分。若没有书面许可，输出 `BLOCKED_COMPLIANCE` 报告，不产生伪候选。
