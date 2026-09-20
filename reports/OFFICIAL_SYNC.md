# Virtual Embryo Challenge — Official Sync

更新时间：2026-09-20（§9 定例刷新；09-01 全量基线不变）

状态：PASS_FOR_COMPETITION_BASELINE；官方页面、panel、scorer、公开元数据和两个
notebook 已复核，资源下载闭环完成，首个服务器 baseline 已取得。科学 promotion
Gate 仍未全部闭合，但不阻断 leaderboard 迭代。

本文件记录当前可访问的官方内容、已落盘的官方工具、逐字节核对结果，以及不能静默忽略的本地数据缺口。官方网页内容优先于 2026-08-14 starter pack 静态快照。

## 1. 官方来源与可用性

| 内容 | 官方入口 | 当前状态 |
|---|---|---|
| Challenge overview | https://virtualembryo.ai/challenge/ | 可访问 |
| Data / splits / panels | https://virtualembryo.ai/challenge/data | 可访问；训练数据下载需要注册登录 |
| Reference rows | https://virtualembryo.ai/challenge/baselines | 可访问 |
| Evaluation / Resources | https://virtualembryo.ai/challenge/evaluation | 可访问；Resources tab 指向 veckit 与 Colab |
| Machine-readable board index | https://virtualembryo.ai/challenge/panels/index.json | 可访问 |
| T1 released-stage composition | https://virtualembryo.ai/challenge/panels/t1_composition.json | 已下载；仅 E8.5/E9.5 released stages |
| Official local scorer | https://github.com/aristoteleo/veckit | 已下载并锁定 commit |
| Reference/baseline Colab | https://colab.research.google.com/drive/11kHZjd4IawoC6uwCqiHNuDGAYpoPlUQO?usp=sharing | 用户已下载到 `baseline/pseudobulk_shift_tutorial.ipynb`；JSON 可读 |
| Evaluation Resources Colab | https://colab.research.google.com/drive/15QvIevX9xy80jEBnm827t_bMCOtq1l3x?usp=sharing | 用户已下载到 `baseline/veckit_tutorial.ipynb`；source-only 内容与 vendored tutorial 一致 |

## 2. 官方任务与 board contract

官方 panel index 当前包含 5 个 board：

| Board | Target | Genes | Submission cells | Required obsm |
|---|---|---:|---:|---|
| T1:val | E10.5 | 32,285 | 1,000–5,118 | none |
| T2:embryo:val_interp | E7.5 | 498 | 583–5,000 | spatial_3D |
| T2:heart:val_extrap | E10.5 | 500 | 1,000–25,179 | spatial_3D |
| T2:heart:val_interp | E8.5 | 500 | 1,000–17,616 | spatial_3D |
| T3:gata4 | Gata4 KO | 500 | 1,000–7,449 | spatial_3D |

官方 index 还给出当前工作副本规模：

- T1: truth 1,249，reference 1,706；
- T2 embryo interpolation: truth 583，reference 1,330；
- T2 heart extrapolation: truth 8,393，reference 5,374；
- T2 heart interpolation: truth 1,185，reference 5,872；
- T3 Gata4: truth 2,320，reference 2,483。

这些是 scorer 工作副本的规模，不是要求预测的细胞数，也不是原始 release 文件的细胞总数。

### T1

- train: E8.5、E9.5；
- validation: E10.5；
- hidden test: E12.5；
- E7.75：2026-09-17 重抓官网 Data 页，列为 unused / not released（held out as Task-2 embryo test stage），不向任何任务分发实测数据；此前“随 release 提供”的缓存作废；
- .X 为 32,285-gene、log1p-normalised、finite、non-negative 表达；
- 不需要空间坐标，也不提交 celltype。

### T2 embryo

- train: E6.75、E7.25、E8.0；
- validation: E7.5；
- hidden test: E7.75；
- 这是 interpolation-only 设置；
- 坐标是每个胚胎自己的 local frame，不做跨时间点绝对坐标注册。

### T2 heart

- train: E8.25、E8.75、E9.5；
- validation: E8.5（interpolation）和 E10.5（extrapolation）；
- hidden test: E12.5；
- .X 为 500-gene MERFISH panel，且必须提供 obsm["spatial_3D"]。

