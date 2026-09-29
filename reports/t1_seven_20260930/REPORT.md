# T1 七路线执行报告（2026-09-30）

用户要求的 **3条新路线＋2条失败案例优化＋2条成功案例优化** 已全部实现并实际运行。七条均执行report与future模型及完整32285基因官方本地scorer。参数事前冻结，未根据结果续调。当前服务器best仍v0035=53.43，本轮均未提交/未评分。

设计与论文检索：[T1_SEVEN_DESIGN_20260930.md](../T1_SEVEN_DESIGN_20260930.md)。[提交包](../../deliveries/t1seven__t1__upload__20260930.zip)，成员数以同名receipt及manifest为准。候选与哈希唯一登记在submissions/INDEX.tsv；报告不维护第二份身份登记表。

## 七条路线与结果

| 分类 | 路线 | 候选/工程结果 | 相对v0035本地五项（改善/持平/变差） |
|---|---|---|---|
| 新尝试 | n1moment 矩约束重加权 | v0037 | 1/0/4 |
| 新尝试 | n2covot 协方差输运整行投影 | v0038 | 1/1/3 |
| 新尝试 | n3graph 图平滑阶段密度 | v0039 | 0/0/5 |
| 失败优化 | f1soft 软状态替代硬聚类 | v0040 | 1/0/4 |
| 失败优化 | f2stable 方向稳定性选择收缩 | v0042 | 2/1/2 |
| 成功优化 | s1growth 增强组成趋势 | v0041 | 2/0/3 |
| 成功优化 | s2mix 高分双模型70/30整行混合 | v0043 | 0/1/4 |

新尝试是项目新机制，不是学术原创声明。n1是惩罚矩匹配，裁剪后不保证精确矩平衡；n2只做Gaussian协方差映射与实测支持上的整行投影，不是完整动态OT；n3是图正则阶段判别，不是生物谱系识别。不存在用“文献中方法名”代替未执行核心模型的情况。

两条失败优化分别追溯v0031（硬状态50.51）和v0033（普遍收缩51.10）；旧失败原因只是假设。f1软责任与平滑、f2方向选择收缩均在新best骨架上执行，对旧版本改善不能单独归因于修复；相对v0035是更严格的净变化对照。成功优化分别针对v0035组成趋势和v0035/v0036互补取舍。

## 完整panel官方本地评分

3357个E8.5 recipient、3411个E9.5 report target，输入32285列；同一反复使用的report划分。DE与方向越高越好，其余三项越低越好。这里是原始指标，不是服务器skill或总分。

| 路线 | DE↑ | 方向↑ | Energy↓ | MMD↓ | Variogram↓ |
|---|---:|---:|---:|---:|---:|
| v0035 best参照 | 0.5926 | 0.5852 | 0.14221 | 0.00937 | 0.000398 |
| v0036备份参照 | 0.5741 | 0.5648 | 0.15512 | 0.00919 | 0.000418 |
| n1moment | 0.5556 | 0.5834 | 0.15258 | 0.00914 | 0.000419 |
| n2covot | 0.5926 | 0.5793 | 0.1515 | 0.00925 | 0.000408 |
| n3graph | 0.537 | 0.5746 | 0.16156 | 0.01018 | 0.000429 |
| f1soft | 0.5741 | 0.5859 | 0.14517 | 0.00954 | 0.000409 |
| f2stable | 0.5926 | 0.5836 | 0.14192 | 0.0094 | 0.000397 |
| s1growth | 0.537 | 0.5932 | 0.16275 | 0.00896 | 0.000419 |
| s2mix | 0.5926 | 0.5806 | 0.14906 | 0.00957 | 0.0004 |

按这五项点估计，对v0035无退步且有改善：无；无改善且有退步：n3graph, s2mix。其余为取舍，不强造单一总分。未采用结果导向换算法或参数救援。

已知反例：v0036服务器53.36接近v0035的53.43，但旧本地多项更差。因此即使本轮本地五项改善，也只能给出提交优先信号，不能晋级现役、承诺提分或证明发育机制。

## 实际模型与训练边界

只使用官方E8.5 16787细胞、E9.5 17057细胞，共32285基因。report使用对应60%训练，20%report、20%reserved；各阶段互斥且完备。最终全量已发布两阶段拟合或复用相应全量模型，输出5118×32285。4个已评分父版本矩阵（v0035/v0036×report/final）逐值复现；公共mass库和latent由这些冻结模型产生，全部SHA锁定。

