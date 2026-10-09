# Backtest faithfulness (2026-10-08)

Lesson from today: the local held-out proxy **did not transfer** to the server.

| board | local backtest prediction | portal (10-08) | transferred? |
|---|---|---|---|
| T2 embryo | E2 (zp+aniso) 63.64 >> E1 50.96 (+12.7, LOO E7.25 from E6.75/E8.0) | E1 59.80 > E2 59.47 | **No** (sign wrong) |
| T2 heart interp | H2 53.38 > H1 53.10 (+0.28) | H1 65.03 > H2 64.87 | **No** (sign wrong, both within noise) |
| T2 heart interp, submetric | zp raises variogram | H2 vario 58.6 vs H1 46.0 | Yes, direction only |
| T2 heart interp, submetric | zp: mmd about flat locally | H2 mmd 52.8 vs H1 57.0 | **No** |
| T2 extrap | X1 52.26 > mean-delta baseline 49.51 | X1 50.44 (floor 50, best 51.12) | Level roughly ok, no ranking info |
| T3 gata4 | Mab21l2 fold: uniform 52.05 > strat_pbmatch 50.66 | v0008 uniform-class 47.93 > A/B (pbmatch) 45.7–45.9 | Yes, direction (1 of 1) |
| T1 | copy_last E8.5→E9.5 65.8 locally | copy_last on val = 47.0 | **No** (level off by about 19 pts) |

Why the proxies are unfaithful:
1. **Wrong problem geometry.** T2 LOO folds hold out a *released* stage (e.g. E7.25 bracketed by E6.75/E8.0, a 1.25-day gap) instead of the real target. The gap, cell-state turnover and panel all differ from the val/test target.
2. **Ceiling/floor construction.** Locally, both truth halves and the floor reference come from the same released stage, so they share sampling noise. The local floor (copy_last) is then too good (T1: 54–66 locally vs 47 on the portal). Local 10%-subsample ceilings are much weaker than the published anchors (T1 variogram 0.0021 vs 0.000158). `ceil_from=<board>` swaps in published anchors, but the floor problem remains.
3. **Submetric noise.** occ/d2/scale/nbhd change by 5–10 points across scorer seeds on 5k-cell targets. Differences under about 1 point (H1 vs H2) are noise, both locally and on the portal.

How to use them now: as **end-to-end smoke tests** (format, panel order, no NaN, no catastrophic collapse) and as a **coarse sanity check** (a recipe that loses >5 pts locally is suspect). **Do not use them to rank recipes** that differ in geometry or zero-handling.

What becomes faithful after 10-20 (truth for E7.5 embryo, E8.5 and E10.5 heart/T1, Gata4 KO released):
- `bt_t2.py --fold embryo_truth|heart_interp_truth|extrap_truth` and `bt_t1.py --target E10.5` score the **actual validation problem** against real truth. **Calibration gate:** re-score files with known portal scores (v0014 62.89, E1 59.80, E2 59.47, H1 65.03, H2 64.87, X1 50.44, T1 copy_last 47.0). Treat the harness as faithful only if (a) it ranks them in portal order and (b) the level stays within about 1.5 pts. Only then use it to choose between test candidates.
- Remaining differences: our split/subsample seeds are not the server's, and the test target (E7.75, E12.5, β-cat) is a different extrapolation distance. For T2 heart E12.5 (2-day extrapolation from E10.5), no backtest spans a comparable gap: E8.5→E10.5 using E9.5 delta is the closest analogue.
- T3: the leave-one-KO-out scaffold (`bt_t3.py`) gets a second fold (Gata4) on 10-20. Two folds are still a tiny sample, so use it only to veto a β-cat recipe that falls below the uniform draw on both folds.

T1 note (10-08): with only E8.5 and E9.5 released, the E8.5→E9.5 backtest can score only copy_last. Shift recipes need two training stages to estimate a delta. Results: copy_last 65.80 with local ceilings, 54.16 with published ceilings, vs 47.0 on the portal. So until 10-20, T1 recipe choice must come from portal calibration uploads (S, S2, M1 vs copy_last 47.0). After 10-20, `bt_t1.py --train E8.5_RNA:8.5,E9.5_RNA:9.5 --target E10.5...` becomes possible.
