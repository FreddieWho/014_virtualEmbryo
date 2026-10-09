# Detection-odds source/operator test: negative result

Direct embryo-level KO/WT detection-log-odds transfer scored 73.8634 against exact v88 74.7376 on the frozen seven-genotype, three-seed full-panel source comparison (delta -0.8741). All seven genotypes and all five components were worse. Scrambled response scored 60.9579 and WT identity 49.0333. No portal candidate was frozen or uploaded; no version or submission quota was consumed.

This is a new source/operator combination, not a new mechanism: older adult-source rounds already included logit decoders. The exact positive-expression response, state composition, support and atlas are unchanged from v88. The local five-metric calibration is distinct from the server calibration and is not a server-score forecast.

Reproduction: use the pinned T3 environment, the restored v88 source archive and scripts/t3_quota_20261009/odds_frozen.py with --route odds --out a fresh output directory. The original source hash matches the run receipt. ODDS_GUARD_AUDIT.json validates every frozen calibration anchor and exact baseline metrics (maximum absolute difference 0.0). Later campaign.py adds fail-closed cache refusal and guard assertions without changing numerical computation.

Source details and limitations: SOURCE_LEDGER.json. Full input archive: t3_v0088_scored_repro_20261008.zip, SHA256 a6598b7a30a18a7943776adcefd1c55e995cf350ee5d1548e7597d3b861c8308. No protected Gata4/Ctnnb1 outcomes, other target alleles/phenocopies, forced target zeroing or score inversion were used.
