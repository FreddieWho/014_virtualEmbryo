# <ATOM_ID> RESULT

## Status

- status: READY_FOR_MANUAL_UPLOAD | SCORE_PENDING | COMPLETE | BLOCKED
- overall decision: PER_BOARD_OR_LANE
- task: <T1 | T2 | T3>
- final lanes: <L1> + <L2>
- boards: <board list>
- final artifacts: <2 or 6>
- server scores: 0/<final artifacts>
- submission mode: manual_user_upload
- git commit:

## Final candidates

| Lane | Board | Candidate ID | Base | Output | SHA256 | Contract | Local primary metrics | Server status | Decision |
|---|---|---|---|---|---|---|---:|---|---|
| L1 | | | | | | | | score_pending | |
| L2 | | | | | | | | score_pending | |

每个 lane 必须填满当前原子规定的 board；不得把两个 lane 合并成一个候选或用一个 aggregate score 代替逐候选记录。

## Atom

- optimized atom:
- primary metric: <按 prompt 填写 raw scorer key>
- protected metrics: <按 prompt 填写>
- hypothesis: <不超过两句>

## Change

用不超过 5 句话分别说明 L1、L2 和临时探索的实际处理。不要写研究综述。

## Server score handoff

| Candidate ID | Upload status | Submission ID | Score returned |
|---|---|---|---|

分数未回填前必须保持 `score_pending`，不得宣称模型进步。服务器 ID 和分数只登记到 `reports/SERVER_SCORE_REGISTRY.md`；不额外要求截图、链接或 JSON 原始证据。

## Protected checks

| Candidate ID | X checksum | obs/var order | spatial shape | 15-NN check | SDD/ODS/NFS delta | Pass/Fail |
|---|---|---|---|---|---:|---|

## Decision

按 board/lane 独立填写 prompt 规定的比较结果；不得手工构造 composite score。

## Only next action

若仍有未回填分数，只写“等待用户人工上传并回填剩余 submission ID 和分数”；不得展开新路线。
