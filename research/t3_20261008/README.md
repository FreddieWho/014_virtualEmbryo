# T3 source reconstruction and developmental response, 2026-10-08

This code/evidence release preserves the measured sequence: reconstructed v0084 49.55; v0086 49.34 rejected; seven-KO generic state response v0087 53.42; conditional-only v0088 53.69 selected. Official scores belong in the repository's canonical score registry; this narrative is not another registry. No new experiment or competition submission was performed for publication.

Seven unrelated embryonic KOs supported a generic developmental response more strongly than gene-identity priors. The major v0084→v0087 server gain is severity, not evidence that Gata4's causal response was identified. v0088 adds conditional zero activation; residual-only and combined arms were rejected by the frozen source test. Conditional-only improved all seven source held-out genotypes (+0.3253 local mean), while residual-only −0.4458 and combined −0.0891 failed. These local metrics are not server forecasts. Source cohorts, stages, chemistry, sex, technical partitions, and adaptive Mab reuse remain limitations.

## Start here

- REPRODUCTION.md: executable read-only replay/tests, omitted inputs and rebuild limits
- SOURCES_AND_PERMISSIONS.md: public source links, source licences versus competition permission
- snapshots/v0083_v0085: original-ID reconstruction, source filtering, validation repairs, recorded replay and source-ranking controls
- snapshots/cpu_20261008 and snapshots/v0086_identity: rejected PSB reconstruction history (early provisional names are historical, not current v87/v88 identities)
- snapshots/v0087: three/seven-KO contrasts, hurdle v1 negative history and v2 repair, embryo/sex controls, shuffled/null controls, frozen protocols and deployment diagnostics
- snapshots/v0088: frozen four-arm emitter, raw/calibrated component metrics, source selection and reconstruction checks
- snapshots/v0088_audit: independent diagnostic audit and test code
- verification: publication-time synthetic tests and read-only exact cached inference

All archived Python files retain their original bytes. SNAPSHOT_INVENTORY.json records original and published hashes; PUBLICATION_REDACTIONS.json identifies seven sanitized evidence files. Frozen protocol/code hashes refer to their historical named files, not new wrappers. Absolute paths in historical scripts describe original execution only. Archived README, SHA256SUMS, MANIFEST and pack receipts refer to fuller original packets and omitted data; they are not valid inventory claims for this public subset. Use SNAPSHOT_INVENTORY.json and portable/test_lightweight.py for this tree's integrity.

No H5ADs, datasets, model binaries, source caches, upload ZIPs, credentials, account links or private recovery dependencies are included. More than one historical snapshot of similarly named code is intentional; do not overwrite existing repository modules with these incompatible versions.

This narrowed release also omits the duplicated historical coordination-policy snapshot; see EXCLUDED_COORDINATION_SNAPSHOT.json. Existing repository policy is not changed.
