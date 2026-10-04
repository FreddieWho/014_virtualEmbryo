# T2 第二轮报告：三新两优化 × 三 board（2026-09-29）

状态：**15 候选全部建成并通过全部本地检查；未提交、未评分；三 board 现役 best 不变**（embryo v0010=62.29、heart v0013=62.04、extrap v0001=50.53 门户选择）。blocks_submission: false。

- 设计冻结：`reports/T2_ROUND2_DESIGN_20260929.md` + `configs/t2_round2/design_20260929.json`（跑前冻结）
- 代码：`scripts/t2_round2/`（common/ops/run/checks/deliver/score_local）；测试 `tests/t2_round2/test_ops.py`（15 项 PASS）
- 证据根：`artifacts/t2_round2/T2-ROUND2-20260929-v1/`（INPUT_LOCK、BUILD_SUMMARY、checks/、local_eval/、逐 lane diag 与 ledger）
- 交付：`deliveries/t2r2__t2__upload__20260929.zip`（15 h5ad + MANIFEST/UPLOAD_MANIFEST/RUN_ID_MAP/EVIDENCE_MANIFEST_POINTERS，成员 SHA/CRC 校验 PASS，receipt READY_NOT_SUBMITTED）
- 登记：`submissions/INDEX.tsv` 15 行（score_pending）；决策 D-20260929-T2ROUND2-001

## 候选一览（每 board：新×3 + 优化×2）

| board | lane | 版本 | 类型 | 一句话 | contract | 工程门 | SHA256(前12) |
|---|---|---|---|---|---|---|---|
| embryo | e_n1_qbridge | v0011 | 新 | 分位数桥+mass（T1 机制移植，保秩分布重映射） | PASS | PASS | afe9f6280433 |
| embryo | e_n2_trend3 | v0012 | 新 | E6.75 首次入候选：三阶段趋势桥+趋势组成 | FAIL_BY_DESIGN_ACCEPTED | PASS | 07e5c731fbe8 |
| embryo | e_n3_substate2 | v0013 | 新 | 组成粒度轴：类型内 KMeans k=2 子状态桥+mass | FAIL_BY_DESIGN_ACCEPTED | PASS | 3f750cb19067 |
| embryo | e_o1_shrinkmerge | v0014 | 优化合并 | v0010 × t 收缩（C=2，v0011 机制） | PASS | PASS | 1ea0c69631d5 |
| embryo | e_o2_scalmass | v0015 | 优化合并 | v0010 × G1 尺度：mass 后 RMS 回锁（×1.00404） | PASS | PASS | 4e8a4ab95ae7 |
| heart | h_n1_qbridge | v0016 | 新 | 分位数桥+mass（λ=0.5，直指 variogram 28.4） | PASS | PASS | ae4cf945a062 |
| heart | h_n2_curve95 | v0017 | 新 | E9.5 首次入 board：Lagrange 曲率桥+曲率组成 | FAIL_BY_DESIGN_ACCEPTED | PASS | 0e0b3a5f48bb |
| heart | h_n3_cmjoin | v0018 | 新 | 组成粒度轴：celltype×cm_group 联合状态桥+mass | FAIL_BY_DESIGN_ACCEPTED | PASS | b16dbba349be |
| heart | h_o1_shrinkmerge | v0019 | 优化合并 | v0013 × t 收缩（C=2） | PASS | PASS | d84de17486a6 |
| heart | h_o2_libnorm | v0020 | 优化迭代 | v0013 + 文库大小保秩重标定 | PASS | PASS | 3e2382bfe721 |
| extrap | x_n1_lineage | v0017 | 新 | 谱系映射 delta：17 个零位移类型首次获得位移 | PASS | PASS | 7ffd3053b456 |
| extrap | x_n2_trend3 | v0018 | 新 | E8.25 首次入候选：三阶段趋势 Δ=2v2−v1 | PASS | PASS | 8f6acfb2945a |
| extrap | x_n3_compmix | v0019 | 新 | 组成趋势外推（log 比线性，倍率 ≤2 封顶）+重采样 | FAIL_BY_DESIGN_ACCEPTED | PASS | 680f2b7fc12d |
| extrap | x_o1_trendshrink | v0020 | 优化合并 | x_n2 趋势 Δ × t 收缩 | PASS | PASS | ab5c6f4ae6b9 |
| extrap | x_o2_shrinkcomp | v0021 | 优化合并 | v0011 收缩表达 × x_n3 组成趋势 | FAIL_BY_DESIGN_ACCEPTED | PASS | 55aae9fd24a2 |

FAIL_BY_DESIGN_ACCEPTED 仅限 R2 既有四类组成变化豁免字符串（obs_names/order、obs metadata、layers content、raw content），与 v0010/v0013 当年同一处置；逐 lane errors 见 `checks/contract_checks.tsv`。

## 本地证据（非 leaderboard 证据；pseudo-target 循环性已声明）

embryo：pseudo-target E7.25 / ref E6.75，**M0 附录 B：只记录不否决**。heart：pseudo-target E8.75 / ref E8.25_late，nmmd 5% 规则。extrap：R1 proxy（E9.5 心脏 cm 靶 / E8.75 参；该 proxy 已在 shrink、spatial 两族上方向错误，只记录）。

