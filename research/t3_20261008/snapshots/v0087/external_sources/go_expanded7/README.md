# Seven-KO outcome-free GO extension

This is a separate immutable-basis extension of ../go_expanded. The previous three-KO artifacts remain unchanged. Same frozen raw GO files, existing scope audit, hash checks, positive-annotation and is_a/part_of closure parser, SVD128 seed20260930, normalization and reconstruction tests apply. No response outcomes or datasets were read.

Requested identities: Dnmt1, Dnmt3a, Dnmt3b, Ehmt2, Kdm2b, Kmt2a, Kmt2b, Mab21l2, Gata4 and Gata6. All have nonzero coverage. Source G9a maps to Ehmt2, independently verified in the approved raw GAF synonym field; exact evidence is in SOURCE_SYMBOL_MAP.json. Two negative Ehmt2 annotation rows were excluded by the existing NOT rule.

Use GO_EXPANDED_EMBEDDING.npz consistently for ALL genes in the seven-KO run. Coordinates differ from both old GO128 and the three-KO expansion; do not mix their rows. Exact normalized GO_TOPOLOGY_EMBEDDING.npz, sparse term incidence and SVD basis are supplied for audit. Missingness, requested cosine matrices and tests are in COVERAGE.tsv, REQUESTED_COSINE_*.tsv, build.log and PROVENANCE.json. build_go.py reproduces features; SOURCE_SYMBOL_MAP.json records the separately verified alias.

Gene Ontology Consortium and annotation contributors, frozen ontology2026-07-26 and annotation headers2026-08-04, CC BY4.0, without warranty. Sources and license: https://geneontology.org/docs/go-citation-policy/ (verified2026-10-08), https://current.geneontology.org/ontology/go-basic.obo and https://current.geneontology.org/annotations/. See ../go_expanded/README.md for full attribution and citations. Derivations: annotation selection, ancestor closure, row normalization and optional SVD projection.

No candidate generated, no portal used. Feature coverage establishes gene identity representation only, not response direction or valid embryo transfer. Model development and final-emitter evaluation remain necessary.
