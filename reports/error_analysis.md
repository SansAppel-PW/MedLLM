# 错误案例分析

## 总体统计
- 主预测文件样本数: 200
- 误判总数: 95
- 漏检数: 0
- 误报数: 95

## 误判来源分布
- medllm_hybrid: 95

## 误判原因分布
- 选项类样本检索噪声: 94
- 长答案熵值偏高: 1

## Top 30 失败案例
| id | 来源 | 类型 | 期望 | 预测 | 分数 | 归因 | 问题摘要 | 回答摘要 |
|---|---|---|---|---|---:|---|---|---|
| medqa_validation_000015_pos | medllm_hybrid | 误报 | low | high | 0.8023 | 长答案熵值偏高 | A 60-year-old man calls his hospital and asks to speak to his physician about laboratory test reports ordered because... | 正确答案: C. """I would like to meet later today at 4:00 PM so that we have enough time to discuss the lab results. If yo... |
| medqa_validation_000082_pos | medllm_hybrid | 误报 | low | high | 0.8006 | 选项类样本检索噪声 | A 17-year-old boy presents for a psychotherapy session after finding out that his girlfriend has been carrying on ano... | 正确答案: A. Channeling his anger about the situation into training for his track meet |
| medqa_validation_000076_pos | medllm_hybrid | 误报 | low | high | 0.8003 | 选项类样本检索噪声 | A 37-year-old male presents with difficulty eating solids and drinking water; which has been progressively worse over... | 正确答案: A. Aperistalsis in the distal two-thirds of the esophagus with incomplete lower esophageal relaxation |
| medqa_validation_000038_pos | medllm_hybrid | 误报 | low | high | 0.7966 | 选项类样本检索噪声 | A 15-year-old girl comes to the physician because of a 2-month history of progressive fatigue and weakness. She also ... | 正确答案: C. Pleomorphic modified smooth muscle cells in the renal cortex |
| medqa_validation_000091_pos | medllm_hybrid | 误报 | low | high | 0.7966 | 选项类样本检索噪声 | Advances in molecular biology have identified important factors and sequences required for transcription and translat... | 正确答案: C. An initiator of translation proximal to the start codon |
| medqa_validation_000037_pos | medllm_hybrid | 误报 | low | high | 0.7919 | 选项类样本检索噪声 | A 25-year-old woman is brought to the emergency department by her husband for abdominal pain. The husband answers all... | 正确答案: B. """Do you feel safe leaving the emergency department?""" |
| medqa_validation_000012_pos | medllm_hybrid | 误报 | low | high | 0.7867 | 选项类样本检索噪声 | A 72-year-old man presents with a recent episode of slurred speech and numbness in his left arm and left leg 2 hours ... | 正确答案: B. Admit the patient for observation and workup |
| medqa_validation_000027_pos | medllm_hybrid | 误报 | low | high | 0.7867 | 选项类样本检索噪声 | A 32-year old woman presents to the office complaining of progressively worsening shortness of breath for 2 months. S... | 正确答案: C. Entrapment of megakaryocytes in the nail bed |
| medqa_validation_000041_pos | medllm_hybrid | 误报 | low | high | 0.7867 | 选项类样本检索噪声 | A 67-year-old African American male presents to his primary care physician for routine follow-up. He has a history of... | 正确答案: C. Centrally acting alpha2 adrenergic receptor agonist |
| medqa_validation_000050_pos | medllm_hybrid | 误报 | low | high | 0.7867 | 选项类样本检索噪声 | A 67-year-old female is admitted to the hospital with enterococcus endocarditis and is treated with penicillin and ge... | 正确答案: A. Ringing in the ears and impaired hearing |
| medqa_validation_000000_pos | medllm_hybrid | 误报 | low | high | 0.7809 | 选项类样本检索噪声 | An investigator is studying the efficacy of antiviral drugs in infected human cells. Harvested human cells are inocul... | 正确答案: C. Phosphorylation by virally-encoded thymidine kinase |
| medqa_validation_000017_pos | medllm_hybrid | 误报 | low | high | 0.7809 | 选项类样本检索噪声 | A 28-year-old woman, gravida 1, para 0, at 32 weeks' gestation comes to the physician for a prenatal visit. She has h... | 正确答案: A. Plan normal vaginal delivery at term |
| medqa_validation_000031_pos | medllm_hybrid | 误报 | low | high | 0.7809 | 选项类样本检索噪声 | A 63-year-old man comes to the physician for the evaluation of difficulty walking for the last 6 months. He reports w... | 正确答案: B. Autoantibodies against voltage-gated calcium channels |
| medqa_validation_000095_pos | medllm_hybrid | 误报 | low | high | 0.7809 | 选项类样本检索噪声 | A previously healthy 45-year-old man is brought to the emergency department after being found by a search and rescue ... | 正确答案: B. Low urine sodium with hyaline casts |
| medqa_validation_000001_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 13-year-old boy is brought to the physician because of pain and redness on his back for 2 days. He returned yesterd... | 正确答案: D. Apply aloe vera-based moisturizer " |
| medqa_validation_000005_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 67-year-old man is brought to the emergency department after the sudden onset of dizziness, blurry vision, and a ra... | 正确答案: B. Left posterior inferior cerebellar artery |
| medqa_validation_000009_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 54-year-old woman comes to the emergency department because of sharp chest pain and shortness of breath for 1 day. ... | 正确答案: A. Unilateral swelling of the leg |
| medqa_validation_000039_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 15-year-old boy is brought to the emergency department by his mother because of severe left testicular pain for 1 h... | 正确答案: C. Positive nucleic acid amplification testing |
| medqa_validation_000046_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 13-year-old African-American girl is brought to the physician for right shoulder pain that has worsened over the pa... | 正确答案: C. Infarction of the bone trabeculae |
| medqa_validation_000064_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 58-year-old woman is brought to the emergency department by her husband because of increasing confusion and general... | 正确答案: B. Syndrome of inappropriate antidiuretic hormone |
| medqa_validation_000068_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 52-year-old man with a history of mild chronic obstructive pulmonary disease (COPD) has been using albuterol as nee... | 正确答案: B. Add tiotropium to treatment regimen |
| medqa_validation_000081_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A 28-year-old man presents to a clinic for a health check-up. He says that he feels great and has not seen a physicia... | 正确答案: D. Inhibition of HMG-CoA reductase |
| medqa_validation_000087_pos | medllm_hybrid | 误报 | low | high | 0.7743 | 选项类样本检索噪声 | A previously healthy 2-month-old boy is brought to the physician because of a 10-day history of poor feeding. He used... | 正确答案: D. Decrease in pulmonary vascular resistance |
| medqa_validation_000003_pos | medllm_hybrid | 误报 | low | high | 0.7666 | 选项类样本检索噪声 | A population study was conducted to evaluate coronary artery disease in the general population. A cohort of 700 patie... | 正确答案: C. Right coronary artery dominance |
| medqa_validation_000042_pos | medllm_hybrid | 误报 | low | high | 0.7666 | 选项类样本检索噪声 | A 2800-g (6-lb 3-oz), 3-day-old newborn is in the intensive care unit for fever, vomiting, tremors, cyanotic episodes... | 正确答案: A. Avoiding unpasteurized milk products |
| medqa_validation_000051_pos | medllm_hybrid | 误报 | low | high | 0.7666 | 选项类样本检索噪声 | A 75-year-old male is brought to the emergency room by his daughter due to slurred speech and a drooping eyelid on th... | 正确答案: A. Posterior inferior cerebellar artery |
| medqa_validation_000055_pos | medllm_hybrid | 误报 | low | high | 0.7666 | 选项类样本检索噪声 | You are on your first day of a pathology rotation and the attending pathologist gives you a biopsy specimen to examin... | 正确答案: C. A urease-positive organism |
| medqa_validation_000065_pos | medllm_hybrid | 误报 | low | high | 0.7666 | 选项类样本检索噪声 | A 55-year-old man comes to the emergency department because of left arm pain after falling from a ladder. Physical ex... | 正确答案: D. Macrophage colony-stimulating factor |
| medqa_validation_000071_pos | medllm_hybrid | 误报 | low | high | 0.7666 | 选项类样本检索噪声 | A 48-year-old man presents to the clinic feeling depressed after a string of failed business projects. His team notic... | 正确答案: A. Serotonin, norepinephrine, and dopamine |
| medqa_validation_000019_pos | medllm_hybrid | 误报 | low | high | 0.7576 | 选项类样本检索噪声 | A 57-year-old man with chronic obstructive pulmonary disease comes to the emergency department because of leg swellin... | 正确答案: D. Chronic hypoxic vasoconstriction |
