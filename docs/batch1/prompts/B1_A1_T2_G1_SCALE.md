# B1-A1 — T2 G1 组织尺度校准：双 lane

## 唯一目标

只优化 T2 的组织尺度原子 G1，使预测点云在目标阶段达到更合理的 RMS 半径，从而改善 TSR。B1-A1 的最终结果固定为两条 lane × 三个 board，共 6 个候选；不得改变表达矩阵、点云归一化形状、点间相对结构或表达-坐标配对。

## 为什么这是独立原子

官方 TSR 使用点云相对质心的 RMS 半径。对全部坐标做同一个正标量缩放：

- 改变 TSR；
- 不改变归一化后的 SDD/ODS；
- 不改变 15-NN 邻接关系，因此原则上不改变 NFS；
- 不改变任何表达指标。

## 输入

从现有工作台自动定位：

1. 已通过格式检查的 T2 base submission；
2. 对应 setting 的已观测训练阶段坐标；
3. stage time 与 board/target 定义；
4. 当前官方 validator/scorer。

分别处理当前工作台支持的 heart 和 embryo board；不得混用两者的尺度曲线。最终 board 固定为 `T2_embryo_val_interp`、`T2_heart_val_interp`、`T2_heart_val_extrap`。

## 最终 lane

- `L1_FORMAL_LOG_RMS`：严格执行既定的分段 `log(RMS)` 插值与最后相邻阶段斜率外推规则。
- `L2_ALL_STAGE_LOG_RMS_OLS`：对同一组织的全部观测训练阶段，以阶段时间为自变量、`log(RMS)` 为因变量做等权 OLS；直接预测目标阶段。

两条 lane 的公式在最终生成前固定，不根据 local proxy、服务器分数或排行榜反馈调节。临时探索最多 4 次全局尝试，每次必须覆盖三个 board，且不构成第三条 lane。

## L1 算法：严格 `log(RMS)` 插值/外推

对每个 setting 独立执行：

目标阶段固定为：embryo E7.5（E7.25/E8.0 之间）、heart interp E8.5（E8.25/E8.75 之间）、heart extrap E10.5（使用 E8.75/E9.5 末段斜率）。`E8.25_late` 按数值阶段 8.25 使用。

1. 对每个已观测阶段，计算
   `rms(t) = sqrt(mean(||C_i - centroid(C)||^2))`。
2. 在 `log(rms)` 空间估计目标阶段尺度：
   - 目标处于两个观测阶段之间：做严格线性插值；
   - 目标晚于最后阶段：使用最后两个阶段的 log-slope 外推；将 slope 截断到该 setting 所有相邻观测 slope 的最小值与最大值之间；若只有一个可用 slope，则直接使用它；
   - 不做参数搜索，不读取 target 坐标。
3. 计算 base prediction 的 `r_pred`，得到唯一缩放因子：
   `scale = exp(log_r_target) / r_pred`。
4. 中心化坐标后统一乘以 `scale`。输出可以以零质心保存，因为官方空间指标忽略平移；若现有 pipeline 依赖原质心，则恢复原质心。
5. 表达矩阵、obs 顺序、var 顺序和表达-坐标行配对必须完全不变。

## L2 算法：全阶段 `log(RMS)` OLS 趋势

1. embryo 使用 E6.75、E7.25、E8.0；heart 使用 E8.25_late、E8.75、E9.5。每个阶段先独立计算上面的 centroid-centered `rms(t)`。
2. 对每个 setting 以阶段时间为自变量、`log(rms(t))` 为因变量做等权 OLS：`log(rms) = a + b * stage`；在固定目标阶段计算 `log_r_target = a + b * stage_target`。
3. 以同一 base prediction 的 `r_pred` 计算 `scale = exp(log_r_target) / r_pred`，然后使用与 L1 完全相同的纯 uniform scaling 和不变量检查。
4. L2 不读取 target 坐标，不使用 hidden target、排行榜反馈或服务器分数；它是预先固定的第二条最终路线。

## 只允许的检查

1. 每次临时尝试和每条最终 lane 都必须确认缩放前后表达 checksum 相同；15-NN 图在无距离并列情况下完全一致，存在并列时只记录差异。
2. 最多 4 次全局临时 source-only 尝试；每次必须覆盖三个 board，输出单独记录，不进入最终候选目录。
3. 两条最终 lane 各生成三个 board 文件；每个文件只做一次固定 public pseudo-holdout 本地 scorer，并由用户人工进行一次线上评分。
4. 每个最终文件生成 `scale_model.json`、指标 JSON、protected checks 和 manifest；根目录生成列出 6 个文件的 `FINAL_SET_MANIFEST.json`。

## 验收

必须满足：

- 六个最终文件分别通过官方 contract；
- `X`、obs/var 顺序和表达-坐标配对完全不变；
- SDD/ODS/NFS 与 base 的差异只允许为数值误差，且记录原始 scorer key；
- 生成每个 board 的 `prediction.h5ad`、`scale_model.json`、指标 JSON 和 MANIFEST，以及根级 `FINAL_SET_MANIFEST.json` 与 RESULT。
- 只要 contract 和不变量通过，两个 lane 的 `recommend_submit` 都为 `true`；local TSR 不改善时仍提交并等待真实服务器分数。

若某个文件的 contract 或不变量失败，才将对应 board 标记为 `REJECT`；不得用失败结果静默替换 lane，也不得为追求更好 TSR 追加第三条最终 lane。

## 禁止

- 禁止学习坐标 MSE；
- 禁止形变、旋转、局部缩放或点云重采样；
- 禁止顺手优化 G2/G3/J1；
- 禁止对 target score 反复调 scale；
- 禁止自动线上提交；人工上传前必须完成当前官方配额预检。
