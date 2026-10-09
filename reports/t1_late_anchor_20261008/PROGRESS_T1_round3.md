# T1 round 3 (2026-10-08 evening): (A) new big direction, (B) optimise on LA3
- LA3 portal 57.99 (de 51.6 dir 64.0 mmd 61.7 vario 52.8). Quota: 2 left today (deadline 08:00 UTC+8 10-09).
- 19:55 Released data: no ATAC / spliced-unspliced layers -> velocity route impossible with released files.
- Plan A (new mechanism): OT-coupled two-part generative displacement (vework/t1ext/otfield.py): within-group entropic OT ext E8.5->E14.5 (GSE230531, same files as LA), cell-specific detection(logit)+level displacement, transferred to carrier cells via kNN in z-scored ext-E8.5 PCA; stochastic gene on/off + level shift (no zp group-mean shift). Carrier v0051 rebuild, tau = 0.187 x 1.46 (same overall strength as LA3 -> clean mechanism comparison).
- Plan B: LA3 + per-group topping amp_g = clip(2 - p_g, 0, 2) (build_t1_v51_anchor.py --amp pergroup).
- Sanity backtest: vework/t1ext/bt_ot.py (E8.5->E9.5; copy / LA_x1 / OT_x1) -> backtests/t1_ot_e85_e95.json; fields cached work/t1r3/fields_14.5.pkl
- 20:30 backtest (3 seeds, E8.5->E9.5): copy de -0.017/dir 0.205/mmd 0.0259/vario 0.00107; LA_x1 0.187/0.304/0.0233/0.00097; OT_x1 (uniform on/off) 0.111/0.284/0.0289/0.00127 -> FAILS sanity (worse than copy on mmd/vario).
- seed-0 variants: level-only 0.138/0.269/0.0229/0.00105; onoff-only 0.121/0.274/0.0304/0.00130; smooth on/off 0.155/0.308/0.0250/0.00125. Cause: net detection loss (ext E14.5 has 20-30% fewer genes/cell than ext E8.5 = protocol/tissue; comp E8.5->E9.5 flat 3836->3878). Fix under test: complexity-neutral switching (per-cell logit offset).
- 20:52 seed-0: OT_neutral 0.138/0.298/0.0244/0.00111; OT_smooth_neutral 0.155/0.297/0.02275/0.00112 -> chosen A config (smooth=True, neutral=True). 3-seed confirm running.
- 20:33 3-seed confirm OT_smooth_neutral: de 0.111 / dir 0.276 / mmd 0.0241 / vario 0.00116 (seeds: 0.155,0.068,0.111). > copy on de/dir/mmd, vario +8% vs copy; below LA_x1 on all four. Building A anyway as the new-mechanism test (no further tuning on backtest).
- 20:36 A built: /workspace/ve/submit/T1_val__A_ot_gen_v51.h5ad sha 35fae3a797acdf44b4c6d141e1a0db65b44744ea218f96218c7909e34eda5dc1 format PASS 5118x32285. nnz 0.13637 vs carrier 0.13645 (on~off per group, complexity-neutral); pb L2 5.78, max |pb| 0.31; median library 10456 (carrier 10000). tau=0.187*1.46, seed 20261009.
- 20:42 B built: /workspace/ve/submit/T1_val__B_v51_anchor_pergroup.h5ad sha 04d73c5d2c9daab7c9fc9db3ba9543c295639f9e4415ca312511c0147adf7fe6 format PASS. amps: CM_A 1.19, CM_V 1.22, EPI 1.20, SHF 0.75, ENDO 2.00, MESO 1.96, NCC 1.97. min 0, finite, median library 10075.
- MANIFEST rows appended for both, GSE230531 disclosure identical to LA3 (no new sources). Nothing uploaded.

## Portal scores (confirmed 2026-10-09 10:40 CST)

| model | score | de | dir | mmd | vario | vs LA3 |
|---|---:|---:|---:|---:|---:|---|
| ot-gen-A | **58.89** | 49.7 | 65.9 | 65.2 | 52.3 | +0.90 |
| pergroup-B | 58.22 | 51.4 | 64.2 | 62.4 | 53.0 | +0.23 |
| LA3 (ref) | 57.99 | 51.6 | 64.0 | 61.7 | 52.8 | — |

Team T1 best now 58.9 (was 58.0). Quota after reset: T1/T2/T3 0/8. Detail A: .../39e6870fb90549e09067e7c3cff92333 ; B: .../455eb227ed4a407382c2f18a4d2ab920 .
