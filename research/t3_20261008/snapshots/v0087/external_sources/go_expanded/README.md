# Expanded outcome-free GO identity priors

Existing approved GO annotation/ontology files were reused, with all three SHA256 values checked against the existing GO__DATA_AUDIT_REPORT.json. No biological response matrix, new external dataset or hidden KO outcome was read. Only Dnmt3a and Kdm2b were missing from the old526-gene list; the expanded list has528 genes. Kmt2a, Mab21l2, Gata4 and Gata6 were already present.

## Load and use

GO_EXPANDED_EMBEDDING.npz contains `genes` (528 symbols) and `embedding` (528×128). Its construction reuses the existing positive GAF annotations, NOT exclusion and is_a/part_of closure parser, then fits SVD128 with seed20260930 and L2-normalizes each nonzero row. The SVD is fitted only on ontology membership, with query-gene identity allowed. No source/target expression outcomes affect basis fitting. Use this file consistently for ALL genes: coordinates are not compatible with the old GO128 file, so do not append these new rows to old embeddings. Save this file hash in the model provenance.

GO_TOPOLOGY_EMBEDDING.npz is the preferred completely transparent alternative: `genes`, `embedding` (528×8261 binary term-incidence rows normalized to L2 norm1), and `features` (ordered GO term IDs). It is free of learned dimensional reduction and directly exposes overlap over the positive ontology closure. All genes share the same feature columns. GO_TERM_INCIDENCE.npz is the sparse unnormalized binary matrix; GO_SVD_BASIS.npz contains terms, projection components and singular values for reconstruction.

Use a single predeclared representation for model development; do not choose based on protected target or leaderboard outcomes. Ontology overlap supplies identity/context priors, not causal response direction, magnitude, cell-state compatibility or independent proof of transfer. Broad shared ancestors increase cosine overlap; SVD compression further changes cosine geometry. Both similarities are supplied for audit, not as evidence of effect-sign agreement.

## Coverage and tests

Requested direct/ancestor-closed term counts:
- Dnmt3a54/189
- Kdm2b33/183
- Kmt2a45/225
- Mab21l2 7/39
- Gata4 106/402
- Gata6 79/324

All requested genes have nonzero features. Twelve other genes have zero annotation coverage in the unchanged exact-symbol parser; COVERAGE.tsv lists them explicitly. No alias inference silently fills missing annotations. GAF duplicates across sources are collapsed to sets. Annotation evidence codes and excluded negative-row counts are reported.

Tests passed inside build_go.py: three frozen source hashes; all requested identities covered; exact reconstruction of their sparse closure terms; SVD projection reconstruction; unit norms; finite outputs; exact NPZ roundtrip. Ontology release2026-07-26 and annotation headers referencing GO2026-08-02 are version-mismatched as in the approved frozen source. All8,261 selected terms exist in the OBO, so no unknown-node topology truncation occurs. TERMS_ABSENT_FROM_OBO.json records this audit.

## Provenance, attribution and limits

PROVENANCE.json records raw and output hashes, original parser hash, build hash, package versions, annotation headers, scope and test outcomes. Running `python build_go.py` reconstructs outputs from local frozen inputs. No old model artifact was overwritten. No submission generated or portal used.

Gene Ontology Consortium ontology and mouse annotations, ontology2026-07-26 and annotation headers dated2026-08-04, are reused under [CC BY4.0](https://creativecommons.org/licenses/by/4.0/). Sources: [ontology](https://current.geneontology.org/ontology/go-basic.obo), [mouse model-organism annotations](https://current.geneontology.org/annotations/MOUSE-mod.gaf.gz), [mouse UniProt annotations](https://current.geneontology.org/annotations/MOUSE-uniprot.gaf.gz). Credit the Gene Ontology Consortium and its annotation contributors. Data are provided without warranty. These derived outputs change the original data through positive-annotation selection, ancestor closure, row normalization and optional SVD projection.

The [official GO licensing/citation policy](https://geneontology.org/docs/go-citation-policy/) was checked2026-10-08 because the existing local audit lacked an explicit licensing statement. No raw dataset was refreshed. Cite Ashburner et al.,2000, DOI10.1038/75556 and The Gene Ontology Consortium, The Gene Ontology knowledgebase in2026, DOI10.1093/nar/gkaf1292, plus the frozen releases above. No publisher abstract or response measurements were incorporated.

Task/candidate: ontology integration only; no candidate ID or parent. Decision: ready for fold-pure cross-KO modeling, not evidence sufficient for submission. blocks_submission:false.
