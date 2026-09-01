# 工具链与环境隔离方案

## 1. 不在一个环境里安装所有东西

建议四个环境：

| 环境 | 用途 | 主要依赖 |
|---|---|---|
| `ve-core` | scorer、AnnData contract、最终 candidate builder | Python、anndata、scanpy、numpy、scipy、pandas、h5py |
| `ve-t1-ot` | coupling、UOT、decoder adapter | moscot、POT；WOT fallback；R/scDesign3 可独立子环境 |
| `ve-t2-geometry` | shape field、point-cloud proxy | pycpd、POT、GeomLoss；Spateo 单独锁版本 |
| `ve-t3-prior` | prior committee | decoupler/CollecTRI、OmniPath client、CellOracle、Pertpy/CINEMA-OT；scTenifoldKnk 可用 R 子环境 |

外部环境只写标准中间件，最终 H5AD 统一由 `ve-core` 写。

## 2. 版本策略

本包不硬编码可能已变化的版本号。P0 必须：

1. 优先记录仓库已有 lock；
2. 若无 lock，在隔离环境中安装可运行版本；
3. 记录精确版本、Python/R 版本、平台、commit 和安装命令；
4. 运行最小 smoke test；
5. 将结果写入 `TOOLCHAIN_LOCK.json`；
6. 后续 task 不再自动升级。

## 3. 工具角色与 fallback

| 能力 | 首选 | 预声明 fallback | 不允许的临时替换 |
|---|---|---|---|
| T1 temporal coupling | moscot `TemporalProblem` | Waddington-OT 或 POT 手工 OT | 临时写完整 ODE/SDE |
| T1 UOT/state mass | moscot/POT | 解析 state transition + shrinkage | 把绝对细胞数当真值 |
| T1 residual decoder | empirical residual bank | module-wise scDesign3；反向亦可作为另一 lane | 全 32k gene copula 暴跑 |
| T2 low-cost field | pycpd | 无；该 lane 若失败则 blocker | 随机换另一 registration 包 |
| T2 domain field | Spateo | pycpd lane仍独立完成 | 用绝对 atlas coordinate 拟合 |
| T2 geometry loss | POT/GeomLoss | NumPy internal-distance proxy | 用坐标 MSE 作为主目标 |
| T3 TF prior | CollecTRI + CellOracle | scTenifoldKnk 作为独立票，不是替代全部 | 单独 Spearman correlation |
| T3 signaling prior | OmniPath | 审计后的 directed pathway graph | TF-only 推 β-catenin |
| T3 response shape | CINEMA-OT/Pertpy | 训练 KO 的解析 sparsity/scale 统计 | 复制 Mab21l2 方向 |

## 4. 每个工具的 smoke test

### moscot/POT

- 小型 20×30 cost matrix 可求 coupling；
- coupling 非负、质量和可解释；
- sparse artifact 可序列化并由 core 读取。

### scDesign3

- 在小型 `state × 50 genes` 数据上完成边缘拟合/采样；
- 输出基因顺序与输入一致；
- 记录 R sessionInfo；
- 不进行全 panel copula smoke test。

### pycpd

- 合成点云刚体/非刚体形变可恢复方向；
- 输出 displacement 与 landmark 索引一致；
- 形变后可重新锁定 RMS。

### Spateo

- 可读取当前空间对象转换后的最小数据；
- 只验证需要的 alignment/vector-field API；
- 不以完整 tutorial 能运行作为准入标准。

### CellOracle/scTenifoldKnk

- 在小型 WT 子集或 synthetic network 上完成 virtual KO；
- sign 定义经已知 toy network 验证；
- 输出标准 vote table，而不是只保存图。

### CollecTRI/OmniPath

- 每条 edge 保留 source、sign、direction、provenance；
- unresolved provenance 不进入 strict lane；
- gene ID 可映射到官方 panel。

### CINEMA-OT

- 能从 observed control/KO 输出个体 effect 或响应模块；
- 只抽取 sparsity、heterogeneity、severity shape；
- 不把训练 KO 的 gene direction写入 target prior。

## 5. 资源控制

- T1 coupling 优先在 state/program latent 或 centroid 上求解；避免细胞×细胞全矩阵失控；
- T2 先用 landmarks 拟合 field，再传播到全点云；
- T3 各 state 独立/分批构建 GRN，记录最小细胞数门槛；
- GPU 不是默认前提。只有工具文档和 profiling 证明 CPU 构成硬阻塞时，才提出 GPU 申请；
- 不因工具安装困难把研究级模型改成默认 backbone。
