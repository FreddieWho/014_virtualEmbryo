# v0088 source-selected emitter repair

Candidate v0088, parent v0087. SCORED53.69, PROMOTE over v0087=53.42 (+0.27). The parent portal worker used the one final authorized submission; no further uploads. No portal access by this builder. `blocks_submission:false`.

Selected arm: **conditional**. File `/workspace/shared/t3_v88_optimization_20261008/v0088/t3_gata4__condhurdle__v0088.h5ad`. SHA256 `d7944880d8f55974946dad4b2c22879582c03bce547ead312921b0fc39bdddc7`. Shape7449×500. Locked contract PASS; portable replay PASS. v87 scored bytes unchanged.

Official result: [account-specific link omitted] . Observed2026-10-08T11:57:10Z. UI submissiontime11:56 has no timezone label. Five skills: DE41.7, DCS51.2, PSS75.2, MMD51.1, CSS43.1. Relative to v87: 0,0,+0.2,+1.4,+0.8. This one test supports the narrow structural repair, not causal generalization or guaranteed future performance. Daily quota8/8 and final authorized attempt spent.

Repository registration is handled separately by the coordinator. This packet does not claim all experimental code or source data were pushed to GitHub. Creation-time MANIFEST.json remains immutable and correctly records submitted:false at build time; SERVER_RESULT.json is the later terminal receipt.

## Frozen experiment and decision

Four-arm 2×2 factorial: baseline, positive-residual retention, WT-conditioned zero activation, both. No amplitude sweep. The source response and composition remain exactly v87. New residual arm preserves actual positive-expression deviations lost by 21-quantile reconstruction; conditional activation replaces independent random zero ties with WT-state association after removing each gene's own PCA contribution. Four arms fixed before new outcome metrics. Selection based on seven held-out genotypes, equal genotype weights, all five actual metrics, paired seeds0/1/2 and weights30/25/25/12/8. MSE unranked.

Source local calibrated means (not official target scores):

              total  de_skill  direction_skill  severity_abs_skill  mmd_skill  variogram_skill
model                                                                                         
baseline    74.4123   69.0891          72.9794             93.4206    58.6889          63.0360
both        74.3232   68.6716          72.7543             93.3884    59.6207          62.8946
conditional 74.7376   69.0891          72.9701             93.3944    61.4173          63.1207
residual    73.9665   68.6716          72.7609             93.4150    56.6158          62.8389

Per-identity totals and selected gain:

model   baseline    both  conditional  residual  selected_minus_baseline
query                                                                   
Dnmt1    81.1715 81.2586      81.4499   80.9389                   0.2784
Dnmt3a   57.3127 57.9694      57.6287   57.6358                   0.3160
Dnmt3b   74.5464 74.6608      74.7529   74.3690                   0.2064
Ehmt2    70.9573 70.7954      71.3789   70.3693                   0.4216
Kdm2b    78.6666 77.4306      78.7165   77.3242                   0.0498
Kmt2a    80.0100 80.0210      80.4654   79.5295                   0.4554
Kmt2b    78.2215 78.1265      78.7709   77.5987                   0.5494

Full selection receipt:

```json
{
  "chosen": "conditional",
  "decisions": [
    {
      "model": "residual",
      "passes": false,
      "mean_gain": -0.44581319478750253,
      "wins": 1,
      "component_delta": {
        "de": -0.4174715307439974,
        "direction": -0.21857640242354087,
        "severity_abs": -0.005554065281846273,
        "mmd": -2.0731297484032174,
        "variogram": -0.19704436036965436
      },
      "per_query_gain": {
        "Dnmt1": -0.2325980467566353,
        "Dnmt3a": 0.3230849628475454,
        "Dnmt3b": -0.17744618652527322,
        "Ehmt2": -0.5879495562600425,
        "Kdm2b": -1.3424676856298845,
        "Kmt2a": -0.48053894579436474,
        "Kmt2b": -0.622776905393863
      }
    },
    {
      "model": "conditional",
      "passes": true,
      "mean_gain": 0.3252895166891189,
      "wins": 7,
      "component_delta": {
        "de": 0.0,
        "direction": -0.009394980764802037,
        "severity_abs": -0.026160385230720555,
        "mmd": 2.7283203717585396,
        "variogram": 0.08474891971220545
      },
      "per_query_gain": {
        "Dnmt1": 0.27843805743462724,
        "Dnmt3a": 0.3159826251211513,
        "Dnmt3b": 0.2064304238727459,
        "Ehmt2": 0.4215874903264165,
        "Kdm2b": 0.04982591123071245,
        "Kmt2a": 0.45538226599997245,
        "Kmt2b": 0.5493798428382064
      }
    },
    {
      "model": "both",
      "passes": false,
      "mean_gain": -0.08909867363137332,
      "wins": 4,
      "component_delta": {
        "de": -0.4174715307439974,
        "direction": -0.2251837381666937,
        "severity_abs": -0.032236970996917434,
        "mmd": 0.9317144013121518,
        "variogram": -0.14134706593408047
      },
      "per_query_gain": {
        "Dnmt1": 0.08710015002310456,
        "Dnmt3a": 0.6566913277117266,
        "Dnmt3b": 0.11440787888631121,
        "Ehmt2": -0.16190056388462892,
        "Kdm2b": -1.235991632123131,
        "Kmt2a": 0.010938424506434785,
        "Kmt2b": -0.09493630053943036
      }
    }
  ],
  "scope": "Adaptive source-local calibrated comparison; not official or target forecast"
}
```

The comparison is adaptive development over seven epigenetic perturbations. Local floor is full matched reference; ceiling resamples disjoint cells within evaluation embryos, a technical ceiling rather than biological-replication evidence. Do not interpret small differences as guaranteed target improvements. The predefined winner is not changed using Mab.

## Secondary released-Mab check

All four target and Mab predictions frozen before loading Mab outcomes. Historically reused Mab is an adaptive diagnostic, not a pristine heldout test. Baseline local total57.2518; selected 57.4788. Paired selected-minus-baseline [0.2143750323772764, 0.24228588746652946, 0.22425822704130383]. This is not a Gata forecast. All12 raw/calibrated rows retained.

## Target input-only diagnostics

Source response/compose unchanged; all composition donor indices identical to baseline. Actual final mean-log drift L20.039629; response L24.235587; response-rank correlation0.99981117; detection0.11084280; maximum row10000 closure error0.003821. Final means are approximately retained, not exact: first three metrics are NOT mathematically protected. No target scores or hidden magnitudes fitted. No Gata4/Gata6 RNA forced zero or half-dosed. OOD inclusion and generic biological scope remain unchanged from v87.

## Verification and reproducibility

- Nine raw source panels byte-identical to v87; exact 157154-cell biological joins,82 embryos, known690 missing WT barcode rows retained as an explicit limitation
- Exact source baseline raw-metric replay audited; all new matrices serialized/reloaded before measurement
- Four-arm null, partial-gene null, closure, finite/nonnegative and deterministic tests PASS; independent own-gene PC-subtraction check PASS
- Exact v87 target baseline replay; protected obs/var/geometry; final H5AD/ZIP CRC and member SHA checked
- Portable inference reads only WT carrier, frozen response, state model and local emitter; exact expression/donor replay PASS
- Code/protocol/input/source permit hashes retained; source/chemistry/confounding and scientific limits inherited; no paid services or hidden target data

The full packet includes all eight normalized source panels and per-embryo sufficient statistics, so source evaluation can run without another raw download. Multi-GB public raw count downloads and redundant prediction matrices are excluded. Rebuild paths and permits are retained. No claims of70, causal Gata4 specificity, source-domain independence or official-score parity are made.

## Timestamped team overview

Parent-reported official overview at2026-10-08T11:58:09Z: Total171.4, Humanrank61 (previous171.1/rank62). Displayed T1=58.0, T2=59.7, T3=53.7 (exact candidate53.69). T1 changes were from another user session; only the T3 improvement is attributable to this run. Rank is time-dependent.
