# B4-T2-R3-HEART-EXTRAP-EXPRESSION-CAL

## 唯一目标

在 T2 最弱的 heart extrapolation board 上，只校准表达外推；冻结 geometry、scale、coordinates 和 expression-coordinate assignment。

当前几何外推路线没有正证据，不能据此关闭表达外推。

## Parent

- current board best 50.5；
- E8.75 / E9.5 training heart；
- parent geometry exact。

解析 parent 的 baseline expression rule，确认是否等于 strict per-celltype pseudobulk shift `damp=1.0`。

## 共用 shift

\[
\Delta_c=\mu_{E9.5,c}-\mu_{E8.75,c}
\]

shared state 使用自身 delta；未共享保持 parent。

## 三条 lane

### L1_DAMP050

\[
X'=X_{E9.5}+0.5\Delta_c
\]

目的：保护 floor，测试 baseline overshoot。

### L2_TIME1333

目标 E10.5 距 E9.5 为 1.0 天，训练间隔 E8.75→E9.5 为 0.75 天：

\[
damp=1/0.75=1.333333
\]

目的：测试旧 baseline 是否漏掉时间间隔归一。

### L3_POPMIX050

population mixture：

```text
50% copy-last E9.5
50% current pseudobulk-shift parent
```

不逐基因平均。

## 不允许

- 改 coordinate；
- 再跑 pycpd / spateo；
- 改 RMS；
- 调 state mass；
- 新增外部 late stage；
- 扫更多 damp；
- 使用服务器差分求真实时间速度。

## Source-only backtest

在可用 heart ladder上模拟：

- 用 E8.25→E8.75 预测 E9.5；
- 或其他不触及 held-out 的 source-only setup。

记录而不作为严格服务器预测。

## 输出

```text
candidates/T2_heart_val_extrap/L1_DAMP050/submission.h5ad
candidates/T2_heart_val_extrap/L2_TIME1333/submission.h5ad
candidates/T2_heart_val_extrap/L3_POPMIX050/submission.h5ad
```

protected checks 要求 coordinates / geometry exact。

完成后停止。
