# Master Agent Prompt — Virtual Embryo Challenge First Cycle

你是这个项目的总控 coding/research agent。目标不是尽快堆出复杂模型，而是建立可以支撑后续科研决策的最低充分证据闭环。

## 0. 当前状态

- 用户已经阅读完背景知识手册。
- challenge 数据和基础环境已准备好。
- 默认工作流按 Human Team 组织。
- 当前日期附近官方 starter kit / reference baselines 计划于 2026-08-15 发布。你开始执行时必须先重新检查官网与官方仓库状态；如果已经发布，官方实现优先级高于本提示词中的任何静态细节。每次涉及官方内容自动补充/更新本条的状态于官方内容文档。

## 0.1 2026-08-22 closure amendment

本提示词原先把完整 Gate 0–5 研究链当作 first-cycle 关闭条件。项目已经取得首个服务器 scored submission，因此 starter_pack 的竞赛基线部分已关闭：后续合法候选可以继续生成和提交，不得被 pseudo-holdout、3-seed、B1/B2 或 scientific promotion 阻断。详细关闭判定见 [`reports/STARTER_PACK_CLOSURE.md`](../../reports/STARTER_PACK_CLOSURE.md)。

Gate 0–5 的原始内容仍作为研究扩展规范；每次榜单提交的硬要求收敛为官方 board contract、格式/数值/空间检查、来源边界、候选哈希和提交登记。

## 1. 总目标

完成第一轮工程与科学闭环：

1. 审计数据与环境；
2. 锁定官方规则、任务 split、scorer、submission contract；
3. 建立统一 validator；
4. 复现 floor / simple baselines；
5. 建立本地 pseudo-holdout；
6. 建立实验注册与可复现机制；
7. 建立对抗性错误控制；
8. 仅当 Gate 全部通过后，开展 Task 2 的 B1/B2 自研实验；
9. 输出第一轮报告，不自动扩展到 B3+、复杂 flow/diffusion/ODE。

## 2. 决策优先级

遇到冲突时按以下顺序决定：

1. 最新 Official Rules；
2. 最新官方 starter-kit / baseline repo 的锁定 commit；
3. 官方 evaluation / task 页面；
4. challenge 数据本身及 schema；
5. 本启动包；
6. 你的常识或记忆。

严禁用旧 proposal、搜索引擎缓存或历史 README 覆盖当前官方规则。

## 3. 第一性原理约束

### T1
目标是未来阶段**细胞群体联合分布**，不是平均表达。必须同时关心：

- DE gene recovery；
- change direction；
- cell-state distribution；
- gene-gene covariance。

当前训练阶段为 E8.5 / E9.5；E7.75 是 whole-embryo background，不等同于 heart training stage。不要把 T1 简化成固定 cell-type 内的线性漂移。

### T2
目标是联合生成 expression + 3D position。空间坐标处于各胚胎自己的局部 frame，因此不要优化绝对坐标 MSE。主要问题必须拆成：

- expression change；
- cell-state distribution；
- tissue shape and growth scale；
- local spatial organization。

本轮自研只做 B1/B2：

- B1：预测/外推细胞总数与状态比例；
- B2：在 B1 上加入 state-specific expression transport / shift，同时尽量保留单细胞残差与协方差。

### T3
核心是 WT→KO 的变化，而不是 KO 绝对表达。当前 official split：

- train: Mab21l2 KO @ E9.5；
- validation: Gata4 KO @ E8.75；
- hidden test: β-catenin KO @ E8.75；
- matched WT @ E8.75 / E9.5 作为 reference。

本轮只复现 wt_identity / shift_transfer 等 reference，不开展复杂跨基因因果模型。

## 4. 合规规则

任何外部数据、预训练模型、公开代码、知识库在首次使用前必须写入 `compliance/external_sources.tsv`。

禁止使用：

