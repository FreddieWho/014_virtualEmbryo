# T1-SIX 六路线批次（2026-10-07）

用户 /goal 授权：3 条既有路线优化/结合（混合只作载体带新组件）＋ 3 条全新路线（本轮检索优先）。

## 路线

| 类别 | lane | 机制 |
|---|---|---|
| 优化/结合 | `ocovstab` | n2covot 升级：投影距离可靠性自适应强度（稳定 0.5/不稳定 0.125）+ k=8 近邻软化选择 |
| 优化/结合 | `osoftcov` | f1soft 软责任 × n2covot 结合：软责任联合权重 + 协方差输运重选 |
| 优化/结合 | `ostabmix` | f2stable 稳定性 × s2mix 结合：per-type 自适应 best/backup 混合比例（0.7/0.3 两级规则） |
| 全新 | `nwasser` | 精确 OT 计划位移场（POT ot.emd）+ k=8 近邻外推放置 |
| 全新 | `nconf` | split-conformal donor 半径校准（α=0.1，fit 半拟合、校准半打分） |
| 全新 | `nbidir` | 前向/后向计划一致性权重（CellRank 双向谱系，替换分类器权重） |

设计冻结：`configs/t1_six/design_20261007.json`；设计文档：`reports/T1_SIX_DESIGN_20261007.md`。

## 执行

```bash
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_six.run prepare --run-dir artifacts/t1_six/T1-SIX-20261007-v1/prepare
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_six.batch
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m pytest tests/t1_six/ -q
LD_LIBRARY_PATH=/opt/anaconda3/lib python -m scripts.t1_six.validate --root artifacts/t1_six/T1-SIX-20261007-v1 --report reports/t1_six_20261007 --zip deliveries/t1six__t1__upload__20261007.zip
```

## 结构

- `common.py`：Context（输入锁定、字节级 SHA、contract、INDEX 串行登记、score_pending）
- `ops.py`：新算子（exact_plan/plan_fields/consistency_distances/stability_fractions/adaptive_sides/covot_reselect_soft/conformal_radius/conformal_reselect/consistency_logw）
- `models.py`：6 lane fit/predict 调度（骨架 = 冻结 r2joint mass 库 + 密度分类器权重 + 组合分配 + SVD-32 潜形）
- `run.py`：prepare（父重建审计 + 计划缓存 + 同环境参照重评）/ score / execute（report + final 双 scope，final 模型重放）
- `validate.py`：独立进程重放 + 逐 lane 验收 + zip 打包（MANIFEST/UPLOAD_MANIFEST/RUN_ID_MAP/EVIDENCE 指针）
- `batch.py`：双 worker 子进程，持久 receipt

复用（只读）：`artifacts/t1_three/T1-THREE-20260929-v1`（r2joint/r3mix 冻结模型）、`artifacts/t1_seven/T1-SEVEN-20260930-v1`（n2covot 产物与投影距离）、`third_party/veckit`（scorer）、`docs/batch3/interfaces`（contract IO）。
