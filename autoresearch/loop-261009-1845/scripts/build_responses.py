"""Precompute T3 response-structure variants in one panel-loading pass.

The emitter cannot move de_skill (2026-10-09: +0.00000 across every emitter
parameter variant) because it only redistributes already-activated cells. de
depends on the response structure itself, so this script recomputes the
84-embryo response under alternative structural assumptions and writes each as
a drop-in replacement for embryo_responses.npz.

Mirrors crossko_hurdle_v2.CrossKOHurdle.summarize_response exactly, exposing
three structural knobs. Same approved panels, same WT-only controls, no target
outcome is read.

delta layout is (S, G, 22): 21 positive-quantile shifts plus a trailing
detection-fraction delta, matching the frozen layout.

Variants
--------
frozen      lam = nk/(nk+50), min_cells=10, unsupported states abstain
lam0        lam = 1.0  -> pure state-local, no global blend
lam10       lam = nk/(nk+10)
lam200      lam = nk/(nk+200)
mincells3   min_cells=3 -> fewer abstentions
mincells30  min_cells=30 -> more abstentions
broadcast   unsupported states receive the global response instead of abstaining
unmasked    drop the global_valid mask, so globally-sparse genes can respond
"""
import os

for k in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[k] = "4"
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

NORM = Path("/home/huyudi/vework/prepared/source_panel/normalized")
ANN = Path("/home/huyudi/vework/annotations")
OUT = Path("/home/huyudi/vework/responses")
GENES = ["Dnmt3a", "Kmt2a", "Kdm2b", "Dnmt1", "Dnmt3b", "Ehmt2", "Kmt2b"]

VARIANTS = {
    "frozen": dict(lam=50.0, min_cells=10, broadcast=False, mask=True),
    "lam0": dict(lam=None, min_cells=10, broadcast=False, mask=True),
    "lam10": dict(lam=10.0, min_cells=10, broadcast=False, mask=True),
    "lam200": dict(lam=200.0, min_cells=10, broadcast=False, mask=True),
    "mincells3": dict(lam=50.0, min_cells=3, broadcast=False, mask=True),
    "mincells30": dict(lam=50.0, min_cells=30, broadcast=False, mask=True),
    "broadcast": dict(lam=50.0, min_cells=10, broadcast=True, mask=True),
    "unmasked": dict(lam=50.0, min_cells=10, broadcast=False, mask=False),
    "lam5": dict(lam=5.0, min_cells=10, broadcast=False, mask=True),
    "lam15": dict(lam=15.0, min_cells=10, broadcast=False, mask=True),
    "lam20": dict(lam=20.0, min_cells=10, broadcast=False, mask=True),
    "lam25": dict(lam=25.0, min_cells=10, broadcast=False, mask=True),
    "lam30": dict(lam=30.0, min_cells=10, broadcast=False, mask=True),
    "lam10_unmasked": dict(lam=10.0, min_cells=10, broadcast=False, mask=False),
    "lam10_mincells3": dict(lam=10.0, min_cells=3, broadcast=False, mask=True),
    "lam15_unmasked": dict(lam=15.0, min_cells=10, broadcast=False, mask=False),
    "lam20_unmasked": dict(lam=20.0, min_cells=10, broadcast=False, mask=False),
    "lam8_unmasked": dict(lam=8.0, min_cells=10, broadcast=False, mask=False),
    "lam12_unmasked": dict(lam=12.0, min_cells=10, broadcast=False, mask=False),
    "lam18_unmasked": dict(lam=18.0, min_cells=10, broadcast=False, mask=False),
    "lam25_unmasked": dict(lam=25.0, min_cells=10, broadcast=False, mask=False),
    "lam15_unmasked_mc3": dict(lam=15.0, min_cells=3, broadcast=False, mask=False),
    "lam15_unmasked_mc20": dict(lam=15.0, min_cells=20, broadcast=False, mask=False),
    "lam18_unmasked_mc3": dict(lam=18.0, min_cells=3, broadcast=False, mask=False),
}


def assign(model, x):
    return model.km.predict(model.pca.transform(x[:, model.features]))