### T3

- train: Mab21l2 KO @ E9.5；
- validation: Gata4 KO @ E8.75，两个 biological replicates；
- hidden test: β-catenin KO @ E8.75，两个 biological replicates；
- reference: matched WT @ E8.75 和 E9.5；
- 差异表达相对于 matched WT 计算，不是相对于前一时间点；
- prediction 是 mutant embryo 本身，不是 response delta。

## 3. Gene panel 核对

官网说明：T2 embryo board 的 panel 是训练阶段与目标阶段实际加载基因的有序交集。由于 Casp4 和 Pnliprp1 在 E6.75/E7.25 未测量，T2 embryo board 正式使用 498 genes；这不是本地数据损坏。

本地目录 data/gene_panel 中的 5 个文件与官网逐字节一致：

| 文件 | 行数 | 本地 SHA-256 前 16 位 | 结果 |
|---|---:|---|---|
| T1__val.genes.txt | 32,285 | 2aeae4cd28493395 | IDENTICAL |
| T2__embryo__val_interp.genes.txt | 498 | e20f726e623e04af | IDENTICAL |
| T2__heart__val_extrap.genes.txt | 500 | bf40079bfb50c78d | IDENTICAL |
| T2__heart__val_interp.genes.txt | 500 | bf40079bfb50c78d | IDENTICAL |
| T3__gata4.genes.txt | 500 | bf40079bfb50c78d | IDENTICAL |

官网 panel index 的短 hash、cell limits 和 required obsm 已按 2026-08-17 页面内容记录在本文件；后续 validator 应以官网 index 和 panel 文件为准，不以原始 .h5ad 的 var index 自行推断 board panel。

用户再次确认 E8.25_late 官方下载为 225 MB；本地文件为 225,091,568 bytes，SHA-256 为 `d56f94d3e2d719ed3074d86c03eae457ccf90b24145d33300f9958f0e8078593`。官网公开 handoff 页面仍显示 288 MB，作为页面版本差异保留记录，但不再阻塞当前资源闭环。

## 4. Reference rows 与 adversarial controls

官网 reference rows 页面定义：

- floor：T1/T2 的 copy_last，T3 的 wt_identity；官网把 floor 固定解释为 50；
- ceiling：目标细胞固定 seed 分成两个不相交 half，一个作为 truth，一个作为 prediction；
- published baselines：T1/T2 pseudobulk_shift，T3 shift_transfer 和 gene_ko；
- controls：ctrl_scale_ref、ctrl_shrink_ref、ctrl_one_cell、ctrl_random_cube、ctrl_squashed_ref、ctrl_scale_wt、ctrl_shrink_wt、ctrl_random_dir。

官网列出的实现来源包括 T1/baselines.py::copy_last、T2/model.py::copy_last、T3/model.py::wt_identity 等，但这些文件没有出现在当前公开 veckit checkout 中；它们的可执行入口是官网提供的 Colab，两个 notebook 现已落盘到 `baseline/`，T2 reference-row 规则已提取为本地 runner 并完成 pseudo-target smoke。

## 5. Official scorer 落盘与 smoke test

已落盘：

- 路径：third_party/veckit
- 仓库：https://github.com/aristoteleo/veckit
- branch：main
- commit：46d41e63f42a9aab815db20b742feeccd249cb17
- package version：0.1.1
- 依赖：numpy、scipy、anndata、scikit-learn
- 附带：T1/T2/T3 metric modules、150-cell sample files、veckit_tutorial.ipynb、MIT LICENSE

当前环境中无需全局安装，使用以下方式运行：

    LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH=third_party/veckit \
      python third_party/veckit/score_h5ad.py --task T1 \
      --input third_party/veckit/data/sample_8.5.h5ad \
      --target third_party/veckit/data/sample_9.5.h5ad

已完成同一 commit 的 T1/T2/T3 sample smoke test，三项均返回 JSON metrics。首次运行因系统动态库优先级导致 SciPy 报缺少 GLIBCXX_3.4.29；补充 LD_LIBRARY_PATH=/opt/anaconda3/lib 后通过。该失败归因于环境，不是 scorer 逻辑失败。