| lane | nmmd vs 父 | de_score vs 父 | de_dir vs 父 | 备注 |
|---|---|---|---|---|
| e_n1 | 0.0297 / 0.0364（−18%） | 0.6207 / 0.7241 | 0.7636 / 0.6589（+0.105） | embryo 记录-only，本地不作排名 |
| e_n2 | 0.0591（+62%） | 0.5862 | 0.5523 | 记录-only |
| e_n3 | 0.0268（−26%） | 0.7241（=父） | 0.6904 | morans 0.5187 vs 0.9208 大幅下滑，如实记录 |
| e_o1 | 0.0309（−15%） | 0.7586（+0.034） | 0.7169（+0.058） | 记录-only |
| e_o2 | 0.0364（=父） | 0.7241（=父） | 0.6589（=父） | 尺度 ×1.004 本地近乎不可见（与 V1 先例一致） |
| h_n1 | 0.0223 / 0.0409（**−45%**） | 0.9022 / 0.5435（**+0.359**） | 0.9682 / 0.7697（+0.198） | flag ok；heart nmmd 有服务器预测力（−0.559） |
| h_n2 | 0.0423（+3.5%，ok） | 0.5761（+0.033） | 0.7679 | 曲率项温和 |
| h_n3 | 0.0415（+1.5%，ok） | 0.5870（+0.044） | 0.7739 | 9 联合状态被解析 |
| h_o1 | 0.0424（+3.7%，ok） | 0.5761（+0.033） | 0.7687 | 收缩 mean_w=0.576 |
| h_o2 | 0.0386（−5.6%） | 0.7500（+0.207） | 0.8281（+0.058） | 文库重标定 |
| x_n1 | 0.2291 / 0.2051（+12%） | 0.2329 / 0.2466 | 0.4391 / 0.4221（+0.017） | proxy 已知方向不可靠，记录-only |
| x_n2 | 0.2077（+1.3%） | 0.2466（持平） | 0.4308（+0.009） | de 持平为机制事实（均值未动类型外） |
| x_n3 | 0.1997（−2.6%） | 0.2466（持平） | 0.4389（+0.017） | 组成趋势 |
| x_o1 | 0.2076（+1.2%） | 0.2466（持平） | 0.4309 | mean_w=0.701 |
| x_o2 | 0.1997（−2.6%） | **0.2603（+0.0137）** | 0.4376（+0.016） | 唯一越过历史 R1 局部双门（de>0.2466 且 dir>0.4221）的 lane；该门已证方向不可靠，仅记录 |

无 LOCAL_DEGRADE_FLAG（heart 5 条均在 5% 规则内）。本地证据一律不作晋级宣称；embryo 与 extrap 的本地读数历史上与服务器反向或无关。

## 组件复用与精确性声明

- v0010/v0013 质量重采样计划按冻结算法+种子（20260904）重放，obs_names（含 `__dup{k}`）与现役逐名一致（e_n1/e_o1/h_n1/h_o1 构建期断言通过）。
- v0011 收缩表达按 g0 float32 路径重算，与已评分 v0011 **逐值一致**（x_o2 内嵌校验通过；首次 float64 路径差异 1.8e-05 已修正并记录）。
- x_o2 行选择与 x_n3 逐名一致（同算法同设计种子 20260929 重放）。
- 15/15 独立重跑字节一致（`checks/replay.json`，replay/ 目录全程独立构建）。
- 谱系映射表（17 条）由冻结确定性规则生成并固化于 INPUT_LOCK.json；未做人工挑选。

## 实现统计（INPUT_LOCK / diag）

- e_n2 三阶段类型 11/18；h_n2 三阶段类型 5/33（E9.5 词表差异大）；x_n2 三阶段类型 5/22。
- e_n3 分裂 33 个括号类型、7 个子状态达标（两端 ≥30），父侧 21 终态。
- h_n3 9 个联合状态达标（celltype×cm_group，两端 ≥30），42 终态全共享。
- x_n1 17 orphan 全部映射到 5 个共享祖先（V-CM/Peri/aPHM/pPHM/NCC 中实际用到 V-CM、Peri、aPHM、pPHM）。
- clip 分数（披露不否决）：e 0–14.0%，h 1.1–60.0%（v0013 当年 60% 已胜），x_n1 47.7%、x_n2/x_o1 17.4%。
- 工程门 15/15 PASS（library q01≥0.25/q99≤4、方差比 0.1–10、有限非负、n_obs/panel 精确）。

## 范围、限制与 NOT_RUN

- 未读取 E7.5/E8.5/E10.5 真值；target_used=false；无外部数据；无服务器上传；无网格搜索；无按服务器分数改方法。
- pseudo-target 循环性：embryo 在 E7.25（桥的源端）、heart 在 E8.75（括号端）评价，绝对水平不可比，仅同靶相对。
- extrap R1 proxy 在两族上方向错误已登记；x 系本地读数仅存档。
- NOT_RUN：服务器评分、门户合计、E12.5/隐藏测试、任何机制/因果宣称。科学限制 blocks_submission: false。
- 实现期两处跑前修正（非结果导向，均记录在案）：(1) x_n1 祖先候选集订正为"共享且 n≥30"（delta 需两端均值，设计文档与 config 已同步订正）；(2) e_n3 括号独有类型的父侧空赋值保护、x_o2 float32 路径对齐。

## 建议（供用户决定，不自动上传）

消耗顺序仅为本地证据排序，不是预测：heart 先 h_n1（nmmd −45% 且该指标在本板有预测力），其次 h_o2；extrap 先 x_o2（唯一过历史局部双门 + 两已评分机制合并），其次 x_n3；embryo 本地无否决权，建议服务器仲裁，e_o1（两已评分机制合并、本地温和为正）先行，e_n1/e_n3 随后。每批回分前 best 不变。
