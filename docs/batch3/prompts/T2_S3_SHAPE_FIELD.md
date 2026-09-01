# T2-S3-SHAPE-FIELD · 冻结 G1 与表达，只改 G2/G3

## 唯一目标

在每个 board 的锁定 parent 上，只改变 3D geometry 的占据形状与内部距离结构：

- 主要原子：G2/ODS、G3/SDD；
- 受保护：G1/TSR、表达分布、表达行顺序、主动 J1 pairing；
- 两条 lane：pycpd 与 Spateo。

本 task 不重新拟合 Batch 1 G1，不做 expression-coordinate permutation，不引入外部 spatial target。

## 前置

- P0 的 board-specific parent 与 G1 RMS lock；
- 当前 T2 scorer/contract；
- 对每 board 的 regime：interpolation 或 extrapolation；
- 可访问相邻观测阶段的官方 3D point clouds。

## 坐标原则

- 每个胚胎是局部 frame；
- 先中心化，必要时使用内部距离/主轴作诊断；
- 不以绝对坐标或 atlas frame 为目标；
- 形变后重新中心化并恢复锁定 RMS；
- 最终 `X`、obs/var、表达行顺序与 parent 完全相同。

## Source-only pseudo-holdout

### Interpolation

在存在两端观测的训练阶段构造 leave-middle-out：

- 以前后阶段估计形变场；
- 预测中间阶段；
- 用 ODS/SDD-like proxy 与当前 scorer 可用实现比较；
- 时间系数由实际 stage distance 解析给出。

### Extrapolation

用较早连续阶段预测下一个已观测阶段：

- 只使用 endpoint 邻域 field；
- 外推系数与收缩预先固定；
- 不复用插值 scale slope；
- 若没有合法 holdout，明确减少结论强度。

## 两条 lane

### L1_PYCPD

1. 对 subsampled landmarks 做 rigid/affine 初始化；
2. 进行 Gaussian-regularized non-rigid CPD；
3. interpolation 使用前后双向 field 的时间加权/对称组合；
4. extrapolation 使用 endpoint field + 强收缩；
5. 将 field 插值传播到全点云；
6. 重新锁 RMS；
7. 不修改表达。

### L2_SPATEO

1. 将观测阶段转换为最小 Spateo 需要的数据对象；
2. 使用其 alignment/morphometric vector field 估计 stage transition；
3. interpolation 与 extrapolation 使用不同配置；
4. 只导出 landmark displacement/field，不让 Spateo 写最终 H5AD；
5. core 应用 field、中心化、锁 RMS；
6. 不做生态位 assignment。

若 Spateo 安装/API 构成硬阻塞：L1 仍完成；L2 标记 `BLOCKED_TOOLCHAIN`。不得用另一包临时替代并仍称为 Spateo lane。

## 几何选择与 protected checks

必须记录：

- RMS before/after 与 locked target；
- point-cloud center；
- internal distance distribution；
- occupancy/voxel proxy；
- kNN overlap 与 topology distortion；
- field displacement quantiles；
- self-intersection/极端离群点检查；
- `X`、obs、var、gene order 的 hash 不变。

形态 proxy 改善但 kNN topology 灾难性变化时只能 `HOLD` 或 `REJECT`，不能因 ODS/SDD proxy 好看就自动提交。

## 正式生成

对每个当前 T2 board：

- 以该 board 的锁定 parent 为输入；
- 每 lane 一次；
- G1 scale 恢复到 P0 tolerance；
- 完成 contract 与一次 local scorer/proxy；
- 输出完整 candidate。

## 输出与停止

每 board 两条 H5AD，加：

```text
intermediates/<board>/<lane>/source_landmarks.npy
intermediates/<board>/<lane>/predicted_landmarks.npy
intermediates/<board>/<lane>/displacement.npy
intermediates/<board>/<lane>/field_meta.json
metrics/<board>/<lane>/geometry_checks.json
metrics/pseudoholdout_report.json
```

完成后停止。不得自动进入 J1。
