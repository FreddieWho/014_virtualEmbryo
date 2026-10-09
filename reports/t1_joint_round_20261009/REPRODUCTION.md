# Reproduction boundaries

The scored H5AD hashes are fixed in submissions/INDEX.tsv. Use those bytes for
exact artifact comparisons. Never overwrite them while fixing documentation.

Code under scripts/t1_joint_round_20261009 includes the frozen integer-rank
operator, source audit, two builders, aggregate diagnostics and minimal-input
v0095 replay. Public runner paths use T1_RECOVERY_ROOT, default t1_recovery_run,
rather than machine-specific directories. The operator itself is byte-identical
to the frozen code; CODE_PROVENANCE.json distinguishes path-configurable exports
from original executed scripts. Syntax checks are rerun after restoration; no
models or scientific experiments are rerun.

v0094 construction used Python3.12.14/numpy1.26.4/scipy1.13.1/anndata0.11.4.
v0095 source/build runtime used Python3.12.14/numpy2.3.5/scipy1.18.1/
scikit-learn1.8.0/anndata0.13.4. Integer rank arithmetic and independent replay
checks avoid introducing runtime-dependent tie differences. These runtimes
are intentionally not described as identical.

The common reconstructed parent has expression SHA256
9974267e6e8ecf114ef1668ab16f297b266bebfb331042ae89771d9de8ee3074
and H5AD SHA256
65270f9782e4fa7111a56cc35658aa67db5300b3de55fd54f77eafbe425577dd.
It is not historical scored v0092. Six archived carrier ancestor digests
match exactly; the recovered v0051 expression matches only the available
historical prefix541d0aa6 because no full historical reference digest exists.

Custom reconstruction helpers are under scripts/t1_recovery_20261009. They
reuse existing repository t1_five/t1_round2/t1_three/t1_seven and t1ext modules;
those existing and third-party sources are not duplicated. Full runs require
the released official inputs and selected external source inputs. The original
recovery staging layout under T1_RECOVERY_ROOT is retained by the helpers;
external-preprocessing modules must be configured for that input root before
fitting. A fresh-path H5AD can differ in metadata bytes even when expression
replay is exact, so preserve original scored files for identity.

No raw expression files, per-cell source mappings, donor barcodes, selection
indices, whole leaderboard snapshots, private Library identifiers or runtime
filesystem paths are published in this recovery overlay. Aggregate cell counts,
checksums and scientific source roles are retained.