注意：scorer 是 offline metric implementation。--target 必须是本地已有的 pseudo target；本地分数不是 leaderboard 预览，也不提供 hidden target 信息。

## 6. Resources tab 与 baseline 依赖状态

官网当前 Resources 内容把 https://github.com/aristoteleo/veckit 作为 baselines repo/source of truth，并同时提供 pip install veckit、Python API、150-cell tutorial sample 和 Colab。

当前 checkout 能稳定提供 scorer、metric modules、tutorial 和 samples，但没有官网 reference rows 页面列出的 T1/baselines.py、T2/model.py、T3/model.py 等 baseline model files。两个官方 notebook 已落盘；T2 的 `copy_last`、`pseudobulk_shift` 和三个官方 T2 controls 已提取为本地可复现模块，T1/T3 baseline 仍未完成独立实现。

本地 baseline/ 中的 `pseudobulk_shift_tutorial.ipynb` 已检查：notebook JSON 有效，共 18 个 cell；纯 Python 实现单元可解析，`pseudobulk_shift`、`shift_transfer` 在临时 synthetic H5AD 上的核心代码 smoke 通过，并确认 T2 的 `spatial_3D` 会随输入保留。该 notebook 的 setup/score 单元仍依赖 `pip install veckit`、`wget` 和 `veckit` CLI，使用的是 veckit sample 数据，不是本地 challenge train/validation 文件；未执行其会联网、安装依赖并写出 sample 文件的完整 notebook。其 `dense()` 路径也不适合直接处理 T1 的约 1.7 万 × 3.2 万矩阵，正式 baseline 需要 memory-safe 改写或官方实现。

另外，third_party/veckit/veckit.py 的模块说明仍引用：

    pip install git+https://github.com/aristoteleo/vec_baselines.git

该地址当前返回 404/认证失败，未下载、未安装，也未将其作为官方依赖。后续若官方页面更新可用地址，应重新同步并记录新 commit。

本轮正式工作新增 `scripts/t2_baseline.py`：直接读取本地 T2 数据，支持 `copy_last` 与 per-celltype `pseudobulk_shift`，按官方 panel 对齐并保留 `spatial_3D`；T2 dense buffer 有显式内存上限，避免教程的 T1 级别误用。新增 `scripts/t2_controls.py` 复现 `ctrl_scale_ref`、`ctrl_random_cube`、`ctrl_squashed_ref`，并显式标记 `ctrl_random_cube` 为 audit-only。baseline 与 controls 回归测试合计 `9 passed`；完整 control 表见 `reports/T2_CONTROLS_AUDIT.md`。

## 7. 本地 data 完整性对照

### 已存在且与官方 split 对应

- T1：E8.5_RNA.h5ad、E9.5_RNA.h5ad；
- T2 embryo train：E6.75.h5ad、E7.25.h5ad、E8.0.h5ad；
- T2 heart train：E8.25_late.h5ad、E8.75.h5ad、E9.5.h5ad；
- T3 train：E9.5_mab21l2_ko.h5ad；
- T3 WT reference 的候选文件：E8.75.h5ad、E9.5.h5ad。

已检查：9/9 个 AnnData 均可读；T1 文件为 32,285 genes 且无 spatial requirement；T2/T3 文件有 spatial_3D，形状为 n_obs × 3 且 finite；表达值均 finite、non-negative。

逐文件 board-aware 比较结果：T1 两个文件、T2 embryo 的 E6.75/E7.25、T2 heart 三个文件和 T3 KO 的 var_names 均与对应 panel 完全一致。E8.0 原始文件为 500 genes，与 498-gene T2 embryo board 的交集完整，额外的两个基因正是 Casp4、Pnliprp1，符合官网对早期胚胎缺测基因的说明。现有空间文件的 spatial_3D 在 H5AD 中保存为 float64，而官网 file contract 文档描述为 float32；当前值 finite 且维度正确，暂不强制转换 raw 文件，后续 submission/processed 层再按官方 validator 决定。

E9.5_mab21l2_ko.h5ad 的 obs index 非唯一，且使用 genotype/time 等字段而非官网 T3 描述中的 condition 字段。官网 board index 当前 obs_required 为空，因此这不是 submission contract 的立即失败项，但会影响 provenance 和 T3 loader，必须在 manifest 中显式记录。

