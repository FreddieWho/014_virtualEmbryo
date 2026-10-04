# T2 goal轮：三board ×（R1新路线 + R2旧优化）（执行前冻结）

用户授权（goal mupdz021-pfttwg）：T2三个board各两轮，R1新路线探索、R2旧路线优化；现役起步
（embryo v0014/62.89、interp v0019/62.36、extrap baseline v0001/50.53）；R1轻微判负照常提交、
严重落后判废重开（只有完成提交的才计轮次）；三board合打一个zip。

本文件在任何训练/构建运行之前冻结；参数同时落盘 `configs/t2_goal/design_20261001.json`。

## 版本号（各board独立命名空间，无碰撞）

| board | R1新路线 | R2旧优化 |
|---|---|---|
| embryo_interp | v0016 `e_r1_compotrend` | v0017 `e_r2_shrinkc1` |
| heart_interp | v0021 `h_r1_compotrend` | v0022 `h_r2_shrinkc1` |
| heart_extrap | v0022 `x_r1_lateref` | v0023 `x_r2_shrinkc1` |

## 冻结路线定义

记号：`pP` = 现役组成份额；`mass` = largest-remainder + 缺额按余数补（`common.counts_from_raw`），
行选择 `common.select_rows` 同机确定性。

### R1新路线（均未提交过）

1. **e_r1_compotrend**：表达与几何 = v0014 逐行一致；行从 v0014 池重采样，
   份额 = 三阶段（E6.75/E7.25/E8.0，t=6.75/7.25/8.0）`share_series_predict`（log空间线性，
   非二次）外推 t=7.5；任一阶段缺失的类型沿用 v0014 份额；归一后计数；seed=20261001 冻结。
   新点：趋势份额 × 现役表达（以往mass均配新位移）。
2. **h_r1_compotrend**：同机制，池 = v0019，三阶段 E8.25late/E8.75/E9.5 → t=8.5，
   seed=20261001。与 h_n2（二次Lagrange + v0013表达）不同：线性趋势 + 现役表达。
3. **x_r1_lateref**：E8.25late锚定基线：Δ = μ95 − μ825late（共享类型，否则0，与baseline同约定），
   施加于 v0001 全行；几何/组成/行选择与 v0001 一致。单冻结参照替换，无搜索。

### R2旧路线优化（单冻结变体，非扫描）

4. **e_r2_shrinkc1**：v0014管线（v0002池 + v0010/v0014行计划逐名一致断言）仅把t收缩常数
   C=2.0 → C=1.0（`ops.shrink_weights` float64路）。依据：T1上C=1胜C=2（48.54 vs 48.48）。
5. **h_r2_shrinkc1**：同上，池 = v0009，行计划 = v0019，C=1.0。
6. **x_r2_shrinkc1**：baseline Δ × t收缩 C=1.0（镜像 `shrunk_delta_f32` float32路，
   仅C不同）；行/几何同 v0001。

## 不重开（沿用R2关闭清单）

空间平滑、FGW微调、幅度族、表达↔坐标重排、moscot/spateo/大模型、追occ/d2、网格搜索、
本地proxy作晋级结论。本地评价一律record-only，不否决、不宣称。

## 数据、工程与门（沿用R2）

- 输入均为已批准官方数据；target_used=false；不读E7.5/E8.5/E10.5真值。
- 父artifact只读SHA锁：v0014 `1ea0c696…`（待核）、v0019 `d84de174…`（待核）、v0001 `f30beba6…`；
  桥池 v0002 `392c470e…`、v0009 `4f2e7552…`。构建时逐位核对，不一致则停。
- 工程门：library比q01≥0.25/q99≤4；方差比0.1–10；X有限非负；n_obs/panel精确；
  组成lane（R1两条）按R2既有四类FAIL_BY_DESIGN_ACCEPTED逐项豁免并披露，其余lane几何/
  obs/var/layers与父逐位一致。
- 每lane独立确定性重放（同config同seed字节一致）；contract走
  `virtual_embryo_tools.contract_io.validate_h5ad_case`。
- 定向测试：趋势份额非负归一+计数守恒、新seed确定性、lateref孤儿零位移、C=1权重界
  （w∈[0,1]且单调）、组成lane不行外来行、小端到端smoke。
- 每lane ≤4 CPU小时、≤64GB。

## 交付与完成标准

- 6候选构建、contract PASS（或预声明豁免）、重放PASS、INDEX逐行score_pending。
- `docs/coordination/T2_TRACKING.md`变更摘要；DECISIONS追加并同步根索引；
  `reports/LANE_VERDICTS.tsv`登记。
- 单一zip `deliveries/t2goal__t2__upload__20261001.zip`：6成员短名（全小写≤50字符）+
  MANIFEST/UPLOAD_MANIFEST/RUN_ID_MAP/EVIDENCE四件套；成员SHA/CRC校验。
- 报告 `reports/t2_goal_20261001/REPORT.md`；blocks_submission:false；
  服务器回分前best不变。
