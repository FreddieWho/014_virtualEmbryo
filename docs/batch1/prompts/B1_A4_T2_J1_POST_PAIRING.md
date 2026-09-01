# B1-A4 — T2 J1：表达-坐标后配对优化

## 唯一目标

固定预测表达行集合和预测三维点云，只重新排列“哪一行表达放在哪一个坐标点上”，使 15-NN 局部邻域表达更符合公开训练阶段学到的生态位规律，从而改善 NFS。

本原子固定两条最终 lane，覆盖三个 board，共六个必须分别人工评分的候选：

- `L1_LATENT_KNN10`：表达 latent 近邻的保守重配；
- `L2_STATE_HASH10`：父本 `celltype` 内的确定性长程重配。

两条 lane 共享模型、目标函数、初始排列、seed 和 proposal 上限，唯一差异是交换候选集。不得根据 local proxy 或服务器反馈取消第二条 lane。

## 父版本与谱系

| board | immediate parent | pre-A1 root | 说明 |
|---|---|---|---|
| `T2_embryo_val_interp` | `submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad` | `submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad` | 继承 A1-L1 尺度 |
| `T2_heart_val_interp` | `submissions/candidates/T2_heart_val_interp/v0003_g1_formal_log_rms/submission.h5ad` | `submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad` | 继承 A1-L1 尺度 |
| `T2_heart_val_extrap` | `submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad` | 同一文件 | 使用 identity scale |

生成前必须重新核对父文件 SHA256、panel、obs order、var order 和 15-NN 兼容性；禁止自动挑选最新版本或覆盖已有 scored artifact。embryo panel 是 498 genes，heart panel 是 500 genes，必须继承实际 panel。

## 输入与 source-only 模型

- embryo 只读取 `E6.75`、`E7.25`、`E8.0`；heart 只读取 `E8.25`、`E8.75`、`E9.5`。两个 heart board 共享 heart 模型，不能与 embryo 混合。
- 每个组织各 stage 取相同数量的细胞，数量为该组织最小 stage 的细胞数；较大 stage 按 `celltype` 和由 seed 派生的固定 seed 分层抽样，并保存 stage/obs-name 选择记录。
- 在每个组织的精确 panel 上拟合固定 30 维 randomized PCA（seed `20260827`），再对 PC scores 做固定训练集标准化。不得调维数、solver 或样本预算。
- 对每个 observed stage 用 scorer 同款 `NearestNeighbors(n_neighbors=15).fit(coords).kneighbors(coords)`；保留其 self-inclusive 语义，计算每个细胞的邻域 latent 均值。
- 使用固定 Ridge：输入 `[z, standardized_time]`，输出 neighborhood latent mean；`alpha=1.0`、`fit_intercept=True`、`solver="cholesky"`。不得读取 target、排行榜结果或外部数据。

## 固定排列目标与算法

令 `q[i]` 表示坐标节点 `i` 接收父候选表达行 `q[i]`：

```text
m_i(q) = mean(z[q[j]] for j in N(i))
L(q)   = mean_i ||m_i(q) - d[q[i]]||²
```

其中 `d[r] = Ridge(z[r], target_time)`，`q` 初始为 identity。

1. 固定坐标 15-NN 图，构建 reverse-neighborhood。
2. 按初始残差降序访问节点，平局按 node index。
3. `L1_LATENT_KNN10` 为每个 donor 固定其 latent 最近的最多 10 个其他 donor。
4. `L2_STATE_HASH10` 仅在相同父本 `celltype` 内，按 `SHA256(seed|obs_name)` 的固定循环顺序取前后各最多 5 个 donor；state 少于两个细胞时不提出交换。
5. 用 inverse permutation 将 donor proposal 映射到当前节点；只计算交换影响到的两个节点及其 reverse-neighborhood 的精确 delta。
6. 每个节点最多接受一次严格降低 `L` 的最佳交换；delta 平局取 donor index 较小者。全程最多 `10*N` proposals、只运行一轮。
7. 结束后从头重算 `L`，与增量账本核对；若 permutation 不是双射、出现非有限值或账本不一致则 fail closed。

## AnnData 写回

- `obs_names` 保持坐标节点 ID 和原顺序；`X_out = X_parent[q]`，表达数值和 dtype 不变。
- `counts`、`log1p`、`raw`、`celltype`、`cm_celltype` 等 expression-row aligned 对象全部按同一 `q` 重排。
- `spatial_2D`、`spatial_3D` 及其他已知 coordinate-aligned 对象完全不变。
- 当前不存在 `obsp` 或未知 row-aligned 字段；若出现无法判定语义的字段，直接停止，不猜测。
- 每个候选必须输出 `prediction.h5ad`、`permutation.npy`、`permutation.tsv`、`pairing_objective.json`、protected checks 和 `MANIFEST.json`。

## 探索、验收与评分

- 最多四次未提交的 source-only 探索；最终只保留两条 lane，不能产生第三条 lane。
- 唯一小功能检查：在公开 observed stage 的固定 512-cell 子集上打乱配对，再运行两条 lane；要求目标函数下降，且至少一条 scorer-exact `neighborhood_mmd` 优于乱序起点。
- 六个最终候选必须通过 contract、双射 permutation、精确表达重排、坐标 hash、15-NN hash、panel/order、cell limit、有限非负性和 `target_used=false` 检查。
- 对六个候选各运行一次固定 public pseudo-holdout scorer；local NFS 只作路线诊断，不替代服务器 board score。由于 scorer 对表达行按索引抽样，`mmd_u`、energy、variogram 的轻微差异不单独判定为行置换失败；geometry 或全量表达统计变化则失败。
- 候选全部保持 `score_pending`，交给用户人工上传。服务器分数回填前不得声称提升、构造 composite score 或进入下一 atom。

## 禁止

- 禁止修改表达值、坐标值、细胞数或 gene order；
- 禁止 hidden target、target 坐标、神经网络、多启动、网格搜索、软 assignment 和人工区域标签；
- 禁止重新拟合 G1 scale；B1-C1 只能重放已冻结 permutation 和 scale，不能重复缩放；
- 禁止自动线上提交。
