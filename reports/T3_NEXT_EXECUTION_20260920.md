# T3 六路线实现与执行交付 — 2026-09-20

六条路线代码已实现；实际执行得到四个合格候选、两条未通过门槛、两条因输入不齐阻塞。未上传、未评分，当前 selection 不变。机器结果汇总见 [执行结果](T3_NEXT_EXECUTION_20260920.json)，原方案见 [设计提案](T3_NEXT_ROUTES_20260920.md)。

| 路线 | 实际计算与结果 | 候选/限制 |
|---|---|---|
| 1 WT 排序重建 | GRAPH 与 SIGNMAX 的逐基因边际值完整保留，用 WT 排序重新分配；两者 contract PASS | v0026、v0027；CANDIDATES_READY |
| 2 异质响应与完整 WT donor 替换 | 4 个空间块交叉拟合、同类型/块匹配；自适应与随机对照实际均替换 1,840 行，排除自身及表达相同 donor；contract PASS | v0030、v0031；CANDIDATES_READY |
| 3 残差保留的条件机制 | 使用全部 24,826 个 WT 细胞，356 个节点，线性和有界样条均完成；零干预恒等检查通过 | FAILED_DISASTER：负值裁剪比例 6.1901% / 2.6755%，均超过预声明 1%；无候选 |
| 4 全转录组隐变量桥接 | 实际读取 68,910 个 atlas 细胞、27,669 基因；选择 64 个 panel 外候选中介；完成 100 个遮蔽基因映射验证 | FAILED_MAPPING_GATE；反事实双模型 NOT_RUN_GATE_FAILED，无候选 |
| 5 非细胞自主信号 | 信号增量传播、关闭信号及置换对照代码完成；完成现有来源审计 | BLOCKED_PROVENANCE；现有 OmniPath 快照缺逐边 ligand/receptor/target 和来源、许可等必需字段，正式模型 NOT_RUN |
| 6 多扰动学习 | Ridge 与可训练双层 GCN、按扰动基因留出、过滤和推理入口完成；完成数据就绪审计 | BLOCKED_DATA_NOT_READY；无合规多扰动训练输入，正式训练/评估/推理均 NOT_RUN |

路线三的空间留出 WT MSE：线性 1.26577、样条 1.26404，类型均值基线 1.28743。这只是 WT 预测诊断，不能抵消干预输出裁剪超限，亦不能证明 Gata4 KO 有效。356 节点共有 29 组相同父节点输入，改为分组多输出 Ridge；数值等价测试通过，数据、节点、正则化和对照未减量。早期逐节点版本中断状态保留。

路线四映射覆盖率 94.0932%，但 5,648 个空间留出细胞上的遮蔽基因 MSE 为 1.64310，差于类型均值基线 1.46161，因此停止后续反事实拟合。Unknown 和 Caudal Epiblast 未映射。这里的空间块来自同一标本，不等于独立生物重复。

路线五须补充具有逐边来源、许可及过滤证据的 ligand–receptor–target 输入；路线六须补充通过 T3 防火墙的单一上下文、多单基因扰动数据（至少 20 个扰动基因、每基因至少 20 个细胞）、对照和对齐的图/嵌入。接口与许可回执格式见 [实现说明](../scripts/t3_next/README.md)。GCN 是本项目自定义比较模型，不是 GEARS/TxPert 的论文复现；合成数据训练测试不代表生物训练已执行。既有外部链接仍保持 model_input=false。

## 交付与验收

- 上传包：[t3next6__t3__upload__20260920.zip](../deliveries/t3next6__t3__upload__20260920.zip)，仅含 v0026、v0027、v0030、v0031 四个 h5ad 及四份身份/证据清单。状态 READY_NOT_SUBMITTED。
- 身份、父版本、SHA256 和 contract 以 [submissions/INDEX.tsv](../submissions/INDEX.tsv) 为准；均为 score_pending。分数登记表本次未修改，上传后需回填四个总分、子项和页面证据。
- v0028/v0029 为路线二首次生成的未提交候选，事后发现随机对照含自 donor，实际替换行数不等；已登记 invalidated_unsubmitted，文件保持原样且未打包。修复后重跑得到 v0030/v0031。
- 定向测试：`LD_LIBRARY_PATH=/opt/anaconda3/lib OPENBLAS_NUM_THREADS=8 python -m pytest tests/t3_next -q`，12 passed。覆盖边际保持、零干预、完整 donor/分层匹配、无自身或相同 donor、信号增量、留出与过滤、实际合成 GCN 训练、遮蔽基因隔离和多输出求解等价。
- 包装程序核对 INDEX、各候选 SHA256、zip 成员哈希和 CRC；候选 writer/validator 核对保护字段和完整 7,449×500 输出。
- 配置已冻结于 `configs/t3_next/design.json`；各 run 保存 INPUT_LOCK、源码快照及 RESULT/FAILURE。正式执行目录见机器汇总。早期环境导入、坐标 dtype 核对、相对路径失败均保留，没有覆盖重跑目录。
- 使用已缓存 atlas，没有新增外部下载；修复生信索引三个失效 v5 路径为实际 v7 输入并登记 SHA256，汇总同步更新。
- 没有目标匹配的 Gata4 隐藏真值，完整本地 scorer 为 NOT_RUN_NO_MATCHED_GATA4_TARGET；不使用 Mab21l2 目标错配分数选择候选。邻域半方差只是描述性检查，不等于服务器 variogram。

任务状态：可执行计算已收口；等待四候选人工上传/回分及路线五、六合规输入。科学状态仍为 NOT_IDENTIFIABLE，blocks_submission: false。未启动 GPU、未替换已评分 artifact、未宣称新 best。
