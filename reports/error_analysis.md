# 错误案例分析

## 总体统计
- 主预测文件样本数: 3600
- 误判总数: 1173
- 漏检数: 435
- 误报数: 738

## 误判来源分布
- BioMistral-7B-Proxy_(whitebox): 1149
- medllm_hybrid: 24

## 误判原因分布
- 选项类样本检索噪声: 738
- 选项错配未识别: 435

## Top 30 失败案例
| id | 来源 | 类型 | 期望 | 预测 | 分数 | 归因 | 问题摘要 | 回答摘要 |
|---|---|---|---|---|---:|---|---|---|
| medqa_train_000057_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.0525 | 选项错配未识别 | A 55-year-old woman comes to the physician because of involuntary hand movements that improve with alcohol consumptio... | 正确答案: ↓ ↓ ↓ |
| medqa_train_000658_neg | medllm_hybrid | 漏检 | high | low | 0.0904 | 选项错配未识别 | A 2-year-old boy is brought to the physician for the evaluation of fever, difficulty breathing, and coughing for the ... | 正确答案: B cells |
| medqa_train_000833_neg | medllm_hybrid | 漏检 | high | low | 0.0904 | 选项错配未识别 | A 9-year-old boy is brought to the emergency department by his mother because of painful swelling in his right knee t... | 正确答案: Protein C |
| medqa_train_000568_neg | medllm_hybrid | 漏检 | high | low | 0.1082 | 选项错配未识别 | A 9-year-old boy who recently emigrated from sub-Saharan Africa is brought to the physician because of a 2-day histor... | 正确答案: Immunoglobulin A action |
| medqa_validation_000048_neg | medllm_hybrid | 漏检 | high | low | 0.1082 | 选项错配未识别 | A 35-year-old woman visits her primary care provider with complaints of easy fatigability, breathlessness on exertion... | 正确答案: Vitamin A deficiency |
| medqa_test_000213_neg | medllm_hybrid | 漏检 | high | low | 0.1082 | 选项错配未识别 | A 23-year-old woman, gravida 2, para 1, at 28 weeks' gestation comes to the physician for a routine prenatal examinat... | 正确答案: Anti-B IgG |
| medqa_train_000242_neg | medllm_hybrid | 漏检 | high | low | 0.1220 | 选项错配未识别 | A 40-year-old woman residing at an iodine-deficient endemic area presents to the physician with a painless and gradua... | 正确答案: Hyperplastic parafollicular C cells |
| medqa_train_000625_neg | medllm_hybrid | 漏检 | high | low | 0.1220 | 选项错配未识别 | A study is designed to assess the functions of immune components. The investigator obtains a lymph node biopsy from a... | 正确答案: V(D)J recombination |
| medqa_test_000119_neg | medllm_hybrid | 漏检 | high | low | 0.1220 | 选项错配未识别 | A 25-year-old woman presents generalized abdominal pain and vomiting for the past hour. She has also had watery diarr... | 正确答案: Perform a gastric lavage |
| medqa_train_000965_neg | medllm_hybrid | 漏检 | high | low | 0.1333 | 选项错配未识别 | A 3-year-old boy is brought to the physician for presurgical evaluation before undergoing splenectomy. One year ago, ... | 正确答案: Vaccination against hepatitis B virus |
| medqa_train_000637_neg | medllm_hybrid | 漏检 | high | low | 0.1428 | 选项错配未识别 | An 18-year-old man comes to the physician with his parents for a routine health maintenance examination. He noticed a... | 正确答案: Refer him to a methadone clinic |
| medqa_train_000078_neg | medllm_hybrid | 漏检 | high | low | 0.1511 | 选项错配未识别 | A 65-year-old man with hypertension and type 2 diabetes mellitus is brought to the emergency department 20 minutes af... | 正确答案: Rupture of a bulla in the lung |
| medqa_train_000147_neg | medllm_hybrid | 漏检 | high | low | 0.1511 | 选项错配未识别 | A 30-month-old boy is brought to the emergency department by his parents. He has burns over his left hand. The mother... | 正确答案: Burn as a result of poor supervision |
| medqa_validation_000109_neg | medllm_hybrid | 漏检 | high | low | 0.1511 | 选项错配未识别 | A 57-year-old man comes to the clinic complaining of nausea and 1 episode of vomiting during the past day. He denies ... | 正确答案: Impaction of a gallstone in the ileus |
| medqa_train_001101_neg | medllm_hybrid | 漏检 | high | low | 0.1584 | 选项错配未识别 | A 26-year-old female college student is brought back into the university clinic for acting uncharacteristically. The ... | 正确答案: The patient may have a history of mania. |
| medqa_validation_000055_neg | medllm_hybrid | 漏检 | high | low | 0.1584 | 选项错配未识别 | A 36-year-old woman presents with a persistent cough productive of blood-streaked sputum, night sweats, and weight lo... | 正确答案: Only active pulmonary tuberculosis is a reportable disease. |
| medqa_validation_000187_neg | medllm_hybrid | 漏检 | high | low | 0.1725 | 选项错配未识别 | A 25-year-old primigravida is admitted to the hospital at 35 weeks gestation with lower leg edema. She denies any oth... | 正确答案: Watch for a spontaneous vaginal delivery at any term from the moment of presentation |
| medqa_train_000102_neg | medllm_hybrid | 漏检 | high | low | 0.1727 | 选项错配未识别 | A 16-year-old man with no significant past medical, surgical, or family history presents to his pediatrician with new... | 正确答案: The patient camped as a side excursion from a cruise ship. |
| medqa_train_000209_neg | medllm_hybrid | 漏检 | high | low | 0.1727 | 选项错配未识别 | An otherwise healthy 49-year-old man presents to his primary care physician for follow-up for a high HbA1C. 3 months ... | 正确答案: Metformin added to a glucagon-like peptide 1 (GLP-1) agonist |
| medqa_train_000369_neg | medllm_hybrid | 漏检 | high | low | 0.1760 | 选项错配未识别 | A 22-year-old woman in the intensive care unit has had persistent oozing from the margins of wounds for 2 hours that ... | 正确答案: Transfuse packed RBC and fresh frozen plasma in a 1:1 ratio |
| medqa_train_000678_neg | medllm_hybrid | 漏检 | high | low | 0.1775 | 选项错配未识别 | An 8-year-old boy and his 26-year-old babysitter are brought into the emergency department with severe injuries cause... | 正确答案: Obtain an emergency court order from a judge to obtain consent to amputate the child’s arm |
| medqa_train_001135_neg | medllm_hybrid | 漏检 | high | low | 0.1843 | 选项错配未识别 | A new study shows a significant association between patients with a BMI >40 and a diagnosis of diabetes (odds ratio: ... | 正确答案: A study of 1000 patients comparing rates of diabetes diagnoses and BMIs of diabetic and non-diabetic patients |
| medqa_train_000099_pos | medllm_hybrid | 误报 | low | high | 0.8082 | 选项类样本检索噪声 | A 55-year-old woman is brought to the emergency department because of worsening upper abdominal pain for 8 hours. She... | 正确答案: D. Capillary leakage |
| medqa_test_000296_pos | medllm_hybrid | 误报 | low | high | 0.8082 | 选项类样本检索噪声 | A 55-year-old woman is brought to the emergency department because of worsening upper abdominal pain for the past 8 h... | 正确答案: B. Capillary leakage |
| medqa_train_000000_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A genetic population study is being conducted to find the penetrance of a certain disease. This disease is associated... | 正确答案: 40% |
| medqa_train_000016_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 34-year-old woman with a history of depression is brought to the emergency department by her husband 45 minutes aft... | 正确答案: Fomepizole |
| medqa_train_000017_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 30-year-old patient comes to the emergency room with a chief complaint of left chest pain and a productive cough wi... | 正确答案: Tuberculosis |
| medqa_train_000029_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 26-year-old woman (gravida 3 para 1) with no prenatal care delivers a boy at 37 weeks gestation. His Apgar score is... | 正确答案: Gentamicin |
| medqa_train_000030_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | An 8-year-old girl is brought to the physician because of repetitive involuntary movements, including neck twisting, ... | 正确答案: Chlorpromazine |
| medqa_train_000031_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 55-year-old man presents to his primary care provider with increased urinary frequency. Over the past 3 months, he ... | 正确答案: Mannitol |
