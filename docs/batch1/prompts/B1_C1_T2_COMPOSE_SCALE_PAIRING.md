# B1-C1 — T2 组合：G1 尺度校准 + J1 后配对

## 唯一目标

不训练新模型，只把 B1-A1 与 B1-A4 的已冻结结果合成为一个 T2 候选，使同一提交同时携带尺度改进与局部生态位配对改进。

## 前置条件

- B1-A1 已生成并冻结 `scale_model.json` 与 scaled coordinates；
- B1-A4 已生成并冻结 `permutation.npy`；
- 两者基于同一个原始 base submission 和同一 board/gene order；若不是，立即停止并写 BLOCKER，不做重对齐猜测。
- 若 B1-A4 的 immediate parent 已经是当前 per-board 选定的 A1 scale，或本身就是 identity-scale baseline，则该 board 已完成组合，不得重复生成 C1 候选；记录 `NOT_NEEDED_PRECOMPOSED`。

## 合成规则

对每个 board：

1. 从共同 base 读取 X 与 C；
2. 应用 A4 的最终 permutation 到 X；
3. 应用 A1 的唯一 uniform scale 到 C；
4. 不做任何进一步拟合、重采样或参数调整；
5. 由于 uniform scaling 不改变 15-NN 图，A4 的 pairing 应保持有效。

只有 A4 从 pre-A1 root 独立生成、且 immediate parent 尚未携带选定 scale 时，才执行上述合成步骤。

## 检查

只检查一次：

- combined X 行多重集合等于 base；
- combined C 等于 A1 C；
- combined permutation 等于 A4；
- 表达边缘和点云归一化形状没有意外变化；
- contract 通过。

## 验收

- 生成一个新的 combined `prediction.h5ad`；
- 最终 scorer 只运行一次；
- 预期 TSR 接近 A1、NFS 接近 A4；其他指标接近共同 base；
- 输出 combined MANIFEST 与 RESULT；
- 若组合出现非预期冲突，标记 HOLD，不回到 A1/A4 自动重训。

## 禁止

- 禁止再次拟合 scale；
- 禁止再次优化 permutation；
- 禁止加入第三个模型；
- 禁止自动线上提交。
