# TEST PHASE PLAN — Human Team "Physical Fossil" (drafted 2026-10-08)

Test phase opens **2026-10-20**: validation truth and test inputs are released. Each board gets **2 official submissions for the whole phase**. Every submission is scored and published as soon as it is made, cannot be withdrawn, and the board ranks on the best of the two. Final deadline **2026-12-02**; evaluation 12-04; winners 12-11.
Test panels and cell limits are **not published yet**: `panels/index.json` still lists only the 5 val boards (rechecked 10-08 14:2x UTC+8).

Pipeline: `vework/test_pipeline.py --config vework/configs/test_20261020.json --index data/index.json`
- Dry runs passed end to end on 10-08:
  - `configs/val_dryrun.json`: 9/9 entries, official panels, format PASS.
  - `configs/test_dryrun.json`: 9/9 entries on test-shaped targets, provisional panels, format PASS.
- Every run writes `PIPELINE_MANIFEST.json` with sha256, panel status, recipe params and disclosure text.
- **Hand-over rule:** do not hand any file over unless its manifest says `panel=official`.

## Per-board recipes

| board / target | Official #1 (submit early) | Official #2 (later, after calibration) |
|---|---|---|
| **T1 E12.5** (inputs E8.5, E9.5 + E10.5 truth) | **ot-gen / LA3 family on E10.5 carrier** (val winner: ot-gen-A **58.89**). Rebuild v0051-class carrier from released E10.5 truth, then apply complexity-neutral OT generative displacement (A) or LA3 late-anchor shift (57.99) toward GSE230531 E14.5, time fraction 0.327 for 10.5→12.5. Prefer A if it still wins after 10-20 calibration; else LA3. | **Hedge:** pergroup-B (58.22) or LA3 if #1 is OT; or OT if #1 is LA3. Same external disclosure. Submit #2 only if calibration gate ranks it ≥ #1 − 0.5, or as uncorrelated hedge. |
| **T2 embryo E7.75** (bracket E7.5 truth / E8.0; prev E7.25) | Recipe that wins on the portal between E3 (v0014-faithful baseline carrier) and E1 → `T2E_S1` (interp_baseline: prev E7.25, left E7.5, right E8.0). Choose by the E3 result. | The other carrier (`T2E_S2`, interp with left carrier). Use local truth backtest on E7.5 to confirm sign first. |
| **T2 heart extrap E12.5** (released stages + E8.5/E10.5 truths) | `T2X_S1`: v0030-class from E10.5, delta E10.5−E9.5, median ×0.9, no timescale, repo row rule (or X1 rows if X2 does not beat X1 today). This board's best on val is near floor (51.12), so stay conservative. | `T2X_S2`: same, with linear timescale ×2 days and damp 0.5. Submit only if the extrap_truth backtest (E8.5→E10.5 using E9.5) ranks it ≥ S1 **and** that harness passed the calibration gate. |
| **T3 β-catenin KO @ E8.75** | `T3_S1`: conservative. Uniform 7449-cell (or official max) draw of E8.75 WT, no edits (v0008/v0013 class: near-floor and robust). If Ctnnb1 is on the test panel, also zero Ctnnb1 in the deleted lineage only. Zeroing the KO gene gave +3.5 on the Mab21l2 fold, mostly severity. | `T3_S2`: biology-driven. S1 + program-loss of canonical Wnt targets (`WNT_PROGRAM`: Dkk1, Wif1, Rspo3, Tbx6, Dll1, Msx2, Fgf8, Wnt3a, Hoxb1, re-picked from the official panel on 10-20) at strength 0.25, applied inside the Mesp1 lineage, zero-preserving. Optional: if Q4 is allowed and the Mab21l2↔Gata4 cross-fold supports it, add the non-lineage "KO-sample" shift seen in released Gata4 truth. |

Choice rule for each #2: submit only if (a) the truth-based harness passes the calibration gate (`backtests/FAITHFULNESS.md`) and ranks #2 ≥ #1 − 0.5, or (b) #2 is a deliberately uncorrelated hedge. A board ranks on max(#1, #2), so a hedge costs nothing as long as #1 is solid.

