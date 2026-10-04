# T2 · M1 承重引用核验记录（第二批：E-I1 / H-N2 的锚点）

- **决策号**：`D-20260927-T2CITE-002`
- **日期**：2026-09-27
- **目的**：`reports/T2_E_I1_TCI_DESIGN_FREEZE_20260927.md` 与 `reports/T2_H_N2_A2C_DESIGN_FREEZE_20260927.md` 的「训练前必须完成」第 1/2 项——用 `web_read` / Europe PMC 读取**原文与官方元数据**后逐条判定，替代第一批（D-20260927-T2CITE-001）只核验了 Perler 与 MacKenzie 的缺口。
- **核验方式**：arXiv 摘要页原文 + Europe PMC REST API 的 `resultType=core` 官方元数据（题名、DOI、期刊、卷期、摘要全文）。**不依赖检索结果摘要。**

---

## 1. `E-I1 TCI` 的锚点：Myronenko & Song 2010, *TPAMI*

**核实到的文献**：A. Myronenko, X. Song, *Point-Set Registration: Coherent Point Drift*，arXiv:0905.2635（2009-05-15 提交；期刊版 *IEEE TPAMI*）。

| 检索简报的说法 | 判定 | 原文依据 |
|---|---|---|
| 「软对应」 | ✅ **成立** | 原文把配准建模为**概率密度估计**：用 GMM 拟合，第一点集为质心、第二点集为数据，最大化似然；E 步给出 GMM 隶属概率，即**软（概率）对应** |
| 「MAP-EM」 | ✅ **成立** | 原文明确 *"we derive a closed form solution of the maximization step of the EM algorithm"* |
| 支持非刚性 | ✅ **成立** | 原文：非刚性情形下 *"we impose the coherence constraint by regularizing the displacement field and using the variational calculus to derive the optimal transformation"*，并给出线性复杂度算法 |
| 「正反一致性自诊断」 | ❌ **不成立** | 摘要提到 noise 与 outliers 是该问题的**挑战**，但**全文未提出**正反（forward–backward）一致性诊断。该子主张**不能归于本文** |

**处置**：`E-I1` 的**核心锚点成立**（概率软对应 + EM + 非刚性位移场，全都在原文里）。「正反一致性自诊断」一节已在设计冻结 §1.2 明确写成**本项目自定的工程选择**（`conf_i` 的定义与线性 `f`），并已标注不依赖该文献——**设计文本无需改动**。

---

## 2. `H-N2 A2C` 的锚点：Aviñó-Esteban et al. 2025, *Development*

**核实到的文献**：L. Aviñó-Esteban, H. Cardona-Blaya, J. Sharpe，***Spatio-temporal reconstruction of gene expression patterns in developing mice***，*Development* **152**(4): dev204313，2025-02，PMID 39982400，DOI `10.1242/dev.204313`（预印本 DOI `10.1101/2024.08.13.607727`）。

| 检索简报的说法 | 判定 | 官方摘要原文 |
|---|---|---|
| 跨阶段插值空间表达图案 | ✅ **成立（核心思想）** | 摘要：*"integrate static snapshots of gene expression patterns across developmental stages, creating a continuous 2D reconstruction of gene expression patterns over time. This method **interpolates small tissue regions over time** to create smooth temporal trajectories of gene expression."* |
| 可作为「解剖坐标条件回归」的承重锚点 | ⚠️ **部分成立——组织与模态均不匹配** | 该文是 **limb（肢芽）** 发育、**2D** 重建、基于**全胚原位杂交（ISH）** 的静态图案；涉及基因含 *Sox9*、*Hand2*。而 `H-N2` 要做的是 **3D 心脏 MERFISH、细胞级、带细胞类型的解剖坐标回归** |

**判定**：**核心思想（跨阶段插值空间表达图案 → 连续时空重建）确有先例**，但这是 **limb / 2D / ISH**，不是 heart / 3D / 单细胞空间组。把它当作 3D 心脏解剖坐标条件回归的**承重**锚点属于**过度外推**——与第一批被判「不撑得住」的 Perler、MacKenzie 属同一类错误，只是程度较轻（核心方法思想确实对得上）。

**处置**：`H-N2` 的锚点降级为**「概念相邻的先例，不同组织/维度/模态」**，**不得**在 RESULT 中声称该文支撑本路线的 3D 心脏构造。设计冻结 §0 的锚点行已相应改写。路线本身**仍可执行**——其价值来自「跨阶段共享同一组位置函数系数」这一自拟设计，而非该文献。

---

## 3. 汇总

| 路线 | 锚点 | 判定 | 是否需改设计 | 是否阻塞执行 |
|---|---|---|---|---|
| `E-I1 TCI` | Myronenko & Song, CPD | ✅ 核心成立（子主张「正反一致性」不成立，已在设计中标注为本项目自定） | 否 | 否 |
| `H-N2 A2C` | Aviñó-Esteban et al. 2025 | ⚠️ 核心思想成立，但 limb/2D/ISH ≠ heart/3D/MERFISH，**承重性降级** | 是（改 §0 锚点行） | 否 |

**累计**：M1 九条路线的承重引用现已核验 **3 条撑不住**（Perler、MacKenzie、本条的过度外推）、**1 条部分成立**（本条）、**1 条核心成立**（CPD）。`X-N2` 的 MacKenzie 前置条件问题仍待其「占据度重定义」条款落实后重核。

## 4. 教训（与第一批一致，值得单独记）

三批核验全部指向同一模式：**researcher 环境的检索只到「题名/期刊/DOI 出现在结果里」这一层，因此机制描述常常是从题名脑补的。** 名字对了不等于被预测量对了——第一批的 Perler 与官方 `variogram` 是同一个坑的两种表现（一个是把文献方法张冠李戴，一个是把指标同名当成同名同物）。**任何后续新增路线的承重引用，必须在设计冻结前用原文级核验（arXiv 摘要页 / Europe PMC `resultType=core` / DOI 落地页）逐条判定，不得以检索命中替代。**

## 5. 边界

本次仅读取公开文献与官方元数据，**未下载任何数据、未训练、未建候选、未改任何已评分文件、未上传**。核验结论只用于「引用能否支撑机制描述」这一判断，**不构成对两条路线科学价值的评估**。`blocks_submission: false`。
