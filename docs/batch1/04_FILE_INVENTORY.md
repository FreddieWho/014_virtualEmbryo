# 文件清单

- `00_START_HERE.md`：第一批范围、顺序、B1-A1/B1-A2 双 lane 终点和使用方式。
- `01_CODEX_CONTROLLER_PROMPT.md`：一次只施工一个原子的总控提示词；当前原子生成两条最终 lane。
- `config/active_atom.yaml`：原子激活配置及双 lane、探索和人工评分预算；Batch 1 已关闭审查，当前无激活原子。
- `config/batch1_manifest.yaml`：机器可读依赖、指标和输出契约。
- `config/scoring_targets.yaml`：当前评分权重与 floor。
- `prompts/B1_A1_T2_G1_SCALE.md`：T2 尺度。
- `prompts/B1_A2_T3_C1_SIGNED_RESPONSE.md`：T3 响应集合与方向。
- `prompts/B1_A3_T1_P2_C7_MASS_RESIDUAL.md`：T1 状态质量与 residual。
- `prompts/B1_A4_T2_J1_POST_PAIRING.md`：T2 生态位配对。
- `prompts/B1_C1_T2_COMPOSE_SCALE_PAIRING.md`：T2 组合结果。
- `templates/ATOM_RESULT_TEMPLATE.md`：强制短结果格式，支持双 lane 原子的 2/6 个候选和 `score_pending`。
- `templates/MANIFEST_SCHEMA.json`：单个候选文件 manifest schema；B1-A1/B1-A2/B1-A3 由 `lane_id`/`candidate_id` 标识。
- `templates/FINAL_SET_SCHEMA.json`：B1-A1、B1-A2、B1-A3 与 B1-A4 的双 lane 冻结结果集 schema。
- `artifacts/atomic_batch1/B1-A1/exploration/`：最多 4 次 source-only 临时尝试的审计目录，不是提交目录。
- `02_DECISION_RULES.md`：保留/提交/淘汰规则。
- `03_NOT_IN_BATCH1.md`：防止 scope creep。
- `reference/OFFICIAL_SOURCE_LOCK_20260827.md`：官方定义锁定。