## External-source disclosure text (paste with each submission)
- **T1 #1 and #2 (OT or late-anchor on E10.5 carrier):** "External data: GEO GSE230531 (mouse heart/embryo 10x scRNA-seq, Sci Data 2023, doi:10.1038/s41597-023-02333-6), per-sample files only: GSM7226268/GSM7226269 (E8.5 embryo; allowed, ≤E9.5) as within-batch baseline, GSM7226272/GSM7226273 (E14.5 heart; allowed, >E13.5) as late anchor, GSM7226274/GSM7226276 (E16.5 heart; allowed) for time-warp calibration only. Banned-window samples of the same series (E10.5 GSM7226279/80, E12.5 GSM7226270/71) were never downloaded or used; no data from after E9.5 through E13.5. No pre-trained models. Gene mask list (immediate-early genes) after van den Brink et al. 2017. Carrier: released E10.5 validation truth (once available)."
- **T2 embryo #1/#2:** "No external data. Released Task 2 embryo stages only (E7.25, E7.5 truth, E8.0)."
- **T2 heart extrap #1/#2:** "No external data. Released Task 2 heart stages only (incl. released E8.5/E10.5 truths)."
- **T3 #1:** "No external data. Released E8.75 WT only."
- **T3 #2:** "No external expression data. Uses released E8.75 WT [and released Gata4/Mab21l2 KO data, only to calibrate generic KO-sample effects — include only if Q4 is approved]. Prior knowledge: a generic canonical-Wnt target gene list (textbook pathway knowledge, not taken from any Ctnnb1 perturbation dataset) and the Mesp1 lineage map (Saga 1999; Devine 2014; Lescroart 2014). No Ctnnb1 or other Wnt-pathway KO data, no phenocopy data, no GSE78125."

## Day-of-release (10-20) checklist (all times UTC+8; releases may land at 00:00 UTC = 08:00 UTC+8)
1. Download new `panels/index.json` + every `*.genes.txt` → `data/`. Confirm new keys: `T1:test`, `T2:embryo:test`, `T2:heart:test_extrap`, `T3:ctnnb1`. Record min/max cells, obsm requirements and anchors.
2. Download test inputs and val truths (E7.5 embryo, E8.5/E10.5 heart, T1 E10.5, Gata4 KO reps) → `data/`. sha256 everything into `data/RELEASE_20261020.sha256`. Check disk first: about 15 GB free is needed.
3. Re-read the task/evaluation pages for any changes: test DE reference, floor definition, replicate handling for β-cat, limits, obs/obsm requirements.
4. Edit the stage names in `configs/test_20261020.json` and update `limits` from the index. Re-pick `WNT_PROGRAM` from the β-cat panel. Check whether Ctnnb1 is on the panel.
5. **Calibration gate:** run `bt_t2.py` embryo_truth / heart_interp_truth / extrap_truth, `bt_t1.py --train E8.5_RNA,E9.5_RNA --target E10.5`, and `bt_t3.py --fold gata4` on the real truths. Re-score files whose portal scores are known. Record pass/fail in `backtests/CALIBRATION_20261020.md`.
6. Run the pipeline (one heavy job at a time; run T1 last). Every entry must show `panel=official` and format PASS.
7. Hand #1 files plus the disclosure texts to Freddie (no agent uploads). Target **10-20 to 10-23**.
8. Use the remaining val-board quota (still scored during the test phase?) to settle #2 choices where allowed.

## Timing
- **#1:** all four boards by **10-23** at the latest. It locks in a robust score early, and published #1 scores do not reveal anything we would act on: we do not difference scores.
- **#2:** decide by **11-10**, submit by **11-15**, and **no later than 11-25**. That leaves a week of slack before the 12-02 deadline for portal or format problems.
- T1 late-anchor #2 depends on the organiser answer. If there is no answer by 11-10, use the fallback.

## T1 late-anchor — IMPLEMENTED 10-08 (see vework/t1ext/README.md, ext/EXTERNAL_SOURCES_T1.md)
Validation LA1 53.14, LA2 53.43, LA3 (v0051 + strength 1.46) **57.99**. Round-3 (scored overnight, confirmed 2026-10-09 CST): **ot-gen-A 58.89** (de 49.7 dir 65.9 mmd 65.2 vario 52.3; new team T1 best), **pergroup-B 58.22** (de 51.4 dir 64.2 mmd 62.4 vario 53.0). Files in `submit/T1_val__A_ot_gen_v51.h5ad`, `T1_val__B_v51_anchor_pergroup.h5ad`. Portal T1 best **58.9**, board rank 79/305.

LA1/LA2/LA3 and round-3 A/B are in `submit/`. Test use: carrier = released E10.5 truth, warp 10.5→12.5 = 0.327 of the E8.5→E14.5 trajectory. Official #1 = ot-gen-A recipe (or LA3 if OT fails calibration); #2 = the other of {OT, LA3/pergroup} as hedge. Disclosure = GSE230531 late-anchor text in MANIFEST / EXTERNAL_SOURCES_T1.md.