### 缺失但按官方保密/发布规则可解释

- T1 E10.5/E12.5：validation/test target，正常不在本地；
- T2 heart E8.5/E10.5/E12.5：validation/test target，正常不在本地；
- T3 Gata4 KO 与 β-catenin KO：validation/test conditions，正常不在本地。

### 已补齐的训练数据

- T2 embryo 的 E6.75 和 E8.0 已补充，连同 E7.25 可按官方三阶段 train split 构造 embryo interpolation workflow。

### 仍缺失但按官方保密/发布规则可解释

- E7.75 T1 single-cell background：2026-09-17 重抓确认 not released（见上），无下载、无 provenance 待登记项；T1-D7 前提不存在，转 CLOSED（D-20260917-T1D7-002）。
- T1 E10.5/E12.5、T2 heart E8.5/E10.5/E12.5、T3 Gata4/β-catenin KO 仍是 validation/test target，正常不在本地；官网 Data 页明确训练数据下载需要注册登录，held-out 数据不公开分发。

### E8.25 文件状态

用户再次确认官网对 E8.25_late.h5ad 的下载标注为 225 MB；当前文件为 225,091,568 bytes，SHA-256 为 `d56f94d3e2d719ed3074d86c03eae457ccf90b24145d33300f9958f0e8078593`。其 shape、500-gene panel、spatial_3D 和 AnnData 结构当前可读。官网公开 handoff 页面显示 288 MB，作为版本差异记录，不再阻塞资源闭环。

状态：STRUCTURAL_PASS_CONFIRMED_BY_USER。仍不把文件宣称为官方 byte-identical，因为没有公开 checksum/manifest；新增文件 SHA-256：E6.75=`ab58b9217d1b9a18b0181f498475a9eb821ac2c92ab2b7e45a623da0e4fffe70`，E8.0=`17530e23fbfa6a139ff68d0353a489d83790f5b60f036b7d2f58303a1ff8a810`。

## 8. 当前 Gate 与下一步

- Gate 0 official sync：WEAK_PASS；
- Gate 1 contract：PARTIAL_PASS（T2 runner 已完成 panel/X/spatial_3D 和 board cell-limit 校验；完整 challenge validator 尚未建立）；
- Gate 2 baseline reproduction：PARTIAL_PASS（本地 T2 `copy_last`/`pseudobulk_shift` 已按官方 notebook 规则实现、生成并配对比较；官方 notebook 的联网安装/完整执行未运行，T1/T3 baseline 尚未独立实现）；
- Gate 3 pseudo-holdout：PARTIAL（3 个 starter-pack T2 proxy、主方法及 expression/geometry exploratory candidates、固定 seed 分层 1,000-cell offline veckit smoke 均完成；不是官方 hidden target，未形成确认性模型选择）；
- Gate 4 adversarial controls：PARTIAL_PASS（T2 三个官方 controls 已实现、9 项 regression/smoke 通过并在三个本地 pseudo-target board 上运行；正式 hidden-board control audit 仍未完成，不能宣称 leaderboard Gate 4 通过）；
- Gate 5 T2-B1/B2：NOT_RUN；
- scored submission：baseline 已完成；`v0002_expression_midpoint_norm` 已取得
  heart interpolation `53.6`，aggregate Total 更新为 `145.9`；科学模型晋级仍
  冻结，但不阻断竞赛提交；
- external sources：已落盘 official veckit 的 6 个 tutorial sample H5AD，仅用于 scorer/tutorial smoke；身份、commit 和 SHA-256 已登记到 infra/bioinf-data-index/；未使用预训练模型；
- root workspace：已执行 `git init`，根目录现为有效 Git repository（当前 branch `master`，未创建 commit；数据与代码均未自动 stage）；官方 scorer 自身的 commit 已锁定。

本轮 pseudo-holdout scorer 结果：T2 embryo `de_score=0.875`、`de_direction=0.9705`；T2 heart `de_score=0.8289`、`de_direction=0.9394`。完整输出位于 `outputs/t2_baseline/pseudo/`，只用于验证 runner/scorer 链路，不代表 leaderboard 结果。

