# Boundary questions to organizers — DRAFT (not sent)

- To: virtual.embryo.moonshot@gmail.com
- Date drafted: 2026-10-01 (agent-drafted, user to review and send; agent has no sending capability)
- Context: Virtual Embryo Challenge, Task 3 (Gata4 KO @ E8.75). Rule cited: §10 "held-out = Gata4/β-catenin KO @ E8.75; same-gene other alleles at comparable stage and phenocopies prohibited; everything else fair game; ask before submitting when unsure."

---

Subject: Task 3 data-boundary questions (Gata4 KO @ E8.75)

Dear organizers,

We are working on Task 3 (Gata4 KO @ E8.75) and want to confirm three data-boundary questions before submitting. We have kept all potentially affected data isolated and have not used any of it for training.

1. Same-gene perturbations at other stages. Is Gata4 perturbation data from non-held-out stages usable — e.g. Gata4 @ E9.5 heart (GSE5298/GSE9652) and Gata4 @ E14.5? In other words, does "comparable stage" cover other embryonic heart stages, or only stages near E8.75?

2. Pathway-member knockouts. Are perturbation data for pathway members / cofactors other than Gata4 itself usable — e.g. Tbx5, Nkx2-5, Gata6 knockouts? These are not the same gene, and we would use them only as source-domain supervision, never as target truth.

3. WT binding data. Is wild-type GATA4 ChIP binding data (no perturbation response, e.g. GSE52123, E12.5 heart WT) usable as prior topology? It contains no KO response signal.

Thank you for clarifying. We will proceed only per your answers.

Best regards,
[team name / captain]