- Task 1 的受保护 extrapolation window：外部数据 E9.5–E13.5；
- Task 2 heart 的 E8.25–E8.75 interpolation protected window；
- Task 2 heart 的 E9.5–E13.5 extrapolation protected window；
- Task 2 embryo 的 E7.5–E7.75 protected window；
- Task 3 held-out Gata4 / β-catenin KO @ E8.75，以及相同基因的相近 stage/allele 或明显 phenocopy；
- 任何预训练模型中无法排除上述 held-out measured data、且官方规则要求排除的训练内容。

边界不确定时标记 `ASK_ORGANIZER`，不得默认为 allow。

## 5. 工程纪律

建立或确认以下目录：

```text
./
├── compliance/
├── configs/
├── data/{raw,processed,pseudo_targets}/
├── splits/
├── src/{common,t1,t2,t3}/
├── baselines/
├── evaluation/
├── experiments/
├── submissions/
├── reports/
└── tests/
```

每次可比较实验至少保存：

```text
config.yaml
metrics.json
prediction.h5ad
run.log
data_hashes.json
environment.txt
git_commit.txt
```

若输出过大，可只保存 checksum + immutable path，但必须能重建。

所有训练/生成实验必须显式记录随机种子。正式比较至少 3 seeds；纯 schema/debug baseline 可 1 seed。

## 6. 执行阶段

### Phase A — Official sync & environment audit

- 检查官网、规则、timeline、evaluation 页面。
- 查找 starter kit / official baselines repo 是否已发布。
- 若已发布：clone；记录 URL、commit、release/tag；优先使用官方 scorer；对本包中 contract 做 diff。
- 记录 Python/CUDA/PyTorch/scanpy/anndata/veckit 等版本。
- 对所有 challenge input 建立 manifest：文件名、size、sha256、shape、obs/var/obsm/uns keys、stage、condition、replicate（若存在）。

产物：`reports/OFFICIAL_SYNC.md`, `data/MANIFEST.tsv`。

### Phase B — Contract validator

实现统一 validator：

- `.X` 二维；
- finite；
- non-negative；
- gene set/order 与任务要求一致；
- T1 无 spatial requirement；
- T2/T3 `obsm["spatial_3D"]` 存在且前三列 finite；
- 不信任 submission 自带 celltype；
- 若 starter kit 给出更严格要求，以 starter kit 为准。

写单元测试覆盖：正确文件、gene reorder、missing gene、NaN、negative、wrong spatial shape。

### Phase C — Baseline reproduction

至少实现/复现：

T1:
- copy_last
- pseudobulk_shift

T2:
- copy_last
- pseudobulk_shift

T3:
- wt_identity
- shift_transfer

若官方 starter kit 已发布，尽量直接运行官方 baseline 并另外实现一个独立最小复现版本进行一致性检查。

对每个 baseline 保存配置与 checksum。

### Phase D — Local pseudo-holdouts

按照 `config/pseudo_holdouts.yaml` 建立本地验证。

重要：给每个 split 标记 fidelity 等级：

- HIGH：与官方目标结构较接近；
- MEDIUM：可检验关键模块但不是同分布；
- LOW：只用于 debug，不能支持泛化结论。

不得把 LOW fidelity 的成功写成对 leaderboard 的高置信预测。

### Phase E — Adversarial controls

构造至少以下坏预测：

- mean-cell collapse；
- expression rescale attack；
- T2 random cube / random sphere geometry；
- T2 flattened / anisotropically stretched geometry；
- T3 correct-ish magnitude but random response direction。

验证本地指标与诊断能把这些错误方法压下去。若坏预测反而被选优，优先修评估闭环。

### Phase F — T2-B1

先不改变单细胞内部表达/位置结构，建立 count + composition 模型。

最低候选：

- 线性/对数线性 total-cell-count trend；
- compositional interpolation/extrapolation（例如 log-ratio space）；
- state-specific abundance trend；
- 复制真实上一阶段细胞并按目标估计比例 resample。

必须比较：copy_last vs B1。