已按 starter pack 的 3 个 T2 proxy 完成 target-blind 运行，并为每个 proxy 配对 `copy_last` floor。随后用固定 seed `20260818`、按 `celltype` 分层的 1,000-cell board-valid slice 重跑；关键结果如下：

| Proxy | Method | de_score | de_direction | energy_distance | pb_rel_err | pseudobulk_pearson | 解释 |
|---|---|---:|---:|---:|---:|---:|---|
| heart interpolation | pseudobulk_shift | 0.4062 | 0.5609 | 1.75497 | 0.4254 | 0.8613 | 相比 floor 有表达变化收益，值得继续 |
| heart interpolation | copy_last | 0.0000 | 0.0000 | 2.39492 | 0.4973 | 0.8125 | floor |
| heart extrapolation | pseudobulk_shift | -0.0658 | -0.0099 | 2.76209 | 0.6133 | 0.7846 | 外推幅度仍过大，library_size_ratio=1.662 |
| heart extrapolation | copy_last | 0.0000 | 0.0000 | 2.39496 | 0.5706 | 0.8125 | floor |
| heart extrapolation | pseudobulk_shift_row_norm (diagnostic) | 0.0526 | 0.1369 | 2.38977 | 0.5013 | 0.8123 | library_size_ratio=1.000，但 DE/方向信号仍弱，不升级 |
| embryo interpolation | pseudobulk_shift | -0.0323 | 0.5952 | 4.84381 | 0.9609 | 0.7971 | expression scale/伪 bulk 误差明显，暂不作为升级方向 |
| embryo interpolation | copy_last | 0.0000 | 0.0000 | 7.29907 | 1.1742 | 0.7380 | floor |

这些结果只支持“runner/scorer 链路可重复”和“heart interpolation 的 shift 值得继续分析”，不支持模型优越性结论。完整 JSON、分层抽样 manifests 和 registry 位于 `outputs/t2_pseudo_holdouts/`；proxy 局限和 target-blind 规则见其 README。

Heart interpolation 的事后 geometry attribution 显示：保留 prediction expression、仅替换为 target 的 oracle `spatial_3D` 后，`d2_shape` 从 0.04791 降至 0.00105，`occupancy_dice` 从 0.7704 升至 0.8223；`de_score` 保持 0.4062 不变。这支持“表达和几何是相对独立的瓶颈”，但 oracle geometry 不能用于真实预测，且 neighborhood 指标并未同步改善。
为 heart extrapolation 加入的行级 log1p library-size 控制把 `library_size_ratio` 从 1.662 修到 1.000，`pb_rel_err` 从 0.6133 降到 0.5013，`energy_distance` 从 2.76209 降到 2.38977；但 `de_score=0.0526`、`de_direction=0.1369` 仍只略高于 copy floor，说明尺度失配得到部分修复，外推响应本身仍未验证可用。该控制保持为诊断，不进入主方法。

Heart interpolation 的两条轨道随后做了正交 exploratory 对照，固定同一个 seed `20260818`、同一个分层 1,000-cell slice：

| 轨道/候选 | de_score | energy_distance | d2_shape | occupancy_dice | neighborhood_mmd | 结论 |
|---|---:|---:|---:|---:|---:|---|
| expression baseline | 0.4062 | 1.75497 | 0.04791 | 0.7704 | 0.12760 | reference |
| expression shrinkage `celltype_weight=0.5` | 0.4375 | 1.32255 | 0.04791 | 0.7704 | 0.11513 | expression-only 指标改善；17 个 celltype 使用 pooled fallback |
| geometry `centroid_weight=0.5` | 0.4062 | 1.75497 | 0.03955 | 0.7888 | 0.13399 | shape 改善但 local graph 略差 |
| geometry `centroid_weight=1.0` | 0.4062 | 1.75497 | 0.03415 | 0.7990 | 0.14554 | 关闭约 29.4% oracle shape gap，但 Moran/neighborhood 变差 |

