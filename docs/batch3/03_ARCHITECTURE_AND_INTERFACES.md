# 架构与标准接口

## 1. 总原则

```text
外部工具环境
  └── 只产生标准中间件（coupling / prior / field / simulator parameters）
        └── core 环境读取中间件
              └── anchor + structured change + calibrated residual
                    └── contract builder
                          └── prediction.h5ad
```

外部工具不得在各自环境中直接写最终提交文件。这样可以：

- 隔离依赖冲突；
- 审计工具实际贡献；
- 在工具失败时保留中间件；
- 保证最终 AnnData contract 只有一个实现入口。

## 2. 十个薄模块

| 模块 | 职责 | 标准输出 |
|---|---|---|
| `contract_io.py` | 读取/校验 AnnData、gene order、normalisation、`spatial_3D`、setting | `ContractReport` |
| `anchor_registry.py` | 锁定 task/board parent、路径、SHA256、score snapshot | `ParentRef` |
| `temporal_coupling.py` | moscot/WOT coupling 和 source-only diagnostics | sparse `.npz` + `coupling_meta.json` |
| `state_mass.py` | coupling → state mass；UOT/shrinkage；比例归一化 | `state_mass.tsv` |
| `population_decoder.py` | state mean + empirical residual / module-scDesign3 decoder | `state_gene_delta.npz` + sampling plan |
| `shape_field.py` | RMS lock、Spateo/pycpd field、geometry checks | landmarks/displacements `.npy` + meta |
| `niche_assignment.py` | FGW/soft mapping 与 NFS proxy gate | coupling/permutation + gate report |
| `perturb_prior_committee.py` | 多工具 signed/ranked evidence 合并 | `prior.json` + `evidence.tsv` |
| `lineage_state_gate.py` | Mesp1、state activity、dosage、target-expression gate | `state_gate.tsv` |
| `atom_calibration.py` | severity、mass、scale、shrinkage、baseline blend | `calibration.json` |

参考函数签名位于 `interfaces/virtual_embryo_tools/`。它们是接口契约，不要求机械复制到仓库；若已有等价模块，写 adapter 即可。

## 3. 标准中间件

### 3.1 Temporal coupling

```text
coupling.npz                # CSR/COO sparse matrix
source_obs_names.txt
 target_obs_names.txt
coupling_meta.json          # tool, version, cost, epsilon, mass mode, hashes
state_transition.tsv        # source_state, target_state, transported_mass
```

不允许只保存不可序列化的 Python 对象或 notebook state。

### 3.2 State mass

```text
state_mass.tsv
  board
  target_stage
  state
  parent_probability
  raw_forecast
  shrunk_probability
  uncertainty
  evidence
```

总质量必须归一化为概率。不要把目标绝对细胞数解释为真值。

### 3.3 Population decoder

```text
state_gene_delta.npz
residual_source_index.npy
sampling_plan.tsv
module_definition.tsv       # 仅 module-scDesign3 lane
```

真实 residual replay 优先保留完整 cell-row residual。禁止逐基因独立噪声替代共变结构。

### 3.4 Shape field

```text
source_landmarks.npy
reference_landmarks.npy
predicted_landmarks.npy
displacement.npy
field_meta.json
geometry_checks.json
```

`field_meta.json` 必须记录：局部坐标 frame、centering、RMS lock、时间 regime、拟合方向、插值/外推系数。

### 3.5 Signed prior

每条记录至少包含：

```text
target_gene
condition_id
stage
state
response_gene
sign                  # -1 / 0 / +1，定义为 KO - WT
rank_score            # [0, 1]
confidence            # [0, 1]
lineage_gate           # [0, 1]
directness_score       # [0, 1]，不等于 sign
source_families
conflict_flag
provenance
```

### 3.6 Candidate

统一表达：

```text
prediction = anchor + structured_change + calibrated_residual
```

- T1：`structured_change = state mass + state mean program`；
- T2：`structured_change = geometry field`，表达被冻结；
- T3：`structured_change = lineage/state gated signed prior × severity`；
- `calibrated_residual` 必须可独立关闭，以便 protected-check 归因。

## 4. 必须保持的 invariant

### 全任务

- parent 路径和 SHA256 已锁定；
- gene order、obs/var schema、normalisation 与 scorer contract 一致；
- lane 配置在 full run 前冻结；
- 每个随机过程使用固定 seed；
- 所有中间件带输入 hash 与工具版本。

### T1

- 输出完整官方基因空间；
- state mass 解释为概率比例，不解释为绝对细胞数量；
- residual replay 保持行级或低秩共变，不逐基因独立加噪；
- S2 不偷偷创建新状态，P1 由独立 state-birth 任务负责。

### T2

- 不优化绝对坐标 MSE；
- 对平移/旋转不敏感；
- G1 winner 的 RMS scale 被精确恢复；
- `X`、gene order、obs 行及表达—坐标对应不做主动重排；
- 记录 kNN overlap，防止形变把 J1 彻底破坏。

### T3

- sign 定义明确为 `KO - matched WT`；
- GATA4/GATA6 和 β-catenin 使用不同 evidence stack；
- Mesp1 lineage gate 生效；
- Gata6 heterozygous dosage 作为独立通道记录，不与 Gata4 静默合并；
- 未响应细胞/基因保持 WT residual；
- 坐标默认复制 WT；
- prior gate 未通过时不生成 residual。
