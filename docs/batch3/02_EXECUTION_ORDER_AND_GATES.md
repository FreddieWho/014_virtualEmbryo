# 执行顺序、依赖与 Gate

## 1. 依赖图

```text
P0-LOCK
├── T3-S1-PRIOR
│   └── [PRIOR_GATE_PASS] T3-S1B-GENERATE
├── T1-PRE-HARMONIZE
│   └── [STATE_GATE_PASS + FULL_PANEL_SCORER_PASS] T1-S2-MOSCOT-DECODER
└── T2-S3-SHAPE-FIELD
    └── [OPTIONAL] T2-J1-PROXY

HX-DYNAMICS-KILLTEST 依赖 T1-S2 或 T2-S3 已形成可比较的结构化主线。
```

## 2. P0 是强制前置，不是形式检查

P0 必须回答：

- scorer bundle、contract 和 board snapshot 是什么；
- 当前 parent 的真实路径、SHA256 与 server registry 对应关系；
- T1 full-panel local scorer 是否可运行；
- 内部历史分数与当前官方 floor 文案是否属于不同 snapshot；
- 已有 Batch 2 数据审计和产物哪些可以复用；
- 各工具应在哪个隔离环境运行。

P0 未通过时，后续只能做代码阅读，不能生成正式候选。

## 3. 推荐顺序

### 第一组：并行信息层

- `T3-S1-PRIOR`：优先级最高，因为 Batch 1 T3 失败假设最清楚。
- `T1-PRE-HARMONIZE`：与 T3 独立，可以并行；它修复 T1 的验证和状态表示前提。

### 第二组：生成层

- `T1-S2-MOSCOT-DECODER`：依赖 state harmonisation 和 full-panel scorer。
- `T2-S3-SHAPE-FIELD`：依赖 P0 与 board-specific G1 parent lock，不依赖 T1/T3。
- `T3-S1B-GENERATE`：依赖 prior gate；方向不成立时禁止优化 PSS。

### 第三组：条件探索

- `T2-J1-PROXY`：只验证 objective 与 source-only NFS-like 指标是否同向，不直接生成正式候选。
- `HX-DYNAMICS-KILLTEST`：只允许一个工具、一个 board、一个 kill metric。

## 4. Task Gate 摘要

| Task | 进入 Gate | 退出产物 | 下一步 Gate |
|---|---|---|---|
| P0-LOCK | 无 | scorer/parent/toolchain locks | scorer 与 parent 可复现 |
| T3-S1-PRIOR | P0 pass；外部 source 审计通过 | prior.json、evidence.tsv、gate_report.json | sign convention + source-only direction gate |
| T1-PRE-HARMONIZE | P0 pass；T1 scorer 可用 | state_vocabulary、crosswalk、stability report | projection 稳定、低置信 state 显式 unresolved |
| T1-S2-MOSCOT-DECODER | T1-PRE pass | 每 board 两条 H5AD | 预定原子改善且 protected checks 通过 |
| T2-S3-SHAPE-FIELD | P0 pass；G1 winner 锁定 | 每 board Spateo/pycpd 两 lane | G1/表达保护；G2/G3 proxy 改善 |
| T3-S1B-GENERATE | T3 prior gate pass | 1–2 条 T3 H5AD | DES/DCS 不同时低于 identity；再看 PSS |
| T2-J1-PROXY | source stages 足以 pseudo-holdout | objective report | 至少两个 holdout 同方向优于 random |
| HX-DYNAMICS-KILLTEST | 结构化主线已完成 | 一条 kill-test candidate/report | 单一假设被支持才保留 |

## 5. 修改 active task

推荐使用激活脚本：

```bash
python scripts/activate_task.py --task T3-S1-PRIOR
```

它会从 `config/active_templates/` 复制对应模板。也可手工只修改 `config/active_task.yaml` 中：

```yaml
active_task: T3-S1-PRIOR
prompt_file: prompts/T3_S1_PRIOR_COMMITTEE.md
```

不要一次配置多个 task。若需要并行，复制两份工作树或使用不重叠的分支与 artifact 目录。
