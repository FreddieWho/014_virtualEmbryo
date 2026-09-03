# T2-J1-FGW-ASSIGNMENT · FGW 软配对正式候选

## 状态

衍生任务。由 `T2-J1-PROXY-20260903-v1` 的 gate `J1_PROXY_PASS` 解锁（`04_DECISION_RULES.md` §7："允许另行授权 assignment candidate"）。本卡是该授权的任务定义。

## 唯一目标

在固定预测表达行集合与固定 3D 点云上，用 J1-PROXY 已验证的 FGW soft-assignment objective 重排"哪一行表达放在哪个坐标点"，生成 embryo/heart 两个 interpolation board 的正式候选，替代 B1-A4 已失败的 hard permutation 路线。

不做：heart extrapolation board（J1-PROXY 未验证 extrap regime；T2-S3 H4 已证明外推无本地证据）、几何改动（G1/G2/G3 全部冻结）、多轮调参。

## 前置

- `T2-J1-PROXY-20260903-v1` gate PASS（objective spec SHA256 `4cf86109…8110e7`）
- P0 locks；当前 board parent SHA256 锁定
- **heart 参考审视（强制第一步）**：J1-PROXY 记录 heart holdout 逐位置 pearson 为负（参考跨 E8.25_late↔E9.5 共 1.25 天、标签交集仅 5）。正式生成 heart 候选前，必须用预声明标准审视参考构建质量（如改用单邻接阶段参考、扩大标签交集、或增大支撑采样）；若无法达到标准，heart board 显式 `HOLD`，本 atom 只出 embryo 候选

## 施工

1. **Objective 冻结**：直接使用 J1-PROXY 的冻结 spec（POT entropic FGW、alpha=0.5、eps=0.005、square_loss、均匀边际、state cost + internal-distance cost、max 归一），不改任何超参。
2. **目标支撑**：parent 候选的坐标点云（J1 不动几何，支撑已知）；参考结构来自 source 观测阶段（embryo: E6.75/E7.25/E8.0；heart: E8.25/E8.75/E9.5，面板各自 498/500 genes）。
3. **Soft→离散规则（薄 adapter，先写死再运行）**：transport plan 转表达行分配必须用确定性规则（barycentric 投影或 argmax+确定性 tie-break），记录规则与冲突数；任何非双射/非有限/账本不一致 → fail closed。
4. **Parent**：
   - embryo interp：`submissions/candidates/T2_embryo_val_interp/v0002_g1_formal_log_rms/submission.h5ad`（当前 board best 60.1）
   - heart interp：`submissions/candidates/T2_heart_val_interp/v0007_t2_s3_l1_pycpd/submission.h5ad`（当前 board best 56.7）
5. 每 board 一次完整生成、一次 contract、一次 local scorer/proxy（pseudo-target 声明照旧）。

## Protected checks（逐条记录）

- 坐标/obs/var/gene order hash 与 parent 完全一致；
- 表达行集合为同一多集（permutation 语义）；逐行内容不变，仅行-点映射变化；
- 细胞数在 board contract 范围内；
- 确定性：同 seed 同输入重跑产物字节一致；
- kNN15 邻域 overlap 与 NFS proxy 记录（改善方向须与 J1-PROXY 一致，不宣称 leaderboard 提升）。

## 输出与停止

```text
candidates/<board>/submission.h5ad + contract_report.json
intermediates/<board>/transport_plan.npz、assignment.tsv、field_meta.json
metrics/<board>/geometry_checks.json（坐标不变性）、nfs_proxy.json
RESULT.md / METHOD_DISCLOSURE.md / stable manifest
```

完成 gate 判定（READY_FOR_MANUAL_SUBMISSION / HOLD_AS_COMPONENT / REJECT / BLOCKED_*）后停止。不上传服务器，不进入其他 atom。
