# T3 v0088 本地重训与复合分迭代 — 2026-10-09

## 目标

在 v0088（现役，T3 53.69）两条最优路线的成分上做迭代优化，使本地复合总分尽可能高。
指标口径复刻冻结评测：`evaluate_source.py` 的加权 skill 复合分
（de .30 / direction .25 / severity_abs .25 / mmd .12 / variogram .08），
7 个 held-out 基因型 × 3 seed 的均值，higher_is_better。

## 为什么要重训

`research/t3_20261008/` 发布了 v0087/v0088 的实现代码，但四个拟合产物
（`state_emitter.joblib`、`generic_response.npz`、`WT_carrier7449.h5ad`、
`expected_donor_rows.npy`）**故意未发布**，无公开下载 URL
（见 `REPRODUCTION.md:17`）。没有它们，本地复合分无法计算。

用户授权：从代码重训生成本地 v0088。

## 已完成的上游重建

| 步骤 | 命令 | 结果 |
|---|---|---|
| GEO 源 | `snapshots/v0087/fetch_public_sources.py --download` | 12/12 文件 SHA256 逐个 assert 通过，退出码 0，共 4.1 GB |
| 注释 TSV | `portable/rebuild_annotations.py --download` | 8/8 逐字节匹配 permit 哈希，`exact_historical_bytes: true` |
| GO embedding | 归档 `go_expanded7/build_go.py` + 三处纯路径替换 | **`GO_EXPANDED_EMBEDDING.npz` 重建为逐字节相同** `a81ff9a593285286d030672d2ed728bed6dd220d…` |

### GO 重建的意义

`PUBLIC_REBUILD_FOLLOWUP.md:54` 明确写了这项"未独立冒烟测试的端到端 GO 重建"。
本次用仓库内已有的 `infra/external_data/sanitized/T3/B2-T3-A1/GO/` 三个原始文件
（`go-basic.obo`、`MOUSE-mod.gaf.gz`、`MOUSE-uniprot.gaf.gz`，哈希与
`GO__DATA_AUDIT_REPORT.json` 一致）加上 `artifacts/t3_priority_six_20260930/GO_EMBEDDING.npz`
（`acdb554d47989a4d…`，与 PROVENANCE 记录的 previous_embedding 一致），
跑归档 build 脚本得到**逐字节相同**的 embedding。

这说明 GO 重建链是可复现的，该条限制可以在后续更新中降级。
**注意**：这是 GO 特征构建的复现，不是 v0088 预测的复现。

### 数值环境

本地默认环境 numpy 2.4.6 / sklearn 1.9.1 / anndata 0.12.19 与冻结版本不符，
且 pandas 依赖的 numexpr/bottleneck 存在 `_ARRAY_API not found` 冲突。
已用 `uv` 建立 `vework/ve-t3` 独立环境，版本与 `snapshots/v0087/VERSIONS.json` 逐项一致：
Python 3.12.11 / numpy 2.3.5 / scipy 1.18.1 / pandas 2.2.3 / sklearn 1.8.0 / anndata 0.11.4。

## 方法与限制

- 所有输入准备步骤走 `portable/rebuild_inputs.py`，它只做路径替换并记录
  `path_only_substitutions`；科学参数不动。
- 官方 E8.75 / E9.5 用 `data/` 下已有副本，SHA256 与 `OFFICIAL_RELEASED_INPUTS.json` 一致。
- **本地源侧指标不是服务器预测。** 项目记录里 v0086 源侧改善、服务器 49.34 低于 v0084；
  T1 v0058、T2 v0035 同样是本地好、服务器不涨。本轮迭代只能筛掉明显劣的成分，
  不能证明服务器会涨。
- 提交额度为 0：registry 记录 v0088 消耗了最后一次授权预算，portal T3 用量 8/8。
  本轮只做本地开发，任何候选都不自动提交。

## 模型重训：完全复现（关键结果）

`portable/rebuild_model.py --execute` 跑通，**v0087/v0088 的表达式哈希逐位复现**：

| 产物 | 重建哈希 | 与归档 MANIFEST |
|---|---|---|
| v0087 表达式 | `2420c6b992fed7c431bf2cf4a4fb30d630fcba9bafa8d9b5898b5caae4db1f98` | assert 通过 |
| v0088 表达式 | `7cfe4e0cfcfe1a76c003e25eed7d3fab58868f1d6d5dd7cb6b0ab14b3dddf77c` | assert 通过，等于 MANIFEST 的 `expression_sha256` |
| `state_emitter.joblib` | `35f61567e91c7e8a…` | 逐字节相同 |
| `generic_response.npz` | `da0b135906e7c8f4…` | 逐字节相同 |
| `expected_donor_rows.npy` | `05ccdc901ff45c62…` | 逐字节相同 |

`REBUILD_MANIFEST.json` 状态 `REBUILT_EXPRESSION_EXACT`。

**这推翻了 `PUBLIC_REBUILD_FOLLOWUP.md:53` 的"完整拟合未验证"限制。**
配合 GO embedding 的逐字节复现，公开 clone 现在可以完整重建 v0088，
不再需要用户提供私有 cache。原始 HDF5 序列化字节仍不必相同（设计如此）。

## 基线复合分：逐位复现

适配后的冻结评测器（仅两处路径替换）跑出的四臂结果与归档
`snapshots/v0088/source_evaluation/summary.csv` **最大绝对差 0.0**，
`SELECTION.json` 三条决策的 `mean_gain` 全部逐位相同：

| 臂 | 本地复合总分 |
|---|---:|
| baseline | 74.412298 |
| residual | 73.966485 |
| both | 74.323200 |
| **conditional（现役 v0088）** | **74.737588** |

