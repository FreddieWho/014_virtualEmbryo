# R6 shape-only 后继分支设计（未训练）

原 signed R6 保留、禁止凭shape-only许可运行。本设计不是对历史实验的追认。

- 目标：每个允许源扰动的500基因均值相对同sample显式NTC的差值，取绝对值并按行L2归一化；零行保留零。绝对值转换后不把原signed delta保存在训练包。禁止把源符号或幅度重新注入特征、embedding、图、权重或选模指标。
- 先按完整perturbation gene划分训练/验证；图/embedding仅WT或获批ontology信息。特征标准化只用训练gene，严禁用验证响应构图。
- 在相同split比较均匀shape、ridge、两层GCN。阈值继承20个扰动/每个20cells；选择指标为unsigned shape MSE，不能沿用signed delta MSE解释结果。
- 预测只提供非负shape权重。方向与总幅度必须由已合规的WT-only估计提供；来源响应不能确定方向。需要显式无shape父版本作对照，零权重/零幅度退回父版本。
- 完整集成前必须固定父artifact、尺度、split、图来源、随机种子及clip门并新建design快照；不得覆盖configs/t3_next/design.json历史设计。
- 已实现 unsigned_response_shape 基础转换和符号/幅度不变性检查；标准化、图、训练、目标推断、候选与服务器评分均未执行。不得把基础组件称为完整路线实现。