Expression candidate 保持 carrier `spatial_3D` 不变；geometry candidate 保持 expression matrix、gene order 和 cell rows 不变。坐标行置乱 control 将 `neighborhood_mmd` 升至 0.29828、`morans_I_agreement` 降至 0.0164，证明图指标对坐标敏感；但 oracle 坐标的 neighborhood 仍未优于 carrier，因此 geometry 结果只能报告为 trade-off，不能宣称真实 geometry 已恢复。完整比较见 `outputs/t2_pseudo_holdouts/T2_heart_interp_proxy/expression_geometry_comparison.json`。

随后对 baseline、expression shrinkage 和 geometry G3 运行 5 个固定 seed（20260818–20260822）的分层 1,000-cell scorer 面板。expression shrinkage 相对 baseline 的 `energy_distance` 和 `pb_rel_err` 在 5/5 个 seed 改善，`de_score` 在 4/5 个 seed 改善，中位数差值为 `+0.0313`；但 `library_size_ratio` 中位数为 1.119，且没有 source-only 内层选择证据，因此仍不升级。Geometry G3 的 `d2_shape` 在 5/5 个 seed 改善，但中位数为 0.04108，未达到预设 0.03854 阈值；`neighborhood_mmd` 和 `morans_I_agreement` 在 5/5 个 seed 变差，也不升级。五个 seed 只证明抽样稳定性，不构成 biological replication。结果见 `outputs/t2_pseudo_holdouts/T2_heart_interp_proxy/seed_panel/analysis.json`。

Source-only artifact/signature audit 为 `PASS_FOR_GENERATION_ONLY`（8/8 checks，15 个 seed manifests）：预测函数没有 target/reference 参数，prediction metadata 未包含 E8.75，expression/geometry 的冻结轨道不变量均通过。该审计不能替代独立生物学验证。

当前科学推进仍受 `reports/BLOCKER_REPORT.md` 限制：缺少不泄漏 target 的独立内层
选择依据。该限制只冻结正式科学模型晋级和 biological claim，不暂停 scored
submission。

下一步顺序（竞赛优先）：

1. 以 `145.7` 作为初始 baseline、`145.9` 作为当前 best，登记每次 submission
   的分数和文件身份；
2. 保留 `v0002` 的 T2 heart interpolation 改进，并为下一次尝试新建 `v0003`；
3. 根据服务器分数决定保留、回退或进入下一个单变量候选；
4. heart extrapolation、embryo interpolation 和 T1/T3 继续作为独立 board 处理，
   不因科学 Gate 未闭合而暂停；
5. 科学路线仅在有独立 stage/replicate 或明确固定参数决策时恢复正式 B1/B2。

官方来源：

- https://virtualembryo.ai/challenge/data
- https://virtualembryo.ai/challenge/baselines
- https://virtualembryo.ai/challenge/evaluation
- https://virtualembryo.ai/challenge/panels/index.json
- https://github.com/aristoteleo/veckit

## 8. T3-S1D official GEO refresh (2026-09-01)

按 cache-first 规则，本次仅在现有缓存缺少目标扰动证据时访问 NCBI GEO/FTP，新增并 hash-lock 三份 official processed series matrix：GSE5298、GSE9652、GSE78125；同时新增其对应 GPL1261/GPL6246 platform annotation。GSE5298/GSE9652 为 E9.5 Gata4 cardiac-tissue contexts，GSE78125 为 E9.5 Ctnnb1 AHF context；raw CEL 未下载，数据未进入 challenge input。

官方入口：[GSE5298](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE5298)、[GSE9652](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE9652)、[GSE78125](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE78125)、[GPL1261 annotation](https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL1nnn/GPL1261/annot/GPL1261.annot.gz)、[GPL6246 annotation](https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL6nnn/GPL6246/annot/GPL6246.annot.gz)。文件身份、字节数和 SHA256 见 `infra/bioinf-data-index/INDEX.tsv` 与 `artifacts/tool_integration/T3-S1D-INDEPENDENT-ACTIVITY-EVIDENCE-20260901-v3/metrics/source_audit.json`；该刷新只补充 contextual evidence，不改变 E8.75 gate。

## 9. 定例刷新（2026-09-20，有变更但无 board contract 变更）

