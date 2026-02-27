# 错误案例分析

## 总体统计
- 主预测文件样本数: 1200
- 误判总数: 507
- 漏检数: 193
- 误报数: 314

## 误判来源分布
- BioMistral-7B-Proxy_(whitebox): 507

## 误判原因分布
- 选项类样本检索噪声: 312
- 选项错配未识别: 193
- 长答案熵值偏高: 1
- 不确定措辞触发风险: 1

## Top 30 失败案例
| id | 来源 | 类型 | 期望 | 预测 | 分数 | 归因 | 问题摘要 | 回答摘要 |
|---|---|---|---|---|---:|---|---|---|
| medqa_validation_000000_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 50-year-old woman presents to the emergency department with severe abdominal pain and discomfort for several hours.... | 正确答案: Asthma |
| medqa_validation_000007_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 28-year-old woman who recently immigrated from Kenya presents with fatigue, shortness of breath, and palpitations f... | 正确答案: Brain |
| medqa_validation_000012_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 33-year-old woman comes to the physician because of a 1-year history of irregular menses and infertility. She has a... | 正确答案: Mifepristone |
| medqa_validation_000015_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 55-year-old woman visits her primary care provider for concerns of frequent headaches. She complains of recurrent h... | 正确答案: Diplopia |
| medqa_validation_000017_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 17-year-old male collapses 25 minutes into a soccer game. He is unresponsive and pulseless. Despite adequate resusc... | 正确答案: Fibrilin |
| medqa_validation_000019_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 24-year-old man is brought to the emergency department for bowling at a local bowling alley while inappropriately d... | 正确答案: Infection |
| medqa_validation_000030_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 24-year-old patient presents to your gastroenterology practice on a referral from her primary care provider. The pa... | 正确答案: Bismuth |
| medqa_validation_000038_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 36-year-old woman comes to the emergency department because of left wrist pain and swelling that started immediatel... | 正确答案: Hamate |
| medqa_validation_000041_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 73-year-old man with a past medical history significant for high blood pressure, hypothyroidism, and diabetes prese... | 正确答案: Terazosin |
| medqa_validation_000045_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 55-year-old woman presents to the emergency department with recent onset confusion and photophobia. Upon questionin... | 正确答案: Acyclovir |
| medqa_validation_000047_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 54-year-old man comes to the physician for a follow-up appointment. Three weeks ago he underwent emergent cardiac c... | 正确答案: Hypermagnesemia |
| medqa_validation_000052_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 28-year-old woman presents with a recent history of severe headaches. The patient states that the headaches came on... | 正确答案: Infection |
| medqa_validation_000056_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 33-year-old woman gravida 2, para 1, at 35 weeks gestation is admitted to the hospital with fever and active labor.... | 正确答案: Amnioinfusion |
| medqa_validation_000061_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 57-year-old woman comes to the emergency department because of severe dyspnea, cough, and pleuritic chest pain for ... | 正确答案: Pericardiocentesis |
| medqa_validation_000064_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 33-year-old man presents to his primary care physician for fatigue, weight loss, and diffuse pruritus. The patient ... | 正确答案: Cirrhosis |
| medqa_validation_000071_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 40-year-old man comes to the physician because of a 5-kg (11-lb) weight loss over the past month and easy bruising.... | 正确答案: Cyclophosphamide |
| medqa_validation_000076_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 34-year-old woman comes to the gynecologist complaining of vaginal swelling and discomfort. She states that over th... | 正确答案: Folliculitis |
| medqa_validation_000081_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 56-year-old woman is brought to the emergency department by her husband 30 minutes after a generalized tonic-clonic... | 正确答案: Meningioma |
| medqa_validation_000082_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 29-year-old woman (gravida 2, para 1) presents at 32 weeks gestation for routine follow-up care. Her previous pregn... | 正确答案: Coagulogram |
| medqa_validation_000089_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 75-year-old man presents to the emergency department from his doctor’s office with a 2-day history of urinary hesit... | 正确答案: Nephrolithiasis |
| medqa_validation_000091_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | An important step in the formation of thyroid hormones is the formation of I2 via oxidation of I-. Which of the follo... | 正确答案: Perchlorate |
| medqa_validation_000093_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 65-year-old man presents to the emergency department with confusion and chest pain. He states his symptoms started ... | 正确答案: Hemodialysis |
| medqa_validation_000097_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 27-year-old woman presents to the emergency department with severe wheezing, which started an hour ago. She informs... | 正确答案: Acetaminophen |
| medqa_validation_000100_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | An investigator is studying determinants of childhood obesity by observing a cohort of pregnant women with obesity. A... | 正确答案: -1.80 |
| medqa_validation_000105_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | An 18-year-old girl comes to the emergency room with abdominal pain. She states that the pain started 6 hours ago, is... | 正确答案: Appendicitis |
| medqa_validation_000110_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 48-year-old patient comes to the physician because of a 4-day history fever, headaches, loss of appetite, and myalg... | 正确答案: Flea |
| medqa_validation_000112_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 3-year-old boy presents to the pediatrician crying with ear pain and his temperature has been 101°F (38.3°C) for se... | 正确答案: Tympanocentesis |
| medqa_validation_000115_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | An investigator is studying the secretion of gastrointestinal hormones before and after food intake. She isolates a h... | 正确答案: Cholecystokinin |
| medqa_validation_000116_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A 45-year-old woman presents to the office with a chief complaint of a cough that has persisted for a month and a hal... | 正确答案: Echinococcosis |
| medqa_validation_000120_neg | BioMistral-7B-Proxy_(whitebox) | 漏检 | high | low | 0.2382 | 选项错配未识别 | A healthy 32-year-old woman enrolls in a study investigating kidney function. Her renal plasma flow (RPF) is 600 mL/m... | 正确答案: Glucose |
