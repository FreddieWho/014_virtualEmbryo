# Ready-to-send organiser query

**Subject:** Clarification on task-scoped external data and prior-knowledge use

Hello Virtual Embryo Challenge organisers,

We are preparing an externally pretrained method and want to confirm the compliance boundary before submitting. We will disclose every source, retain raw and filtered manifests, and remove protected samples before any training or representation learning.

Could you please clarify three points?

1. **External measured data for Tasks 2 and 3.** The Official Rules broadly allow external public data, while the Data page says Task 1 “additionally permits” external public single-cell data. May external measured scRNA/spatial data be used for Tasks 2 or 3 when it lies strictly outside the applicable protected stage/genotype windows and is fully disclosed? For Task 2 heart extrapolation, does the explicit “after E13.5 may be used” relaxation apply, or is it Task-1-specific?

2. **WT target-gene binding and curated prior knowledge for Task 3.** May we use WT GATA4 ChIP-seq from E12.5 mouse heart, plus curated GRN/pathway resources such as CollecTRI, OmniPath, Reactome and Gene Ontology, provided that no Gata4/Gata6/β-catenin mutant or comparable-stage target perturbation data are used, and every edge/resource is disclosed? The ChIP data would be used only for target directness, not as a measured knockout response.

3. **Generic Perturb-seq pretraining.** May we pretrain only a generic response-shape module (sparsity, standardized magnitude and heterogeneity) on non-embryonic public Perturb-seq after removing GATA4, GATA6, CTNNB1, MESP1, canonical-WNT and cardiac-lineage perturbations and any plausible phenocopies? Target-specific direction would come from separate WT/knowledge sources, not from the Perturb-seq corpus.

We would appreciate a written answer that we can retain with our method disclosure. We will not activate the ambiguous routes before clarification.

Best regards,

[Team name / captain]