conditional 臂分项：de 69.089 / direction 72.970 / severity_abs 93.394 /
mmd 61.417 / variogram 63.121。

本地分现在可信，可以作为迭代目标。

## 迭代配置

- 指标：conditional 臂复合总分，higher_is_better
- 每次只改发射器里一个成分，锚点做 `count==1` 断言
- 变体树互相隔离，归档快照永不改写
- 响应缓存（84 个胚胎响应）与发射器无关，跨变体复用
- 单次评测约 5.5 分钟

### 可动旋钮

| 轴 | 位置 | 冻结值 |
|---|---|---|
| `propensity_penalty` | `emitter_v88.py:20` | 0.1 |
| `propensity_min_cells` | `emitter_v88.py:11` | 20 |
| `composition_clip` | `emitter_v88.py:34` | ±2 |
| `detection_offset` | `emitter_v88.py:46` | 1.0 |
| `zero_frac_scale` | `emitter_v88.py:46` | 1.0 |

`propensity_penalty` 是 v0088 胜出的那条 ridge 的正则强度，优先级最高。

## 状态

上游重建与模型重训全部完成并通过哈希校验；基线复合分已确立并逐位复现。
迭代循环运行中。

## 迭代结果（14 次）

指标：conditional 臂复合总分，higher_is_better，基线 **74.737588**。
完整日志 `autoresearch/loop-261009-1450/loop/results.tsv`。

| 变体 | 轴 | 值 | 总分 | Δ |
|---|---|---:|---:|---:|
| prop_penalty_0p2 | propensity_penalty | 0.2 | 74.740974 | **+0.003386** |
| prop_penalty_0p15 | propensity_penalty | 0.15 | 74.739233 | +0.001645 |
| prop_penalty_0p3 | propensity_penalty | 0.3 | 74.737902 | +0.000314 |
| *（冻结基线）* | — | 0.1 | 74.737588 | 0 |
| prop_mincells_10/40 | propensity_min_cells | 10/40 | 74.737588 | ±0.000000 |
| comp_clip_1/3 | composition_clip | ±1/±3 | 74.737588 | ±0.000000 |
| prop_penalty_0p5 | propensity_penalty | 0.5 | 74.735910 | −0.001678 |
| det_offset_1p5 | detection_offset | 1.5 | 74.673126 | −0.064462 |
| det_offset_0p5 | detection_offset | 0.5 | 73.031681 | −1.705907 |
| zero_frac_0p9 | zero_frac_scale | 0.9 | 72.653997 | −2.083590 |
| zero_frac_1p1 | zero_frac_scale | 1.1 | 72.651035 | −2.086553 |

（`prop_penalty_0p05` = 74.734510，Δ −0.003078。）

### 三个结构性发现

**一、DE 端在发射器层面不可动。** 所有 propensity_penalty 变体的
`de_skill` 变化恰好是 **+0.00000**。de 分只由响应结构决定，
而发射器只重新分配已激活细胞给谁 —— 改激活顺序不会改变 DE 集合。
服务器上 v0088 的 de 只有 41.7，是真正的短板，但**这个短板不在发射器里**。
要动它必须改 `response`（即 `summarize_response` 的 delta 结构）或组成重采样，
不是改 tie-breaking。

**二、检测比例被钉死在 1.0。** `zero_frac_scale` ±10% 各损失约 2.08 分，
`detection_offset` ±50% 损失 0.06 到 1.71 分。这些轴的曲率极陡，
说明冻结值附近就是窄峰，进一步扫是浪费。

**三、增益幅度是噪声级的。** 最好变体 +0.0034 分（+0.0045%），
且只来自 mmd 一个子项（+0.0285），de 零变化、variogram ±0.0005、severity −0.0007。
`propensity_penalty` 在 0.1–0.3 之间是一条几乎平坦的缓坡，
0.15/0.2/0.3 的排序与差值（0.0016/0.0034/0.0003）不足以支撑"0.2 更好"的结论 ——
0.3 反而低于 0.2，趋势不单调。

### 结论

**不建议把 `propensity_penalty=0.2` 作为改动提交。** 理由：

1. 增益 +0.0034 分，比服务器分数的显示精度（两位小数）小两个数量级；
2. 本地源侧指标历史上多次不转化为服务器收益 —— v0086 源侧改善、
   服务器 49.34 低于 v0084；T1 v0058、T2 v0035 同样本地好、服务器不涨；
3. 该变体 de 分零变化，只动 mmd，而服务器上 mmd 的贡献不确定；
4. 换 0.1→0.2 是"再扫一次权重"，正是 `ATOM_MAP.md` 判定饱和的那一类动作。

冻结值 0.1 已经在合理的缓坡中部。**成分迭代这条路在发射器层面已经走到头。**

### 下一步该往哪走（需要你定方向）

发射器层面无空间。可动的下一个层次：

- **组成重采样**：v0088 的 `mass*=np.exp(np.clip(response['composition'],-2,2))`
  只按状态边际质量重采样，不改变 donor 内部构成。改动它等于换一条路线，
  不是成分迭代。
- **响应结构**：改 `summarize_response` 的 delta 定义（如分位数间隔、
  状态支持阈值）。这是唯一能同时动 de 和 direction 的位置，
  但它已经冻结过一次（hurdle v1→v2），改动等于开新路线。
- **换目标**：本地分已经不是有效目标。建议改用服务器分做仲裁，
  但额度为 0。

## 并行工作提醒

迭代期间仓库被另一路工作推进到 `29a8e19`：T1 late-anchor/OT
新增 v0089–v0093 并回分，v0092 = **58.89**（T1 新 board best，
T3 v0088 53.69 未变）。我的 fast-forward 无冲突，T3 范围未受影响。