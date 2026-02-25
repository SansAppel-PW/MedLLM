# 数据目录与许可登记

| 数据集/资源 | 用途 | 来源 | 许可状态 | 本地路径 | 负责人 | 更新时间 |
|---|---|---|---|---|---|---|
| MedQA (Chinese) | SFT/评测 | HuggingFace: `fzkuji/MedQA`（默认 config: `med_qa_zh_source`） | 待核验 | `data/raw/medqa/` | 待定 | 待填写 |
| CMtMedQA | 多轮评测 | HuggingFace: `Suprit/CMtMedQA` | 待核验 | `data/raw/cmtmedqa/` | 待定 | 待填写 |
| CMeKG | KG校验/实体对齐 | 待补充 | 待核验 | `data/kg/cmekg/` | 待定 | 待填写 |
| PubMed 指南片段库 | 检索核查 | 待补充 | 待核验 | `data/raw/pubmed_refs/` | 待定 | 待填写 |

## 规则
- 未确认许可的数据不得用于模型训练与发布。
- 每次数据更新必须记录版本号、时间戳、变更说明。
- 涉及个人隐私的原始数据必须先脱敏再入库。
