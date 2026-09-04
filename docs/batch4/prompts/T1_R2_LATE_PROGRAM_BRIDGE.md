# B4-T1-R2-LATE-PROGRAM-BRIDGE

## 定位

这是 Batch 2 已规划但未真正端到端完成的 gap completion，不是新架构探索。

## 唯一目标

在 strict-shift parent 上注入极少量、合法 E14.5+ WT late-program support，测试“训练阶段不存在的晚期程序”是否比继续调整已有状态更重要。

## 进入条件

必须同时满足：

1. P0 完成；
2. 有已登记 allowlist；
3. 有已经净化的 processed expression，或能在短网络窗口获取 processed object；
4. 不含 E10.5–E13.5；
5. 不含 mutant；
6. 不处理 raw FASTQ；
7. 不建设新 atlas；
8. 不根据服务器分数选择程序。

若 processed data 在一次发现/下载窗口内不可得：

```text
status: BLOCKED_DATA_NOT_READY
```

立即停止。不得花数天修数据。

## Parent

T1 v0004 strict shift 或 P0 锁定的当前 best，不依赖 R1 服务器结果。

## 方法边界

- late data 只定义 gene-program direction/support；
- 不复制 late cells；
- 不把 E14.5 当 E10.5 伪标签；
- 不使用 late cell proportions；
- 程序必须连接到 E9.5 precursor；
- 使用低秩 program，不逐基因自由拟合；
- 保留 E9.5 residual bank；
- 总 birth mass 极低。

## 建议实现

1. 对 official E9.5 与 sanitized E14.5+ WT 做 gene intersection；
2. 按已有 state/program crosswalk 对 precursor/late program 建 soft linkage；
3. 提取少量稳定 program direction；
4. 映射回 T1 full transcriptome；
5. 对 parent 中高 precursor-probability cells 施加收缩 program residual；
6. 未匹配程序和细胞完全保留 parent。

## 两条 lane

### L1_BIRTH005

- 总 program-modified cell mass 5%；
- 单 program ≤2%；
- amplitude = late-vs-E9.5 program difference 的 0.10；
- 每 gene cap = E9.5 state SD 的 0.25。

### L2_BIRTH010

- 总 mass 10%；
- 单 program ≤3%；
- amplitude = difference 的 0.20；
- 每 gene cap 同上。

## 禁止

- 用 E13.5；
- 用 E10.5/E12.5；
- 用外部目标比例；
- 新增第三 lane；
- 训练 flow/ODE；
- 复制 late cell；
- 修改未选择细胞；
- 把 local proxy 当成 late state 真值。

## 输出

两个候选或一个明确 blocker。  
附：

```text
DATA_SOURCES_USED.tsv
sanitization_receipt.json
late_programs.tsv
precursor_linkage.tsv
modified_cell_ledger.tsv
```

## 决策

- 若数据未就绪：`BLOCKED_DATA_NOT_READY`；
- 若程序无法连接 E9.5：`REJECT_IMPLEMENTATION`；
- contract-valid 候选全部进入人工服务器候选池；
- 本任务不自动成为主线。