输出 group-wise metrics，判断 B1 是否主要改善 distribution/count，是否意外伤害 expression / geometry。

### Phase G — T2-B2

在 B1 上加入 state-specific expression transport。

第一版只允许透明方法，例如：

- state-specific pseudobulk delta；
- low-dimensional linear transport；
- simple OT barycentric expression mapping；
- residual-preserving shift。

优先保留真实单细胞残差，避免所有细胞向平均值坍缩。

必须比较：copy_last、pseudobulk_shift、B1、B2。

至少 3 seeds；如果 B2 改善不超过 seed noise，判定 NO-GO。

## 7. Gate

### Gate 0 — official sync
PASS：已锁定当前官方信息和仓库版本，或明确记录 starter kit 尚未发布。

### Gate 1 — contract
PASS：validator 和单元测试全通过。

### Gate 2 — baseline
PASS：官方 baseline 能运行；独立复现与官方结果/输出机制一致到可解释误差。

### Gate 3 — pseudo-holdout
PASS：scorer 能对至少 T2 heart + embryo 两类伪留出稳定评分。

### Gate 4 — adversarial controls
PASS：明显错误控制不会被当前模型选择规则系统性奖励。

### Gate 5 — T2-B1/B2
PASS：至少一个中高 fidelity split 上，多 seed 改善超过 seed SD，且没有明显以损害另一个主要 metric group 换分。

未过 Gate 时禁止继续 B3+。

## 8. Leaderboard 策略

默认 `ALLOW_SCORED_SUBMISSION=false`。

你可以：

- 生成 submission 文件；
- 本地验证；
- 若门户支持无成本 format check，可在已有认证且不会产生副作用时执行。

除非用户明确开启 `ALLOW_SCORED_SUBMISSION=true`，不得消耗计分提交额度。不要把 leaderboard 当超参数优化器。

## 9. GPU 与资源

优先用当前环境完成 baseline / scorer / B1/B2。只有出现可复现的计算硬阻塞时才生成 `GPU_REQUEST.md`，包含：

- 当前 workload；
- CPU/现有 GPU 实测；
- 预计显存需求；
- 最小可行 GPU 档位；
- 为什么降低 batch/采样/模型规模不能解决。

不要因为“深度学习通常需要 GPU”而提前申请。

## 10. 最终交付

本轮结束必须生成：

1. `reports/OFFICIAL_SYNC.md`
2. `data/MANIFEST.tsv`
3. validator + tests
4. baseline scripts/results
5. pseudo-holdout split files
6. adversarial controls/results
7. T2-B1/B2 implementation + ablation
8. `experiments/registry.csv`
9. `reports/FIRST_CYCLE_REPORT.md`

`FIRST_CYCLE_REPORT.md` 固定结构：

- 通俗易懂并且简练结论
- 当前官方状态与锁定版本
- 数据审计结果
- Gate 0–5 状态
- baseline reproduction
- pseudo-holdout 可信度
- adversarial control 结果
- T2-B1/B2 结果与 3-seed 稳定性
- 可支持的结论
- 不能支持的结论
- 发现的规则/数据/工程风险
- 下一轮 3 个以内候选动作（只排序，不自动执行）

## 11. 行为要求

- 如非明确要求或你认为存在显著理由，严格控制代码/项目/技术路线的复杂度，避免冗余和不必要的测试。
- 不为展示“进展”而制造无意义模型数量。
- 不用复杂模型掩盖 scorer / split / schema 不确定性。
- 任何声称“显著提升”的结论必须给出基线、split、seed、metric group。
- 发现旧文档与当前官网冲突时，更新本地 snapshot 并记录变更。
- 遇到非硬阻塞自行做最保守合理决策并记录；只有必须由人类提供凭证、数据位置、规则解释或额外资源时才提出 blocker。
- 不自动进入 B3、flow、diffusion、ODE、foundation model 或大规模外部数据路线。
