# CM3KG -> CMeKG 集成构建报告

## 输入统计
- medical.csv 行数: 8808
- disease alias 实体数: 2335
- symptom alias 实体数: 1682
- 额外合并 demo 三元组行数: 5

## 输出统计
- 三元组总数: 298498
- 输出文件: `/Users/bibo/Desktop/MedLLM_codex/data/kg/cmekg_integrated.jsonl`

## 关系分布
| relation | count |
|---|---:|
| treats | 59738 |
| recommended_drug | 59736 |
| has_symptom | 54710 |
| requires_check | 39418 |
| alias_of | 28413 |
| diet_avoid | 22239 |
| diet_recommendation | 22230 |
| comorbidity | 12011 |
| contraindicated_for | 2 |
| dosage_range_mg | 1 |

## 来源分布
| source | count |
|---|---:|
| CM3KG.medical | 270080 |
| CM3KG.alias | 28413 |
| cmekg_demo | 5 |
