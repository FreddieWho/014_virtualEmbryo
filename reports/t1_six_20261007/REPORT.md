# T1 六路线执行报告（2026-10-07）

用户 /goal 授权的 **3 条既有路线优化/结合 + 3 条全新路线** 已全部实现并实际运行。六条均执行 report 与 final 模型、完整 32285 基因官方本地 scorer、独立进程重放、contract 检查。参数事前冻结（configs/t1_six/design_20261007.json），未根据结果续调。当前服务器 best 仍 **v0051=53.92**，本轮全部未提交/未评分。

设计与论文检索：[T1_SIX_DESIGN_20261007.md](../T1_SIX_DESIGN_20261007.md)。[提交包](../../deliveries/t1six__t1__upload__20261007.zip)（6 成员＋4 manifest，READY_NOT_SUBMITTED，zip sha `22e99637f39afc2e…`）。候选与哈希唯一登记在 submissions/INDEX.tsv；报告不维护第二份身份登记表。

## 六条路线与结果

| 分类 | 路线 | 候选 | 本地五项（DE↑/方向↑/Energy↓/MMD↓/Variogram↓） | 相对 v0035 净变化 |
|---|---|---|---|---|
| 优化/结合 | ocovstab n2covot 升级（per-scope 可靠性强度＋k=8 软化） | v0061 | 0.5370 / 0.4959 / 0.29240 / 0.01800 / 0.000688 | 全劣（k=8 软化劣于 k=1 硬投影） |
| 优化/结合 | osoftcov f1soft 软责任 × n2covot 结合 | v0057 | 0.4815 / 0.4679 / 0.44416 / 0.01862 / 0.000911 | 全劣 |
| 优化/结合 | ostabmix f2stable 稳定性 × s2mix 结合（per-type 自适应比例） | v0058 | **0.6111** / 0.5836 / 0.14400 / 0.00949 / 0.000399 | **de +0.0185 改善**，其余基本持平（dir −0.0016/Energy +0.0018/MMD +0.00012/Vario +1e-6） |
| 全新 | nwasser 精确 OT 计划位移场 | v0062 | 0.5000 / 0.5073 / 0.26997 / 0.01856 / 0.000638 | 全劣 |
| 全新 | nconf split-conformal donor 半径校准 | v0059 | 0.5000 / 0.5201 / 0.23317 / 0.01729 / 0.000589 | 全劣 |
| 全新 | nbidir 前向/后向计划一致性权重 | v0060 | 0.5556 / **0.5877** / **0.14089** / 0.00973 / **0.000397** | dir/Energy/Vario 改善，de −0.037、MMD +0.00036 变差（3优2劣取舍） |

按五项点估计：对 v0035 无退步且有改善：无（ostabmix de 改善但 dir 微降、nbidir 取舍）；无改善且有退步：ocovstab、osoftcov、nwasser、nconf。未采用结果导向换算法或参数救援。新尝试是项目新机制，不是学术原创声明：nwasser 是非参数测地位移场不是完整动态 OT；nconf 是统计校准半径过滤不是保真保证；nbidir 是计划一致性权重不是谱系识别。不存在用"文献中方法名"代替未执行核心模型的情况。

## 完整 panel 官方本地评分

3357 个 E8.5 recipient、3411 个 E9.5 report target，输入 32285 列；同一反复使用的 report 划分。参照与路线同表（参照为本环境重评，另存冻结旧环境 SCORER.json 作语境）：

| 参照 | DE↑ | 方向↑ | Energy↓ | MMD↓ | Variogram↓ |
|---|---:|---:|---:|---:|---:|
| v0035（骨架） | 0.5926 | 0.5852 | 0.14221 | 0.00937 | 0.000398 |
| v0036（备份） | 0.5741 | 0.5648 | 0.15512 | 0.00919 | 0.000418 |
| v0038 n2covot | 0.5926 | 0.5793 | 0.15150 | 0.00925 | 0.000408 |
| mix36×38 50/50 report 类比（诊断，非 v0051 本体） | 0.5926 | 0.5729 | 0.14049 | 0.00959 | 0.000387 |

