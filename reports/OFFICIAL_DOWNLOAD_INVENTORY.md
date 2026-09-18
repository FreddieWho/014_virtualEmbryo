# Official download inventory

更新日期：2026-08-21

这是当前官网资源的下载与可用性清单。状态只按官网当前页面判定，不把本地文件存在误认为官方 byte-identical。

## 结论

- 当前公开的 9 个 challenge H5AD 已全部在工作区：T1 的 E8.5/E9.5 RNA、T2 embryo 的 E6.75/E7.25/E8.0、T2 heart 的 E8.25_late/E8.75/E9.5、T3 的 Mab21l2 KO。
- 官方 5 个 board gene panels 与本地文件逐字节一致；官方机器可读 board index 已落盘到 `data/gene_panel/index.json`。
- 官方公开的 T1 released-stage composition 元数据已落盘到 `data/reference/t1_composition.json`。
- `E8.25_late.h5ad` 已由用户再次人工确认官方下载为 225 MB；本地是 225,091,568 bytes，结构校验通过。官网公开 handoff 页面仍显示 288 MB，作为页面版本差异保留，不再阻塞当前资源闭环。
- 验证/测试真值不是漏下载，而是官网主动 withheld/hidden；不应通过外部来源寻找或替代。

## 已自动下载并校验

| 资源 | 本地位置 | 状态 |
|---|---|---|
| Board index | `data/gene_panel/index.json` | 5 boards、cell limits、required `obsm` 已通过 JSON 检查；SHA-256 `26830523bcba077fe27481ee53cddcf49c6b35cf5bdd7acabc5f6b7c94ea7f78` |
| T1/T2/T3 panels | `data/gene_panel/*.genes.txt` | 5/5 与官网逐字节一致 |
| T1 released composition | `data/reference/t1_composition.json` | 只含 E8.5/E9.5；不含 E10.5/E12.5；JSON 检查通过 |
| Official scorer | `third_party/veckit/` | remote HEAD 与本地锁定提交一致：`46d41e63f42a9aab815db20b742feeccd249cb17` |
| Baseline notebook | `baseline/pseudobulk_shift_tutorial.ipynb` | nbformat JSON 检查通过；用户已确认下载完成 |
| Resources notebook | `baseline/veckit_tutorial.ipynb` | nbformat JSON 检查通过；source-only 内容与 vendored tutorial 一致，差异仅 notebook 元数据/执行输出 |

## 已人工补齐的公开资源

### 1. Baseline implementation Colab

官网 Reference rows 页将 floor、`pseudobulk_shift`、T3 transfer、`bake.py` 和 adversarial controls 的实现指向 Colab；这些实现文件不在当前公开 `veckit` checkout 中。打开后在 Colab 选择 **File → Download → Download .ipynb**：

- [Official baseline implementations Colab](https://colab.research.google.com/drive/11kHZjd4IawoC6uwCqiHNuDGAYpoPlUQO?usp=sharing)

用户已将下载结果落在 `baseline/pseudobulk_shift_tutorial.ipynb`；文件完整可读。由于 Colab 原始下载端点没有可取得的公开 hash，仍不宣称 byte-identical，但资源已可用于后续逐 cell 审阅。

### 2. Evaluation Resources Colab

- [Evaluation → Resources](https://virtualembryo.ai/challenge/evaluation?section=resources)
- [Resources tab 的官方 Colab](https://colab.research.google.com/drive/15QvIevX9xy80jEBnm827t_bMCOtq1l3x?usp=sharing)

用户已将下载结果落在 `baseline/veckit_tutorial.ipynb`。其代码单元内容与 `third_party/veckit/veckit_tutorial.ipynb` 一致，差异仅为 notebook 元数据、cell id 和已执行输出。

### 3. E7.75 single-cell（未发布，无下载）

2026-09-17 重抓官网 Data 页：E7.75 列为 **unused / not released — held out as the Task-2 embryo test stage**，原文“no measured data from that stage is distributed for any task”。此前“已发布/911 MB/登录下载”的缓存记录作废（来源：https://virtualembryo.ai/challenge/data，2026-09-17 实抓）。T1-D7 前提不存在，转 CLOSED；不得从第三方镜像补齐（withheld 清单：T2 embryo E7.75 test；外部数据若落在 protected window 或同一 genotype 属违规风险）。

## 当前不可下载的内容

官网当前明确 withheld/hidden 的内容包括：

- T1：E10.5 validation、E12.5 test；
- T2 embryo：E7.5 validation、E7.75 test；
- T2 heart：E8.5 validation、E10.5 validation、E12.5 test；
- T3：Gata4 KO @ E8.75 validation、β-catenin KO @ E8.75 test。

官网说明验证数据只返回分数，最终阶段才释放 validation answers；test ground truth 不作为普通下载分发。外部数据若落在 protected window 或同一 genotype，也属于违规风险。

官网还提到 richer reference baselines 依赖的两个文件尚未进入 shared storage，但没有给出公开文件名或下载地址。当前不能猜测文件名、从第三方镜像补齐，或把它们标为已部署；floor 和 simple baseline 不依赖它们。

## 官方入口总表

- [Data / account download](https://virtualembryo.ai/challenge/data)
- [Evaluation Resources](https://virtualembryo.ai/challenge/evaluation?section=resources)
- [Reference rows / baselines](https://virtualembryo.ai/challenge/baselines)
- [Official board index](https://virtualembryo.ai/challenge/panels/index.json)
- [Official scorer repository](https://github.com/aristoteleo/veckit)
