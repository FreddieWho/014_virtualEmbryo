# T3 autoresearch 复现入口

本轮已完成，目标固定开发MSE降低20%，达到20.3112%。不要继续在原test上调参。

保留模型/冻结评估/完整Git位于 `artifacts/autoresearch/t3-20261002-v1/`。
本目录 `retained_model.py` 是最终模型的逐字节副本，便于随主仓库复用。
模型 `predict(train, query)` 返回source尺度的响应delta；支持既有26扰动与Gata4的静态特征，
不能当作通用任意基因接口或直接上传的MERFISH预测器。

从项目根目录复算固定开发指标：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 artifacts/autoresearch/t3-20261002-v1/evaluate.py
```

查看控制器状态（不会启动新实验）：

```bash
python3 /home/huyudi/.codex/skills/codex-autoresearch/scripts/autoresearch.py status --repo artifacts/autoresearch/t3-20261002-v1
```

`prepare.py`生成冻结开发集；其余prepare脚本重建WT/来源对照特征，拒绝覆盖既有产物。
`final_check.py`仅用于模型固定后的那一次留出检查，也拒绝覆盖。现有结果直接读取
`reports/t3_autoresearch_20261002/FINAL_CHECK.json`，不要反复用test挑选模型。

报告：`reports/t3_autoresearch_20261002/REPORT.md`。
全部结果是来源域预测证据；不是Gata4目标真值评分或服务器分数。
