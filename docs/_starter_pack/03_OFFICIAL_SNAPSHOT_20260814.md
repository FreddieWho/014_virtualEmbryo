# Official Challenge Snapshot — 2026-08-14

> 本文件是启动时的规则快照，不是永久真相。Agent 每次正式提交前必须重新核对官网与官方仓库。

## 1. 当前赛事阶段

截至 2026-08-14 官网：

- P1 development 已开放；
- starter kit + reference baselines 计划于 2026-08-15 发布；
- P3 final test phase：2026-10-20；
- final submissions：2026-12-02；
- official evaluation：2026-12-04；
- winners：2026-12-11。

Authoritative timeline:
https://virtualembryo.ai/challenge/timeline

Challenge overview:
https://virtualembryo.ai/challenge/

## 2. 当前官方 split

### T1 — Temporal

- modality: dissociated single-cell RNA, whole transcriptome, 32,285 genes；
- train: E8.5, E9.5；
- validation: E10.5；
- hidden test: E12.5；
- E7.75 whole-embryo stage ships as background, but is outside the heart split。

Scoring weights:

- DE gene recovery 25%；
- change direction 25%；
- cell-state distribution 30%；
- gene-gene co-variation 20%。

Official page:
https://virtualembryo.ai/challenge/tasks/temporal

### T2 — Spatial-temporal

Modality: 3D MERFISH, 500-gene panel + per-cell 3D coordinates。

Heart:

- train: E8.25, E8.75, E9.5；
- validation: E8.5 (interpolation), E10.5 (extrapolation)；
- hidden test: E12.5 (extrapolation)。

Embryo:

- train: E6.75, E7.25, E8.0；
- validation: E7.5；
- hidden test: E7.75。

Scoring groups, each 25%:

- expression change；
- cell-state distribution；
- tissue shape and growth scale；
- local spatial organisation。

Official page:
https://virtualembryo.ai/challenge/tasks/spatial

### T3 — Perturbation

Current official split (注意不要使用早期 proposal 的反向版本)：

- train: Mab21l2 KO @ E9.5；
- validation: Gata4 KO @ E8.75；
- hidden test: β-catenin KO @ E8.75；
- matched WT @ E8.75 / E9.5。

Scoring weights:

- response gene recovery 30%；
- response direction 25%；
- response magnitude 25%；
- cell-state distribution 20%。

Tissue shape 当前不进入 T3 ranking composite。

Official page:
https://virtualembryo.ai/challenge/tasks/perturbation

## 3. Submission contract — 已由官网明确的部分

Portal 当前明确检查：

- `var_names` 必须与 task gene list 一致、顺序一致；
- `.X` 是 cells × genes 2D matrix；
- sparse 会 densify，最终 cast float32；
- `.X` 必须 finite；
- `.X` 必须 non-negative；
- T2/T3 必须有 `obsm["spatial_3D"]`，至少读取前三列且 finite；
- T1 不携带 coordinates；
- `obs["celltype"]` 可选并会被忽略，organizer 用 frozen probe 统一分类。

Portal:
https://virtualembryo.ai/challenge/account/submissions

Starter kit 发布后需要补充/覆盖：

- exact minimum cell count；
- exact uns metadata；
- task-specific target naming；
- scorer CLI/API；
- allow-reorder behavior；
- file-size/serialization细节。

## 4. Baselines — 官网当前声明

T1:

- copy_last
- pseudobulk_shift
- shift_ode
- neural_ode
- dynode_flow

T2:

- copy_last
- pseudobulk_shift
- spatiotemporal_ode
- dynode_flow

T3:

- wt_identity
- shift_transfer
- gene_ko
- perturb_ode
- dynode_flow

不要根据名字自行推断实现。starter kit 发布后以源码为准。

## 5. External-data protected regions

Official Rules 当前关键限制：

### T1

外部 measured data 从 E9.5 到 E13.5 属于 extrapolation protected window，不可使用。E10.5/E12.5 绝对禁止。

### T2 heart

- interpolation protected window: E8.25–E8.75；
- extrapolation protected window: E9.5–E13.5。

### T2 embryo

- interpolation protected window: E7.5–E7.75。

### T3 genotype

Held-out conditions:

- Gata4 KO @ E8.75；
- β-catenin KO @ E8.75。

同一 gene 的其他 allele、相近 stage，或明显 phenocopy 也可能被视为 held-out condition。

预训练模型若通过训练语料间接包含这些 held-out measured data，同样可能违规。

Official Rules:
https://virtualembryo.ai/challenge/rules

## 6. Submission quotas

Rules 当前写明：

- P1: 20 scored submissions / team / task / UTC day；
- P2: 8 scored submissions / team / task / UTC day；
- P3: 2 official submissions / board / whole phase；
- format checks unlimited；
- single prediction file ≤ 1200 MB。

开发中默认不消耗 scored quota，除非用户显式授权。

## 7. Human Team vs Agent Team

Human Team：人类可以查看中间结果、设计/选择方法。

Agent Team：人类可以写 initial prompt、harness、预算等，但不能读取中间结果并据此指导下一步。Agent submission 至少需要两类 distinct evidence 才进入 scoring queue；最终奖项还涉及 trajectory/prompts/harness 的可审计性。

本启动包按 Human Team 使用。

## 8. 官方信息冲突处理

搜索引擎可能缓存早期 proposal，尤其 T3 split 曾出现过不同排列。不要使用缓存摘要。优先级：

1. Official Rules；
2. official starter-kit source at locked commit；
3. current task/evaluation pages；
4. timeline；
5. search snippets / old proposal（只用于历史，不用于执行）。
