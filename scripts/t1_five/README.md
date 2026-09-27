# T1 五路线（2026-09-27）

设计契约：`reports/T1_FIVE_DESIGN_20260927.md`；冻结参数：`configs/t1_five/design_20260927.json`。本实现使用完整32,285列，不下载外部数据或读取E10.5/E12.5隐藏真值。

从仓库根目录运行（每次使用不存在的新run目录）：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_five.run prepare \
  --run-dir artifacts/t1_five/T1-FIVE-20260927-v1/shared
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_five.run n1density \
  --run-dir artifacts/t1_five/T1-FIVE-20260927-v1/n1density
```

其余路线：`n2param`、`n3borrow`、`o1mass`、`o2rate`。`prepare` 逐值复现旧R1伪评价与最终v0023，核对官方伪目标/参照，再允许复用旧基线scorer。`run.py` 的 `SHARED` 是本轮锁定审计路径；新批次须新配置/路径，不覆盖本轮目录。

每条先做完整训练区拟合和伪评价预测，再全数据重拟合和最终预测；实际序列化模型重放通过后才注册candidate，最后执行全panel官方scorer。中途失败留下`FAILURE.json`和已注册partial candidates，只有最终`RESULT.json`成功且scorer完成的run可交付。不得因模型已产出就声称完整路线已完成。

候选登记串行，文件父版本统一v0023。o1mass算法父版本R1，o2rate算法父版本R2；其余是项目内新路线。训练区/最终模型分别保存，参数快照在run/code/design.json。精确复现旧版本需在隔离checkout恢复对应代码快照，不能从code目录直接执行相对依赖。

最后独立重放五模型并打包：

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_five.deliver \
  --root artifacts/t1_five/T1-FIVE-20260927-v1 \
  --report reports/t1_five_20260927 \
  --zip deliveries/t1five__t1__upload__20260927.zip
```

默认8 CPU线程、每路线6小时上限；未进行GPU租赁。E8.5→E9.5评价已经见过同阶段训练细胞，且多轮研究反复使用同一report split，只能提供探索性信息，不是独立时间外推或胚胎验证。
