# docs 入口（审计从这里开始，不要全目录扫描）

1. `../AUDIT.md` —— 一页纸记分牌（脚本生成：`python scripts/generate_audit.py`）
2. `../reports/LANE_VERDICTS.tsv` —— 31 lane verdict 表（关 lane 时必须追加一行）
3. `../submissions/INDEX.tsv` —— 候选＋SHA＋服务器分（唯一真源）
4. `../TODO.md` —— 当前待办＋分支记录（根目录）
5. `coordination/DECISIONS.md` —— 决策日志（只追加）；`coordination/T{1,2,3}_TRACKING.md` —— 路线变更
6. `coordination/KNOWLEDGE.md` —— 科学结论（带成熟度）；`../reports/SERVER_SCORE_REGISTRY.md` —— 分数证据

冻结区：`batch1/`、`batch2/`、`batch3/` 的 prompts/templates/compliance（各有 SUPERSEDED 说明）。
活代码契约：`batch3/interfaces/`（contract_io，被 20+ 脚本 import）、`batch3/config/`（dependency lock）、`_starter_pack/`（官方快照，只读）。
