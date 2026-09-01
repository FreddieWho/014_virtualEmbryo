# 外部数据合规规则快照

日期：2026-08-29  
官方规则：https://virtualembryo.ai/challenge/rules  
官方数据说明：https://virtualembryo.ai/challenge/data

> 本文件是工程执行快照，不替代组织者书面解释。规则更新或组织者书面答复优先。

## 1. 总规则

1. 可以使用公开外部数据、预训练模型和已发表代码，前提是许可证允许，并在方法摘要中披露。
2. 每个外部 source 都必须披露，即使最终影响很小。
3. 不得通过任何路径使用 held-out stage/genotype 的 measured data，包括公开数据集或在其上预训练的模型。
4. 一个通用资源若包含保护样本，可以在训练前删除这些样本；必须披露删除过程。
5. 阶段保护按真实发育时间判断，不按文件名判断；somite/Theiler stage 必须转换。
6. 同基因其他 allele、相近阶段 perturbation 或 phenocopy 也可能被视为 held-out genotype。
7. 边界不清楚时必须先问组织者。

## 2. Task 1

绝对 held-out：

- E10.5
- E12.5

外部数据窗口：

- `<= E9.5`：允许；E9.5 明确允许。
- `(E9.5, E13.5]`：禁止。
- `> E13.5`：允许，但必须明确披露阶段。

操作解释：

- E-MTAB-6967 的 WT E6.5–E8.5 可用；
- E-MTAB-11763 的 WT E8.5–E9.5 可用；
- GSE193346 只能保留 WT E9.5 与 E14.5 及更晚阶段；E10.5、E11.5、E12.5、E13.5 全部删除；
- 任何 mutant/chimera 默认删除；
- 含受保护阶段训练语料的基础模型禁止使用。

## 3. Task 2

Embryo interpolation 保护窗口：

- E7.5–E7.75 禁止外部 measured data。

Heart interpolation 保护窗口：

- E8.25–E8.75 禁止外部 measured data。

Heart extrapolation held-out：

- E10.5
- E12.5

保守执行：

- T2 外部 measured spatial/transcriptomic data 必须逐 board 审计；
- Data 页面关于 “Task 1 additionally permits external public single-cell data” 的措辞与 Rules 的广义许可存在可解释空间；
- 在收到书面答复前，不启用 T2 外部空间 atom；
- 即使获准，也不能使用对应保护窗口中的 stage，且不得从多个切片重建 held-out target。

## 4. Task 3

Held-out genotype：

- Mesp1-Cre; Gata4 F/F; Gata6 F/+ @ E8.75
- Mesp1-Cre; β-catenin/Ctnnb1 F/F @ E8.75

禁止：

- 同基因其他 allele 在可比阶段；
- 明显 phenocopy 的 perturbation；
- 上述目标条件的 measured expression/spatial data；
- 在这些数据上训练且无法移除影响的模型。

允许且本包采用的严格解释：

- 匹配 WT 与其他 WT developmental data；
- 非 perturbational 的 WT GATA4 binding/occupancy 数据，仅用于 target directness；
- 通用 ontology/pathway 知识；
- 只在净化后的 WT 数据上现场训练的 CellOracle/scTenifoldKnk；
- 通用 Perturb-seq 仅在目标基因和 phenocopy blacklist 全部删除后，用于响应形状而非方向。

需要书面确认的部分：

- 聚合 GRN/pathway 中 target-specific edge 的 provenance 边界；
- 通用 Perturb-seq 在严格 blacklist 后的使用；
- T2/T3 对外部 measured data 的广义许可范围。

## 5. 预训练模型

允许的模型必须满足至少一项：

- 本项目只在 sanitized allowlist 数据上自行训练；
- 公开 checkpoint 的全部训练语料可枚举，并能证明不含当前 task 的保护数据。

以下情况直接 `REJECT`：

- 训练语料未知或只给出模糊“public single-cell corpus”；
- 语料包含 mouse embryogenesis 但不能按 stage/genotype 排除；
- checkpoint 可能看过 challenge held-out condition 或对应 public phenocopy 数据。

因此本批不默认使用 Geneformer、scGPT、scFoundation 等不易逐样本审计的公开 checkpoint；可以使用其架构，但必须从 sanitized data 重新训练。

## 6. 排行榜使用

- P2 每 task 每 UTC 日最多 8 次 scored submissions；format check 不限。
- 分数可用于选择候选，但不得通过差分/反演恢复目标属性。
- 本包默认 `allow_server_submission: false`，只产出人工上传包。
