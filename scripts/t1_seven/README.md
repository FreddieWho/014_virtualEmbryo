# T1 七路线（2026-09-30）

设计：`reports/T1_SEVEN_DESIGN_20260930.md`。3新模型、2失败路线优化、2成功路线优化。冻结参数：`configs/t1_seven/design_20260930.json`。

运行需要项目 Conda Python 和 `LD_LIBRARY_PATH=/opt/anaconda3/lib`。输入仅已批准的E8.5/E9.5 RNA，完整32285基因；final5118行。训练源、模型、旧评分候选和scorer全部检查哈希。文件不可覆盖。

本批执行：

```bash
env LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_seven.run prepare --run-dir artifacts/t1_seven/T1-SEVEN-20260930-v1/shared
env LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_seven.batch
env LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_seven.validate --root artifacts/t1_seven/T1-SEVEN-20260930-v1 --report reports/t1_seven_20260930 --zip deliveries/t1seven__t1__upload__20260930.zip
```

复现应复制脚本/配置到新版本namespace并指定新的shared/run常量，不可原地再次运行覆盖已有目录；源码快照保存在每个run的code、code_three、code_round2、code_legacy目录。冻结公共cache与模型同为计算输入，完整文件哈希在shared/CACHE_LOCK.json；缓存是已评分模型的完整逐值复现，不是替代核心运算的代理。

`batch`仅两个计算子进程，不创建agent，不发网络消息，不上传。每个process回执从RUNNING转COMPLETED或FAILED；状态判断以真实进程或终态回执为准，不高频轮询。每条失败保留FAILURE.json；不静默跳过模型、评分或改参数救结果。

`validate`用独立进程重新预测report/final，核对相应训练行边界、方法特定参数、全部输出和完整scorer收据，再生成包含合格候选的ZIP及四份manifest。它不证明E10.5未来预测科学有效，更不等同服务器分数。
