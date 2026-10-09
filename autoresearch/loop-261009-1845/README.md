# T3 route loop, 2026-10-09 — response structure, combination, new architecture

Bounded loop over three substitution channels on the reconstructed v0088 model:
existing-route optimization (emitter parameters), route combination (response
structure × emitter), and new architectures (joint transport; state/quantile
families).

Metric: skill-weighted composite total, conditional arm, 7 held-out genotypes ×
3 seeds, weights de .30 / direction .25 / severity_abs .25 / mmd .12 /
variogram .08 (replicating frozen `evaluate_source.py`). higher_is_better.
Guard: emitted artifact contract — shape 7449×500, finite, non-negative, closed
panel total 10000 within 0.02.

## Layout

- `loop/results.tsv` — 30-row ledger
- `loop/handoff.json` — machine-readable handoff
- `scripts/` — response precompute, route driver, new-architecture emitters, reporting
- `route_results/` — 33 per-route result payloads

## Headline

Incumbent v0088 = 74.737588. Best route `lam15 + unmasked + min_cells20`
= **74.936110 (+0.1985)**, passes the frozen v0088 decision gate.

The emitter channel (2026-09 loop) saturated at +0.003 with de immovable. This
loop moved the **response structure** instead:

| route | total | Δ |
|---|---:|---:|
| incumbent v0088 | 74.737588 | 0 |
| lam50 masked (frozen) | 74.737588 | 0 |
| lam15 masked | 74.816398 | +0.0788 |
| unmasked (lam50) | 74.811536 | +0.0739 |
| **lam15 + unmasked** | **74.930254** | **+0.1927** |
| lam15 + unmasked + min_cells20 | 74.936110 | +0.1985 |
| joint rank transport (new arch) | 62.668426 | −12.07 |

## Key findings

1. **de_skill is immovable at the emitter, movable at the response.** The emitter
   only redistributes already-activated cells, so it cannot change which genes
   are detected together. Reducing response shrinkage and dropping the
   global_valid mask moves de by +0.354 — the first real de movement found.
2. **Combination is super-additive.** unmasked alone +0.074, lam15 alone +0.079,
   together +0.193.
3. **New architecture (joint rank transport) is a clean negative.** −12.07, with
   the control arm held at the frozen 74.412, so the drop is attributable to the
   transport operator, not the harness. The composite rewards marginal
   calibration.
4. **lam plateau at 12–18 (span 0.006); min_cells is noise.** The signal is
   `unmasked + reduced shrinkage`, saturated at ≈ +0.198.
5. **Not uniform.** 4/7 per-genotype wins; mean carried by Ehmt2 +1.0,
   Kmt2b +0.87, Kmt2a +0.59 against Dnmt1 −0.855.
6. **State/quantile families blocked.** S≠8 or nq≠21 responses fail closed
   because the refitted model fixes S and positive_q; these need a full model
   refit, not a response swap.

## Caveat

Local source-side score has repeatedly failed to transfer to the server
(v0086: source-proxy gain → server 49.34, below v0084). A +0.198 local gain is
a development signal, not a server prediction. Submission budget remains
unresolved for T3.

## Reproducing

    ../ve-t3/bin/python scripts/route.py --name <n> --response <r>

Requires the rebuilt model and normalized panels described in
`reports/t3_rebuild_20261009/REPORT.md`.