# T2 goal轮执行报告（2026-10-01，goal mupdz021-pfttwg）

设计冻结：`reports/T2_GOAL_DESIGN_20261001.md` + `configs/t2_goal/design_20261001.json`
（SHA `4303ece7…`）。实现 `scripts/t2_goal/`（新建；复用 t2_round2 common/ops 只读）。
目标：三board各两轮（R1新路线 + R2旧优化），合打一包。

## 候选一览

| lane | board | 版本 | parent | contract | 备注 |
|---|---|---|---|---|---|
| e_r1_compotrend | embryo_interp | v0016 | v0014 | pass_with_deviation | 趋势份额×现役表达；18/33三阶段类型命中；组成lane四类豁免（预声明） |
| h_r1_compotrend | heart_interp | v0021 | v0019 | pass_with_deviation | 同上；33/33三阶段类型命中 |
| x_r1_lateref | heart_extrap | v0022 | v0001 | pass | E8.25late锚定基线；行/几何与父一致 |
| e_r2_shrinkc1 | embryo_interp | v0017 | v0014管线 | pass | C=1.0；行计划与v0014逐名一致；mean_w 0.557 |
| h_r2_shrinkc1 | heart_interp | v0022 | v0019管线 | pass | C=1.0；行计划与v0019逐名一致；mean_w 0.692；clip 0.58已披露 |
| x_r2_shrinkc1 | heart_extrap | v0023 | v0001 | pass | C=1.0 float32路；行/几何与父一致 |

## 轻微/严重判定（goal约定）

- 无contract FAIL → 无严重落后，无判废重开，6条全部提交（计6轮）。
- embryo两条工程门var比出界：根因为分母≈0基因（ref_var=0），现役v0014自身同数量级
  出界（lo 3/hi 28；e_r2与现役逐项一致，e_r1 hi 28一致、lo 14为重采样效应）。
  判轻微，如实记录，不拦截。
- h_r2 clip 0.58：v0013先例60% clip仍胜，披露不否决。

## 确定性重放

6/6 字节一致（`replay` 子命令，tmp重建比对SHA；证据 `checks/replay.json`）。

## 实现修正记录

1. `dedup_names_pool`：现役池已含`__dupK`名，旧去重会碰撞；改为输出内去重
   （首现保留裸名）。回归测试 `tests/test_t2_goal.py` 5项通过。
2. contract判定：验证器返回键为`status`/`valid`，组成lane四类偏差按冻结豁免判
   `pass_with_deviation`（与R2 x_n3先例一致）。
3. replay harness临时目录路径 relativize 修复（仅harness，不影响候选字节）。

## 交付

- `submissions/INDEX.tsv` 6行（score_pending）；上传包
  `deliveries/t2goal__t2__upload__20261001.zip`（6成员 + 四件套，SHA/CRC校验）。
- 服务器回分前best不变；blocks_submission:false。
