# T3-S1B 状态连接与外部证据集成方案及收口

版本：2026-09-01
atom：`T3-S1B-STATE-JOIN-20260901-v3`
父版本：`T3-S1A-STATE-JOIN-20260901-v7`

## 目标与边界

本 atom 的目标是把已审计的 CollecTRI/OmniPath 全量小鼠快照接入 S1A 的状态证据链，闭合三类审计：

1. parent state 到 external context 的确定性映射、collision 保留和 unmatched fail-closed；
2. raw evidence 与派生 canonical sign 的冲突归零；
3. 从 family-native biological rows 重算的 leave-one-family-out 和四条 route-specific claim gate。

本 atom 不下载新外部数据，不重跑 CellOracle/scTenifold，不生成 H5AD，不运行 scorer，不提交服务器。

## 固定执行方案

- 锁定并逐文件校验 S1A v7 的 stable manifest、`state_gate.tsv`、`source_votes.tsv` 和本地 deployment manifest。
- 重新通过 `load_audited_snapshot` 校验 CollecTRI/OmniPath 的 source、dataset、mouse taxon、schema、license、字节数、行数和 SHA256。
- 外部 edge/path 无 state-specific activity 注释，统一标记为 `GLOBAL_CONTEXTUAL`、`SUPPORTING_KNOWLEDGE`、`activity_eligible=false`；不改变 activity gate、CellOracle applicability、signed biological claim 或 independent family 数。
- 冲突仅对同一 evidence channel 的 signed rows 判断；派生 `canonical_sign` 在冲突时为 0，保留 `raw_sign` 并标记 `CONFLICT`。unsigned rank、真实零、N/A/缺失不混为冲突。
- LOFO 先删除 family，再从剩余 family-native rows 重做 conflict/claim；external edge/path 与 unsigned rank 不作为 signed biological family。
- 四条 route 固定为：GATA4/GATA6 L1、GATA4/GATA6 L2、beta-catenin L1、beta-catenin L2；route gate 分别报告 biological claim、unsigned rank 和 contextual support。

## 执行结果

- 实现：`scripts/t3_s1b_state_join.py`
- 测试：`tests/test_t3_s1b_state_join.py`
- stable artifact：`artifacts/tool_integration/T3-S1B-STATE-JOIN-20260901-v3/`
- stable manifest：27 个文件；SHA256 `396b15d976e10700709c7628539dd2e9cac21b66612d9b72faa772921413744e`
- gate report：SHA256 `a4be63a1653353b238ce5cb29436cea834e438d9b2a3a3e85cb467d121d00e21`
- implementation script：SHA256 `cd480790fa6cbf7e6618ec28675983143466788847e79e73040d63df7dfe9d8c`，已写入 input lock、stable manifest、gate 和 completion；Git 状态为无 initial commit/branch unknown
- external raw：128 条；state-joined contextual：5808 条；总 source rows：137148 条
- external identity comparison：`PASS`，missing/unexpected rows 均为 0
- route：4/4 `HOLD`；selected signed records：0
- biological activity：`NOT_VALIDATED`
- candidate generation：`false`
- server submission：`false`
- `blocks_submission`：`false`
- 验证：53 项 S1A/S1B/interface tests PASS；py_compile PASS；JSON/YAML 解析 PASS；stable manifest 自校验 PASS；未产生 H5AD

## 科学结论边界

S1B 证明了外部 directed knowledge 可以被审计、复现并作为 contextual support 接入；它没有证明状态特异的 in-vivo activity，也没有把 external evidence 变成独立 biological replicate 或第三个 signed model family。Gata6/Ctnnb1 不会因 external context 恢复为当前 CellOracle base GRN 的适用 target。

当前结果为 `HOLD_AS_COMPONENT`，不是候选生成许可。下一步只有两条合规路径：取得独立且可审计的 biological activity/stability 证据，或另行授权并审计 target-compatible GRN atom；不能用 proxy、降采样或未等价替代解除 gate。

## 版本说明

`T3-S1B-STATE-JOIN-20260901-v1` 的首次运行在外部输入身份比较阶段正确 fail-closed，但适配器错误地将 unresolved OmniPath path 的 hop-based rank 写成 0，产生 `BLOCKED_INPUT_IDENTITY`。v1 receipt 保留在对应目录；v2 修正封装后使用同一 parent、同一快照和同一参数重跑，未覆盖 v1。独立 tester 随后发现 v2 未记录实现脚本 SHA；v3 只补齐该 provenance 绑定，使用同一 parent、同一快照和同一参数重跑，未覆盖 v2。
