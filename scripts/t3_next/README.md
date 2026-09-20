# T3 six-route implementation

Entry point (run from the repository root):

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_next.run r1 --run-dir artifacts/t3_next/NEW_UNIQUE_RUN/r1
```

Replace r1 with r2–r6. The run directory must not exist. Each route records its design/input/code hashes, a copy of the executed source, exact candidate contracts and a final RESULT or FAILURE receipt. Do not overwrite prior runs. Archived source is an audit snapshot; to replay it, restore it under `scripts/t3_next/` in an isolated checkout with the same input tree, rather than executing from the receipt directory. The launcher uses eight BLAS/OpenMP threads and the predeclared wall timeout. The 64 GB memory budget is a design allocation, not an enforced OS address-space limit.

`configs/t3_next/design.json` freezes thresholds and model choices before scientific execution. The raw-to-parent coordinate check reproduces the historical float64→float32 conversion; it never modifies parent coordinates. New candidates use the existing protected-parent writer/validator; scoring values are never fabricated. **Run routes that can register candidates serially**: INDEX/version allocation is coordinator-owned. Candidate registration additionally uses a filesystem lock. Read-only matrix/preflight work may overlap, at most two heavy jobs.

| Route | Implementation | Primary diagnostic |
|---|---|---|
| r1 | Per-gene WT rank reconstruction of GRAPH/SIGNMAX values | Exact column multiset; NO_OP detection |
| r2 | Spatial-block cross-fitted WT activity, confound residualization, matched distinct whole-cell donors | Equal actual adaptive/random replacement counts; no self donors |
| r3 | Motif shortest-path DAG, type-interaction ridge / bounded spline mechanisms, preserved individual residual | Zero-intervention identity; independent spatial-block WT prediction; explicit dropped edges |
| r4 | Full sanitized atlas loading, broad-group restricted nearest-neighbor mapping with masked-gene validation, panel/augmented conditional operator | Mapping must beat celltype mean before counterfactual fitting |
| r5 | Source-audited ligand/receptor/target signal response, intrinsic off/on and sender permutation | No raw-expression smoothing; edge provenance required |
| r6 | Whole-perturbation-gene holdout; ridge and a trained two-layer GCN residual predictor | No-change/ridge comparison; no held-out response in training |

R4 uses all 68,910 atlas cells when loading/selecting features. Its internal 64 off-panel motif targets are predeclared model capacity, not a hidden reduction of a promised dense whole-transcriptome network. Mapping and counterfactual inference have separate statuses. The implementation is a stated nearest-neighbor/conditional model, not a claim to reproduce Tangram.

R6 is an explicit, from-scratch graph-conditioned comparator. It is **not** an implementation claim for the complete GEARS or TxPert papers, does not load their checkpoints, and does not automatically download their datasets. The public GEARS README also explicitly limits cross-cell-type use. Eight/further synthetic algorithm tests validate mechanics only, never T3 effectiveness. The actual test count is recorded in the execution report.

## Supplying admissible sources to r5 or r6

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t3_next.run r5 --run-dir artifacts/t3_next/NEW_RUN/r5 --source-manifest path/to/audited_manifest.json
```

The manifest must be an actual reviewed local artifact, not an edited template marking an unaudited dataset approved. It binds `task=T3:gata4`, `status=APPROVED_SANITIZED`, `forbidden_records_remaining=0`, license, primary source reference, a hash-bound filter receipt (JSON with matching task and zero forbidden records), and file paths/SHA256. File paths are relative to the repository root. All new external data must first be added to `infra/bioinf-data-index/` and task-specific permits.

R5 `files.edges` is TSV with columns `ligand, receptor, target, source_reference, license, target_phenocopy_free`. All accepted rows must carry actual target/phenocopy-free provenance. The existing generic OmniPath file cannot be used in its place: it lacks roles and per-edge references. Zero overlapping complete edges produces BLOCKED_PANEL_COVERAGE.

R6 requires `species=mouse`, `embedding_role=WT_OR_ONTOLOGY_ONLY`, `adjacency_role=WT_OR_ONTOLOGY_ONLY`, a single declared source `cell_type`, and these files:

- `files.expression`: sanitized log-normalized H5AD, all 500 output genes, canonical mouse gene symbols as `var_names`; `obs.condition` has `ctrl` or canonical perturbed-gene names, `obs.cell_type` identifies context. Human sources require an independently audited one-to-one orthology conversion before this interface.
- `files.embedding`: NPZ with unique string `genes` and float `embedding` rows, including all eligible perturbations and Gata4. Only permitted WT/ontology information may inform it; response-trained embeddings without fully audited corpus are prohibited.
- `files.adjacency`: CSR NPZ, in exactly the embedding gene order, constructed from permitted outcome-free sources.
- Filter receipt must cover all conditions, including combination members, protected stages/genotypes, source licensing and provenance of embeddings/graph. Merely blacklisting a few symbols is not a complete data audit.

The runtime rechecks condition symbols against the conservative target/phenocopy blacklist and requires at least 20 source perturbations with at least 20 cells each. Unsupported combinations are excluded from the initial single-gene model; no combinatorial generalization is claimed. The target Gata4 response is never a training label. The first experiment is one-context training; transfer to embryonic E8.75 remains unvalidated even if source-gene holdout passes.

## Checks

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib OPENBLAS_NUM_THREADS=8 python -m pytest tests/t3_next -q
```

This is a scoped behavior suite; broad project tests are not required for new isolated scripts. Candidate validation invokes the project's existing board/protected-field/round-trip checks. There is no valid hidden Gata4 expression target locally, so the historical mismatched Gata4-vs-Mab21l2 scorer is deliberately not run or presented as validation. Each receipt marks the local full-panel scorer NOT_RUN_NO_MATCHED_GATA4_TARGET.

## 2026-09-20 response-use gate

The existing R6 learns signed responses. It now requires `allowed_response_role=SIGNED_RESPONSE` plus a hash-bound, human-verified organizer scope record and original written evidence before opening an external matrix. A shape-only permit does not authorize this route. See `source_roles.py` for the required fields; no approved production record currently exists. The shape-only successor is described in `reports/t3_r56_readiness_20260920/R6_SHAPE_DESIGN.md`; only its unsigned-target primitive is implemented, not its complete training/inference pipeline.
