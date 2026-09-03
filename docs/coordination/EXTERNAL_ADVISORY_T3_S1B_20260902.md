# 外部建议：batch3 T3-S1B 阻塞与 GitHub 仓库跟进

日期：2026-09-02  
对象：执行 agent（T3 / batch3 协调）  
背景：当前 `T3-S1B-GENERATE` gate 未通过，全局 `HOLD_AS_COMPONENT`；GitHub 仓库 `https://github.com/FreddieWho/014_virtualEmbryo` 已完成首次推送（main 分支）。

---

## 1. 一句话判断

- 方案没有偏，资源全压在 T3 gate 链是按计划走。
- S1B 卡住不是 bug，是“方法接通、生物学证据没通”。
- 下一条合法路是：**用 S1C-A/B 已打通的 target-compatible GRN，去补独立、可审计的 biological activity**，不要再去抓 E8.75 附近 Gata4/Ctnnb1 扰动数据。

---

## 2. 当前进度核查

- 执行顺序与 `docs/batch3/02_EXECUTION_ORDER_AND_GATES.md` 完全一致：P0 → T3-S1-PRIOR → S1A(v7) → S1B(v3) → S1C-A/B → S1D(v3)。
- 约束遵守：`single_task / 薄adapter / 确定性seed / artifacts 隔离 / 不自动提交服务器 / 不网格搜索` 均未违规。
- T1/T2 暂无进展是预期内（batch3 把资源让给 T3），不算偏移。
- 服务器分数仍只认 `reports/SERVER_SCORE_REGISTRY.md`；当前 T3 best `wt_identity 45.3` 未变。

---

## 3. T3-S1B-GENERATE 为什么没过 gate

- S1B 的任务：把已审计的 CollecTRI/OmniPath 全量快照接入 S1A 状态链，看能不能成为第3票 signed biological family。
- 结果：接入成功（5,808 条 contextual rows，137,148 总 rows，identity 校验 PASS），但被判为 `GLOBAL_CONTEXTUAL / SUPPORTING_KNOWLEDGE`。
- 关键缺口：没有 **E8.75 state-matched in-vivo activity**；`independent signed family = 0`，LOFO 无法解锁；`4/4 route HOLD`。
- 结论：方法/审计 PASS，生物学验证 `NOT_VALIDATED / NOT_IDENTIFIABLE`。所以 `candidate_generation=false, server_submission=false, blocks_submission=false`。

---

## 4. 外部数据合规边界（重要）

按 `docs/batch2/compliance/DATA_FIREWALL_SPEC.md` 和 `protected_windows.yaml`：

- **不可用**：E8.5–E9.0 附近窗口、Gata4/Gata6/Ctnnb1 目标扰动、同组织的表达数据 —— 会踩 target leakage。
- **可用**：sanitized WT 外部表达、远离 E8.5–E9.0 窗口的非目标扰动、官方已审计的 CollecTRI/OmniPath（仅作 contextual support）。
- S1D v3 的 GSE5298/GSE9652/GSE78125 属 `off-target context / 组织限定`，只能做 background，不能当 E8.75 state-matched signed family。

---

## 5. 下一步执行建议（按优先级）

1. **不要再重跑 S1B 或去找“更近的 E8.75 KO 数据”** —— 合规风险高，且找不到等价证据。
2. **启动 `T3-S1C` 后续 atom**（已有基础）：
   - S1C-A/v1 已用 CellOracle 原生 `TFdict` 构建 Gata6/Ctnnb1 target-compatible adapter。
   - S1C-B/v3 已在真实 CellOracle 0.22.0 完成 2/2 synthetic fit/simulate smoke。
   - 缺口：生物学活性验证。建议用 **允许的 WT/远窗口数据** 对该新 GRN 做隔离验证，生成可审计的 `biological activity` 证据。
3. **保持 `blocks_submission: false`**：
   - 科学阻塞 ≠ 提交阻塞。T3 当前 best 45.3 可继续保分；S1 系列作为研究分支继续，不干扰 leaderboard。
4. **任何新 atom 前** 先在 `docs/coordination/T3_TRACKING.md` 追加变更记录，并锁定输入 SHA256；失败 receipt 保留，不覆盖。

---

## 6. GitHub 仓库状态与使用

- 仓库：`https://github.com/FreddieWho/014_virtualEmbryo`，分支 `main`。
- 已推内容：251 个文件（代码/文档/配置），大文件按 `.gitignore` 排除：`data/`, `artifacts/`, `outputs/`, `deliveries/`, `infra/external_data/quarantine|sanitized|manifests`, `*.h5ad/*.h5/*.zip`。
- 鉴权：SSH `git@github.com:FreddieWho/014_virtualEmbryo.git`（`id_ed25519_github` 已可用）。
- 后续操作：正常 `git add/commit/push` 即可；新增大文件不会误推。若必须传大文件，请另开分支启用 `git lfs track "*.h5ad"`，不要污染 main。

---

## 7. 需要执行 agent 做的事

- [ ] 阅读并确认本建议与 `docs/batch3/02_EXECUTION_ORDER_AND_GATES.md`、`docs/coordination/T3_TRACKING.md` 一致。
- [ ] 决定是否授权启动 `T3-S1C` 后续 biological activity 验证 atom；如授权，请给出输入数据范围与 audit 要求。
- [ ] 在 `docs/coordination/T3_TRACKING.md` 追加一条变更记录，说明是否采纳本建议及下一步计划。
- [ ] 若需向 GitHub 继续提交，请先拉取 `main` 并确认本地与远端一致。

---

备注：本文件为外部建议，不改变任何现有 gate 结果；所有科学结论仍以 `reports/SERVER_SCORE_REGISTRY.md` 和 `submissions/INDEX.tsv` 为准。