def summarize(model, control, ko, cl, kl, cfg):
    G, Q = model.G, len(model.positive_q)
    S = model.S
    nc = np.bincount(cl, minlength=S)
    nk = np.bincount(kl, minlength=S)
    zero = np.zeros((G, Q))
    cq, cv = model.positive_quantiles(control, zero)
    kq, kv = model.positive_quantiles(ko, cq)
    global_delta = kq - cq
    global_detect = (ko > 0).mean(0) - (control > 0).mean(0)
    global_valid = cv & kv

    result = []
    supports = []
    for s in range(S):
        ok = nc[s] >= cfg["min_cells"] and nk[s] >= cfg["min_cells"]
        supports.append(ok)
        if not ok and not cfg["broadcast"]:
            result.append(np.zeros((G, Q + 1)))
            continue
        if ok:
            a = control[cl == s]
            b = ko[kl == s]
            aq, _ = model.positive_quantiles(a, cq)
            bq, _ = model.positive_quantiles(b, kq)
        else:
            a = control[cl == s] if nc[s] else control
            b = ko[kl == s] if nk[s] else ko
            aq, _ = model.positive_quantiles(a, cq)
            bq, _ = model.positive_quantiles(b, kq)
        lam = 1.0 if cfg["lam"] is None else nk[s] / (nk[s] + cfg["lam"])
        d = lam * (bq - aq) + (1 - lam) * global_delta
        rate = lam * ((b > 0).mean(0) - (a > 0).mean(0)) + (1 - lam) * global_detect
        if cfg["mask"]:
            d[~global_valid] = 0
            rate[~global_valid] = 0
        result.append(np.c_[d, rate])

    comp = np.log((nk + 0.5) / (nk.sum() + 0.5 * S)) - np.log(
        (nc + 0.5) / (nc.sum() + 0.5 * S)
    )
    comp = comp - comp.mean()
    return np.array(result), comp, np.array(supports)


def main():
    sys.path.insert(0, "/home/huyudi/vework/eval")
    from crossko_hurdle_v2 import CrossKOHurdle

    OUT.mkdir(parents=True, exist_ok=True)
    data = {}
    for gene in ["WT"] + GENES:
        label = "G9a" if gene == "Ehmt2" else gene
        a = ad.read_h5ad(NORM / f"{gene}_whitelisted_panel10000.h5ad")
        obs = pd.read_csv(ANN / f"{label}_E8.5_cell_annotations.tsv", sep="\t")
        keep = obs.barcode.isin(a.obs_names)
        idx = a.obs_names.get_indexer(obs.loc[keep, "barcode"])
        sub = a[idx].copy()
        obs = obs.loc[keep].reset_index(drop=True)
        sub.obs = obs.set_index("barcode")
        data[gene] = (sub.X.astype("float32"), obs)
        print("loaded", gene, sub.shape, flush=True)

    wt, wo = data["WT"]
    model = CrossKOHurdle(states=8, min_cells=10).fit_atlas(wt)
    print("atlas fitted G=", model.G, "S=", model.S, flush=True)

    controls = {}
    rng = np.random.default_rng(711)
    for sex in wo.sex.unique():
        blocks = []
        for e in wo.loc[wo.sex == sex, "embryo"].unique():
            ix = np.flatnonzero((wo.sex == sex) & (wo.embryo == e))
            blocks.append(wt[rng.choice(ix, 500, replace=len(ix) < 500)])
        controls[sex] = np.concatenate(blocks)
    cl_cache = {s: assign(model, v) for s, v in controls.items()}
    print("controls", {k: v.shape for k, v in controls.items()}, flush=True)

    recs = []
    for gene in GENES:
        x, obs = data[gene]
        for e in sorted(obs.embryo.unique()):
            mask = np.asarray(obs.embryo == e)
            sex = obs.loc[mask, "sex"].iloc[0]
            recs.append((gene, str(e), sex, controls[sex], x[mask]))
    print("embryo records", len(recs), flush=True)

    acc = {k: [] for k in VARIANTS}
    for gene, e, sex, ctrl, ko in recs:
        kl = assign(model, ko)
        for name, cfg in VARIANTS.items():
            acc[name].append(summarize(model, ctrl, ko, cl_cache[sex], kl, cfg))

    meta = [dict(gene=g, embryo=e, sex=s) for g, e, s, _, _ in recs]
    for name in VARIANTS:
        parts = acc[name]
        delta = np.stack([p[0] for p in parts])
        comp = np.stack([p[1] for p in parts])
        sup = np.stack([p[2] for p in parts])
        np.savez_compressed(OUT / f"{name}.npz", delta=delta, composition=comp, support=sup)
        (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2))
        print(
            f"{name:12} delta{delta.shape} comp{comp.shape} "
            f"support={sup.mean():.4f} "
            f"genes_with_delta={int((np.abs(delta).max(0).max(0) > 0).sum())} "
            f"det_nonzero={float((delta[..., -1] != 0).mean()):.4f}",
            flush=True,
        )


if __name__ == "__main__":
    main()