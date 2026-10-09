"""New T3 route family: different structural assumptions for the response.

Two assumptions the frozen route never varied, each a genuinely different
structural premise rather than a parameter nudge:

states      the WT atlas is clustered into 8 states (states=8). Finer or coarser
            states change WHICH cells are grouped as a coherent context, which is
            a different assumption about what a developmental state is.
quantiles   the response curve is sampled at 21 positive quantiles. A denser or
            coarser grid changes how much of the response shape is representable.

Both keep the marginal quantile transport, because the joint-transport route
measured -12.07 on 2026-10-09 and the local composite rewards marginal
calibration. So these test structural granularity, not transport operator.

Writes drop-in embryo_responses.npz replacements keyed by name, e.g.
states12_lam15_unmasked.
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

# name -> (states, quantiles, lam, min_cells, mask)
FAMILIES = {
    "states4": (4, 21, 15.0, 10, False),
    "states12": (12, 21, 15.0, 10, False),
    "states16": (16, 21, 15.0, 10, False),
    "states32": (32, 21, 15.0, 10, False),
    "quant11": (8, 11, 15.0, 10, False),
    "quant31": (8, 31, 15.0, 10, False),
    "quant41": (8, 41, 15.0, 10, False),
    "states12_frozen": (12, 21, 50.0, 10, True),
}


def assign(model, x):
    return model.km.predict(model.pca.transform(x[:, model.features]))


def summarize(model, control, ko, cl, kl, lam_k, min_cells, mask):
    G, Q, S = model.G, len(model.positive_q), model.S
    nc = np.bincount(cl, minlength=S)
    nk = np.bincount(kl, minlength=S)
    zero = np.zeros((G, Q))
    cq, cv = model.positive_quantiles(control, zero)
    kq, kv = model.positive_quantiles(ko, cq)
    gd = kq - cq
    gdetect = (ko > 0).mean(0) - (control > 0).mean(0)
    gvalid = cv & kv

    out, sup = [], []
    for s in range(S):
        ok = nc[s] >= min_cells and nk[s] >= min_cells
        sup.append(ok)
        if not ok:
            out.append(np.zeros((G, Q + 1)))
            continue
        a, b = control[cl == s], ko[kl == s]
        aq, _ = model.positive_quantiles(a, cq)
        bq, _ = model.positive_quantiles(b, kq)
        lam = nk[s] / (nk[s] + lam_k)
        d = lam * (bq - aq) + (1 - lam) * gd
        rate = lam * ((b > 0).mean(0) - (a > 0).mean(0)) + (1 - lam) * gdetect
        if mask:
            d[~gvalid] = 0
            rate[~gvalid] = 0
        out.append(np.c_[d, rate])

    comp = np.log((nk + 0.5) / (nk.sum() + 0.5 * S)) - np.log(
        (nc + 0.5) / (nc.sum() + 0.5 * S)
    )
    return np.array(out), comp - comp.mean(), np.array(sup)


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
    wt, wo = data["WT"]
    print("panels loaded", flush=True)

    # WT-only controls are identical across families so any delta is structural.
    controls, rng = {}, np.random.default_rng(711)
    for sex in wo.sex.unique():
        blocks = []
        for e in wo.loc[wo.sex == sex, "embryo"].unique():
            ix = np.flatnonzero((wo.sex == sex) & (wo.embryo == e))
            blocks.append(wt[rng.choice(ix, 500, replace=len(ix) < 500)])
        controls[sex] = np.concatenate(blocks)
    print("controls", {k: v.shape for k, v in controls.items()}, flush=True)

    recs = []
    for gene in GENES:
        x, obs = data[gene]
        for e in sorted(obs.embryo.unique()):
            mask = np.asarray(obs.embryo == e)
            sex = obs.loc[mask, "sex"].iloc[0]
            recs.append((gene, str(e), sex, controls[sex], x[mask]))

    meta = [dict(gene=g, embryo=e, sex=s) for g, e, s, _, _ in recs]

    for name, (S, nq, lam_k, mc, mask) in FAMILIES.items():
        model = CrossKOHurdle(states=S, quantiles=nq, min_cells=mc).fit_atlas(wt)
        cl_cache = {s: assign(model, v) for s, v in controls.items()}
        acc = []
        for gene, e, sex, ctrl, ko in recs:
            kl = assign(model, ko)
            acc.append(summarize(model, ctrl, ko, cl_cache[sex], kl, lam_k, mc, mask))
        delta = np.stack([a[0] for a in acc])
        comp = np.stack([a[1] for a in acc])
        sup = np.stack([a[2] for a in acc])
        np.savez_compressed(OUT / f"{name}.npz", delta=delta, composition=comp, support=sup)
        (OUT / f"{name}.json").write_text(json.dumps(meta, indent=2))
        print(
            f"{name:20} S={S:<3} nq={nq:<3} delta{delta.shape} support={sup.mean():.4f} "
            f"genes_with_delta={int((np.abs(delta).max(0).max(0) > 0).sum())}",
            flush=True,
        )


if __name__ == "__main__":
    main()