# T1 late-anchor / OT generative — portal score return (2026-10-08/09)

**Renumber note:** mistaken draft IDs v0063–v0067 retired (already T3:gata4). Assigned
**v0089–v0093**. SHA-256 unchanged.

Human Team track. Artifacts remain local (`*.h5ad` gitignored); SHA-256 values match
`reports/t1_late_anchor_20261008/MANIFEST.tsv`. Code under `scripts/vework/` and
`scripts/vework/t1ext/`. External scope: GEO GSE230531 only (E8.5/E14.5/E16.5);
banned-window E10.5/E12.5 never downloaded.

| Candidate | Detail score | de_score | de_direction | mmd_u | variogram | Verdict |
|---|---:|---:|---:|---:|---:|---|
| v0089 LA1 late_anchor_x1 | 53.14 | — | — | — | — | REJECT (−0.78 vs incumbent v0051 53.92) |
| v0090 LA2 late_anchor_x2_comphalf | 53.43 | — | — | — | — | REJECT (−0.49 vs v0051) |
| v0091 LA3 v51_anchor_auto | 57.99 | 51.6 | 64.0 | 61.7 | 52.8 | PROMOTED vs v0051 (+4.07); later superseded by v0092 |
| v0092 ot-gen-A ot_gen_v51 | **58.89** | 49.7 | 65.9 | 65.2 | 52.3 | **PROMOTED current T1 best** (+0.90 vs LA3) |
| v0093 pergroup-B v51_anchor_pergroup | 58.22 | 51.4 | 64.2 | 62.4 | 53.0 | scored backup (−0.67 vs A; +0.23 vs LA3) |

Portal detail IDs:
- A: https://virtualembryo.ai/challenge/account/submissions/39e6870fb90549e09067e7c3cff92333
- B: https://virtualembryo.ai/challenge/account/submissions/455eb227ed4a407382c2f18a4d2ab920

Exact uploaded SHA256:
- LA1 `f876b1ef0983c635833fe7ca8713034712b777b091413196923fac5282d84282`
- LA2 `7dbc0eb05f5ab578fffe3590158bbb5b33cd1230acb26522759a1db5e217fa09`
- LA3 `79af479a577c53a182b5c74aeba5066c8b9a553e1a9570ccf4b9a15c540052d2`
- A `35fae3a797acdf44b4c6d141e1a0db65b44744ea218f96218c7909e34eda5dc1`
- B `04d73c5d2c9daab7c9fc9db3ba9543c295639f9e4415ca312511c0147adf7fe6`

**Current T1 selection: v0092 ot-gen-A, 58.89.** Ask before any official test-phase portal upload.
Merged into `reports/SERVER_SCORE_REGISTRY.md` under heading
`# T1 late-anchor OT score return 20261009`.
