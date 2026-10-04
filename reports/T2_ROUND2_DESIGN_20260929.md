# T2 第二轮：三新两优化 × 三 board（执行前冻结）

用户授权：专注 T2 三个子任务（board），每个 board 5 个可提交 h5ad，其中 3 条新路线探索、2 条既有路线优化改良（允许合并多条已有路线或单路线迭代）。可参考 REVIEW.md 历史教训与联网检索。本文件在任何训练/构建运行之前冻结；参数同时落盘 `configs/t2_round2/design_20260929.json`。

## 当前权威锚点（服务器已评分）

| board | 现役最佳 | 分数 | 次优/相关 |
|---|---|---|---|
| T2:embryo:val_interp | v0010 b4_t2_r2_l2_mean_mass_bridge | **62.29** | v0009 mean-only 61.79；v0002 G1 scale 60.1 |
| T2:heart:val_interp | v0013 b4_t2_r2_l2_mean_mass_bridge | **62.04** | v0012 mean-only 56.27；v0009 FGW 57.3 |
| T2:heart:val_extrap | v0001 baseline pseudobulk_shift | **50.53** | v0011 shrink 50.64（已评分未入门户选择） |

子项余量（服务器子项，REV­IEW/子项台账）：embryo variogram 52.0 / de_score 54.1 / scale 90.8 有余量，occupancy_dice 与 d2_shape 已证服务器反向不得追；heart variogram **28.4** 极端异常、de_score 60.6 有余量，scale 97.9 近满；extrap 八项全部 46–53 宽余量，无一项拉满。

## 已关闭、本轮不重开（服务器或预声明判据否定）

- 均值场 + 加性空间对比（任意幅度；L-008 未解，LOWAMP 服务器 −0.52）
- 空间平滑 / kNN 平滑 delta（外推 ×5 全负）；FGW ε/求解器微调（近平庸化，TIE）
- 外推位移幅度族（damp/time/popmix，局部耗尽且用户关闭未评分）
- 表达↔坐标重排（B1-A4 J1）、moscot/MIOFlow/spateo/大生成模型
- 追 occupancy_dice / d2_shape（两个插值板服务器反向）
- embryo 行-点配对（L-006）；E-N2 VGM / H-I1 rank-k（预测量已证伪）
- 网格搜索；按服务器分数改方法；本地 proxy 充当 leaderboard 结论

## 本地-服务器关系门（M0 + 附录 B，冻结）

- embryo：本地指标（含 neighborhood_mmd）只记录、不否决；服务器仲裁优先（Spearman +0.833 反向已证实）。
- heart_interp / heart_extrap：`neighborhood_mmd` 相对现役同靶劣化 >5% 标记 LOCAL_DEGRADE_FLAG，写入报告与包 manifest，不自动拦截交付（用户要求每 board 5 件全部可提交；旗帜供用户决定消耗配额）。
- extrap 的 R1 proxy gate 已在两个族上方向错误（shrink 局部负服务器正、spatial 反之），本轮只做记录，不作否决。

## 冻结路线（每 board：新 ×3 + 优化 ×2）

记号：`λ` = board 冻结插值权重（embryo 1/3，heart 1/2）；`shift_s` = 类型 s 的均值位移；mass = v0010/v0013 同款组成重采样（largest-remainder + 有放回补满，seed 冻结）。

### T2:embryo:val_interp（父版本 v0010；版本 v0011–v0015）

