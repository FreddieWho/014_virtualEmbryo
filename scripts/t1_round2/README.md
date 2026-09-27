# T1 第二轮三新两优化

设计：`reports/T1_ROUND2_DESIGN_20260928.md`。参数在 `configs/t1_round2/design_20260928.json`，完整32285基因；只用官方已发布E8.5/E9.5。

从项目根目录执行，目录必须不存在：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_round2.run prepare \
  --run-dir artifacts/t1_round2/T1-ROUND2-20260928-v1/shared
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_round2.run n1stack \
  --run-dir artifacts/t1_round2/T1-ROUND2-20260928-v1/n1stack
```

另外四条为 `n2composition`、`n3states`、`o1caldensity`、`o2shrinkmass`。prepare必须先成功；每条真实拟合/冻结模型复用、完整预测、scorer都完成后才能交付。已有高分组件复用实际保存模型，prepare核对其输入/源码锁和完整表达逐值一致。不重复训练已冻结模型，不读取隐藏时间点。

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_round2.deliver \
  --root artifacts/t1_round2/T1-ROUND2-20260928-v1 \
  --report reports/t1_round2_20260928 \
  --zip deliveries/t1r2__t1__upload__20260928.zip
```

deliver独立重放最终模型、核查实际拟合参数/折划分、scorer/contract/哈希、候选差异并校验zip全部成员。生成参数与预测不可因本地分数而修改。新实验须使用新目录和新的shared配置；精确重现则在隔离checkout恢复对应run的code、code_legacy及design.json快照，复用锁定组件。

每条默认8CPU线程，6小时上限。不租GPU。stage分类的OOF仅对监督分类器交叉拟合：SVD在整个fit区域内无监督拟合，校准内部诊断不是严格整流水线独立验证：校准器使用OOF结果的再划分，各基础折模型训练集彼此重叠；其Brier只能作探索性诊断。目标scorer中的E9.5 report细胞不进入report拟合。最终模型合法使用全部发布数据，不能据此把同阶段cell holdout当未来时间验证。

T1不使用celltype评分；候选继承parent的obs注释代表recipient槽，**预测类型在uns['predicted_celltype']**，整行donor索引在FINAL_OPERATOR.json。组成模型改变粗类型人数；其他路线在类型内操作。重复抽样不代表新增独立细胞或胚胎。

定向测试：`LD_LIBRARY_PATH=/opt/anaconda3/lib python -m pytest -q --import-mode=importlib tests/t1_round2/test_ops.py tests/t1_five`。使用importlib避免两个测试目录的同名test_ops模块冲突。
