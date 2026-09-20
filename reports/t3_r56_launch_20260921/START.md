# R5/R6 开工入口

R5已有父v0009的v0032/v0033，合约通过；上传包：deliveries/r5sig__t3__upload__20260920.zip。下一步取得服务器总分、五子分及原始证据，不重复生成。本轮未上传。

R6输入准备完成，以下命令尚未执行：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 python -m scripts.t3_next.run r6 --run-dir artifacts/t3_next/T3-R6-OP2-20260921-v1 --source-manifest reports/t3_r56_launch_20260921/SOURCE_MANIFEST.json
```

运行目录必须不存在。沿用configs/t3_next/design.json的seed、训练量和门槛，完整gene holdout比较no-change/ridge/GCN；失败保留FAILED_GENE_HOLDOUT，不改阈值，不静默替换为子集。满足门槛后才拟合最终模型并生成候选；新候选仍须合约检查和服务器评分。不得载入其他未获准数据、恢复未审查条件或使用目标响应标签。若更改设计，另建版本并登记T3_TRACKING。

当前parent计划沿用现有R6配置；运行时由INPUT_LOCK及候选INDEX记录确切身份。所有模型计算和目标推断目前NOT_RUN。