| lane | 版本 | 类型 | 冻结定义 |
|---|---|---|---|
| e_n1_qbridge | v0011 | 新 | 分布/分位数桥 + mass：每共享类型 s、每基因 g，取两端经验分位函数 Q_L/Q_R，Q*(u)=(1−λ)Q_L(u)+λQ_R(u)；父行按其在 (s,g) 内的经验秩 r 映射到 Q*(r)，负值截 0（零质量隐式处理）；(s,g) 任一端 <30 细胞退回均值位移；未匹配类型保持父版本。行选择与 v0010 逐名一致（同算法同 seed 重放断言）。 |
| e_n2_trend3 | v0012 | 新 | 三阶段趋势桥：**E6.75 首次进入任何候选**。三阶段齐全的类型：μ(t) 对 (6.75,7.25,8.0) 线性回归，取 μ(7.5) 为位移目标；仅两端共享→v0010 位移；未匹配→父。mass 份额：log 比对三阶段线性趋势取 7.5，截非负归一；未匹配沿用 v0010 规则（0.5pP+0.5pL）。 |
| e_n3_substate2 | v0013 | 新 | 组成粒度轴（"多少类型"）：括号两端合并细胞在 panel 对数空间 PCA-10 上按粗类型内 KMeans k=2（seed 冻结；类型总细胞 <120 不分裂）得到子状态；子状态两端各 ≥30 细胞者在子状态级做均值桥+mass，否则回落粗类型级。 |
| e_o1_shrinkmerge | v0014 | 优化（合并） | v0010 × v0011(extrap shrink) 两已评分机制合并：(s,g) 位移按 t 统计量收缩 w=|t|/(|t|+C)，C=2.0 冻结，收缩后施加；mass 与 v0010 逐名一致。 |
| e_o2_scalmass | v0015 | 优化（合并） | v0010 × G1 尺度机制合并：表达与行选择同 v0010 完全一致；质量重采样后点云 RMS 半径偏离父版本目标，统一重缩放坐标使重采样云 RMS 等于 v0002 形式 log-RMS 插值目标（G1 已评分机制，本板 +3.4 的来源）。 |

### T2:heart:val_interp（父版本 v0013；版本 v0016–v0020）

| lane | 版本 | 类型 | 冻结定义 |
|---|---|---|---|
| h_n1_qbridge | v0016 | 新 | 同 e_n1 机制，λ=0.5；直指 variogram 28.4 极端异常（保秩分布重映射替换常数位移）。行选择与 v0013 逐名一致。 |
| h_n2_curve95 | v0017 | 新 | **E9.5 首次进入本 board**：三阶段类型 (s,g) 用 (8.25,8.75,9.5) 二次 Lagrange 在 8.5 求值（权重 0.4 / 0.6667 / −0.0667，无调参）；缺任一阶段→v0013 均值桥。mass 份额同法二次求值（log 比空间，截非负归一）。 |
| h_n3_cmjoin | v0018 | 新 | 组成粒度轴（真实注释）：cm_celltype 经冻结字表归组 {CC/CM,vCM1,vCM2,aCM1,aCM2→CM；FHF/JCF1,FHF/JCF2,FHF/JCF→FHFJCF；aSHF1,aSHF2,aSHF→aSHF；pSHF→pSHF；其余→自身/Unknown}；联合状态=粗 celltype×cm_group（cm=Unknown 用粗类型）；联合状态两端各 ≥30 细胞者在联合级做均值桥+mass，否则回落粗类型。 |
| h_o1_shrinkmerge | v0019 | 优化（合并） | v0013 × shrink（同 e_o1，C=2.0）。 |
| h_o2_libnorm | v0020 | 优化（迭代） | v0013 + 文库大小重标定：桥+mass 后，每行按其 (s) 内文库秩映射到 λ 插值的两端经验文库分布（保秩、非负；机制即既有 `pseudobulk_shift_row_norm` 变体，从未在插值板提交）。 |

### T2:heart:val_extrap（父版本 v0001 baseline；版本 v0017–v0021）

| lane | 版本 | 类型 | 冻结定义 |
|---|---|---|---|
| x_n1_lineage | v0017 | 新 | **谱系映射 delta**：17 个 E9.5 独有粗类型当前零位移（最大结构缺口）。祖先映射用确定性规则跑前生成并冻结于 INPUT_LOCK：每个 E9.5 独有类型，在 E8.75∩E9.5 共享且 E8.75 侧 ≥30 细胞的候选类型（即 baseline delta 有定义的 5 个类型）中取 panel 对数空间 pseudobulk 余弦最近者；Δ_t = Δ_ancestor（damp=1.0，与 baseline 同约定）；5 个共享类型保持 baseline 位移；表达= v0001 + 谱系位移，几何/组成不变。 |
| x_n2_trend3 | v0018 | 新 | **E8.25_late 首次进入候选**：三阶段类型 (s,g)：日速度 u1=(μ8.75−μ8.25)/0.5，u2=(μ9.5−μ8.75)/0.75；Δ=v2+0.5·(u2−u1)·0.75（加速度项阻尼 0.5 冻结）；缺阶段类型保持 baseline Δ=v2。几何/组成不变。 |
| x_n3_compmix | v0019 | 新 | **组成趋势外推**（本板首次）：三阶段份额 log 比线性趋势（按天）外推 E10.5，截非负、归一、单类型倍率 ≤2 封顶（冻结）；按预测份额重采样 v0001 行（25179，largest-remainder+有放回，R2 同机同 seed）；表达=v0001 完全一致。 |
| x_o1_trendshrink | v0020 | 优化（合并） | x_n2 趋势位移 × t 收缩（C=2.0，v0011 已评分机制）合并；行/几何同 v0001。 |
| x_o2_shrinkcomp | v0021 | 优化（合并） | v0011 收缩表达 × x_n3 组成趋势重采样合并（收缩机制本板已评分 50.64；组成机制两插值板已评分 +2.14/+4.79）。行选择与 x_n3 逐名一致。 |

