# Final daily T2 slot: v0026 copula refinement

One candidate is selected, no upload by builder. It uses exact H1 carrier and exactly the v25 final heart-specific B, changing only rank blend from0.5 to0.75. V25 arrays are re-created exactly as the matched comparator, not iterated on. All candidate/parent hashes, sources and invariants are in HANDOFF.json.

## Bounded selection
Three alternatives only: global0.75, global1.0, within-state rank pooled precision0.5. Same released E8.25_late+E9.5 training predicts withheld-from-fit E8.75; same H1 geometry/carrier and3 fixed scoring seeds. After all predictions froze, E8.75 was loaded for evaluation. The heldout analogue of v25, not final E8.75-trained v25, was the comparator.

Selection required mean raw neighborhood MMD<=1.05× and variogram<=1.10× comparator, then mean local total highest; practical mean gain>0.1 and each seed positive. Alternatives and primary rules were specified before run. A secondary practical-gain/tie addendum was written after run start but before score inspection; the winner is unchanged by this addendum. There was no expanded search after seeing outcomes.

- global_b075: total mean 54.771684; paired gains [0.28520708009004636, 0.3077002052231066, 0.35042664165445103]; nmmd ratio 0.982145; variogram ratio 1.002523
- global_b100: total mean 54.679614; paired gains [0.20392790970869612, 0.21595506864900216, 0.2472418813810151]; nmmd ratio 0.986344; variogram ratio 1.000996
- within_state_b050: total mean 54.422434; paired gains [-0.0020241588641738417, -0.047628945957704616, -0.054762833920037224]; nmmd ratio 1.004870; variogram ratio 0.990372
- gene_shuffle_b050: total mean 52.782681; paired gains [-1.721418780668877, -1.6293960329685078, -1.6728602872862481]; nmmd ratio 1.133173; variogram ratio 0.986019
- v25: total mean 54.457239; paired gains [0.0, 0.0, 0.0]; nmmd ratio 1.000000; variogram ratio 1.000000

Global0.75 wins the frozen comparison. Global1 is weaker and produces wider cell-library tails; within-state residual fit is slightly worse on all seeds. The existing0.5 gene-shuffle null was not winner-matched, so a fixed0.75 shuffle was added after selection solely for diagnosis; mean total 52.330268, versus winner 54.771684. Choice was not changed based on this diagnostic.

## Final build and risks
Final fit only uses released E8.25_late/E8.75. No target E8.5, embryo-trained B, new endpoint, random seed search, row reorder or server-specific gaming. Final B is exactly the previous v25 B. File/arrays replay independently with one numerical thread. All per-state gene value multisets, rows, stored metadata and coordinates match v25; libraries and classifier-derived state mass are not invariants. Final library ratio min/p1/median/p99/max: [0.693519379327521, 0.8127172127235801, 0.9913668701029545, 1.146777265765061, 1.2782350205657975]. Absolute within-state mean correlation rises, a real over-correlation risk that is smaller than blend1 in development.

The reused E8.75 development fold is exploratory tuning;3 sampling seeds are not independent biological validation. Local expected gain is modest, not a promise of leaderboard gain or causal biological discovery. Variogram is gene-pair expression structure, not spatial lag. Final upload requires parent approval and independent review.

Run artifact:python run.py --mode dev --out NEW_DIR; final/replay use --mode final or replay --choice global_b075. Data and repo runtime paths are explicit in run.py. No old scored artifact is overwritten.

Metadata clarification: RESULT.fit_global includes inherited blend=0.5 and parameter_search=false from the unchanged B-fitting helper. Those values describe the old helper default and are not the v26 operator setting or this campaign search status. This campaign explicitly compared three preset challengers; the applied blend is0.75 in arms.global_b075.blend and the candidate provenance.

## Official outcome and closure

Final authorized slot consumed; today8/8, no further submission. Exact candidate SHA10db96db40d9ffbfd22a5d54a76c70a27ceab1284535e0170391dfcb3086d5e4, portal ID178b3ff4be5440e286f53cf6e96805af, model heart-copula075-v0026, submitted2026-10-09 10:48UTC. UI66.78; official API66.7846 at10:49:34UTC, scored_at10:48:52Z. Relative to v25 66.7064, +0.0782 remains within±0.1; keep project incumbent v25 while portal numeric best isv26. Full eight API submetrics are in SERVER_SUBMETRIC_REGISTRY.tsv. MMD +1.2511, variogram +0.0811, neighborhood −0.4699, other five unchanged. T2 portal best-per-board mean60.3139666667, Human71/187; heart Human38/174. API supplies numeric/model/time evidence; ID and file identity come from terminal portal detail, not API.

Single axis: conditional rank blend0.5→0.75 on same exact H1 carrier, exactly same heart B asv25. Not repeated application tov25. Full single-thread independent B/X and byte replay, 5872×500 panel, state-gene marginals/metadata/geometry pass. Development3seed +0.285/+0.308/+0.350; nmmd improved1.79% but variogram raw worsened0.25%. Other2 predetermined challengers fully disclosed. Matched0.75 shuffled null added only after choice freeze; no retuning. Reused development stage and local selection optimism are limitations. Inherited fit-helper metadata blend0.5/searchfalse does not describe this3-challenger campaign or applied0.75. Per-cell libraries/classifier mass are not invariants. No new protected data, seed/row gaming or remote push. Report: reports/t2_final_slot_20261009/REPORT.md.

Generation-time ready/unsubmitted fields in frozen logs describe the earlier build, not current status. This report and SCORE_RETURN.json record the terminal result.
