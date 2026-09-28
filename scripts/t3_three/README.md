# T3 三个可上传候选

设计：`reports/T3_THREE_DESIGN_20260929.md`；配置：`configs/t3_three/design_20260929.json`。三路线为r1agree、r2damp、r3diffuse，完整7449×500推断。

从仓库根目录运行；所有run目录必须不存在：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_three.run prepare \
  --run-dir artifacts/t3_three/T3-THREE-20260929-v1/shared
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_three.run r1agree \
  --run-dir artifacts/t3_three/T3-THREE-20260929-v1/r1agree
```

另外两条用各自lane名和新目录。prepare复现冻结高分H/G，重审来源用途与输入哈希，重新拟合四个空间留出Hurdle并做条件覆盖的高低组诊断。最终模型复用原始全量高分组件，三路线只改变响应算子；不重新训练旧GCN。没有匹配Gata4 KO真值评分，不以WT替代它。

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_three.validate \
  --root artifacts/t3_three/T3-THREE-20260929-v1 \
  --report reports/t3_three_20260929 --export deliveries/t3three_20260929
```

独立验证后用scripts.t3_next.deliver的三个`--run-dirs`打包。已交付目录不得覆盖；新批次需新的shared路径/配置，精确复现则在隔离checkout恢复各run的code（旧依赖）、code_three（本批实现）与code/design.json快照。

测试：`LD_LIBRARY_PATH=/opt/anaconda3/lib python -m pytest -q --import-mode=importlib tests/t3_three/test_ops.py tests/t3_next/test_five.py`。校验和测试证明工程身份与算子约束，不证明KO准确率或因果机制。
