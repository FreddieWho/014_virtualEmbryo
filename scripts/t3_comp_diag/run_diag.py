"""T3 composition diagnostic: does the observed Mab21l2 KO change population composition,
and does the change track where the target gene is expressed?

Label-free: frozen k-means on WT E9.5 (PCA space), KO cells assigned to nearest centroid.
Rule test: correlate per-cluster WT target-gene level vs log(KO/WT proportion).

Pure diagnostic. No candidate, no scorer against Gata4 truth, no external data.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import anndata as ad

ROOT = Path('/home/huyudi/014_virtualEmbryo')
RUN = ROOT / 'artifacts/t3_comp_diag/T3-COMP-DIAG-20261001-v1'
SEED = 20261001
K = 30          # frozen cluster count
NPCS = 30       # frozen PC count
TARGET = 'Mab21l2'


def load_panel_matrix(path):
    a = ad.read_h5ad(path)
    x = a.X
    x = np.asarray(x.toarray() if hasattr(x, 'toarray') else x, dtype=np.float32)
    return x, a


def main():
    t0 = time.time()
    RUN.mkdir(parents=True, exist_ok=False)
    genes = (ROOT / 'data/gene_panel/T3__gata4.genes.txt').read_text().splitlines()
    xwt, awt = load_panel_matrix(ROOT / 'data/E9.5.h5ad')
    xko, ako = load_panel_matrix(ROOT / 'data/E9.5_mab21l2_ko.h5ad')
    if list(awt.var_names) != genes:
        ix = awt.var_names.get_indexer(genes)
        xwt = xwt[:, ix]
    if list(ako.var_names) != genes:
        ixk = ako.var_names.get_indexer(genes)
        xko = xko[:, ixk]
    ti = genes.index(TARGET)
    # also E8.75 WT for Gata4 targeting (used only descriptively here)
    x875, a875 = load_panel_matrix(ROOT / 'data/E8.75.h5ad')
    if list(a875.var_names) != genes:
        x875 = x875[:, a875.var_names.get_indexer(genes)]
    g4i = genes.index('Gata4')

    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    pca = PCA(n_components=NPCS, random_state=SEED).fit(xwt)
    zwt = pca.transform(xwt)
    zko = pca.transform(xko)
    km = KMeans(n_clusters=K, random_state=SEED, n_init=10).fit(zwt)
    cwt = km.labels_
    # assign KO to nearest centroid
    d = ((zko[:, None, :] - km.cluster_centers_[None]) ** 2).sum(-1)
    cko = d.argmin(1)

    out = {'k': K, 'npcs': NPCS, 'seed': SEED, 'target': TARGET}
    # cluster stats
    rows = []
    nwt, nko = len(cwt), len(cko)
    for c in range(K):
        m_w = cwt == c
        m_k = cko == c
        pw = m_w.mean()
        pk = m_k.mean()
        tgt_wt = float(xwt[m_w, ti].mean()) if m_w.any() else 0.0
        rows.append({
            'cluster': c, 'wt_frac': float(pw), 'ko_frac': float(pk),
            'log2_ko_over_wt': float(np.log2((pk * nko / max(pk * nko, 1e-9)) / max(pw, 1e-9)) if pw > 0 else np.nan),
            'log2_ratio': float(np.log2(max(pk, 1e-9) / max(pw, 1e-9))),
            'target_wt_mean': tgt_wt,
            'target_wt_detect': float((xwt[m_w, ti] > 0).mean()) if m_w.any() else 0.0,
        })
    # rule correlation: does KO preferentially lose target-high clusters?
    tw = np.array([r['target_wt_mean'] for r in rows])
    lr = np.array([r['log2_ratio'] for r in rows])
    import scipy.stats as st
    spear = float(st.spearmanr(tw, lr).statistic)
    pear = float(np.corrcoef(tw, lr)[0, 1])
    out['rule_test'] = {
        'spearman_targetlevel_vs_logratio': spear,
        'pearson_targetlevel_vs_logratio': pear,
        'interpretation': 'negative => KO loses target-high populations (composition rule supported)',
    }
    # pseudobulk delta: does composition-only reproduction match observed delta direction?
    mu_wt = xwt.mean(0)
    mu_ko = xko.mean(0)
    obs_delta = mu_ko - mu_wt
    # composition-only predicted delta: reweight WT clusters to KO proportions
    comp_mu = np.zeros_like(mu_wt)
    for c in range(K):
        m_w = cwt == c
        if m_w.any():
            comp_mu += xwt[m_w].mean(0) * (cko == c).mean()
    comp_delta = comp_mu - mu_wt
    # direction: partial correlation of ranks controlling for ref expression (mirror de_direction)
    def rankdata(v):
        return st.rankdata(v)
    rp, rt, rr = rankdata(comp_delta), rankdata(obs_delta), rankdata(mu_wt)
    C = np.corrcoef([rp, rt, rr])
    denom = np.sqrt(max((1 - C[0, 2] ** 2) * (1 - C[1, 2] ** 2), 1e-12))
    dcs = float((C[0, 1] - C[0, 2] * C[1, 2]) / denom)
    # within-DE-set slope (severity proxy): truth DE = |obs lfc| >= 0.25 on pseudobulk
    de_mask = np.abs(obs_delta) >= 0.25
    if de_mask.sum() > 5 and np.std(comp_delta[de_mask]) > 1e-2 * np.std(obs_delta[de_mask]):
        beta = float((comp_delta[de_mask] @ obs_delta[de_mask]) / (obs_delta[de_mask] @ obs_delta[de_mask]))
        r2 = float(np.corrcoef(comp_delta[de_mask], obs_delta[de_mask])[0, 1] ** 2)
    else:
        beta, r2 = 0.0, 0.0
    out['composition_only_vs_observed'] = {
        'n_de_truth': int(de_mask.sum()),
        'direction_partial_corr': dcs,
        'slope_beta_on_de_set': beta,
        'r2_on_de_set': r2,
        'delta_std_ratio': float(np.std(comp_delta) / max(np.std(obs_delta), 1e-12)),
    }
    # descriptive: which WT E9.5 clusters are Mab21l2-high; Gata4 across E8.75 cell types
    ct = awt.obs['celltype'].astype(str).to_numpy()
    type_tbl = []
    for t in sorted(set(ct)):
        m = ct == t
        type_tbl.append({'type': t, 'n': int(m.sum()),
                         'mab21l2_mean': float(xwt[m, ti].mean()),
                         'mab21l2_detect': float((xwt[m, ti] > 0).mean())})
    out['e95_type_mab21l2'] = sorted(type_tbl, key=lambda r: -r['mab21l2_mean'])[:10]
    ct875 = a875.obs['celltype'].astype(str).to_numpy()
    g4_tbl = []
    for t in sorted(set(ct875)):
        m = ct875 == t
        g4_tbl.append({'type': t, 'n': int(m.sum()),
                       'gata4_mean': float(x875[m, g4i].mean()),
                       'gata4_detect': float((x875[m, g4i] > 0).mean())})
    out['e875_type_gata4_top'] = sorted(g4_tbl, key=lambda r: -r['gata4_mean'])[:10]
    out['e875_gata4_overall'] = {'mean': float(x875[:, g4i].mean()), 'detect': float((x875[:, g4i] > 0).mean())}
    out['wall_s'] = time.time() - t0
    (RUN / 'RESULT.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'rule_test': out['rule_test'], 'composition_only_vs_observed': out['composition_only_vs_observed'],
                      'top_mab21l2_types': [(r['type'], round(r['mab21l2_mean'], 3), round(r['mab21l2_detect'], 3)) for r in out['e95_type_mab21l2'][:5]],
                      'top_gata4_types_e875': [(r['type'], round(r['gata4_mean'], 3), round(r['gata4_detect'], 3)) for r in out['e875_type_gata4_top'][:6]],
                      'gata4_overall_e875': out['e875_gata4_overall']}, indent=2))


if __name__ == '__main__':
    main()