消融结构：x_n2/x_o1 仅差收缩；x_n3/x_o2 仅差表达源；e_n1/e_o1 对照分位映射 vs 收缩均值；e_o2 隔离尺度机制。

## 数据、工程与门

- 输入全部为本项目已批准官方数据：data/E6.75/E7.25/E8.0/E8.25_late/E8.75/E9.5.h5ad；无外部数据；target_used=false；不读取 E7.5/E8.5/E10.5 真值。
- 父 artifact 只读、SHA 锁：v0010/v0013/v0001/v0011 逐位核对后使用；已评分文件不覆盖。
- 工程门（冻结）：逐行 library 比 q01≥0.25、q99≤4；方差比 0.1–10；X 有限非负；clip 分数只披露不否决（v0013 60% clip 已胜）；n_obs 与 panel 精确符合 board contract；几何/obs/var/layers 与父逐位一致（组成 lane 按 R2 既有 FAIL_BY_DESIGN_ACCEPTED 四类逐项豁免）。
- 每 lane 独立确定性重放（同 config 同 seed 重跑字节一致）；contract 检查走 `virtual_embryo_tools.contract_io.validate_h5ad_case`，豁免字符串集合跑前冻结。
- 本地评价：embryo 同靶 E7.25 pseudo-target（ref E6.75，seed 20260830，记录-only）；heart_interp 同靶 E8.75 pseudo-target（ref E8.25_late）；extrap R1 proxy（E9.5 心脏 cm 子集靶/E8.75 参）+ nmmd；全部记录，用途限于旗帜（见上节），不作晋级宣称。
- 定向测试 tests/t2_round2/：分位映射端点恒等/单调/零处理、Lagrange 端点复现与线性数据中点恒等、收缩权重界、mass 计划确定性与计数守恒、谱系映射合法性（祖先 ∈ E8.75 类型）、文库重映射保秩非负、尺度回锁 RMS 达标、组成 lane 不伪造新行（全部行来自父库）、小端到端 smoke。
- 每 lane ≤4 CPU 小时、≤64GB。

## 交付与完成标准

- 15 候选全部构建、contract PASS（或预声明豁免）、确定性重放 PASS、工程门 PASS 或如实记录失败证据。
- `submissions/INDEX.tsv` 逐行登记（score_pending，不宣称进步）；`docs/coordination/T2_TRACKING.md` 变更摘要；DECISIONS 追加轮次决策并同步根目录索引行；`reports/LANE_VERDICTS.tsv` 登记 lane 状态。
- 单一 zip `deliveries/t2r2__t2__upload__20260929.zip`：15 成员（短名 ≤50 字符）+ MANIFEST.tsv + UPLOAD_MANIFEST.tsv + RUN_ID_MAP.tsv + EVIDENCE_MANIFEST_POINTERS.tsv；成员 SHA/CRC 校验。
- 报告 `reports/t2_round2_20260929/REPORT.md`：逐 lane 分母、对照、风险、NOT_RUN；科学限制 blocks_submission:false；不上传、不自动宣称提分；服务器回分前 best 不变。

## 灵感来源声明

新路线以本项目证据为主：分位桥=T1 v0023 机制移植（本项目已评分）；三阶段趋势/曲率=外推"3-stage trend untried"与 h_n2 "E9.5 未入 board" 缺口；组成粒度=REVIEW 明示"组成估计用多少细胞、多少类型"未关闭轴；谱系映射=外推 17/22 类型零位移结构缺口。外部检索（2024–2025 spatiotemporal OT 方法如 stVCR、Waddington-OT 综述）与本项目历史一致：大 OT/流模型在本赛已反复失败，不采用；分布级窄修改是唯一有服务器证据的方向。
