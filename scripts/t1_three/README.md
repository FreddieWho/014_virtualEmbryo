# T1 三个组合候选

设计与参数：reports/T1_THREE_DESIGN_20260929.md、configs/t1_three/design_20260929.json。当前已评分父模型v0029/v0030只读复用；本批实际执行新组合和完整推断，不声称重新训练基础SVD/密度分类器/分位数模型。

从仓库根目录执行，run目录必须不存在：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_three.run prepare \
  --run-dir artifacts/t1_three/T1-THREE-20260929-v1/shared
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_three.run r1compose \
  --run-dir artifacts/t1_three/T1-THREE-20260929-v1/r1compose
```

另两条为r2joint、r3mix。prepare先复现两个高分模型的report/final完整表达和输入锁，再运行三条。每条保存两个场景的模型、完整预测、选行映射、官方scorer和contract，只有RESULT与scorer都成功才可交付。

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_three.deliver \
  --root artifacts/t1_three/T1-THREE-20260929-v1 \
  --report reports/t1_three_20260929 \
  --zip deliveries/t1three__t1__upload__20260929.zip
```

独立校验包括：完整模型重放、整行身份、r1/r2相同类型人数、r3父模型配额及父模型内不放回、基因行序/非负/contract/哈希、单ZIP四manifest。输出行名是预测槽，预测类型在uns['predicted_celltype']；父模型和有效源行索引见FINAL_OPERATOR.json，重复抽样不是独立生物重复。

测试：`LD_LIBRARY_PATH=/opt/anaconda3/lib python -m pytest -q --import-mode=importlib tests/t1_three/test_ops.py tests/t1_five/test_ops.py`。

精确重放用各run的code、code_legacy、code_round2和code/design.json在隔离checkout恢复；新批次修改shared路径并使用新目录，不能覆盖本批。仅官方已发布E8.5/E9.5完整32285列，scorer保留官方内部默认。隐藏E10.5/E12.5真值、portal上传和服务器评分均未运行；cell holdout只能作探索性对照。
