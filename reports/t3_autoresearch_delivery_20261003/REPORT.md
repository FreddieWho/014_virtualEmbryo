# T3 autoresearch H5AD交付补齐

已生成可交付 **v0070**，完整 **7449×500**，contract **PASS**，已登记为 `score_pending`。**未提交/未评分**。

- [直接上传的H5AD](../../deliveries/t3_gata4__ar_complex__v0070.h5ad)
- [完整上传包](../../deliveries/t3ar__t3__upload__20261003.zip)，含H5AD及4份必需清单。
- [候选权威索引](../../submissions/INDEX.tsv)，board `T3:gata4`、version `v0070`；身份以该条SHA256为准。
- [检查结果](ACCEPTANCE.json)、[交接记录](HANDOFF.json)、[生成脚本](../../scripts/t3_autoresearch/build_submission.py)。

模型采用上一轮锁定版本，重新使用全部26个已批准条件执行预测，与最终保存的Gata4响应向量在1e-12容差内一致。未重开autoresearch、未根据原val/test继续调参。

父版本是v0009的WT/Gata4-zero载体。预测公式为 `X = max(parent.X + model_delta, 0)`，再将Gata4列置零；原细胞、基因顺序、空间坐标及内部契约保护的WT参考layers/raw保留。**预测位于X，layers/raw是母本参考，不是本次预测。** 没有使用Gata4 KO真值。

这一步是新完成的跨域发射，不能把上一轮来源开发MSE降低20.31%当成该H5AD的目标评分。具体影响已实测记录：输出非零比例0.6220（母本0.1046），新激活1927060个原零条目，截负1385559个下游条目；截负后最大逐基因平均响应偏差为0.241725。这些是输出诊断，不是效果验证。[完整诊断](../../artifacts/t3_autoresearch_delivery_20261003/DIAGNOSTICS.json)。

初始未登记草稿v0069缺少母本layers/raw，内部保护检查FAIL。失败文件与报告保留、未上传；v0070修复参考元数据，已核对X逐值不变。只交付v0070，不覆盖旧评分artifact。

建议：作为锁定模型的探索候选手动上传，并回传总分、各子项、submission ID/截图。服务器现役在回分前保持不变。目标域效果未知，科学限制 `blocks_submission:false`。

决策：D-20261003-T3ARDEL-001。
