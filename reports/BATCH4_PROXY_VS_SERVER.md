# Batch 4 Proxy vs Server

| Case | Local proxy said | Server said | Lesson |
|---|---|---|---|
| T2-R1 global matching | NFS/Moran/objective 全优 | tie (57.3/57.31 vs 57.25) | proxy 乐观：离散化质量≠board 收益 |
| T2-R2 heart L2 | 60% clip 担忧 | +4.79 大胜 | proxy 悲观也会错：clip≠损伤 |
| T1-R1 family | pseudo-target 高分传统 | 全灭（最高 47.85） | pseudo-target（E9.5 同阶段）循环论证，只保灾难 |
| T3-R1 | 无方向预测能力（诊断只验改动） | +0.15 tied best | target-free 诊断诚实：只验“改了什么”，不猜方向 |
| T3-R2 | 方向只覆盖 5/33 states（弱预期） | 双败符合预期 | 覆盖度低的本地判断这次是对的，但仍需服务器确认才算数 |
| Floor probes | 无本地验证手段 | 47.0/46.8 | floor 缺口本地不可见是结构性的，不是 proxy 调参问题 |

Standing rule（已执行，不重复）：本地 proxy 只排序和防灾难，不再以“稍差一点”阻止服务器探针，也不再以“全优”宣称晋级。
