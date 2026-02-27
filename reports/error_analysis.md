# 错误案例分析

## 总体统计
- 主预测文件样本数: 2000
- 误判总数: 998
- 漏检数: 3
- 误报数: 995

## 误判来源分布
- medllm_hybrid: 998

## 误判原因分布
- 选项类样本检索噪声: 992
- 选项错配未识别: 3
- 长答案熵值偏高: 2
- 不确定措辞触发风险: 1

## Top 30 失败案例
| id | 来源 | 类型 | 期望 | 预测 | 分数 | 归因 | 问题摘要 | 回答摘要 |
|---|---|---|---|---|---:|---|---|---|
| medqa_test_000428_neg | medllm_hybrid | 漏检 | high | low | 0.1404 | 选项错配未识别 | Hypoxia-inducible factor 1-alpha (HIF-1a) is a transcription factor with increased activity under conditions of cellu... | 正确答案: A Northern blot will show increased HIF-1α, compared to a hypoxic control cell. |
| medqa_test_000254_neg | medllm_hybrid | 漏检 | high | low | 0.1452 | 选项错配未识别 | A group of researchers from Italy conducted a case register study that included all patients from a city who had an I... | 正确答案: The number of deaths in a specific age group divided by a mid-year population in that age group |
| medqa_validation_000318_pos | medllm_hybrid | 误报 | low | high | 0.8060 | 选项类样本检索噪声 | A 2-week-old infant is brought to the pediatrician for the first time by his parents. His mother received regular pre... | 正确答案: D. Document the visit, specifically the detailing of risks and benefits and the parents' refusal of treatment |
| medqa_validation_000444_pos | medllm_hybrid | 误报 | low | high | 0.8047 | 选项类样本检索噪声 | A 52-year-old man presents to the clinic complaining of blood in his urine. He had a mild respiratory illness 3 weeks... | 正确答案: B. Donor A: tA7/A5, ttB8/B2, ttC3/C8 |
| medqa_test_000188_pos | medllm_hybrid | 误报 | low | high | 0.8047 | 选项类样本检索噪声 | In a study to determine the risk factors for myocardial infarction (MI) at a young age (age < 30 years), 30 young pat... | 正确答案: A. The association is not statistically significant, and low education is not a risk factor. |
| medqa_validation_000400_pos | medllm_hybrid | 误报 | low | high | 0.8042 | 选项类样本检索噪声 | A 36-year-old woman presents with a persistent cough productive of blood-streaked sputum, night sweats, and weight lo... | 正确答案: A. If this patient is diagnosed with active pulmonary tuberculosis, it should be reported even without the pati... |
| medqa_test_000257_pos | medllm_hybrid | 误报 | low | high | 0.8038 | 选项类样本检索噪声 | A 23-year-old woman, gravida 2, para 1, at 20 weeks of gestation comes to the physician for a routine prenatal exam. ... | 正确答案: A. Repeat antibody screening at 28 weeks. Administer anti-D immunoglobulin at 28 weeks and after delivery if th... |
| medqa_validation_000122_pos | medllm_hybrid | 误报 | low | high | 0.8031 | 选项类样本检索噪声 | A 57-year-old woman presents to the emergency department with acute pain in the left lower abdomen associated with na... | 正确答案: C. Herniation of mucosa and submucosa through the muscular layer of the colon |
| medqa_test_000139_pos | medllm_hybrid | 误报 | low | high | 0.8028 | 选项类样本检索噪声 | A 38-year-old nursing home worker presents to the clinic with complaints of fever, loss of appetite, fatigue, and pro... | 正确答案: C. It consists of a largely circumscribed granuloma with epithelioid cells with Langhans cells. |
| medqa_validation_000266_pos | medllm_hybrid | 误报 | low | high | 0.8027 | 选项类样本检索噪声 | A 22-year-old woman college student presents with diarrhea and crampy abdominal pain that is relieved by defecation. ... | 正确答案: C. Symptoms present at least 1 day per week for 3 consecutive months with symptom onset at least 6 months befor... |
| medqa_validation_000105_pos | medllm_hybrid | 误报 | low | high | 0.8025 | 选项类样本检索噪声 | A 34-year-old man comes to the physician for a routine health maintenance examination required for his occupation as ... | 正确答案: B. """Have you ever experienced a situation in which you wished you smoked less marijuana?""" |
| medqa_validation_000254_pos | medllm_hybrid | 误报 | low | high | 0.8025 | 选项类样本检索噪声 | A 40-hour-old baby girl is being evaluated for failure to pass meconium. She is the product of a full-term vaginal de... | 正确答案: A. Absence of ganglion cells in the submucosal plexus on suction biopsy of the rectum |
| medqa_test_000085_pos | medllm_hybrid | 误报 | low | high | 0.8025 | 选项类样本检索噪声 | A 45-year-old man comes to his primary-care doctor with his wife for a 4-week history of constipation. The patient re... | 正确答案: C. Na+/Cl- cotransporter in the membranes of epithelial cells in the distal convoluted tubule |
| medqa_validation_000015_pos | medllm_hybrid | 误报 | low | high | 0.8023 | 长答案熵值偏高 | A 60-year-old man calls his hospital and asks to speak to his physician about laboratory test reports ordered because... | 正确答案: C. """I would like to meet later today at 4:00 PM so that we have enough time to discuss the lab results. If yo... |
| medqa_test_000134_pos | medllm_hybrid | 误报 | low | high | 0.8022 | 选项类样本检索噪声 | A 70-year-old woman with no significant medical history begins to experience memory loss and personality changes. Ove... | 正确答案: C. Conversion of a protein from an a-helix to a ß-pleated form, which resists degradation. |
| medqa_validation_000135_pos | medllm_hybrid | 误报 | low | high | 0.8018 | 选项类样本检索噪声 | A team of scientists is researching the synthesis of a drug that would potentially reduce blood pressure in hypertens... | 正确答案: C. Drug A will not decrease blood pressure, regardless of its dose or supplementation of B or E |
| medqa_test_000338_pos | medllm_hybrid | 误报 | low | high | 0.8016 | 选项类样本检索噪声 | A 29-year-old woman presents to her OB/GYN for a preconception visit. She wishes to become pregnant within the next s... | 正确答案: B. 3 months prior to conception, begin a restricted diet to lower phenylalanine levels to below 6 mg/dL |
| medqa_validation_000175_pos | medllm_hybrid | 误报 | low | high | 0.8008 | 选项类样本检索噪声 | A researcher is studying the association between hemoglobin levels and BMI. He divides volunteers who wish to partici... | 正确答案: D. If the null hypothesis is true, there is a 10% probability to get this difference of 0.4 g/dL or higher due ... |
| medqa_test_000072_pos | medllm_hybrid | 误报 | low | high | 0.8008 | 选项类样本检索噪声 | A 16-year-old female patient with a history of mental retardation presents to your clinic with her mother. The mother... | 正确答案: C. Refuse the procedure because it violates the ethical principle of autonomy |
| medqa_test_000087_pos | medllm_hybrid | 误报 | low | high | 0.8008 | 选项类样本检索噪声 | A 12-year-old boy is brought to the emergency department for the evaluation of persistent bleeding from his nose over... | 正确答案: D. Squeezing the nostrils manually for 10 minutes with the head elevated |
| medqa_test_000242_pos | medllm_hybrid | 误报 | low | high | 0.8008 | 选项类样本检索噪声 | A 19-year-old female college soccer player presents to a sports medicine clinic with right knee pain. One day prior s... | 正确答案: B. Prevent excess anterior translation of the tibia relative to the femur |
| medqa_test_000361_pos | medllm_hybrid | 误报 | low | high | 0.8008 | 选项类样本检索噪声 | A 28-year-old male presents to the emergency department with chest pain. He reports that one hour ago he was climbing... | 正确答案: B. Late systolic crescendo murmur at the apex with mid-systolic click |
| medqa_validation_000082_pos | medllm_hybrid | 误报 | low | high | 0.8006 | 选项类样本检索噪声 | A 17-year-old boy presents for a psychotherapy session after finding out that his girlfriend has been carrying on ano... | 正确答案: A. Channeling his anger about the situation into training for his track meet |
| medqa_validation_000121_pos | medllm_hybrid | 误报 | low | high | 0.8006 | 选项类样本检索噪声 | A 23-year-old woman presents to her gynecologist for a routine visit. She is nulliparous, does not report any gynecol... | 正确答案: A. Repeat Pap test in 3 years as a usual screening schedule suggests |
| medqa_test_000046_pos | medllm_hybrid | 误报 | low | high | 0.8006 | 选项类样本检索噪声 | A 23-year-old man is admitted to the hospital with fever, chest discomfort, tachypnea, pain, needle-like sensations i... | 正确答案: B. The drug caused uncoupling of the electron transport chain and oxidative phosphorylation. |
| medqa_validation_000429_pos | medllm_hybrid | 误报 | low | high | 0.8004 | 选项类样本检索噪声 | A 28-year-old G2P1001 presents for a routine obstetric visit in her 36th week of pregnancy. She has a history of type... | 正确答案: D. Treat with oral nitrofurantion for 10 days then continue for prophylaxis until delivery |
| medqa_test_000428_pos | medllm_hybrid | 误报 | low | high | 0.8004 | 选项类样本检索噪声 | Hypoxia-inducible factor 1-alpha (HIF-1a) is a transcription factor with increased activity under conditions of cellu... | 正确答案: D. A Western blot will show increased HIF-1α compared to a normoxic control. |
| medqa_validation_000076_pos | medllm_hybrid | 误报 | low | high | 0.8003 | 选项类样本检索噪声 | A 37-year-old male presents with difficulty eating solids and drinking water; which has been progressively worse over... | 正确答案: A. Aperistalsis in the distal two-thirds of the esophagus with incomplete lower esophageal relaxation |
| medqa_test_000062_pos | medllm_hybrid | 误报 | low | high | 0.8003 | 选项类样本检索噪声 | A research group has created a novel screening test for a rare disorder. A robust clinical trial is performed in a gr... | 正确答案: D. If the sensitivity of this screening test were decreased, the statistical power would decrease. |
| medqa_test_000290_pos | medllm_hybrid | 误报 | low | high | 0.8003 | 选项类样本检索噪声 | A 74-year-old woman is brought to her primary care doctor by her adult son. The son says she has been very difficult ... | 正确答案: D. Ask the son to step out so you can speak with the patient alone |
