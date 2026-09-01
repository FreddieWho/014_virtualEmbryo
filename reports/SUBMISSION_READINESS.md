# Submission readiness and competition loop

更新时间：2026-08-21

## 官方硬条件

提交入口：<https://virtualembryo.ai/challenge/account/submissions>

根据官方 Rules、T2 Evaluation 和 board index，T2 提交必须满足：

- 选择一个具体 board/setting；heart 与 embryo 分开提交；
- `.h5ad` 的 `var_names` 与该 board 的 gene panel 完全一致、顺序一致；
- `.X` 为二维 cells × genes，finite、non-negative、log-normalized；
- `obsm["spatial_3D"]` 存在，至少三列且 finite；
- 细胞数在该 board 的区间内；
- 外部公开数据、代码和模型按规则披露；不得使用 held-out stage/genotype 的测量数据；
- Human Team 与 Agent Team 的提交证据要求不同。本项目当前按 Human Team 工作流，不能把人工看过分数后迭代的结果申报为 Agent Team。

官方还提供 unlimited format checks；P2 每个 task 每天最多 8 次 scored submissions。Format check 只验证文件，不返回生物学分数。

## 项目级优先级

本项目优先追求合法 leaderboard 分数。科学路线用于辅助候选筛选、解释风险和控制
违规，不是 scored submission 的前置门槛。`BLOCKED_FOR_PROMOTION` 只表示不能作
正式 biological claim；不能解释为暂停竞赛提交。

## 首次服务器分数

首个 baseline scored submission 已获得服务器返回结果，完整登记见
[`reports/SERVER_SCORE_REGISTRY.md`](SERVER_SCORE_REGISTRY.md)。当前 baseline 为：

- Total：`145.7`
- T1：`47.0`
- T2：`53.4`（heart interpolation `53.0`、heart extrapolation `50.5`、
  embryo interpolation `56.7`）
- T3：`45.3`

submission ID、board/phase 和实际上传文件映射按用户回填，保持 `pending`，不作推测；不额外要求截图、链接或 JSON 原始证据。
后续每次 scored submission 后，必须先回填服务器分数，再进行模型进步比较；缺少服务器分数
时标记为 `score_pending`。

## Submission artifact inventory

| Candidate | Board | Method | Cells | Target used | Local contract |
|---|---|---|---:|---|---|
| `submissions/scored/baseline-001/T2_embryo_val_interp/submission.h5ad` | T2 embryo val_interp | official `pseudobulk_shift` | 5,000 | no | pass |
| `submissions/scored/baseline-001/T2_heart_val_extrap/submission.h5ad` | T2 heart val_extrap | official `pseudobulk_shift` | 25,179 | no | pass |
| `submissions/scored/baseline-001/T2_heart_val_interp/submission.h5ad` | T2 heart val_interp | official `copy_last` floor | 5,872 | no | pass |
| `submissions/scored/baseline-001/T1_val/submission.h5ad` | T1 val | official `copy_last` floor | 5,118 | no | pass; SHA-256 `11dbf50a0eb876a1a3c53a283459c8f53e14dcd314f1e7725a3a6107618c981e` |
| `submissions/scored/baseline-001/T3_gata4/submission.h5ad` | T3 gata4 | official `wt_identity` floor | 7,449 | no | pass; SHA-256 `8ed2373e16a037291f5ebb6e2308072639093e250ea10bc17b690ea183caeacd` |
| `submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad` | T2 heart val_interp | fixed midpoint expression interpolation + library-size normalization | 5,872 | no | pass; SHA-256 `402b0a893672e9ce267af0a39bcdf8e00975cdf3dc7dca00fab80858ae2d08b4` |

每个文件都带有 `uns["ve_submission_prep"]`，记录 board、输入文件、seed、采样策略和 `target_used=false`。

## 最近一次服务器结果

`submissions/scored/submission-002/T2_heart_val_interp/submission.h5ad`
已取得服务器结果：heart interpolation `53.6`，相对 baseline `53.0` 提升 `+0.6`；
aggregate Total 从 `145.7` 提升到 `145.9`。完整记录见
[`reports/SERVER_SCORE_REGISTRY.md`](SERVER_SCORE_REGISTRY.md)。

该版本保留为当前 T2 heart interpolation best。下一次候选需要新建更高版本，不能
覆盖 `v0002`。

## 下一步

继续以单 board、单主要变量方式生成 `v0003`，或在确认新的候选前保持当前 best；
不得覆盖已评分的 `v0002`。

## 当前尚未完成

- 首个 baseline scored submission 已完成；submission ID 和 board/phase 映射仍待用户回填，baseline 文件 SHA-256 已登记；
- 后续候选的服务器分数和 submission ID 仍待用户回填；不新增原始证据环节；
- 后续 scored submission 仍可能需要用户完成账号登录、验证码或二次确认；
- submission 不等于科学模型晋级。榜单分数可用于竞争反馈，但不能替代独立
  biological validation。

T1/T3 的首提交含义：T1 复制 released E9.5 RNA stage；T3 复制 matched WT
E8.75。两者都只使用 released reference 数据，不使用 E10.5、Gata4 KO 或其他
held-out truth。

官方链接：

- <https://virtualembryo.ai/challenge/rules>
- <https://virtualembryo.ai/challenge/evaluation?section=submissions&task=2>
- <https://virtualembryo.ai/challenge/baselines>
