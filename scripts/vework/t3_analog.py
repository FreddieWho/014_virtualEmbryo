"""Local analog of the T3 board on released training data only:
WT reference = 10% subsample of E9.5 WT (as the scorer does for E8.75), truth = 10% of Mab21l2 KO E9.5.
Studies how de_score/de_direction/severity behave for floor-type and scaled-WT predictions."""
import sys; sys.path.insert(0, '/workspace/ve/veckit_latest'); sys.path.insert(0, '/workspace/ve/vework')
import numpy as np
from vecommon import load_stage, panel
from common.core_metrics import de_score, de_direction, severity_slope, pseudobulk, _signed_overlap, de_genes
from scipy.stats import spearmanr
g = panel('T3:gata4')
wt = load_stage('E9.5', g); ko = load_stage('E9.5_mab21l2_ko', g)
rng = np.random.default_rng(0)
ref = wt.X[rng.choice(wt.n_obs, wt.n_obs // 10, replace=False)]
tru = ko.X[rng.choice(ko.n_obs, ko.n_obs // 10, replace=False)]
pbr = pseudobulk(ref); dt = pseudobulk(tru) - pbr
up, dn, _ = de_genes(tru, ref)
print('n_up', len(up), 'n_dn', len(dn), 'c_up', _signed_overlap(pbr, up, dn)[0], 'c_dn', _signed_overlap(-pbr, up, dn)[0])
print('spearman(dt,pb_ref)', spearmanr(dt, pbr)[0])
def show(name, P):
    d = de_score(P, tru, ref); s = severity_slope(P, tru, ref)
    print(f"{name:28s} de {d['score']:+.3f} raw {d['raw']:.3f} ch {d['chance']:.3f} dir {de_direction(P, tru, ref):+.3f} sev {s[0]:+.3f} r2 {s[1]}")
show('floor (ref itself)', ref)
for k in range(3):
    show(f'indep WT draw 7449 #{k}', wt.X[rng.choice(wt.n_obs, 7449, replace=False)])
S = wt.X[rng.choice(wt.n_obs, 7449, replace=False)]
for f in [0.99, 0.97, 0.95, 0.9, 1.03, 1.05]:
    show(f'WT draw x{f}', S * f)
