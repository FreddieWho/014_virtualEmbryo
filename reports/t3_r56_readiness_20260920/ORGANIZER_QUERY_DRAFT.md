# Organizer clarification draft — NOT_SENT

Subject: T3 Gata4: task-specific use of filtered adult mouse Perturb-seq and curated signaling topology

We request written clarification before training. No external source below has been used for normalization, embedding, pseudobulk, marker analysis, model fitting or target prediction. Only metadata inspection, immediate filtering and structural validation have been performed.

For T3 Gata4, may we use GSE261783 (GSM8151756 and GSM8151757, resting OP2 primary adult mouse cardiac fibroblasts, 8 weeks; Aguado-Alvaro et al., doi:10.1038/s41467-025-66597-9; author-linked Zenodo doi:10.5281/zenodo.14794723, CC-BY4.0)? The current provisional subset has 4998 cells, 23 perturbations and 220 explicit non-targeting controls. It excludes ambiguous/multiple guide assignments, the project target/phenocopy blacklist, Tgfbr1/Smad2/Smad3/Smad4, and conservatively Chd4/Smarca4/Yy1. The remaining list is attached as R6_CONDITION_REVIEW.tsv; it has NOT been certified phenocopy-free.

We propose learning only absolute, unit-normalized response shape, with no source response signs or absolute response amplitudes transferred to Gata4. Source perturbation genes would be held out in their entirety for validation. Target directions and amplitude would come only from separately permitted WT inputs. Graph/embedding construction would use only permitted WT or audited outcome-free ontology information, without pretrained checkpoints. Is this source/context and role admissible, and what further gene/context exclusions are required?

For a separate ligand-receptor-target route, may generic curated topology from Reactome/SIGNOR be used after edge-level citation, species and experimental-context review excluding protected target/phenocopy perturbation evidence? Coefficients would be fitted on permitted WT only. We currently have no approved complete edge list and request clarification of the provenance boundary, not approval of an unseen future network. We will separately document the exact rows and data license before use.

Please specify the permitted task, source/version, use role, exclusions and whether target-specific generic topology is acceptable. This request does NOT seek permission to use held-out expression, nearby protected alleles, equivalent phenocopies, or contaminated checkpoints.

Attachments available locally: PREPARATION_RECEIPT.json, R6_CONDITION_REVIEW.tsv, R6_SHAPE_DESIGN.md, R5_EDGE_ADMISSION.tsv. No message or attachment has been sent.