## T1 late-anchor candidates (assessed 10-08)
T1 tissue is a heart-region dissection (cardiomyocyte subtypes, SHF, endocardium, pericardium, proepicardium, foregut/hepatocyte/ST). An external heart-only set can therefore anchor only the cardiac/endothelial/epicardial cell types, never the overall composition. Rule: use data strictly after E13.5 (E14.5+), disclosed. E10.5 and E12.5 are banned absolutely, and nothing from E10.0–E13.5 may be used.
1. **GSE230531** (preferred). Sci Data 2023, C57BL/6J; samples E8.5, E10.5, E12.5, E14.5, E16.5, P3, all as separate per-sample 10x MTX files.
   - **Download only** GSM7226272/3 (E14.5 rep1/2, matrix 85+66 MB) and optionally GSM7226274/6 (E16.5, 98+78 MB): about 0.33 GB total. Never fetch `GSE230531_RAW.tar` (1.3 GB): it contains the banned E10.5/E12.5 samples.
   - Format: raw **unfiltered** CellRanger 3.1 matrices (737,280 barcodes, 27,998 features, mm10-3.0.0 reference). Cell calling is needed (knee/EmptyDrops-style UMI threshold), plus QC (mito %, doublets).
   - Gene overlap: 25,943 of the 32,285 T1 panel genes match by symbol (80%). The rest stay unanchored, i.e. keep the E10.5 values.
   - Licence: GEO/NCBI data have no use restrictions; the article is open access (CC BY).
   - Harmonise: normalise to 1e4 and log1p like the panel; drop non-heart contaminants. Map clusters to our cardiac labels (V-CM, OFT/RV-CM, IFT/atrial-CM, endocardium/endothelium, epicardium) via marker genes. Use only per-type pseudobulk means as anchors.
2. **GSE193346** (Feng et al., Nat Commun 2022, PMID 36575170). Wild-type CD1 and C57BL/6 hearts, chamber-separated, many stages.
   - Post-E13.5 cells: C57BL6 E14.5 821, E15.5 1,733, E16.5 1,098; CD1 E14.5 2,363, E15.5 1,778, E16.5 1,480 (from the 3 MB metadata, downloaded).
   - Files: **only whole-series Seurat RDS** (C57BL6 4.6 GB, CD1 5.0 GB). Both are **>3 GB, so they need your OK before download**. They also include the banned E10.5–E13.5 cells, so we would filter immediately and delete the rest. Converting needs R/SeuratObject.
   - This is the second choice: fewer cells per stage, but better-matched chamber annotation.
- Not recommended: Qiu et al. 2024 (GSE228590, whole-embryo sci-RNA-seq3, 11.4M nuclei; files are huge and nuclei ≠ 10x cells); DeLaughter 2016 (~1,200 Fluidigm cells in total).

## Open organiser questions (draft, NOT sent; see bottom)
The 10-03 email (Gata4 boundary: same-gene other stages, pathway-member KOs, WT GATA4 ChIP) is **still unanswered**. Its answers mostly affect validation T3. They matter for test only by analogy: β-cat at other stages / Wnt-pathway members are already excluded by our own hard rules.

---
### Draft: test-phase questions to organisers (for Freddie to review/send)
To: virtual.embryo.moonshot@gmail.com
Subject: Test-phase clarification questions (Tasks 1–3) — team Physical Fossil

Dear organizers,

Before the test phase opens on 20 October we would like to confirm a few points. We will follow your answers and disclose all sources.

1. **Task 1, late external anchor.** For the E12.5 test target, may we use public mouse heart scRNA-seq strictly after E13.5 (e.g. E14.5 samples from GSE230531), with disclosure? We would download only the E14.5+ sample files and never touch E10.5–E13.5 samples from the same series. Is that acceptable, or must the whole series be avoided because it also contains E10.5/E12.5 samples?
2. **Test panels and limits.** Will the test-board gene panels, cell-count limits and any obsm requirements be published in panels/index.json on 20 October, or earlier? For the Task 2 embryo E7.75 target, is the DE/floor reference the released E7.5 truth (the nearest earlier stage) or E7.25?
3. **Task 3 β-catenin replicates and reference.** The KO has two replicates and is scored against each. Is the final T3 score the mean over replicates? Is the WT reference for DE/severity the released E8.75 WT?
4. **Use of released KO truth.** Once the Gata4 KO truth is released on 20 October, may we use it (and the Mab21l2 KO) to model generic, gene-agnostic KO-sample effects for the β-catenin submission, e.g. a shared batch/sample shift? We would not use any Wnt-pathway or β-catenin perturbation data.
5. **Generic pathway prior.** For β-catenin, may we use a generic textbook list of canonical-Wnt target genes as a prior, provided it is not derived from any Ctnnb1 perturbation dataset? Or does any Ctnnb1-KO literature-derived signature count as prohibited?
6. **Validation boards during test.** Do the validation boards stay open (with daily limits) during the test phase?
7. Our 3 October email (Task 3 Gata4 data boundaries) is still pending. We would be grateful for an answer when possible.

Best regards,
Freddie Who — Human Team "Physical Fossil"
