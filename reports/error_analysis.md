# 错误案例分析

## 总体统计
- 主预测文件样本数: 1200
- 误判总数: 600
- 漏检数: 2
- 误报数: 598

## 误判来源分布
- medllm_hybrid: 600

## 误判原因分布
- 选项类样本检索噪声: 596
- 选项错配未识别: 2
- 不确定措辞触发风险: 1
- 长答案熵值偏高: 1

## Top 30 失败案例
| id | 来源 | 类型 | 期望 | 预测 | 分数 | 归因 | 问题摘要 | 回答摘要 |
|---|---|---|---|---|---:|---|---|---|
| medqa_test_000037_neg | medllm_hybrid | 漏检 | high | low | 0.1404 | 选项错配未识别 | Hypoxia-inducible factor 1-alpha (HIF-1a) is a transcription factor with increased activity under conditions of cellu... | 正确答案: A Northern blot will show increased HIF-1α, compared to a normoxic control cell. |
| medqa_validation_000219_pos | medllm_hybrid | 误报 | low | high | 0.8059 | 选项类样本检索噪声 | A 49-year-old man is undergoing an elective hernia repair. No significant past medical history or current medications... | 正确答案: C. The patient’s doctor should have included possible complications of the given operation and risks and benefi... |
| medqa_validation_000099_pos | medllm_hybrid | 误报 | low | high | 0.8047 | 选项类样本检索噪声 | A 52-year-old man presents to the clinic complaining of blood in his urine. He had a mild respiratory illness 3 weeks... | 正确答案: B. Donor A: tA7/A5, ttB8/B2, ttC3/C8 |
| medqa_validation_000055_pos | medllm_hybrid | 误报 | low | high | 0.8042 | 选项类样本检索噪声 | A 36-year-old woman presents with a persistent cough productive of blood-streaked sputum, night sweats, and weight lo... | 正确答案: A. If this patient is diagnosed with active pulmonary tuberculosis, it should be reported even without the pati... |
| medqa_validation_000180_pos | medllm_hybrid | 误报 | low | high | 0.8020 | 选项类样本检索噪声 | A 19-month-old boy comes into the emergency department with his parents. He has burns on his buttocks and perineal ar... | 正确答案: D. Circular burns of equal depth restricted to the buttocks, with sparing of the hands and feet |
| medqa_validation_000214_pos | medllm_hybrid | 误报 | low | high | 0.8017 | 选项类样本检索噪声 | A 51-year-old inmate was released from prison 1 month ago and visits his general practitioner for evaluation of a pos... | 正确答案: D. Advise the patient the positive diagnosis will be reported to the public health office, but you would also e... |
| medqa_test_000248_pos | medllm_hybrid | 误报 | low | high | 0.8011 | 选项类样本检索噪声 | A 55-year-old male with a history of stage I colon cancer status-post left hemicolectomy presents to your office for ... | 正确答案: D. "I really haven't thought about the colonoscopy until today. Worrying before getting the results wasn't goin... |
| medqa_test_000191_pos | medllm_hybrid | 误报 | low | high | 0.8008 | 选项类样本检索噪声 | A 29-year-old female presents to the clinic for a regular check-up. She has no specific complaints. Vital signs inclu... | 正确答案: A. These cells transform to macrophages when they migrate to peripheral tissues. |
| medqa_validation_000084_pos | medllm_hybrid | 误报 | low | high | 0.8004 | 选项类样本检索噪声 | A 28-year-old G2P1001 presents for a routine obstetric visit in her 36th week of pregnancy. She has a history of type... | 正确答案: D. Treat with oral nitrofurantion for 10 days then continue for prophylaxis until delivery |
| medqa_test_000037_pos | medllm_hybrid | 误报 | low | high | 0.8004 | 选项类样本检索噪声 | Hypoxia-inducible factor 1-alpha (HIF-1a) is a transcription factor with increased activity under conditions of cellu... | 正确答案: D. A Western blot will show increased HIF-1α compared to a normoxic control. |
| medqa_test_000100_pos | medllm_hybrid | 误报 | low | high | 0.8003 | 选项类样本检索噪声 | A 14-year-old girl comes to the physician because she has not yet had her period. She is at the 10th percentile for h... | 正确答案: A. Pregnancy success rate with donor oocytes is similar to patients with primary ovarian failure |
| medqa_test_000134_pos | medllm_hybrid | 误报 | low | high | 0.8003 | 选项类样本检索噪声 | A 17-year-old high school student was in shop class when he accidentally sawed off his pointer finger while making a ... | 正确答案: C. Wrap finger in moist gauze, put in a plastic bag, and place on ice |
| medqa_test_000254_pos | medllm_hybrid | 误报 | low | high | 0.7999 | 选项类样本检索噪声 | A 72-year-old woman with a 40 pack-year history of smoking presents to your office with jaundice. After a thorough wo... | 正确答案: B. "I have bad news I need to share with you. Please sit down so we can discuss." |
| medqa_test_000268_pos | medllm_hybrid | 误报 | low | high | 0.7999 | 选项类样本检索噪声 | During the normal catabolism of protein, urea and ammonia are produced as waste products. If these waste products are... | 正确答案: A. NH3 + HCO3- + 2 ATP --> carbamoyl phosphate + 2 ADP + Pi |
| medqa_test_000171_pos | medllm_hybrid | 误报 | low | high | 0.7982 | 选项类样本检索噪声 | A 28-year-old G1P0 woman at 12 weeks estimated gestational age presents with malaise, joint pain, fever, and chills f... | 正确答案: A. It can lead to hydrops fetalis secondary to fetal anemia. |
| medqa_test_000234_pos | medllm_hybrid | 误报 | low | high | 0.7982 | 选项类样本检索噪声 | A 72-year-old man presents to his primary care physician with a 6-month history of shortness of breath. He says that ... | 正确答案: C. Increased residual volume and decreased 1 second forced expiratory volume |
| medqa_validation_000040_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 55-year-old woman is rushed to the emergency department after being found lying unconscious in a burning house by a... | 正确答案: A. The curve would be shifted left due to an increased oxygen binding affinity by hemoglobin. |
| medqa_validation_000042_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 65-year-old woman with a 6-month history of acute promyelocytic leukemia managed with all-trans-retinoic acid prese... | 正确答案: C. PT: ↑ | PTT ↑ | Bleeding time: ↑ | Fibrin split products: ↑ | D-dimer: ↑| Fibrinogen: ↓ | Platelet count: ↓ |
| medqa_validation_000044_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 66-year-old man presents with palpitation, syncope, and difficulty breathing. He has a past medical history of stro... | 正确答案: B. Amiodarone inhibits CYP2C9 leading to an increased risk of bleeding |
| medqa_validation_000108_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A regional hospital system has decided to institute a new task group for quality improvement and patient safety. The ... | 正确答案: D. Changing the electronic medical record to only allow a maximum of 7 days per prescription |
| medqa_validation_000109_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 57-year-old man comes to the clinic complaining of nausea and 1 episode of vomiting during the past day. He denies ... | 正确答案: A. Accumulation of N-acetyl-p-benzoquinone imine in the liver |
| medqa_validation_000128_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 45-year-old man presents to the emergency room with fever and headache. He recently had a middle ear infection. On ... | 正确答案: D. Glucose: ↓, Proteins: ↑, Cells: 90% neutrophils, Lactic Acid (mmol/l): 4.5 |
| medqa_validation_000156_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 42-year-old overweight restaurant waiter develops excruciating pain in the heel of his right foot. Symptoms are mos... | 正确答案: C. This was caused by excessive strain on the medial fascicle. |
| medqa_validation_000181_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 44-year-old woman presents to the physician for evaluation of recurrent episodes of pounding headache, palpitations... | 正确答案: C. 24-h urine catecholamine by-products (vanillylmandelic acid (VMA), metanephrine, and normetanephrine) |
| medqa_validation_000187_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 25-year-old primigravida is admitted to the hospital at 35 weeks gestation with lower leg edema. She denies any oth... | 正确答案: A. Induction of vaginal delivery at 37 weeks’ pregnancy if not begin spontaneously earlier |
| medqa_validation_000291_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 27-year-old nullipara makes an appointment with her gynecologist to discuss the results of her cervical cancer scre... | 正确答案: B. Close follow-up with cytology and colposcopy may be considered in this patient. |
| medqa_test_000020_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A 28-year-old woman, gravida 2, para 1, at 40 weeks gestation is brought to the emergency department by her husband. ... | 正确答案: C. Treat and transfer the patient after she makes a written request |
| medqa_test_000052_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | While traveling abroad a physician is asked to attend a meeting regarding healthcare in the region. The rate of chlam... | 正确答案: C. “I can not help you due to the ethical principle of nonmaleficence.” |
| medqa_test_000073_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 选项类样本检索噪声 | A multi-specialty physician practice is meeting to determine which compensation scheme would best serve the practice ... | 正确答案: C. Fee-for-service may incentivize physicians to increase healthcare utilization irrespective of quality |
| medqa_test_000081_pos | medllm_hybrid | 误报 | low | high | 0.7980 | 不确定措辞触发风险 | A 16-year-old female presents to her physician’s office after noticing a round lump in her left breast 2 months ago. ... | 正确答案: C. This mass will most likely decrease in size or disappear over time |
