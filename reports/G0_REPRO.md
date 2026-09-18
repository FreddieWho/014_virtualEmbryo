# G0 统一交付 — 复现与重测说明（2026-09-16）

## 上传包（deliveries/，成员字节已校验 = 源文件）
- `g0t1__t1__upload__20260916.zip`（7 全覆盖）：v0015–v0021（推荐先传 v0021 + v0018；v0015 持平可选，v0016/v0017 退化 lane 可跳过）
- `g0t3__t3__upload__20260916.zip`（5 全覆盖）：v0013–v0017（推荐先传 v0016 + v0017）
- `g0t2__t2__upload__20260916.zip`（6 全覆盖）：v0011–v0016（推荐先传 v0016 + v0015；v0011 负向、v0013 持平、v0014 与 v0012 同分可跳过）
- 记账诚实声明：15 locked runs，其中 T2-R1 为门控轮（无新候选，只有 proxy 切片 + 旧 lane 校准）；T1-R5/T2-R4 为一轮多 lane 扫参。故 15 runs → 18 candidates，均在包内。
- 每包内 MANIFEST.tsv（成员/源路径/SHA256/字节数）。Portal Model 列显示 zip 名，身份以 SHA256 与 INDEX 为准。

## 本地重测（任一候选，同口径复算）
```bash
# T1: --task T1 --input <cand> --target data/E9.5_RNA.h5ad --reference data/E8.5_RNA.h5ad
# T2-heart: --task T2 --setting heart --input <cand> \
#   --target artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_target_e95_cardiac.h5ad \
#   --reference artifacts/g0/G1-T2-R1-EXTRAP-GATE-20260916-v1/intermediates/proxy_ref_e875_cardiac.h5ad
# T3: --task T3 --input <cand> --target data/E9.5_mab21l2_ko.h5ad --wt data/E9.5.h5ad
LD_LIBRARY_PATH=/opt/anaconda3/lib PYTHONPATH=third_party/veckit \
python third_party/veckit/score_h5ad.py --seed 20260916 --out /tmp/x.json ...
```

## 各轮复跑（确定性，同种子同线程复现）
- T1-R1：`scripts/g0/t1_r1_neural_ode.py --run-dir <newdir>`（torch 线程 16，~20min）
- T1-R2/R3/R4/R5：`t1_r2_substate.py / t1_r3_maturity.py / t1_r4_shrink.py [--shrink-c C --lane L --out-version V]`
- T3-R1..R5：`t3_r1_directprop.py / t3_r2_gradeddose.py / t3_r3_lineagedose.py / t3_r4_combo.py / t3_r5_amp2.py`
- T2-R1（门控）：`t2_r1_extrap_gate.py`；R2/R3/R4/R5：`t2_r2_shrink.py [--shrink-c] / t2_r3_spatial.py [--knn-k K --lane L --out-version V]`
- 每轮目录 `artifacts/g0/<RUN>/RESULT.json`（门结论/sha/复跑断言）+ `RESULT.md`（诊断）。

## 证据链
- 候选与 SHA：`submissions/INDEX.tsv`（G1- 前缀行，score_pending，上传后回填分数）
- 本地分：`reports/G0_LOCAL_SCORE_TABLE.tsv` + `reports/G0_RESEARCH_BRIEF.md`（基线/口径/短名单）
- 服务器分数：用户统一上传后回填（INDEX/registry/SUBMETRIC 按立规）
