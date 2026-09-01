# Official source lock — 2026-08-27

施工时优先使用项目现有的、更晚的锁定版本。若没有，则以以下官方页面为准：

- Evaluation: https://virtualembryo.ai/challenge/evaluation
- Reference rows / baselines: https://virtualembryo.ai/challenge/baselines
- Leaderboard: https://virtualembryo.ai/challenge/leaderboard
- Rules: https://virtualembryo.ai/challenge/rules

当前关键事实：

- T2 四组等权：expression、population、geometry、NFS 各 25%；geometry 内 SDD/ODS/TSR 各约三分之一。
- T2 空间指标忽略平移和旋转；提交可自行选择细胞数，超过 contract 最低值后不要求匹配真值细胞数。
- T3 权重：DES 30%、DCS 25%、PSS 25%、MMD/CSS 20%。
- floor：T1/T2 为 copy_last，T3 为 wt_identity；floor 在打印分数中定义为 50。
- 官方 baseline implementation 已通过 Reference rows 页面的 notebook 提供。

本批不要求 Codex 每个原子都重新浏览官网。只需在第一次执行时记录当前 scorer/index/official source commit；后续原子复用同一锁定版本，除非现有工作台明确检测到官方更新。