抓取源（fresh）：`challenge/`、`challenge/data`、`challenge/baselines`、
`challenge/evaluation`（T1 节）、`challenge/panels/index.json`、
`challenge/panels/t1_composition.json`、`challenge/timeline`；
veckit 上游 HEAD 经 git ls-remote 核对为 `46d41e6`（与本地 pin 一致，无 scorer 更新）。

### 确认无变更（与 09-01/09-17 缓存一致）
- 5 board 的 genes/cell limits/truth/ref 规模：index.json 逐项对过，全同（T1 32285/1000–5118/1249/1706；T2 embryo 498/583–5000/583/1330；heart extrap 500/1000–25179/8393/5374；heart interp 500/1000–17616/1185/5872；T3 500/1000–7449/2320/2483）。
- E7.75 仍为 unused / not released（Data 页＋evaluation 页双确认，09-17 订正继续有效）。
- Baselines 页引用行定义与 §4 一致（floor=50 按定义、逐 board 实测；controls 含 structure-gate 修补故事）。
- Panel 文件未重抓（无变更信号；本地 SHA 见 §3）。

### 新增入库（规则/策略相关，非 contract 变更）
- **Test-phase 规则**（timeline 页，权威日程）：P3 自 2026-10-20 起全任务释放 validation 答案；test inputs 无标签下发；**每 board 整个 phase 限 2 个 official test submissions**；final due 12-02；eval 12-04；NeurIPS 公布 12-11。deadline 只延不提前。
- **修正窗口声明**：timeline 页明示 datasets 与 metric formulations 仍可能被修正——定例刷新继续。
- index.json anchors 首次入库：逐 board floor/ceiling（如 T1 de ceiling 0.8464/dir 0.7901；T3 severity_slope floor −6.9078/ceiling −0.0088）。无法确认是否变更过，记为首次捕获，供本地门校准参考。
- Data 页新增操作细节：scorer 先对每 stage 下采样 10%；MMD 取 2000、energy/variogram 各 1500；cell 数只影响证据量不影响排名；T1 心脏中心解剖说明（Neural Tube E8.5 占 4.6%、E9.5 为 0，composition.json 已含 18/21 类型与未调和词表警告）。
- 口径注记：evaluation 正文称 E8.5/E9.5 共享 "5 cell types"，composition.json 列 exact-name 共享 11 个——系调和词表差异，非规则变更；本地 lineage（28 states→10）不受影响。
- 外部数据披露规则确认（evaluation 页）：可训外部公开单细胞数据，须随 submission 披露——与 `infra/bioinf-data-index/` 做法一致。
- 奖金 $112K（winner $54K＋generality $8K＋travel $30K＋community $20K），备查非规则。

### 策略含义（记录，不形成决策）
- Validation probing 有明确截止（10-20 转 test ranking）；test 期每 board 只有 2 发——攒足证据再打。

## 2026-09-20 — T3 外部数据收集前复核

来源：https://virtualembryo.ai/challenge/rules（本轮在线读取；原始网页、SHA256 见 reports/t3_data_intake_20260920/FETCH_RECEIPT.json）。T3 held-out genotype、同基因其他 allele/近似表型和预训练污染禁用边界与既有缓存一致；未据此放宽本地 generic Perturb-seq 的响应形状用途及书面确认要求。未重新抓取其他官方页面、未重定其他任务许可。实际新数据均隔离，未训练。

- 2026-09-20 R5/R6规则复核：重新获取 https://virtualembryo.ai/challenge/rules ，§10正文与前次缓存一致；缓存 `infra/external_data/quarantine/T3-R5-COMPLETION-20260920/official_rules.html`，哈希见 `reports/t3_r5_completion_20260920/FETCH_RECEIPT.json`。纠正归因：统一书面确认和shape-only为项目内部保守约束，不是官网逐字要求；官方为边界不确定时提交前询问。

- 2026-09-20内部规则适度性评审：再次在线核对 https://virtualembryo.ai/challenge/rules §10，相关规定仍为许可与披露、禁止held-out/phenocopy、边界不确定时提交前询问；没有找到统一书面预审批或shape-only条款。与此前缓存的相关规定一致；建议见 reports/T3_INTERNAL_RULE_REVIEW_20260920.md，尚未生效。
