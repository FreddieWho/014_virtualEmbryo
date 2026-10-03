# T2:heart:val_extrap 本地优化交接（2026-10-03）

**回分更新（2026-10-03）：v0029已评分，REJECT；当前scale0.9配置关闭。以下保留提交前本地实验历史，未提交/未评分与HOLD描述已被本次回分取代。** 详见[服务器复盘](../t2_scale_score_review_20261003/REPORT.md)，总分与8项原始回分以服务器登记为准。

用户确认前台目标 ≥6.0，已完成。一次实验保留，零次回退；固定三种子中位数从 **3.912955 → 7.523743**（+3.610789）。控制器状态 `complete`，停止条件为达到确认目标，不代表穷尽所有模型路线或找到全局最优。

## 实际改动与边界

继承时间归一分位数外推 × 组成重采样，将坐标绕各自质心乘 **0.9**。表达矩阵、细胞顺序、组成和元数据不变。

**全部增益来自 `scale_log_ratio` 一个通道；其他七个综合分通道逐种子相同。** 缩放通道已触及原冻结综合公式的 +30% 截断上限。不能将此解释为表达预测改善、新机制发现或整体生物模型进步。

评分目标是冻结 E9.5 心脏子集，几何缩小很可能利用其空间范围偏差；上一轮代理与服务器排序相关仅0.122。本轮仅确认本地开发评分，未做独立留阶段验证，未读取 E10.5/E12.5 真值，未提交/未评分。服务器现役和最高分不变。后续优先建立留阶段外推评估再研究模型，而不是继续缩小坐标追逐同一已饱和通道。

## 固定评价结果

| 种子 | 原分数 | 新分数 | 护栏 |
|---|---:|---:|---|
| 20260929 | 3.912955 | 7.523743 | PASS |
| 20261007 | 4.008804 | 7.700799 | PASS |
| 20261008 | 3.605816 | 7.495028 | PASS |

三次完整500基因评分/轮；基线与试验共六次。所有种子通过原数值护栏（DE、library ratio、variance ratio、pseudobulk relative error）及结构检查。`comparison.json` 保存原始通道变化，controller receipt 保存全部指标。

## 交接

- task：T2:heart:val_extrap。
- candidate ID：`AR-T2LOCAL-20261003/T2:heart:val_extrap/v0029`。
- parent：`v0024_qte_tc_s929`，其祖先为 baseline v0001；祖先组成变更的历史豁免仍保留。
- artifact：[`v0029_ar_scale09/submission.h5ad`](../../submissions/candidates/T2_heart_val_extrap/v0029_ar_scale09/submission.h5ad)；采用固定三种子中位数对应种子20260929。
- SHA256：以 [`submissions/INDEX.tsv`](../../submissions/INDEX.tsv) 的 v0029 行为权威；本次身份复核 `ef2f4786819950701286df0fc557cf41fa2f6065a1749dc74e26c137f4b27a47`。
- contract：相对直接父版本 **PASS**，无错误；[`contract_v0029.json`](contract_v0029.json)。这不消除父版本相对v0001的历史组成偏离。
- 检查：表达逐值相同、obs/var/行序相同、float32坐标与中心缩放公式逐值相同；三种子护栏PASS；复制后SHA相同。
- 建议决策：`HOLD_LOCAL_ONLY`，保留本地结果，不凭此推荐服务器晋级；本地目标完成。
- blocker：无；`blocks_submission: false`。服务器未评；独立外推验证 `NOT_RUN`。

## 复现与审计

独立Git仓库：`artifacts/autoresearch/t2-extrap-20261003-v1`。
Run ID：`4c13e854a96e450b834647507385bfe5`；保留提交：`621f24f0b5c87d2d1f0c09f52d5417506262e637`。

```bash
cd artifacts/autoresearch/t2-extrap-20261003-v1
env PYTHONDONTWRITEBYTECODE=1 LD_LIBRARY_PATH=/opt/anaconda3/lib OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python evaluate.py
python evaluate.py --guard
```

`model.py`与`config.json`为保留模型；`prepare.py`重建基线并核对历史种子表达/坐标/行序精确一致。输入、评分程序和公式SHA已冻结在`input_manifest.json`；评分器未改动。

[HTML实验记录](../../artifacts/autoresearch/t2-extrap-20261003-v1/autoresearch-results/report.html) · [机器事件](../../artifacts/autoresearch/t2-extrap-20261003-v1/autoresearch-results/events.jsonl) · [通道比较](comparison.json)。原项目没有自动commit或revert；自动Git操作仅发生在独立仓库。

归档交付包：[t2local__t2__upload__20261003.zip](../../deliveries/t2local__t2__upload__20261003.zip)，含一个候选、四份清单及本地结果说明；CRC/成员SHA通过。仅打包，未上传；若后续提交，需回填服务器分数与证据。