- n1实际优化16项latent一二阶矩的有惩罚对偶目标，保存收敛记录。
- n2实际拟合类型内协方差、Gaussian运输矩阵、均值位移，并在同类型recipient整行库投影；不能生成该库完全不支持的细胞状态。
- n3实际建立类型内15NN图并迭代求解，保存残差和训练节点原始ID；查询排除同一行，阶段先验校正。
- f1实际拟合diag-GMM，保存两阶段软责任计数；没有把标签硬切再称为软模型。
- f2固定4份训练分区，分别重算零率和阳性均值方向；≥3份一致保留原步，否则乘0.25。保留完整分区证据、权重和修改后的mass模型。
- s1仅加强类型组成趋势到0.75，倍率界仍0.5–2；s2固定70/30分层整行混合，不平均表达。

共同类型支持不足时保留原骨架。输出行名是synthetic slots，不能当作同一真实细胞轨迹；预测类型在uns记录，实际donor或父模型行号在FINAL_OPERATOR.json。官方T1评分不直接读取我们写入的celltype标签。

## 验收与复现

8项定向测试通过（TESTS.json/tests.log）；独立进程对七条report/final共14个完整输出重放，并检查训练行界、方法特定参数、代码/输入哈希、源组件身份、候选唯一性、contract及全部7次完整panel评分终态。证据VALIDATION.json。归档ZIP的成员SHA与CRC通过，无自动上传。

scorer接收全部32285基因；沿用官方内部默认energy≤1500细胞、MMD≤2000细胞和30PC、variogram≤1500细胞/20000基因对；没有偷偷换小panel，也不把内部抽样称为全组合穷举。

执行日志与每条终态在artifacts/t1_seven/T1-SEVEN-20260930-v1，模型为report_model.pkl/final_model.pkl，完整研究输出report_prediction.h5ad/full_prediction.h5ad，即使工程未入包也保留。统一命令见scripts/t1_seven/README.md。源代码快照、模型和公共cache是完整复现输入。

## Handoff及限制

任务T1:val，所有本轮候选文件parent=v0035；模型另复用v0036及历史mass/density组件。完整artifact路径、SHA256、contract以submissions/INDEX.tsv及ZIP传输manifest为准。

- v0037 / n1moment：[t1_val__n1moment__v0037.h5ad](../../submissions/candidates/T1_val/v0037_seven_n1moment/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/n1moment](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/n1moment)。
- v0038 / n2covot：[t1_val__n2covot__v0038.h5ad](../../submissions/candidates/T1_val/v0038_seven_n2covot/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/n2covot)。
- v0039 / n3graph：[t1_val__n3graph__v0039.h5ad](../../submissions/candidates/T1_val/v0039_seven_n3graph/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/n3graph](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/n3graph)。
- v0040 / f1soft：[t1_val__f1soft__v0040.h5ad](../../submissions/candidates/T1_val/v0040_seven_f1soft/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/f1soft](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/f1soft)。
- v0042 / f2stable：[t1_val__f2stable__v0042.h5ad](../../submissions/candidates/T1_val/v0042_seven_f2stable/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/f2stable](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/f2stable)。
- v0041 / s1growth：[t1_val__s1growth__v0041.h5ad](../../submissions/candidates/T1_val/v0041_seven_s1growth/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/s1growth](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/s1growth)。
- v0043 / s2mix：[t1_val__s2mix__v0043.h5ad](../../submissions/candidates/T1_val/v0043_seven_s2mix/submission.h5ad)，未提交/未评分；模型、评分及检查见 [artifacts/t1_seven/T1-SEVEN-20260930-v1/s2mix](../../artifacts/t1_seven/T1-SEVEN-20260930-v1/s2mix)。

科学成熟度EXPLORATORY_LOCAL：相邻两个时间点不能唯一识别未来动力学，组成变化可能混有取样和注释差异；report划分反复使用，细胞级分割不是独立胚胎验证。**E10.5/E12.5真值评分NOT_RUN_NO_TRUTH；独立胚胎验证NOT_AVAILABLE；服务器评分NOT_RUN。** 不能以本地指标代替上述缺失证据。无新外部生信数据下载，无需新增数据索引条目；blocks_submission:false。

建议依据逐项结果与方法差异安排提交预算，先回填本轮提交后的服务器分数及原始证据，再讨论替换v0035。上传动作未执行。