对现役 v0051=53.92 的净变化对照：v0051 是 final-scope 已提交 artifact（服务器 53.92；子项 de 47.2/dir 60.0/mmd 56.7/vario 50.6），本轮六条均未提交，服务器对照在用户回填前为 pending。本地信号：ostabmix 的 de 改善落在现役家族最弱子项（de）上且无 de↔variogram 互换，是本轮最强提交优先信号；nbidir 的 dir/Energy/Vario 改善以 de 为代价，是次强取舍信号。

## 实际模型与训练边界

只使用官方 E8.5 16787 细胞、E9.5 17057 细胞，共 32285 基因；report 使用对应 60% 训练、20% report、20% reserved；各阶段互斥且完备。最终全量已复用冻结 r2joint 全量模型，输出 5118×32285。4 个已评分父版本矩阵（v0035/v0036×report/final）逐值复现；公共 mass 库和 latent 由冻结模型产生，全部 SHA 锁定（CACHE_LOCK 37 项）。

- ocovstab 实际：per-scope 冻结投影距离（report 10 类型中位 0.9491；final 11 类型含 NCC 中位 0.9498）→ 类型级强度（稳定 0.5/不稳定 0.125）＋k=8 逆距离平方加权抽样；类型不足 k 个回退 k=1。
- osoftcov 实际：f1soft 冻结 GMM（32 维标准化、diag、reg_covar .05）软责任联合权重（logw=0.5·log(密度权重)+0.5·(responsibility@step)）＋covot k=1 重选（8 维、cov_shrink 0.1、强度 0.5）。
- ostabmix 实际：f2stable 4-part 稳定性证据 → per-type 阳性方向稳定基因占比 ≥0.5 → 0.7，否则 0.3；非 common 类型（EXEM 等）保留原骨架 identity 行；混合只作载体、新组件=per-type 自适应比例。
- nwasser 实际：POT ot.emd 精确计划（32 维标准化、双侧均匀质量、边缘残差 ≤5.1e-16）→ 早/晚位移场 → k=8 距离加权位移均值 → 最近 query cell 放置。
- nconf 实际：每类型 train 50/50 split（fit/校准，seed 20260921）、covot 映射只在 fit 半拟合、校准半 nonconformity 得分=映射 target 到最近晚侧潜形距离、R=⌈(n+1)(1−α)⌉/n 分位（α=0.1）；半径内逆距离加权抽样、无候选回退 k=1。
- nbidir 实际：同一精确计划的行/列双向读取 → 一致性距离 → logw=−d²/(2σ²)（σ=该类型 train 中位）替换密度分类器权重 → joint_donors。

输出行名是 synthetic slots，不能当作同一真实细胞轨迹；预测类型在 uns/obs 记录，实际 donor 或父模型行号在 FINAL_OPERATOR.json。官方 T1 评分不直接读取我们写入的 celltype 标签。

## 环境修复与运行前修订（2026-10-07）

