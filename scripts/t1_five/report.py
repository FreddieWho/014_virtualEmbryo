"""Write one consolidated closeout only after complete execution and delivery audit."""
import json
from pathlib import Path
import numpy as np
from .common import ROOT,dump


def main():
    report=ROOT/'reports/t1_five_20260927';root=ROOT/'artifacts/t1_five/T1-FIVE-20260927-v1'
    validation=json.loads((report/'VALIDATION.json').read_text());assert validation['status']=='PASS' and validation['routes_executed']==5 and validation['full_panel_scorers']==5
    lanes=['n1density','n2param','n3borrow','o1mass','o2rate']
    names={'n1density':'新1：类型内整细胞密度重加权','n2param':'新2：零质量/阳性参数化分布映射','n3borrow':'新3：晚期特有类型的变化迁移','o1mass':'优化1：R1显式零质量与阳性分位数外推','o2rate':'优化2：R2非负倍率残差decoder'}
    results={s:json.loads((root/s/'RESULT.json').read_text()) for s in lanes}
    evals={s:json.loads((root/s/'EVALUATION.json').read_text()) for s in lanes}
    checks={s:json.loads((root/s/'CHECKS.json').read_text()) for s in lanes}
    candidate={s:results[s]['candidates'][0]['version'] if results[s]['candidates'] else '无候选（见工程门）' for s in lanes}
    audit={r['lane']:r for r in validation['routes']}
    def metrics_row(label,m):
        return '| '+label+' | '+' | '.join(str(m[k]) for k in ['de_score','de_direction','energy_distance','mmd_u','variogram'])+' |'
    lines=['# T1：三条新路线与两条既有优化交付（2026-09-27）','',
           '**五条路线均已实现并完成真实全量拟合、完整panel官方本地评分与最终预测。未上传、未获服务器新分数；best仍为v0023=50.82。**',
           '',f"交付 {validation['package_candidates']} 个通过contract的候选：[上传包](../../deliveries/t1five__t1__upload__20260927.zip)。包SHA和成员数见同目录receipt；候选路径、父版本与SHA以 `submissions/INDEX.tsv` 为权威，不维护第二份候选身份表。",'',
           '| 路线 | 最终候选 | 计算状态 | 工程状态 |','|---|---|---|---|']
    for s in lanes:lines.append(f"| {names[s]} | {candidate[s]} | 完整拟合/预测/官方scorer已执行 | {checks[s]['status']} |")
    lines+=['','五条文件父版本均为v0023；算法祖先分别为三个新路线、R1经验分布方案、R2逐细胞残差方案。新路线只指本项目此前未执行的路线，不是学术原创性声明。',
            '', '## 本地比较与决策边界','',
            '下表是锁定官方scorer的原始本地指标，不是服务器skill或比赛总分。DE/方向越高越好；energy/MMD/variogram越低越好。所有行使用同一3357个E8.5 recipient、3411个E9.5 outer伪目标和32,285列。',
            '', '| 方法 | DE ↑ | 方向 ↑ | energy ↓ | MMD ↓ | variogram ↓ |','|---|---:|---:|---:|---:|---:|',metrics_row('v0023规则，同划分基线',evals['n1density']['v0023_rule_same_split'])]
    for s in lanes:lines.append(metrics_row(s,evals[s]['model']))
    lines += ['',
      '- n1density：整行重加权保留被抽中细胞的完整共表达向量，但总体权重变化会改变群体协方差。三个分布指标改善伴随DE/方向退步，不能称为全面提升。',
      '- n2param：DE与基线相同，方向几乎持平，分布指标小幅改善。模型对阳性 **log1p表达值的对数** 拟合正态分布，不是拟合原始UMI；极稀疏/少阳性条目回退父版本。',
      '- n3borrow：本地五个主要指标均优于基线，值得服务器仲裁；逐类型留出相对平均倍率的优势仍弱，不能声称邻近类型已识别真实发育谱系。',
      '- o1mass：DE降至0.6111、MMD升至0.01320，只有部分分布指标略好；显式零质量外推在此设定下未形成整体收益。阳性分位数使用预先定义的非负、单调参数投影，不能把输出无负值等同于完全没有边界约束。',
      '- o2rate：DE仅0.4630、energy升至0.24492，五项主要指标均弱于基线。消除加法裁剪是工程修正，但这个非负残差预测器在当前report场景没有预测优势；不推荐作为替换best的依据。',
      '', '没有E10.5独立真值，也没有新的服务器分数，五个候选均不得晋级。多轮研究已重复使用同一report split，这些结果只能作为探索性筛选，不能当作一次独立预注册验证。',
      '', '## 实际范围、模型与限制','',
      '- 输入全部官方E8.5的16,787细胞及E9.5的17,057细胞、32,285基因；输入SHA逐run重核对。最终每个候选完整5118×32285，行列按v0023保持。没有下载新外部数据、借用T3许可、使用E7.75、训练预训练检查点或租GPU。',
      '- 拟合区10072/10234细胞，outer评价3357/3411，另20%保留未用于拟合；训练区和outer逐阶段不重叠。最终模型在全部已发布两阶段数据上重拟合，再独立生成E9.5→E10.5候选。它没有看E10.5真值。',
      '- n1density使用全基因32维TruncatedSVD与类型内阶段分类，训练区10个/全量11个分类器；归一化log密度权重限制±log(2)，确定性整行重采样，粗类型标注人数保持。分类器可能学习批次差异；复制次数不计作独立生物重复。',
      '- n2param是新的参数化重复映射；o1mass显式预测零质量和101个条件阳性分位数。每类型最少30训练细胞，每阶段阳性少于5的类型/基因组合保留父版本。所有32,285列仍输出并参加官方scorer，不能把可拟合组合数量称作完整模型覆盖率。',
      '- n3borrow最终只改变E9.5中特有类型，其他行保留v0023；三个近邻由全基因类型均值余弦关系决定。关系只是表型相似，不是细胞谱系；来源倍率作用强度固定0.5。',
      '- o2rate重新拟合原强度均值的log倍率并做类型×基因响应rank≤8分解，再通过 log1p(expm1(x)×exp(rate)) 输出，倍率限制0.5–2，观察零值保持。不是对旧加法delta套exp；“原强度”是归一化强度而非UMI。它不能激活原零值，可能失去R1有效部分。',
      '', '官方scorer完整运行与内部默认计算边界：DE基于完整panel，当前伪目标识别30个上调/26个下调基因；energy在完整32,285维上按官方默认抽取最多1500细胞；MMD按官方默认使用目标拟合的30PC和最多2000细胞；variogram默认最多1500细胞与20000随机基因对。未改scorer或自行缩减输入。这些内部默认不是“全细胞所有基因对穷举”，也不是本轮用小panel替代正式计算。',
      '', '## 实现到声明的修正','',
      '基线审计实际复现旧伪评价矩阵与已评分v0023，均逐值一致。旧R1 builder的p_pred变量未参与输出，实际是E8.5→E9.5经验映射再次作用于E9.5，而不是显式logit零率外推；原评分仍有效，旧机制解释须收窄。o1mass正是对这一实现缺口的独立优化；旧artifact未改变。',
      '', '模型与配置先于对应路线执行冻结，保存在run/code。首批实现期间给分布模型补齐了“零分布变化严格恒等”分支，并在n2param/o1mass正式运行前通过测试；不同run应使用各自快照，不用当前源码替代历史证据。',
      '', '## 输出变化与身份验证','',
      '| 路线 | 改变细胞 | 改变基因 | 改变条目 | 原强度library比q01/q99 |','|---|---:|---:|---:|---|']
    for s in lanes:
        a=audit[s];c=checks[s]
        lines.append(f"| {s} | {a.get('changed_cells','无候选')} | {a.get('changed_genes','无候选')} | {a.get('changed_entries','无候选')} | {c['library_ratio_q01']:.4f}/{c['library_ratio_q99']:.4f} |")
    density=json.loads((root/'n1density/FINAL_OPERATOR.json').read_text());dup=sum(v.get('duplicate_draws_not_replicates',0) for k,v in density.items() if k!='donor_indices')
    lines+=['',f'n1density最终类型内重复抽取{dup}次；这些是表达分布权重，不是新增独立细胞或重复实验。',
            '', '类型迁移的逐类留出（每类型32,285基因，类型等权平均；无生物重复推断）：','',
            '| 拟合范围 | 类型数 | 邻近迁移MSE | 平均倍率MSE | 不变MSE |','|---|---:|---:|---:|---:|']
    for name,label in [('TYPE_HOLDOUT_REPORT.json','60%拟合区'),('TYPE_HOLDOUT_FINAL.json','全部已发布训练数据')]:
        d=json.loads((root/'n3borrow'/name).read_text());vals=[np.mean([x[k] for x in d]) for k in ['mse','mean_rate_mse','no_change_mse']]
        lines.append(f'| {label} | {len(d)} | '+ ' | '.join(f'{v:.8f}' for v in vals)+' |')
    lines+=['', '## 证据、复现与交接','',
      '九项针对性测试通过（TESTS.json）；代码行为边界包含整行/类型保留、非负有界解码、零变化恒等、显式零质量、已拟合模型输入隔离和既有算子定义。测试不是科学验证。',
      '', 'VALIDATION.json独立重新核对五个run的源码/输入/配置哈希、完整无交集划分、32,285列官方scorer完成状态，重放保存的完整最终模型并与交付表达逐值比较，核对INDEX、contract及包成员SHA/CRC。所有最终候选表达彼此不同。',
      '', '完整run入口：`artifacts/t1_five/T1-FIVE-20260927-v1/{n1density,n2param,n3borrow,o1mass,o2rate}/`。每条包含 INPUT_LOCK.json、SPLITS.npz、report_model.pkl、final_model.pkl、report_prediction.h5ad、SCORER.json、EVALUATION.json、MODEL_REPLAY.json、CHECKS.json、CONTRACT.json（有候选时）和RESULT.json。共享基线证明为 shared/READY.json；环境见 ENVIRONMENT.json。',
      '', '代码入口与精确重放说明：`scripts/t1_five/README.md`；设计：`reports/T1_FIVE_DESIGN_20260927.md`；冻结参数：`configs/t1_five/design_20260927.json`。再次执行必须使用新的不可变run目录；不覆盖此次模型、候选或已评分祖先。',
      '', '**未执行项明确保留：E10.5/E12.5真值评分 NOT_RUN_NO_TRUTH；portal上传与服务器评分 NOT_RUN；独立胚胎验证 NOT_AVAILABLE_NO_EMBRYO_IDS；因果机制 NOT_VALIDATED。** 五条承诺的实际训练/拟合/预测和已发布阶段完整panel本地scorer均已执行，没有用smoke代替。',
      '', '建议决策：五路线实现/本地交付完成，合规候选进入服务器仲裁，selection v0023保持。优先关注n3borrow，n2param作参数化对照；其余按本地取舍谨慎解释，不以本地指标提前晋级。所有候选父版本/身份见INDEX与包清单。无工程blocker；科学限制blocks_submission: false。决策D-20260927-T1FIVE-001。']
    (report/'REPORT.md').write_text('\n'.join(lines)+'\n')
    dump(report/'LOCAL_COMPARISON.json',{'baseline':evals['n1density']['v0023_rule_same_split'],'routes':{s:{'candidate':candidate[s],'metrics':evals[s]['model'],'checks':checks[s]} for s in lanes},'scope':'official local report-scenario metrics, not server scores'})
    print('Wrote consolidated REPORT.md and local comparison after five-route validation')


if __name__=='__main__':main()
