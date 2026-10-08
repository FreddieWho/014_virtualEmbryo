# T2 endpoint-rank final result and reproducibility record

## Decision and baseline uncertainty

v0036 scored **50.47: REJECT**, 0.65 below incumbent v0030 (51.12) and 0.67 below numerical high v0032 (51.14). Retain v0030. Exact identity, server skill channels and submission evidence remain solely authoritative in [SERVER_SCORE_REGISTRY](../SERVER_SCORE_REGISTRY.md#t2-heart-extrap-endpoint-rank-v0036-score-return-20261008) and [submissions/INDEX.tsv](../../submissions/INDEX.tsv). No second server-score registry is introduced.

The exact historical v0030 binary/emitter was unavailable. Our median09-library baseline reconstructs that recipe; it is not a reproduction of the historical binary. Neither the local comparison nor the whole-candidate server result identifies a causal effect of E14.5 data relative to legacy v0030.

## Data boundary and executed method

Official released training stages are E8.25 late, E8.75 and E9.5. Development fits use E8.25 late/E8.75; reused E9.5 supplies development/reserve diagnostic rows. Final source medians use E8.75/E9.5. The selected predictor uses only those permitted released inputs plus raw E14.5 spatial endpoint counts. External E9.5 was inspected/considered but was not used in development or in the selected final model. No E10.5/E12.5 measurements or protected-stage checkpoint is used.

The source recipe applies 0.9 times the exact shared-celltype median temporal delta and conserves each source row's implied library. Orphan labels copy the latest stage at baseline. The endpoint contains 1,079 anatomical Heart mixed spatial bins from one MOSTA E14.5_E1S3 section; all satisfy the fixed requirement of at least two positive markers among Tnnt2, Tnni3, Actc1, Myh6, Myh7, Myl2 and Myl7. Exact gene matching retains 483 of 500 genes; 17 absent columns are placeholders explicitly excluded, not biological zeros. Original normalized X, gene programs, regulons, clustering, embeddings, trajectories, coordinates and original uns are omitted.

Endpoint counts are normalized on the common panel and summarized with deterministic PCA32/k-means32 microstates. Within-profile gene ranks are matched to source CM rows and rendered through each source row's own expression quantiles. Matched-drift residual weight is q=3u²−2u³=0.104 for u=(10.5−9.5)/(14.5−9.5). The selected endpoint changes only common genes in 7,633 CM rows; all non-CM rows and unmeasured genes remain source-recipe exact. The 25,179-row stratified source sample and spatial_3D geometry are unchanged. This is a short-horizon regularizer, not a complete developmental trajectory, pure-CM atlas or causal maturation model.

## Executed controls and interpretation

All 11 development arms were scored on all 500 genes at seeds 20261003, 20261011 and 20261019 (33 score calls). Arms: copy, reconstructed incumbent_recipe, PCA/GO microstate flow, graph-EB/permuted graph, endpoint Hermite/endfree/permuted endpoint, matched-drift/permuted endpoint. The Hermite path also changed source drift; matched-drift was an explicitly adaptive ablation. It is not preregistered independent validation.

After MODEL_SELECTION_LOCK, three frozen arms were scored on reserved E9.5 rows at the same three seeds (nine additional score calls). The reserve stage has historical research use and is not an independent biological replicate. No settings changed after selection. All 42 run JSONs, split/row manifests and complete metric summaries are included in evaluation/. Neighborhood MMD uses scorer seed 0 internally; these are not three independent neighborhood-MMD replicates. Logistic-probe convergence warnings occurred; scorer metrics/settings were not silently dropped. Variogram measures gene-pair expression structure here.

Local selected-versus-recipe MMD and neighborhood-MMD gains were small (development approximately -0.33% and -0.17%), direction improved, DE tied, and gene-pair variogram error worsened approximately 0.51%. Reserved-row direction matched that pattern. These diagnostic gains did not predict leaderboard improvement. GO/function topology did not establish a useful developmental mechanism. The distant mixed-bin endpoint leaves temporal, composition and assay-shift confounding unresolved.

## Reproduction and publication boundary

The code package includes unchanged frozen implementations/protocol locks, separate path-portable launchers, source filters and permits, original hashes, and all local evaluations. H5AD/model binaries and private delivery receipts are excluded. The official input acquisition page may require authentication. Omitted selected-model weights are fully rebuildable from the specified official inputs and reconstructed small endpoint. Public source acquisition does not imply redistributed source ownership; follow source policies and attribution.

Publication tests ran from an unrelated current directory against existing original files: five bounded synthetic tests; inference replay and refit with exact X, row IDs, genes and coordinates (max X error 0); original public E14.5 extraction reproduced the exact 193,628-byte endpoint SHA256. These are software reproducibility results, not additional modeling experiments. See PUBLICATION_TESTS.json and [runtime instructions](../../scripts/t2_heart_extra_20261008/README.md). No new training search, scorer run or portal submission occurred during publication preparation.
