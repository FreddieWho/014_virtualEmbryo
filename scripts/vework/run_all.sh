#!/usr/bin/env bash
# Rebuild every candidate in /workspace/ve/submit from released stages (box-local). One heavy job at a time.
# For the 2026-10-20 retrain, change only the stage:time arguments / --target / --n (board max cells or ref cells).
set -euo pipefail
cd /workspace/ve; PY=venv/bin/python; S=submit
$PY vework/t2_recipes.py interp --board T2:embryo:val_interp --left E7.25:7.25 --right E8.0:8.0 --target 7.5 --n 5000 --geometry logrms --out $S/T2_embryo_val_interp__E1_bridgeC2_logrms.h5ad
$PY vework/t2_recipes.py interp --board T2:embryo:val_interp --left E7.25:7.25 --right E8.0:8.0 --target 7.5 --n 5000 --geometry aniso --zero-preserve --out $S/T2_embryo_val_interp__E2_bridgeC2_aniso_zp.h5ad
$PY vework/t2_recipes.py interp --board T2:heart:val_interp --left E8.25_late:8.25 --right E8.75:8.75 --target 8.5 --n 5872 --geometry aniso --out $S/T2_heart_val_interp__H1_bridgeC2_aniso.h5ad
$PY vework/t2_recipes.py interp --board T2:heart:val_interp --left E8.25_late:8.25 --right E8.75:8.75 --target 8.5 --n 5872 --geometry aniso --zero-preserve --out $S/T2_heart_val_interp__H2_bridgeC2_aniso_zp.h5ad
$PY vework/t2_recipes.py extrap --board T2:heart:val_extrap --prev E8.75:8.75 --last E9.5:9.5 --target 10.5 --n 25179 --damp 0.9 --out $S/T2_heart_val_extrap__X1_median09_libpreserve.h5ad
$PY vework/t3_build.py --pbmatch --gata4-zero mesp1 --gata6-factor 0.5 --out $S/T3_gata4__A_pbmatch_gata4mesp1_gata6half.h5ad
$PY vework/t3_build.py --pbmatch --gata4-zero all --gata6-factor 1.0 --out $S/T3_gata4__B_pbmatch_gata4all.h5ad
$PY vework/t1_recipe.py --method copy_last --out $S/T1_val__F_copy_last_E9.5.h5ad
$PY vework/t1_recipe.py --method shift --w 0.5 --damp 0.5 --timescale linear --out $S/T1_val__S_shrunk_shift_w05_d05_lib.h5ad
