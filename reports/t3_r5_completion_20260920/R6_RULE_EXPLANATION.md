# 路线六规则原文与当前处置（2026-09-20）

应纠正上一轮的归因：官网没有要求所有外部Perturb-seq预先获得书面批准，也没有限定只能学shape。书面确认、shape-only是本项目2026-08-29内部保守解释，不能称为主办方原文。当前仍按项目约束执行；不把这次解释当成取消约束。

## 官方规则

来源：https://virtualembryo.ai/challenge/rules ，§10；本日重新下载，正文§10与上次缓存一致。

外部公共数据、预训练模型和公开代码允许使用，前提是使用符合许可并在方法中披露。外部来源必须披露；禁止通过原数据、混合数据集或预训练模型使用held-out实测数据。T3保护对象为E8.75 Gata4及β-catenin KO，且同基因可比阶段其他allele或phenocopy也按held-out处理。通用资源须先去掉受保护部分。

官网对不确定来源的原文为：

> If a source sits near the boundary and you are unsure, ask before submitting.

注意这里是边界不确定时在提交前询问；不是对所有外部数据设置统一书面预审批，更没有要求shape-only。

## 项目内部规则原文

`docs/batch2/03_COMPLIANCE_RULES_SNAPSHOT_20260829.md` §4（64–88行）列出：

> 允许且本包采用的严格解释：
> 通用 Perturb-seq 仅在目标基因和 phenocopy blacklist 全部删除后，用于响应形状而非方向。

随后原文：

> 需要书面确认的部分：
> - 聚合 GRN/pathway 中 target-specific edge 的 provenance 边界；
> - 通用 Perturb-seq 在严格 blacklist 后的使用；
> - T2/T3 对外部 measured data 的广义许可范围。

`docs/batch2/compliance/DATA_FIREWALL_SPEC.md` §3把organizer clearance列为CONDITIONAL来源的permit条件。这是项目自己的执行防火墙，不能反推官网禁止所有尚未回信的来源。

## 对当前数据的具体意义

GSE261783的OP2是8周龄成年小鼠心脏成纤维细胞。它没有因“成年”或“Perturb-seq”而被官方一概禁止，也没有被本次审查证明全部不合规。当前是尚未完成用途和背景审查。

- 已删除目标/固定黑名单、多重或不明确guide，再保守删除Chd4、Smarca4、Yy1。当前4998细胞、23扰动、220明确NTC；500panel均唯一映射。
- 保守删除3项是风险管理，不能说已证实它们是E8.75目标的完全同表型；其他23项也不能因为不在名单就全部PASS。
- 原R6模型学习哪些基因上调/下调，因此不符合项目shape-only限制。新用途门实施的是项目限制，不是新增官方条款。
- CC-BY4.0解决使用许可问题，不能自动证明比赛合规。相反，未取得书面确认也不等于该数据已经被主办方判违规。
- 当前保持QUARANTINE；未标准化、未构图、未训练。可继续逐扰动审查及实现不读取这些数据的代码。确认草稿仍NOT_SENT，未联系主办方。