- **环境修复**：自 09-30 后用户级 numpy 升至 2.4.6，与 anaconda 的 h5py 3.11/xarray 旧版 ABI 冲突（anndata 与 scorer 导入链全断）。修复：用户级安装 h5py 3.16.0 + xarray 2026.9.0；修复后 anndata 0.12.19 + veckit scorer 导入与重评验证通过（v0035 参照重评与旧环境数值逐位一致）。冻结父模型拟合于 numpy 1.26.4/sklearn 1.5.1；跨版本 SVD 潜形漂移 3.4e-05（相对 5.3e-07）未翻转 donor（0/3357）与 mass（0.0 diff），v0035/v0036 report/final 四个矩阵字节级复现成立。
- **POT 修订**：原冻结 numpy Sinkhorn（ε=0.05）在原始平方距离尺度上发散（exp 溢出）且 LSE 每迭代 ~0.17s 太慢；POT 经环境修复恢复可用，改用 ot.emd 精确 LP（无 ε 依赖、无收敛问题；最大类型 2405×871 边缘残差 ≤1e-16、~0.9s）。
- **ocovstab per-scope 修订**：首次批次暴露 NCC 无 report-scope 距离（report 划分无 NCC train 细胞），改 per-scope 来源（report 用 REPORT_OPERATOR、final 用 FINAL_OPERATOR）。
- **ostabmix 非 common 修订**：无冻结比例的阶段特有类型保留原骨架 identity 行。
- **验证器修订**：模型 cfg 比对改为该 lane 自己 run 目录里的设计快照（INPUT_LOCK 锁定）；osoftcov 协方差检查改为收缩协方差（与拟合一致）。
- **批次收据**：v4 批次 ocovstab/nwasser 失败后重跑完成，原部分收据保留于 BATCH_RESULT_v4_partial.json，BATCH_RESULT.json 如实更新。

## 验收与复现

- 单元测试：`tests/t1_six/test_ops.py` 13 项全过（exact plan 边缘、位移场恒等、稳定性两级规则、adaptive_sides 确定性/配对计数/骨架回退、conformal 半径与模式、一致性权重界、无 truth 输入结构守卫）。
- 独立进程重放：6 lane × final 模型 reload → predict 字节级相等（MODEL_REPLAY PASS×6）；validate 独立进程重放 report/final 双 scope ×6 全部 ACCEPTED。
- 验收：reports/t1_six_20261007/VALIDATION.json PASS（requirements 3+3/6 路线/6 scorer）；METRICS.json；zip CRC+SHA 逐成员验证 PASS。
- 复现命令见 scripts/t1_six/README.md。

## Handoff 及限制

任务 T1:val，所有本轮候选文件 parent=v0035；模型另复用 v0036/v0038 及历史组件。完整 artifact 路径、SHA256、contract 以 submissions/INDEX.tsv 及 zip 传输 manifest 为准。

- v0057 / osoftcov：[t1_val__osoftcov__v0057.h5ad](../../submissions/candidates/T1_val/v0057_six_osoftcov/submission.h5ad)，未提交/未评分。
- v0058 / ostabmix：[t1_val__ostabmix__v0058.h5ad](../../submissions/candidates/T1_val/v0058_six_ostabmix/submission.h5ad)，未提交/未评分。
- v0059 / nconf：[t1_val__nconf__v0059.h5ad](../../submissions/candidates/T1_val/v0059_six_nconf/submission.h5ad)，未提交/未评分。
- v0060 / nbidir：[t1_val__nbidir__v0060.h5ad](../../submissions/candidates/T1_val/v0060_six_nbidir/submission.h5ad)，未提交/未评分。
- v0061 / ocovstab：[t1_val__ocovstab__v0061.h5ad](../../submissions/candidates/T1_val/v0061_six_ocovstab/submission.h5ad)，未提交/未评分。
- v0062 / nwasser：[t1_val__nwasser__v0062.h5ad](../../submissions/candidates/T1_val/v0062_six_nwasser/submission.h5ad)，未提交/未评分。

科学成熟度 EXPLORATORY_LOCAL：相邻两个时间点不能唯一识别未来动力学，组成变化可能混有取样和注释差异；report 划分反复使用，细胞级分割不是独立胚胎验证。**E10.5/E12.5 真值评分 NOT_RUN_NO_TRUTH；独立胚胎验证 NOT_AVAILABLE；服务器评分 NOT_RUN。** 不能以本地指标代替上述缺失证据。无新外部生信数据下载，无需新增数据索引条目；blocks_submission: false。

建议依据逐项结果与方法差异安排提交预算：优先 ostabmix（de 改善落在现役家族最弱子项上）、次选 nbidir（dir/Energy/Vario 改善取舍）；软 donor 重选家族（ocovstab/ osoftcov/nconf/nwasser）本地全劣，如无服务器意外不建议优先。上传动作未执行。
