# ROADMAP — 技术路径节点

建立日期：2026-09-04。每个节点绑定它检验的 PLAN 假设；节点完成或路径调整时更新。
当前进度：**7/8 节点完成**（N8 待授权）。

| 节点 | 内容 | 检验的假设 | 状态 |
|---|---|---|---|
| N1 `[infra]` | P0 锁定：数据契约、基因面板、scorer 锚点、工具链固定 | 全部假设的可执行性前提 | ✅ 完成（2026-08-30 前） |
| N2 | batch1 四 atom（B1-A1 双 lane 几何/表达、B1-A2 T3 signed-response、B1-A3 T1 partition、B1-A4 J1 配对初探） | H1 第一轮 | ✅ 完成并全部服务器评分：B1-A1 局部有效（embryo 60.1），其余不替换 best；batch1 CLOSED_FOR_REVIEW |
| N3 | T3-S1 prior 链（S1A state join → S1B 外部证据集成 → S1C target-compatible adapter → S1D 独立 activity 检索 → 可满足性审计） | H4 | ✅ 完成：UNSATISFIABLE_UNDER_FIREWALL，CLOSED_AS_RESEARCH_COMPONENT（2026-09-02） |
| N4 | T1-PRE-HARMONIZE（28 union state 词表）+ T1-S2-MOSCOT-DECODER（moscot 耦合+mass forecast 双 lane） | H1@T1 时间外推 | ✅ 完成：服务器 44.9/44.8 双否，路线关闭；词表组件保留复用 |
| N5 | T2-S3-SHAPE-FIELD（相邻 stage 位移场 G2/G3，双 lane pycpd/spateo） | H1/H3 @几何方向 | ✅ 完成：heart_interp 56.7（+0.4）晋级；外推 regime 无证据（H4 holdout 全负） |
| N6 | T2-J1-PROXY（FGW objective 条件 gate）→ T2-J1-FGW-ASSIGNMENT（冻结 spec 正式候选） | H1/H3 @行-点配对方向 | ✅ 完成：proxy 7/7 PASS；heart_interp 57.3（+0.6）晋级，embryo HOLD |
| N7 | HX-DYNAMICS-KILLTEST（MIOFlow 增长/死亡单假设，单 board 单 kill metric） | H1 边界：动力学先验是否补足 moscot 残差 | ✅ 完成：REJECT（0.7475 未优于 moscot 0.6645）；mass 环节非 T1-S2 失败点 |
| N8 | batch4 方向选择：embryo J1 重评（补同靶参照）、heart_extrap 攻坚、T1 新假设、或封板 | 待定 | ⏸ 待用户授权 |

## 路径备注

- N4 与 N7 的否定结果共同收窄了 T1 的可行空间：结构化外推与动力学先验均未胜出，T1 停留在 strict-shift 48.5；重启需要全新假设而非调参。
- N5/N6 的阳性结果都在 T2 插值 regime；外推 regime（heart_extrap 50.5）是 selection 中最弱且无本地证据路线的 board。
- 连续 infra 节点检查：N1 之后无非 infra 节点连续两个以上为纯基础设施，未触发提醒阈值。
