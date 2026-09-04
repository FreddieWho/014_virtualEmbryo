# 为大型架构调整保留的接口与 closeout 要求

## 1. Batch 4 不应制造架构锁定

禁止把以下内容写成全项目不可替换假设：

- celltype 是唯一状态表示；
- pseudobulk shift 是唯一表达头；
- FGW 是唯一空间联合机制；
- developmental delay 是 T3 的真实机制；
- Gata4 validation 规则可以直接迁移到 β-catenin；
- 500-gene T2 表示可以直接替代 T1 全转录组；
- 当前 local proxy 是最终训练目标。

Batch 4 的每个修复必须是可拆除 transform。

## 2. 标准中间接口

下一代架构至少应能复用或替换这些对象：

### `ParentArtifact`

```text
candidate_id
board
h5ad_path
sha256
n_obs
var_hash
obs_names_hash
coordinate_hash
score_status
server_score
```

### `StateMassPlan`

TSV：

```text
state_id
parent_mass
proposed_mass
confidence
source_component
unresolved_policy
```

### `ExpressionDelta`

NPZ/TSV：

```text
state_id × gene_id delta
lane
time_basis
amplitude
cap
uncertainty
```

### `ResidualBank`

```text
state_id
row_id
center_hash
residual_vector_or_pointer
source_stage
```

### `GeometryPlan`

```text
point_id
dx
dy
dz
scale_locked
transform_source
```

### `AssignmentPlan`

```text
position_id
expression_row_id
soft_mass
rank
global_matching_cost
```

### `GenotypeTransform`

```text
gene
allele_action
dosage
lineage_probability
state_gate
transform_domain
```

每个接口必须带 parent hash 和 gene-order hash。

## 3. 代码隔离

Batch 4 新实现：

```text
scripts/batch4/
├── common.py
├── floor_parity.py
├── t1_conservative_family.py
├── t1_late_program_bridge.py
├── t2_fgw_assignment_repair.py
├── t2_expression_bridge.py
├── t2_extrap_expression_cal.py
├── t3_genotype_ablation.py
└── t3_developmental_axis.py
```

不要：

- 改写 `third_party/veckit/`；
- 把新逻辑塞进旧 100k 行脚本；
- 让一个脚本同时负责 T1/T2/T3；
- 让 candidate builder 隐式下载数据；
- 让 geometry 代码修改 expression；
- 让 scoring wrapper 修改 candidate。

## 4. closeout 必须生成的架构重置材料

`B4-CLOSEOUT-ARCHITECTURE-HANDOFF` 生成：

```text
reports/BATCH4_PHASE_REPORT_<DATE>.md
reports/BATCH4_SCORE_GAP.md
reports/BATCH4_ERROR_SIGNATURES.md
reports/BATCH4_COMPONENT_LEDGER.tsv
reports/BATCH4_PROXY_VS_SERVER.md
reports/ARCHITECTURE_RESET_BRIEF.md
reports/ARCHITECTURE_INPUT_READINESS.tsv
```

## 5. `ARCHITECTURE_RESET_BRIEF.md` 必须回答

1. 正确 floor 是否复现；
2. T1/T2/T3 当前 best 与 62/62/68 的差距；
3. 哪些变换有服务器正信号；
4. 哪些组件只在 local proxy 有信号；
5. 哪些失败来自信息缺失，哪些来自 decoder，哪些来自离散化；
6. 哪些外部数据已经 sanitized 可直接训练；
7. 哪些数据仍缺 processed object；
8. 当前可用 GPU/CPU/内存与可接受预算；
9. 下一代架构必须同时解决哪些能力；
10. 哪些 Batch 4 规则不能进入 test phase；
11. validation 与 hidden test 的分布转移；
12. 需要比较的 2–4 个大型架构家族，而不是直接指定一个。

## 6. 架构重构候选空间只留接口，不在 Batch 4 实现

可能的下一阶段包括但不限于：

- T1 开放集状态出生 + 外部多阶段预训练；
- T1 非自主/分支 flow 或 diffusion；
- T2 表达—组成—几何—生态位联合生成；
- T2 interpolation / extrapolation mixture-of-experts；
- T3 多扰动预训练的 gene-conditioned model；
- T3 gene / pathway encoder + stage/lineage conditional flow；
- 三任务共享 WT developmental representation，任务专属 decoder。

Batch 4 不选择其中任何一个，也不为它们预装大依赖。

## 7. 架构切换时可直接保留

- 官方 scorer / contract wrapper；
- immutable candidate registry；
- Agent Team run-lock / evidence harness；
- external data firewall 与 sanitized caches；
- floor parity constructor；
- state crosswalk，但只能作为可替换输入；
- residual bank；
- per-board parent；
- server score ledger；
- proxy-vs-server 误差记录。

## 8. 架构切换时默认丢弃

- validation-specific top-k；
- 手工幅度；
- 旧 GRN unanimity gate；
- 旧 greedy assignment；
- 特定 lane 的 hard-coded文件名；
- local proxy 的固定权重；
- 对 β-catenin 未经验证的 Gata4 规则；
- Batch 4 临时的 target-only candidate 逻辑。

## 9. 决策原则

Batch 4 是修路，不是宣布这条路通向领奖台。  
若修完仍有双位数差距，应停止给旧路线加装饰，启动独立的大型架构方案包。
