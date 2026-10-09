# T3 gata4: why the "exact floor" copy scored 46.8 instead of 50

Board weights (repo-derived): de 0.30, dir 0.25, sev 0.25, mmd 0.12, vario 0.08.
v0008 = 0.3*38.8 + 0.25*49.7 + 0.25*50 + 0.12*51.3 + 0.08*50.9 = 46.79, so the entire gap comes from de_score.

The official floor (wt_identity) is the scorer's own hidden 10% WT subsample of E8.75 (2483 cells), used both as
the prediction and as wt_X. That makes dp = pb(pred) - pb(wt) exactly 0, so the relative guard
`std(dp) < 1e-2*std(dt)` fires and returns de=0 / dir=0 / sev=log(1e-3), i.e. skill 50 by construction.
Reproduced locally (pred = wt subsample): de 0.000, dir 0.000, sev -6.9078.

Any WT sample we draw ourselves differs from that hidden subsample by sampling noise, which is far above the 1%
guard. de_score is then computed on a noise ranking and compared with the expression-magnitude null
max(overlap(+pb_ref), overlap(-pb_ref)), so it lands below 0. A skill of 38.8 corresponds to de of about -0.50.
Cell count and gene order are not the cause.

The exact floor can't be replicated: the subsample indices live in the organisers' private data.py, which isn't in
veckit or the repo. I did not try to recover them from the portal.

Mab21l2 E9.5 analog (released data only, wt_ref = 10% of E9.5 WT, truth = 10% of the KO):
  uniform draw de -0.049 | stratified draw -0.056 | stratified + pb-match -0.034 | + KO-gene zero -0.030 (sev -6.9 -> -5.1)
On the analog that would be about 52. On the real board, the same class scored 46.8 to 46.95 (v0008/v0009), so the
analog does not predict this board. No legitimate candidate here is expected to reach 50.
A scaled-WT (x0.97 / x1.03) file would only bring de up to 0 if its sign matched the truth's dominant direction.
The team's own spec treats that as an adversarial control (C2 scale attack), so I didn't build it.
