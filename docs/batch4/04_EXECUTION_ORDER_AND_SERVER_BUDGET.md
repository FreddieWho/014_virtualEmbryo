# Batch 4 执行顺序、并行关系与服务器预算

## 1. 总原则

- 每个 task 是独立 locked run；
- 不在一个 run 内等待服务器分数后继续改；
- 服务器结果回填后，可以由人决定是否启动一个新的、重新锁定的 run；
- 自动上传关闭；
- 格式检查优先，格式检查不替代 scored submission；
- 本地 proxy 用于排序和灾难检测，不是隐藏分数预测器。

官方 P2 上限为每 task 每 UTC 日 8 次 scored submissions。Batch 4 设置更低的内部软上限，避免浪费。

## 2. Wave 0：状态和 floor

### `B4-P0-STATE-FLOOR-PARITY`

必须最先完成。

输出：

- 本地 score registry 一致性报告；
- v0006/7 旧路线关闭记录建议；
- T1 exact-floor candidate；
- T3 exact-floor candidate；
- floor builder 差异表；
- 上传包。

服务器建议：

| Task | 候选数 |
|---|---:|
| T1 | 1 |
| T3 | 1 |
| T2 | 0；只审计 parent |

若 exact floor 仍明显偏离 50，打开 `FLOOR_PARITY_UNRESOLVED`，但可以继续低风险候选生成；不得把 exact floor 直接作为正确 parent 写死。

## 3. Wave 1：最高信息量修复

P0 完成后可在不同 worktree 并行：

### T1：`B4-T1-R1-CONSERVATIVE-FAMILY`

4 个候选：

1. strict shift `damp=0.5`;
2. 50/50 population mixture；
3. strict expression + 25% moscot mass graft；
4. strict expression + 50% moscot mass graft。

加 exact floor，共最多 5 次 T1 scored submissions。

### T2：`B4-T2-R1-FGW-ASSIGNMENT-REPAIR`

heart interpolation 2 个候选：

1. 原 epsilon + 全局双射；
2. 较低 epsilon + 全局双射。

这是 Batch 4 中服务器先验最强的路线，优先上传。

### T3：`B4-T3-R1-GENOTYPE-ONLY-ABLATION`

3 个候选：

1. Gata4 全细胞置零；
2. Gata4 hard lineage 置零；
3. Gata4 soft lineage + Gata6 F/+。

加 exact floor，共最多 4 次 T3 scored submissions。

## 4. Wave 2：补齐未覆盖评分轴

### T2：`B4-T2-R2-INTERPOLATION-EXPRESSION-BRIDGE`

四个候选：

- embryo L1/L2；
- heart interpolation L1/L2。

若同一天已经上传 T2-R1 两个，T2 当日共 6 次，仍低于官方 8 次。

### T3：`B4-T3-R2-DEVELOPMENTAL-AXIS-REPAIR`

两个候选：

- low delay；
- medium delay。

与 T3 floor + R1 合计最多 6 次。

### T2：`B4-T2-R3-HEART-EXTRAP-EXPRESSION-CAL`

三个候选。建议另一个 UTC 日执行，避免与 R1/R2 混在同一批中难以阅读。

### T1：`B4-T1-R2-LATE-PROGRAM-BRIDGE`

条件任务。最多两个候选。建议在 R1 分数回填后才决定是否启动新的 locked run，但其 prompt 和参数不能依据分数反推 target；只允许决定“是否值得花资源”。

## 5. Wave 3：分数回填与 closeout

每批服务器结果回来后：

1. 用户提供原始 score / submission ID；
2. coordinator 更新 `reports/SERVER_SCORE_REGISTRY.md`；
3. coordinator 更新 `submissions/INDEX.tsv`；
4. 追加 `docs/coordination/DECISIONS.md`；
5. 同步对应 `T*_TRACKING.md`；
6. 不覆盖 scored artifact；
7. 激活 `B4-CLOSEOUT-ARCHITECTURE-HANDOFF`。

closeout 不生成候选，只生成架构切换材料。

## 6. 上传顺序

每个 task 内按以下顺序：

1. exact floor；
2. 能隔离单一修复的候选；
3. 组合候选；
4. 高风险 lane。

不要先上传最复杂候选，否则低分无法判断是基线、幅度、mass、pairing 还是表达桥的问题。

## 7. 分数使用规则

允许：

- 选择已完成 run；
- 决定哪个候选成为下一 run parent；
- 决定是否启动下一组预先规划的工作；
- 正常比较有限参数族。

禁止：

- 根据分数差推断目标细胞比例、基因方向、组织尺度或真实 effect size；
- 构造方程求 hidden target；
- 在同一个 locked run 中用服务器反馈改变 H5AD；
- 人手修改 agent 产出的 H5AD。

## 8. 内部停止规则

### T1

- 若 exact floor ≈50 且所有 R1 lane ≤50：关闭 Batch 4 的 T1 微调，R2 仅在数据已就绪时执行；
- 若 mass graft 胜 strict family：保留 `state_mass.tsv` 接口；
- 若只 damp / mix 胜出：下一代架构继续使用 conservative anchor。

### T2

- 若全局 assignment 不胜 v0009：关闭 FGW 离散化微调，不继续扫 epsilon；
- 若 expression bridge 在任一 board +1：允许一次机械组合 run；
- 若 heart extrap 三 lane 全 ≤50.5：停止低容量外推修补。

### T3

- 若 target-only 任一 lane > floor：证明旧下游 residual 有害，保留 genotype interface；
- 若 developmental axis > target-only：保留 stage-conditioning interface；
- 若全部 ≤正确 floor：标记 `ARCHITECTURE_RESET_REQUIRED`，不再手工调 prior。

## 9. 推荐上传包命名

遵守项目既有规则：

```text
<t短码>_<board>__<lane>__vNNNN.h5ad
```

总长 ≤50 字符。ZIP：

```text
<b4短码>__<task>__upload__<YYYYMMDD>.zip
```

必须包含：

```text
UPLOAD_MANIFEST.tsv
RUN_ID_MAP.tsv
EVIDENCE_MANIFEST_POINTERS.tsv
```
