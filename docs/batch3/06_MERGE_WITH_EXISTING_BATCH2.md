# 与已有 Batch 2 外部信息施工包的合并规则

## 1. 先检测，不重复施工

若存在以下任一目录：

```text
docs/batch2_external/
Virtual_Embryo_Batch2_External_Data_Optimization_Pack_20260829/
artifacts/atomic_batch2/
infra/external_data/
```

P0 必须检查其 manifest/hash，而不是重新下载或重新净化数据。

## 2. 任务映射

| 已有 Batch 2 | 本包任务 | 处理 |
|---|---|---|
| `P0_DATA_AUDIT_AND_INGEST` | P0-LOCK 的 data-audit 子项 | hash 一致则复用；规则 snapshot 不同则重新审计，不重下原始数据 |
| `B2-T3-A1` | `T3-S1-PRIOR` | 复用 GATA4 evidence、state gate、CellOracle/scTenifold vote；按本包标准 prior schema 转换 |
| `B2-T3-A2` | `T3-S1B-GENERATE` | 只有 prior gate 通过才复用；禁止其改变方向 |
| `B2-T1-A1` | `T1-PRE-HARMONIZE` | 复用 state vocabulary/crosswalk/late program admission；先做 hash 与 scorer snapshot 检查 |
| `B2-T1-A2` | `T1-S2-MOSCOT-DECODER` | 复用 early operator/coupling；补齐标准中间件和双 decoder lane |
| `B2-T1-C1` | 后续组合 | 不自动执行；两个上游任务均通过后才能机械组合 |
| `B2-T2-X1` | 不等于 `T2-S3-SHAPE-FIELD` | X1 是外部空间数据条件路线；S3 先用官方观测阶段和现有工具做 G2/G3，不需要外部数据授权 |

## 3. 复用条件

一个旧产物只有在以下条件全部成立时才可复用：

- 有 immutable path 与 SHA256；
- 输入 source 与当前 task 合规一致；
- scorer/contract snapshot 可映射；
- gene/state ID schema 可转换；
- 旧产物的方法职责与本包 task 一致；
- 不包含后续被否决的服务器反向调参。

不满足时，旧产物只能作为诊断参考，不能静默当作新 task 输入。

## 4. 新包实际增加的东西

- 工具环境隔离与标准中间件；
- 十个薄模块的统一接口；
- T2 `Spateo vs pycpd` 的 board-specific shape-field 路线；
- T3 prior 与候选生成的强制分离；
- T1 coupling、mass、mean 与 residual 的职责拆分；
- 统一 gate/manifest/schema 与 source-only 证据边界。

## 5. 禁止覆盖

- 不修改旧 Batch 1/2 candidate；
- 不把旧 artifact 移入新目录后删除原路径；
- 不重写旧 server score registry；
- 新结果通过后，以新 candidate ID 追加登记。
