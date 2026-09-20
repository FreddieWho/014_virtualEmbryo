# ARCHIVED — dead root scripts (AST-verified, 2026-09-20)

以下 `scripts/*.py` 经 AST 逆依赖分析确认**零 incoming import**（全仓库 `.py` 范围，
含 `docs/batch*/scripts`；分析脚本见本次工作记录），属 batch1–3 时代一次性 worker。
审计时跳过；如需复活从 git 历史取，不要 import 它们。

**为什么只立牌不搬家**：其中 18 个用 `Path(__file__).parents[1]` 定位仓库根，
搬进子目录会静默指错根（校验 HOLE-1 同类问题），修 18 个死文件得不偿失。
`generate_audit.py`、`package_manual_upload.py`、`prepare_t2_submission.py`、
`batch3_contract_preflight.py` 虽零 incoming 但是现行入口/包装工具，**不在此列**。

死脚本清单（24）：
b2_p0_audit, b2_t3_a1_signed_prior, finalize_b2_t3_a1, finalize_batch1_a1,
hx_dynamics_killtest, hx_mioflow_worker, repair_t3_s1a_route_artifact,
t1_mass_residual, t2_controls, t2_expression_model, t2_g1_scale,
t2_geometry_attribution, t2_geometry_model, t3_prior_local_deployment,
t3_s1a_state_join, t3_s1b_knowledge_preflight, t3_s1b_state_join,
t3_s1c_regulator_prior, t3_s1c_source_adapter_smoke,
t3_s1d_exact_activity_evidence, t3_s1d_independent_activity_evidence,
t3_signed_response, t3_stability_preflight, write_t3_s1a_runtime_blocked

活脚本（有 incoming，勿动）：t1_temporal_model (18), t2_baseline (5),
t2_pseudo_holdout (4), t2_s3_shape_field (3), t2_j1_pairing (2), t2_j1_proxy (2),
prepare_t1_t3_submission, t1_pre_harmonize, t1_s2_moscot_decoder,
t2_j1_fgw_assignment, t3_s1_prior, t3_shift_transfer, 以及 scripts/g0/ 全体。
