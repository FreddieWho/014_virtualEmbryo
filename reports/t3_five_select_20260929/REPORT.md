# T3 五路线完整执行、选三交付

五条全部实现并执行，按事前规则选三；唯一提交包：[t3five3__t3__upload__20260929.zip](../../deliveries/t3five3__t3__upload__20260929.zip)，内含 **3 个 h5ad + 4 份 manifest**。状态 READY_NOT_SUBMITTED / score_pending。现役 v0048=47.93 不变。

## 五条执行结果

| 路线 | 实现与全量运行 | 开发 WT 组均值 MSE↓ | 审计 WT 组均值 MSE↓ | 决策 |
|---|---|---:|---:|---|
| r1active 活动量门控来源组合 | 完整 7449×500 / PASS | 0.151705875 | 0.462168577 | PARKED：同族开发排名未入选；完整输出保留 |
| r2gene 基因同号来源组合 | 完整 7449×500 / PASS | 0.151410562 | 0.461504202 | v0057 入包，未提交/未评分 |
| r3bag 四次 bootstrap hurdle | 完整 7449×500 / PASS | 0.156339810 | 0.474023667 | v0059 入包，未提交/未评分 |
| r4spline 非线性 hurdle | 完整 7449×500 / PASS | 0.154562035 | 0.472640024 | v0058 入包，未提交/未评分 |
| r5local 局部残差校正 | 完整 7449×500 / PASS | 0.157153581 | 0.479800470 | PARKED：同族开发排名未入选；完整输出保留 |
| 不调整WT | 局部诊断参照 | 0.203425867 | 0.587620573 | 非新候选 |
| 训练块拟合的H基准 | 局部诊断参照 | 0.156071170 | 0.474304399 | 非新候选 |

事前选拔：来源族选1，学习族选2；开发块 MSE 排序，固定顺序打破同分。SELECTED.json 锁定后才算审计块，审计未改名单，工程 fallback 未触发。r1active 与 r5local 没有工程失败，只因固定族内名额未入包。bootstrap 开发结果略差于 H，入选理由是学习族第二名及方法差异，不能描述为已胜过基准。

来源组合在开发及审计上均较H低；非线性hurdle有小幅同向信号。局部残差模型的 factual MSE 在三种新模型中最低，但高低活动组响应诊断较差，说明表达重构更好不能推出干预预测更好。本轮不据此改参数或挽救路线。

## 实际计算与证据边界

训练块0/1、开发块2、审计块3，均来自同一WT胚胎的 z 四分块。开发 **3组，277 high / 783 low，排除30组**；审计 **2组，91 high / 297 low，排除25组**。MSE 对499个非Gata4响应基因的组均值计算，按 high人数×499 加权；不是逐细胞配对误差，细胞不是生物重复。资格阈值及低活性干预值只从训练块拟合，组明细/排除原因见 DEVELOPMENT.json 与 AUDIT_BLOCK.json。所有路线一致使用同组。

局部比较的H、bootstrap、样条及残差模型仅用训练块拟合；最终推断使用全 **24826 WT细胞**。bootstrap 在局部和全量各实际拟合4个Hurdle，逐类型有放回抽样；样条两阶段分别训练，knots只取训练正活动量分位点；残差 donor 排除相同原始行ID，包括干预查询。最终来源组合复用已评分H/G组件，全量训练门控或gene mask；最终同号mask为292个响应基因。H/G精确复现原文件，源角色和已有数据哈希复核通过。没有新增外部生信数据，也没有重训或冒称重训冻结的G。

WT空间块属于反复探索过的单胚胎数据，类型覆盖很小、混杂和dropout未消除；来源组合在WT低活性代理干预中使用固定来源rate，这不等于真实KO剂量响应。**匹配Gata4 KO官方评分：NOT_RUN_NO_MATCHED_GATA4_TARGET；服务器评分：NOT_RUN；科学结论：NOT_IDENTIFIABLE。** 科学限制不阻断合规提交，blocks_submission:false。

## 工程验收

- 五条完整输出 contract、有限/非负值、Gata4=0、500基因及7449行、spatial_3D身份、原模型重放、灾难边界、旧候选及五条互相去重全部 PASS。
- 6 项针对性测试通过；独立进程14项验收 PASS，覆盖训练边界、四个bootstrap的类型计数、样条训练knots、残差供体训练集、开发排名复算、先锁名单后审计、输入与执行代码哈希、三件登记内容。
- ZIP 恰含3个 h5ad，成员短名规范、SHA256 和 CRC 全部通过。receipt 位于同名 .receipt.json。
- 首次进程在SciPy导入前因系统 libstdc++ 的 GLIBCXX_3.4.29 缺失退出，未生成run；设置 LD_LIBRARY_PATH=/opt/anaconda3/lib 后在正式项目完整运行，未跳过或替代任何计算。完整运行约114秒，日志随报告保存。

## Handoff

任务 T3:gata4；三件父版本均v0048，WT carrier=v0009；r2gene还使用已评分v0046来源组件。候选ID、canonical artifact、完整SHA256和contract以 [submissions/INDEX.tsv](../../submissions/INDEX.tsv) 为唯一登记权威，ZIP的MANIFEST用于传输核验。

- **v0057 / r2gene**：[t3_gata4__r2gene__v0057.h5ad](../../submissions/candidates/T3_gata4/v0057_five_select_r2gene/submission.h5ad)；run [artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r2gene/registered](../../artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r2gene/registered)。建议优先来源组合v0057，其次非线性v0058，bootstrap v0059用于新模型分歧；均未提交/未评分。
- **v0058 / r4spline**：[t3_gata4__r4spline__v0058.h5ad](../../submissions/candidates/T3_gata4/v0058_five_select_r4spline/submission.h5ad)；run [artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r4spline/registered](../../artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r4spline/registered)。建议优先来源组合v0057，其次非线性v0058，bootstrap v0059用于新模型分歧；均未提交/未评分。
- **v0059 / r3bag**：[t3_gata4__r3bag__v0059.h5ad](../../submissions/candidates/T3_gata4/v0059_five_select_r3bag/submission.h5ad)；run [artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r3bag/registered](../../artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1/r3bag/registered)。建议优先来源组合v0057，其次非线性v0058，bootstrap v0059用于新模型分歧；均未提交/未评分。

未选两条完整表达、模型、contract：[artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1](../../artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1)；各lane/research.h5ad 仅为研究输出，不在上传包、未登记为候选。五模型保存在 full_models/，训练局部模型在 local_models/，抽样原始行ID随model.pkl保存。

执行入口：`env LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_five_select.run --run <新的不可变run目录>`；验收入口 `env LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_five_select.validate --run artifacts/t3_five_select/T3-FIVE-SELECT-20260929-v1`。设计及固定参数见 [设计](../T3_FIVE_SELECT_DESIGN_20260929.md) 与 configs/t3_five_select/design_20260929.json。

风险：没有目标KO真值；来源迁移、空间混杂、稀疏组覆盖、bootstrap信号很弱。建议保持当前best，等待服务器证据。**上传前先核对旧v0049–v0056是否已提交，提供服务器分数和原始证据，避免重复提交。** 当前交付无工程blocker，不自动上传。
