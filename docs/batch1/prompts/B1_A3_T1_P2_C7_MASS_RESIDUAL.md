# B1-A3 — T1 P2 + C7：状态质量外推与残差一致性

## 唯一目标

在不训练新动力学模型、不创造新生物学状态原型的前提下，调整 T1 预测群体中各状态的概率质量，并用状态条件 residual bank 保持状态内异质性和基因共表达。由于公开的 E8.5/E9.5 标签词表未 harmonise，本原子先冻结一个 source-only state partition，再生成两个正式 lane；主要优化 P2、P3、P4，对应 MMD/CSS；不把本轮包装成 P1 新生状态方案。

## 输入

自动定位：

1. 当前有效 T1 base submission；
2. E8.5、E9.5 训练表达与 stage 信息；
3. 项目已有 cell state label、frozen latent partition 或固定 cluster assignment；若不存在，使用本原子登记的 source-only partition freeze；
4. 当前 T1 board 的目标 stage；
5. 当前 validator/scorer。

必须复用已有状态划分。若没有跨阶段合法 partition，可在本原子内先执行 source-only partition freeze；不得读取目标阶段、外部 protected 数据或服务器成绩，不得重新训练 embedding 或重新选择聚类数。

### 0. Source-only partition freeze

两个正式 lane 使用同一父版本，但明确登记不同的固定状态规则：

1. `L1_SHARED_UNRESOLVED`：保留两阶段同名状态，其余阶段特有标签统一标记为 `UNRESOLVED_STAGE_SPECIFIC`；不对标签做人工生物学映射。
2. `L2_E95_EXPRESSION_PROBE`：以 E9.5 已有 `celltype` 作为固定词表，用全 T1 panel 的 cosine expression centroid 将 E8.5 投影到该词表；E9.5 自身 assignment 保持原标签。

每条 lane 必须保存 assignment 覆盖率、输入 SHA256、规则/centroid hash 和 partition hash。两个 lane 都是正式候选，不是只读对照。

## 最小算法

### 1. 状态质量趋势

对每个状态 c：

1. 从 E8.5/E9.5 计算平滑比例 `p_c(t)`，使用统一 pseudocount；
2. 计算 log-ratio growth：
   `g_c = [log(p_c(t1)+eps)-log(p_c(t0)+eps)]/(t1-t0)`；
3. 将小状态的 `g_c` 向全局中位 growth 收缩，权重仅由该状态训练细胞数解析决定；收缩强度使用“状态中位细胞数”作为固定经验贝叶斯尺度，不做搜索；
4. 将 growth 截断到全部状态观测 growth 的 5%-95% 范围，防止两个快照造成爆炸；
5. 外推目标状态质量：
   `p_c(t*) ∝ p_c(t1) * exp(g_c_shrunk * (t*-t1))`，最后归一化。

状态只在 E9.5 出现时，视为 emerging state，允许正 growth；只在 E8.5 出现而 E9.5 消失时，保留极小 floor，不强行复活。

### 2. 基于 base prediction 做重采样

- 先给 base prediction 的每个细胞分配已有状态；
- 总细胞数保持 base 不变，因为当前评分不要求精确 n_pred=n_true；
- 按目标 `p_c(t*)` 分配每个状态的目标 cell count；
- 状态内优先无放回抽样；不足时才使用 residual bank 生成补充细胞。

### 3. residual bank

对每个状态：

1. 从 base 或 E9.5 计算状态均值与细胞 residual；
2. 新细胞 = base 预测的状态均值 + 从同状态 residual bank 抽取的完整 residual 向量；
3. 不逐基因独立采样；完整 residual 向量整体重放，以保护 P3/P4；
4. 负值截断为 0；
5. 状态均值必须与 base 中该状态均值近似相同，因此本原子不另行优化 E1/E2。

## 只允许的检查

1. 检查重采样后的状态比例是否达到解析目标；
2. 检查每个状态 pseudobulk 与 base 的偏差接近 0；
3. 检查同状态 residual covariance/variogram 与来源 bank 的差异；
4. 每条 lane 完整候选和最终 scorer 各一次。

## 验收

- contract 通过；
- 输出总细胞数与 base 相同；
- 目标状态比例写入 `state_mass_forecast.tsv`；
- 每状态均值基本不变，变化主要来自 state mass；
- CSS 不因逐基因独立噪声而恶化；
- 两条 lane 各完成一次官方评分；
- 输出 prediction、mass forecast、residual bank manifest、指标、MANIFEST、RESULT。

即使某条 lane 的 MMD 未改善，也要交付该 lane 的有效文件并标记 `recommend_submit=false`；不得在同一原子内加入 open-set 新生状态、OT、ODE 或 flow。

## 禁止

- 禁止重新聚类；
- 禁止手工修改某个状态比例以追榜；
- 禁止生成训练集合之外的新状态；
- 禁止未登记的临时标签 crosswalk 或 silent raw-label fallback；
- 禁止逐基因高斯噪声；
- 禁止改变 base 的状态内均值模型；
- 禁止自动线上提交。
