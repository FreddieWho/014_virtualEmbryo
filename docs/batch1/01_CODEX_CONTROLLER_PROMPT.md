# Codex 总控施工提示词：第一批原子优化

你正在一个已经完成第一次有效提交、且基础工作台已经搭建完成的 Virtual Embryo Challenge 项目中工作。不要重做数据下载、环境搭建、通用 validator、官方 baseline 复现或大规模测试框架。

## 任务

读取：

1. `00_START_HERE.md`
2. `config/active_atom.yaml`
3. `config/batch1_manifest.yaml`
4. `config/scoring_targets.yaml`
5. 对应的 `prompts/<prompt_file>`
6. `templates/ATOM_RESULT_TEMPLATE.md`

然后只施工 `active_atom.yaml` 指定的一个原子。每个原子最终结果集都固定为两条 lane（1+1）；完成结果集并建立人工评分 handoff 后立即停止，不自动进入下一原子。

B1-A1 的最终 lane 固定为：

- `L1_FORMAL_LOG_RMS`：按 prompt 规定的分段 `log(RMS)` 插值/末段外推；
- `L2_ALL_STAGE_LOG_RMS_OLS`：使用该组织全部训练阶段的 source-only `log(RMS)` 等权 OLS 趋势。

每条 lane 必须生成 `T2_embryo_val_interp`、`T2_heart_val_interp`、`T2_heart_val_extrap` 三个候选。最多允许 4 次全局临时 source-only 尝试；一次尝试必须覆盖三个 board，临时结果不提交、不评分、不计入最终候选。

B1-A2 的最终 lane 固定为 prompt 中的 `L1_CELL_LEVEL_SPEARMAN` 和
`L2_STATE_PSEUDOBULK_SPEARMAN`，每条 lane 生成一个 `T3_gata4` 候选。两条通过 contract/invariant 的候选都必须交给用户人工上传并分别获得服务器分数。

B1-A4 的最终 lane 固定为 prompt 中的 `L1_LATENT_KNN10` 和
`L2_STATE_HASH10`，每条 lane 生成三个 T2 board 候选。六条通过
contract/invariant 的候选都必须交给用户人工上传并分别获得服务器分数。

## 先做的最小仓库定位

最多用一次仓库扫描定位以下现有资产：

- 当前 git root 与当前 commit；
- 第一次有效提交及其生成配置；
- 官方 index / gene order / board 定义；
- 当前 validator 与 scorer 命令；
- 当前提交输出目录；
- 已有 experiment registry 或结果记录。

优先读取已有 manifest、README、registry、run config 和提交脚本；不要通过全仓库逐文件阅读重新理解项目。

若存在多个第一次提交候选，选择“已经成功通过官方格式检查且记录最完整”的文件作为 base；不要为了选择 base 重新跑所有旧实验。

## 不可违反的施工原则

1. **一个原子，一条最小代码路径；B1-A1/B1-A2 都必须冻结两个最终 lane，每个 board 的终点是 1+1 个候选。**
2. 只修改完成当前原子所需的文件；不得顺手重构其他任务。
3. 不新增训练框架，不替换现有数据层，不改官方 scorer。
4. 不做超参数 sweep、架构比较、多 seed 重复或无关 ablation；仅允许当前原子配置的最多 4 次 source-only 临时路线尝试，不能增加第三条最终 lane。
5. 默认只用现有依赖；除非硬阻塞，不新增包。
6. 所有参数必须来自解析关系、训练数据统计量或现有配置；不得隐藏手工试分。
7. 当前原子允许临时尝试，但最终只运行并冻结两条 lane；每条 lane 的每个 board 各进行一次最终评分。评分后不得根据服务器结果调参或追加候选。
8. 使用 `allow_scored_submission=true` 配合 `submission_mode=manual_user_upload`：所有最终文件必须通过官方 contract 并交给用户上传；代理始终保持 `auto_submit=false`，不得访问线上提交入口。服务器 ID 和分数由用户回填；不额外要求截图、链接或 JSON 原始证据。
9. 不使用隐藏 target、排行榜反馈或未登记外部数据来拟合参数。
10. 若某条 lane 的科学假设失败，只要 contract 和不变量通过，仍须把它作为第二条最终 lane 交付并评分；只有硬性 contract/invariant 失败才可标记该 board 为 `REJECT`，并明确当前原子要求的全部分数终点未达成。

## 统一结果要求

最终必须生成（按当前原子的 lane/board 数量展开）：

```text
artifacts/atomic_batch1/<ATOM_ID>/
├── final/<lane>/<board>/prediction.h5ad
├── final/<lane>/<board>/MANIFEST.json
├── exploration/attempt-<nnn>/<board>/（如有）
├── metrics/<lane>/<board>/local_or_official.json（如适用）
├── metrics/<lane>/<board>/protected_checks.json
├── config_resolved.yaml
├── FINAL_SET_MANIFEST.json
├── RESULT.md
└── run.log
```

`RESULT.md` 必须短，严格使用模板，明确：

- 优化了哪个原子；
- 基于哪个提交；
- 改了什么；
- 主要指标是否按预期改变；
- 受保护指标是否保持；
- 文件路径和 SHA256；
- `SUBMIT / HOLD / REJECT`；
- 下一步只允许一句话，不展开新工作。

## 结束条件

B1-A1、B1-A2 或 B1-A4 以下条件同时满足后停止：

- 当前原子的两条 lane × board 数量个输出文件通过当前官方 contract；
- 为最终输出使用同一 scorer 版本和固定 public pseudo-holdout 完成本地验证；
- 生成对应数量的候选 manifest 和一个 `FINAL_SET_MANIFEST.json`；
- 所有文件交给用户人工上传；在用户回填全部 submission ID 和分数前，状态必须保持 `score_pending`；
- commit 当前原子相关改动（若仓库已有可用 git 基线），commit message 以 `<ATOM_ID>:` 开头；
- 不启动下一原子。
