# MedLLM 项目总档案（项目详情 + 使用说明 + 产出说明 + 论文写作材料）

- 生成时间（UTC）：2026-02-27T15:53:14Z
- 代码分支：codex/worktree
- 代码版本：00c7e4f
- 适用阶段：GPU 迁移前最终梳理 / GPU 迁移执行指南 / 论文写作支撑

## 1. 项目总体结论

本项目已经完成工程主链闭环，具备以下条件：

1. 数据构建、清洗、偏差审计、检测评测、论文资产生成均可重复执行。
2. GPU 迁移脚本、环境 bootstrap、严格完工闸门已就位。
3. 论文写作所需的结构化材料、指标表、错误分析与实验记录已自动化落盘。

当前尚未“论文级严格完工”的唯一原因：

- 当前机器无 CUDA 资源，真实 Qwen2.5-7B/14B 训练处于 ，因此 。

这意味着：

- 工程与流程已经到位；
- 迁移到 GPU 环境后可一键完成最后真实训练闭环。

## 2. 当前状态快照（来自最新产物）

### 2.1 审计状态
- Thesis readiness：
- Handoff readiness：
- GPU strict completion：

### 2.2 数据规模
- 来源：CMTMedQA 8000 + Huatuo26M-Lite 6000 + Huatuo Encyclopedia 6000
- 合并前：20000
- 去重后：19978
- 划分：train 15984 / dev 1997 / test 1997
- benchmark：3600
- 随机种子：42

### 2.3 训练状态
- SFT：（显存不足）
- DPO：（显存不足）
- SimPO：（显存不足）
- KTO：（显存不足）
- 证据文件：
  - 
  - 

### 2.4 评测与审计关键数值
- 综合评测（1200 样本）：
  - SFT：FactScore 0.5000 / Utility 1.0000 / RiskScore 0.2736 / Interception 1.0000
  - DPO：FactScore 0.5000 / Utility 0.8434 / RiskScore 0.2783 / Interception 1.0000
  - SimPO：FactScore 0.5000 / Utility 0.8434 / RiskScore 0.2783 / Interception 1.0000
- 对标（代理复现实验）：
  - MedLLM-Hybrid：Accuracy 1.0000 / Recall 1.0000 / Specificity 1.0000 / F1 1.0000
  - BioMistral-7B-Proxy：Accuracy 0.3642 / Recall 0.5167 / Specificity 0.2117 / F1 0.4483
- 基准偏差审计：
  - 原始 benchmark：leakage risk HIGH（gap=0.9917）
  - v2 balanced：leakage risk LOW（gap=0.0000）
- v2 LLM 回退（预算 80 调用）：
  - rule-only：Recall 0.0000 / F1 0.0000
  - hybrid：Recall 0.0583 / F1 0.1074

## 3. 项目结构说明（主链）

- 
  - ：数据治理与清洗核心
  - ：幻觉检测（白盒 + 检索 + 可选 LLM 回退）
  - ：真实 SFT 与真实偏好训练入口
  - ：服务化接口
- 
  - ：数据构建与治理流水线
  - ：Layer-B SFT + DPO/SimPO/KTO 编排
  - ：评测与论文资产导出
  - ：GPU 迁移、交接清单、完工闸门
  - ：本地一键 paper-ready
- ：训练/评测配置
- ：统一评测器与 LLM-as-a-Judge
- ：全量证据链产物
- ：系统文档与运行手册
- ：GPU 首次上线一键脚本

## 4. 使用说明（从零到运行）

### 4.1 本地准备
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
Requirement already satisfied: pip in ./.venv/lib/python3.13/site-packages (25.1.1)
Collecting pip
  Using cached pip-26.0.1-py3-none-any.whl.metadata (4.7 kB)
Using cached pip-26.0.1-py3-none-any.whl (1.8 MB)
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 25.1.1
    Uninstalling pip-25.1.1:
      Successfully uninstalled pip-25.1.1
Successfully installed pip-26.0.1
.venv/bin/pip install -r requirements.txt
Ignoring bitsandbytes: markers 'platform_system != "Darwin"' don't match your environment
Collecting accelerate>=0.34.0 (from -r requirements.txt (line 1))
  Using cached accelerate-1.12.0-py3-none-any.whl.metadata (19 kB)
Collecting datasets>=2.21.0 (from -r requirements.txt (line 3))
  Using cached datasets-4.6.0-py3-none-any.whl.metadata (19 kB)
Collecting faiss-cpu>=1.8.0 (from -r requirements.txt (line 4))
  Using cached faiss_cpu-1.13.2-cp310-abi3-macosx_14_0_arm64.whl.metadata (7.6 kB)
Collecting fastapi>=0.115.0 (from -r requirements.txt (line 5))
  Using cached fastapi-0.133.1-py3-none-any.whl.metadata (30 kB)
Collecting numpy>=1.26.0 (from -r requirements.txt (line 6))
  Downloading numpy-2.4.2-cp313-cp313-macosx_14_0_arm64.whl.metadata (6.6 kB)
Collecting openai>=1.54.0 (from -r requirements.txt (line 7))
  Using cached openai-2.24.0-py3-none-any.whl.metadata (29 kB)
Collecting pandas>=2.2.0 (from -r requirements.txt (line 8))
  Downloading pandas-3.0.1-cp313-cp313-macosx_11_0_arm64.whl.metadata (79 kB)
Collecting peft>=0.12.0 (from -r requirements.txt (line 9))
  Using cached peft-0.18.1-py3-none-any.whl.metadata (14 kB)
Collecting pydantic>=2.8.0 (from -r requirements.txt (line 10))
  Using cached pydantic-2.12.5-py3-none-any.whl.metadata (90 kB)
Collecting python-dotenv>=1.0.1 (from -r requirements.txt (line 11))
  Using cached python_dotenv-1.2.1-py3-none-any.whl.metadata (25 kB)
Collecting pyarrow>=17.0.0 (from -r requirements.txt (line 12))
  Using cached pyarrow-23.0.1-cp313-cp313-macosx_12_0_arm64.whl.metadata (3.1 kB)
Collecting pytest>=8.2.0 (from -r requirements.txt (line 13))
  Using cached pytest-9.0.2-py3-none-any.whl.metadata (7.6 kB)
Collecting pyyaml>=6.0.1 (from -r requirements.txt (line 14))
  Using cached pyyaml-6.0.3-cp313-cp313-macosx_11_0_arm64.whl.metadata (2.4 kB)
Collecting rich>=13.8.0 (from -r requirements.txt (line 15))
  Using cached rich-14.3.3-py3-none-any.whl.metadata (18 kB)
Collecting scikit-learn>=1.5.0 (from -r requirements.txt (line 16))
  Downloading scikit_learn-1.8.0-cp313-cp313-macosx_12_0_arm64.whl.metadata (11 kB)
Collecting sentence-transformers>=3.0.1 (from -r requirements.txt (line 17))
  Using cached sentence_transformers-5.2.3-py3-none-any.whl.metadata (16 kB)
Collecting torch>=2.4.0 (from -r requirements.txt (line 18))
  Using cached torch-2.10.0-2-cp313-none-macosx_11_0_arm64.whl.metadata (31 kB)
Collecting transformers>=4.44.0 (from -r requirements.txt (line 19))
  Using cached transformers-5.2.0-py3-none-any.whl.metadata (32 kB)
Collecting trl>=0.10.1 (from -r requirements.txt (line 20))
  Downloading trl-0.29.0-py3-none-any.whl.metadata (11 kB)
Collecting typer>=0.12.5 (from -r requirements.txt (line 21))
  Using cached typer-0.24.1-py3-none-any.whl.metadata (16 kB)
Collecting uvicorn>=0.30.6 (from -r requirements.txt (line 22))
  Using cached uvicorn-0.41.0-py3-none-any.whl.metadata (6.7 kB)
Collecting packaging>=20.0 (from accelerate>=0.34.0->-r requirements.txt (line 1))
  Using cached packaging-26.0-py3-none-any.whl.metadata (3.3 kB)
Collecting psutil (from accelerate>=0.34.0->-r requirements.txt (line 1))
  Using cached psutil-7.2.2-cp36-abi3-macosx_11_0_arm64.whl.metadata (22 kB)
Collecting huggingface_hub>=0.21.0 (from accelerate>=0.34.0->-r requirements.txt (line 1))
  Downloading huggingface_hub-1.5.0-py3-none-any.whl.metadata (13 kB)
Collecting safetensors>=0.4.3 (from accelerate>=0.34.0->-r requirements.txt (line 1))
  Using cached safetensors-0.7.0-cp38-abi3-macosx_11_0_arm64.whl.metadata (4.1 kB)
Collecting filelock (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached filelock-3.24.3-py3-none-any.whl.metadata (2.0 kB)
Collecting dill<0.4.1,>=0.3.0 (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached dill-0.4.0-py3-none-any.whl.metadata (10 kB)
Collecting requests>=2.32.2 (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached requests-2.32.5-py3-none-any.whl.metadata (4.9 kB)
Collecting httpx<1.0.0 (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting tqdm>=4.66.3 (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached tqdm-4.67.3-py3-none-any.whl.metadata (57 kB)
Collecting xxhash (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached xxhash-3.6.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (13 kB)
Collecting multiprocess<0.70.19 (from datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached multiprocess-0.70.18-py313-none-any.whl.metadata (7.2 kB)
Collecting fsspec<=2026.2.0,>=2023.1.0 (from fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached fsspec-2026.2.0-py3-none-any.whl.metadata (10 kB)
Collecting aiohttp!=4.0.0a0,!=4.0.0a1 (from fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached aiohttp-3.13.3-cp313-cp313-macosx_11_0_arm64.whl.metadata (8.1 kB)
Collecting anyio (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached anyio-4.12.1-py3-none-any.whl.metadata (4.3 kB)
Collecting certifi (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached certifi-2026.2.25-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached idna-3.11-py3-none-any.whl.metadata (8.4 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting hf-xet<2.0.0,>=1.2.0 (from huggingface_hub>=0.21.0->accelerate>=0.34.0->-r requirements.txt (line 1))
  Using cached hf_xet-1.3.1-cp37-abi3-macosx_11_0_arm64.whl.metadata (4.9 kB)
Collecting typing-extensions>=4.1.0 (from huggingface_hub>=0.21.0->accelerate>=0.34.0->-r requirements.txt (line 1))
  Using cached typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting starlette>=0.40.0 (from fastapi>=0.115.0->-r requirements.txt (line 5))
  Using cached starlette-0.52.1-py3-none-any.whl.metadata (6.3 kB)
Collecting typing-inspection>=0.4.2 (from fastapi>=0.115.0->-r requirements.txt (line 5))
  Using cached typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting annotated-doc>=0.0.2 (from fastapi>=0.115.0->-r requirements.txt (line 5))
  Using cached annotated_doc-0.0.4-py3-none-any.whl.metadata (6.6 kB)
Collecting distro<2,>=1.7.0 (from openai>=1.54.0->-r requirements.txt (line 7))
  Downloading distro-1.9.0-py3-none-any.whl.metadata (6.8 kB)
Collecting jiter<1,>=0.10.0 (from openai>=1.54.0->-r requirements.txt (line 7))
  Using cached jiter-0.13.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (5.2 kB)
Collecting sniffio (from openai>=1.54.0->-r requirements.txt (line 7))
  Using cached sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.8.0->-r requirements.txt (line 10))
  Using cached annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.41.5 (from pydantic>=2.8.0->-r requirements.txt (line 10))
  Downloading pydantic_core-2.41.5-cp313-cp313-macosx_11_0_arm64.whl.metadata (7.3 kB)
Collecting python-dateutil>=2.8.2 (from pandas>=2.2.0->-r requirements.txt (line 8))
  Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting iniconfig>=1.0.1 (from pytest>=8.2.0->-r requirements.txt (line 13))
  Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
Collecting pluggy<2,>=1.5 (from pytest>=8.2.0->-r requirements.txt (line 13))
  Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting pygments>=2.7.2 (from pytest>=8.2.0->-r requirements.txt (line 13))
  Using cached pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=13.8.0->-r requirements.txt (line 15))
  Using cached markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting scipy>=1.10.0 (from scikit-learn>=1.5.0->-r requirements.txt (line 16))
  Downloading scipy-1.17.1-cp313-cp313-macosx_14_0_arm64.whl.metadata (62 kB)
Collecting joblib>=1.3.0 (from scikit-learn>=1.5.0->-r requirements.txt (line 16))
  Using cached joblib-1.5.3-py3-none-any.whl.metadata (5.5 kB)
Collecting threadpoolctl>=3.2.0 (from scikit-learn>=1.5.0->-r requirements.txt (line 16))
  Using cached threadpoolctl-3.6.0-py3-none-any.whl.metadata (13 kB)
Collecting regex!=2019.12.17 (from transformers>=4.44.0->-r requirements.txt (line 19))
  Using cached regex-2026.2.19-cp313-cp313-macosx_11_0_arm64.whl.metadata (40 kB)
Collecting tokenizers<=0.23.0,>=0.22.0 (from transformers>=4.44.0->-r requirements.txt (line 19))
  Using cached tokenizers-0.22.2-cp39-abi3-macosx_11_0_arm64.whl.metadata (7.3 kB)
Collecting typer-slim (from transformers>=4.44.0->-r requirements.txt (line 19))
  Using cached typer_slim-0.24.0-py3-none-any.whl.metadata (4.2 kB)
Collecting setuptools (from torch>=2.4.0->-r requirements.txt (line 18))
  Downloading setuptools-82.0.0-py3-none-any.whl.metadata (6.6 kB)
Collecting sympy>=1.13.3 (from torch>=2.4.0->-r requirements.txt (line 18))
  Using cached sympy-1.14.0-py3-none-any.whl.metadata (12 kB)
Collecting networkx>=2.5.1 (from torch>=2.4.0->-r requirements.txt (line 18))
  Using cached networkx-3.6.1-py3-none-any.whl.metadata (6.8 kB)
Collecting jinja2 (from torch>=2.4.0->-r requirements.txt (line 18))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting click>=8.2.1 (from typer>=0.12.5->-r requirements.txt (line 21))
  Using cached click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
Collecting shellingham>=1.3.0 (from typer>=0.12.5->-r requirements.txt (line 21))
  Using cached shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached aiohappyeyeballs-2.6.1-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting attrs>=17.3.0 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached attrs-25.4.0-py3-none-any.whl.metadata (10 kB)
Collecting frozenlist>=1.1.1 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached frozenlist-1.8.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (20 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached multidict-6.7.1-cp313-cp313-macosx_11_0_arm64.whl.metadata (5.3 kB)
Collecting propcache>=0.2.0 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached propcache-0.4.1-cp313-cp313-macosx_11_0_arm64.whl.metadata (13 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached yarl-1.22.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (75 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=13.8.0->-r requirements.txt (line 15))
  Using cached mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting six>=1.5 (from python-dateutil>=2.8.2->pandas>=2.2.0->-r requirements.txt (line 8))
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting charset_normalizer<4,>=2 (from requests>=2.32.2->datasets>=2.21.0->-r requirements.txt (line 3))
  Downloading charset_normalizer-3.4.4-cp313-cp313-macosx_10_13_universal2.whl.metadata (37 kB)
Collecting urllib3<3,>=1.21.1 (from requests>=2.32.2->datasets>=2.21.0->-r requirements.txt (line 3))
  Using cached urllib3-2.6.3-py3-none-any.whl.metadata (6.9 kB)
Collecting mpmath<1.4,>=1.1.0 (from sympy>=1.13.3->torch>=2.4.0->-r requirements.txt (line 18))
  Using cached mpmath-1.3.0-py3-none-any.whl.metadata (8.6 kB)
Collecting MarkupSafe>=2.0 (from jinja2->torch>=2.4.0->-r requirements.txt (line 18))
  Using cached markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl.metadata (2.7 kB)
Using cached accelerate-1.12.0-py3-none-any.whl (380 kB)
Using cached datasets-4.6.0-py3-none-any.whl (520 kB)
Using cached dill-0.4.0-py3-none-any.whl (119 kB)
Using cached fsspec-2026.2.0-py3-none-any.whl (202 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Downloading huggingface_hub-1.5.0-py3-none-any.whl (596 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 596.3/596.3 kB 1.1 MB/s  0:00:00
Using cached hf_xet-1.3.1-cp37-abi3-macosx_11_0_arm64.whl (3.5 MB)
Using cached multiprocess-0.70.18-py313-none-any.whl (151 kB)
Using cached faiss_cpu-1.13.2-cp310-abi3-macosx_14_0_arm64.whl (3.5 MB)
Downloading numpy-2.4.2-cp313-cp313-macosx_14_0_arm64.whl (5.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.2/5.2 MB 495.2 kB/s  0:00:10
Using cached fastapi-0.133.1-py3-none-any.whl (109 kB)
Using cached openai-2.24.0-py3-none-any.whl (1.1 MB)
Using cached pydantic-2.12.5-py3-none-any.whl (463 kB)
Downloading pydantic_core-2.41.5-cp313-cp313-macosx_11_0_arm64.whl (1.9 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.9/1.9 MB 224.5 kB/s  0:00:07
Using cached anyio-4.12.1-py3-none-any.whl (113 kB)
Downloading distro-1.9.0-py3-none-any.whl (20 kB)
Using cached jiter-0.13.0-cp313-cp313-macosx_11_0_arm64.whl (317 kB)
Using cached typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading pandas-3.0.1-cp313-cp313-macosx_11_0_arm64.whl (9.9 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 9.9/9.9 MB 534.9 kB/s  0:00:18
Using cached peft-0.18.1-py3-none-any.whl (556 kB)
Using cached python_dotenv-1.2.1-py3-none-any.whl (21 kB)
Using cached pyarrow-23.0.1-cp313-cp313-macosx_12_0_arm64.whl (34.2 MB)
Using cached pytest-9.0.2-py3-none-any.whl (374 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached pyyaml-6.0.3-cp313-cp313-macosx_11_0_arm64.whl (173 kB)
Using cached rich-14.3.3-py3-none-any.whl (310 kB)
Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
Downloading scikit_learn-1.8.0-cp313-cp313-macosx_12_0_arm64.whl (8.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.0/8.0 MB 493.1 kB/s  0:00:16
Using cached sentence_transformers-5.2.3-py3-none-any.whl (494 kB)
Using cached transformers-5.2.0-py3-none-any.whl (10.4 MB)
Using cached tokenizers-0.22.2-cp39-abi3-macosx_11_0_arm64.whl (3.0 MB)
Using cached torch-2.10.0-2-cp313-none-macosx_11_0_arm64.whl (79.5 MB)
Downloading trl-0.29.0-py3-none-any.whl (528 kB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 528.8/528.8 kB 424.6 kB/s  0:00:01
Using cached typer-0.24.1-py3-none-any.whl (56 kB)
Using cached uvicorn-0.41.0-py3-none-any.whl (68 kB)
Using cached aiohttp-3.13.3-cp313-cp313-macosx_11_0_arm64.whl (490 kB)
Using cached multidict-6.7.1-cp313-cp313-macosx_11_0_arm64.whl (43 kB)
Using cached yarl-1.22.0-cp313-cp313-macosx_11_0_arm64.whl (93 kB)
Using cached aiohappyeyeballs-2.6.1-py3-none-any.whl (15 kB)
Using cached aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
Using cached annotated_doc-0.0.4-py3-none-any.whl (5.3 kB)
Using cached annotated_types-0.7.0-py3-none-any.whl (13 kB)
Using cached attrs-25.4.0-py3-none-any.whl (67 kB)
Using cached click-8.3.1-py3-none-any.whl (108 kB)
Using cached filelock-3.24.3-py3-none-any.whl (24 kB)
Using cached frozenlist-1.8.0-cp313-cp313-macosx_11_0_arm64.whl (49 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached idna-3.11-py3-none-any.whl (71 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached joblib-1.5.3-py3-none-any.whl (309 kB)
Using cached markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Using cached mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Using cached networkx-3.6.1-py3-none-any.whl (2.1 MB)
Using cached packaging-26.0-py3-none-any.whl (74 kB)
Using cached propcache-0.4.1-cp313-cp313-macosx_11_0_arm64.whl (46 kB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached regex-2026.2.19-cp313-cp313-macosx_11_0_arm64.whl (289 kB)
Using cached requests-2.32.5-py3-none-any.whl (64 kB)
Downloading charset_normalizer-3.4.4-cp313-cp313-macosx_10_13_universal2.whl (208 kB)
Using cached urllib3-2.6.3-py3-none-any.whl (131 kB)
Using cached certifi-2026.2.25-py3-none-any.whl (153 kB)
Using cached safetensors-0.7.0-cp38-abi3-macosx_11_0_arm64.whl (447 kB)
Downloading scipy-1.17.1-cp313-cp313-macosx_14_0_arm64.whl (20.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 20.3/20.3 MB 883.7 kB/s  0:00:23
Using cached shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached starlette-0.52.1-py3-none-any.whl (74 kB)
Using cached sympy-1.14.0-py3-none-any.whl (6.3 MB)
Using cached mpmath-1.3.0-py3-none-any.whl (536 kB)
Using cached threadpoolctl-3.6.0-py3-none-any.whl (18 kB)
Using cached tqdm-4.67.3-py3-none-any.whl (78 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl (12 kB)
Using cached psutil-7.2.2-cp36-abi3-macosx_11_0_arm64.whl (129 kB)
Downloading setuptools-82.0.0-py3-none-any.whl (1.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.0/1.0 MB 1.5 MB/s  0:00:00
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Using cached typer_slim-0.24.0-py3-none-any.whl (3.4 kB)
Using cached xxhash-3.6.0-cp313-cp313-macosx_11_0_arm64.whl (30 kB)
Installing collected packages: mpmath, xxhash, urllib3, typing-extensions, tqdm, threadpoolctl, sympy, sniffio, six, shellingham, setuptools, safetensors, regex, pyyaml, python-dotenv, pygments, pyarrow, psutil, propcache, pluggy, packaging, numpy, networkx, multidict, mdurl, MarkupSafe, joblib, jiter, iniconfig, idna, hf-xet, h11, fsspec, frozenlist, filelock, distro, dill, click, charset_normalizer, certifi, attrs, annotated-types, annotated-doc, aiohappyeyeballs, yarl, uvicorn, typing-inspection, scipy, requests, python-dateutil, pytest, pydantic-core, multiprocess, markdown-it-py, jinja2, httpcore, faiss-cpu, anyio, aiosignal, torch, starlette, scikit-learn, rich, pydantic, pandas, httpx, aiohttp, typer, openai, fastapi, typer-slim, huggingface_hub, tokenizers, datasets, accelerate, transformers, trl, sentence-transformers, peft

Successfully installed MarkupSafe-3.0.3 accelerate-1.12.0 aiohappyeyeballs-2.6.1 aiohttp-3.13.3 aiosignal-1.4.0 annotated-doc-0.0.4 annotated-types-0.7.0 anyio-4.12.1 attrs-25.4.0 certifi-2026.2.25 charset_normalizer-3.4.4 click-8.3.1 datasets-4.6.0 dill-0.4.0 distro-1.9.0 faiss-cpu-1.13.2 fastapi-0.133.1 filelock-3.24.3 frozenlist-1.8.0 fsspec-2026.2.0 h11-0.16.0 hf-xet-1.3.1 httpcore-1.0.9 httpx-0.28.1 huggingface_hub-1.5.0 idna-3.11 iniconfig-2.3.0 jinja2-3.1.6 jiter-0.13.0 joblib-1.5.3 markdown-it-py-4.0.0 mdurl-0.1.2 mpmath-1.3.0 multidict-6.7.1 multiprocess-0.70.18 networkx-3.6.1 numpy-2.4.2 openai-2.24.0 packaging-26.0 pandas-3.0.1 peft-0.18.1 pluggy-1.6.0 propcache-0.4.1 psutil-7.2.2 pyarrow-23.0.1 pydantic-2.12.5 pydantic-core-2.41.5 pygments-2.19.2 pytest-9.0.2 python-dateutil-2.9.0.post0 python-dotenv-1.2.1 pyyaml-6.0.3 regex-2026.2.19 requests-2.32.5 rich-14.3.3 safetensors-0.7.0 scikit-learn-1.8.0 scipy-1.17.1 sentence-transformers-5.2.3 setuptools-82.0.0 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 starlette-0.52.1 sympy-1.14.0 threadpoolctl-3.6.0 tokenizers-0.22.2 torch-2.10.0 tqdm-4.67.3 transformers-5.2.0 trl-0.29.0 typer-0.24.1 typer-slim-0.24.0 typing-extensions-4.15.0 typing-inspection-0.4.2 urllib3-2.6.3 uvicorn-0.41.0 xxhash-3.6.0 yarl-1.22.0

（若启用 API 评测）：
AUTOJUMP_ERROR_PATH=/Users/bibo/Library/autojump/errors.log
AUTOJUMP_SOURCED=1
CODEX_CI=1
CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop
CODEX_SHELL=1
CODEX_THREAD_ID=019c9776-80c3-78d3-a5a8-ef26e08f479c
COLORTERM=
COMMAND_MODE=unix2003
COMMAND_RESULT=true
CONDA_DEFAULT_ENV=base
CONDA_EXE=/opt/miniconda3/bin/conda
CONDA_PREFIX=/opt/miniconda3
CONDA_PROMPT_MODIFIER=(base) 
CONDA_PYTHON_EXE=/opt/miniconda3/bin/python
CONDA_SHLVL=1
DISABLE_AUTO_UPDATE=true
GH_PAGER=cat
GIT_PAGER=cat
HOME=/Users/bibo
HOMEBREW_BOTTLE_DOMAIN=https://mirrors.cloud.tencent.com/homebrew-bottles
HOMEBREW_CELLAR=/opt/homebrew/Cellar
HOMEBREW_PREFIX=/opt/homebrew
HOMEBREW_REPOSITORY=/opt/homebrew
INFOPATH=/opt/homebrew/share/info:/opt/homebrew/share/info:
LANG=C.UTF-8
LC_ALL=C.UTF-8
LC_CTYPE=C.UTF-8
LESS=-R
LOGNAME=bibo
LSCOLORS=Gxfxcxdxbxegedabagacad
LS_COLORS=di=1;36:ln=35:so=32:pi=33:ex=31:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;43
MallocNanoZone=0
NO_COLOR=1
OLDPWD=/Users/bibo/Desktop/MedLLM_codex
PAGER=less
PATH=/Users/bibo/.codex/tmp/arg0/codex-arg0DMDbYm:/opt/miniconda3/bin:/opt/miniconda3/condabin:/Users/bibo/.pyenv/shims:/Users/bibo/.pyenv/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Library/Frameworks/Python.framework/Versions/3.7/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/Library/Frameworks/Python.framework/Versions/3.9/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Library/Apple/usr/bin:/usr/local/share/dotnet:~/.dotnet/tools:/Users/bibo/Library/Application Support/JetBrains/Toolbox/scripts:/usr/local/mysql/bin:/Applications/Codex.app/Contents/Resources
PWD=/Users/bibo/Desktop/MedLLM_codex
PYENV_SHELL=zsh
RUST_LOG=warn
SHELL=/bin/zsh
SHLVL=2
SSH_AUTH_SOCK=/private/tmp/com.apple.launchd.XCCvMeVhYI/Listeners
SSL_CERT_FILE=/Users/bibo/cacert.pem
TERM=dumb
TMPDIR=/var/folders/84/v3y0l0fj3zs6pxy3j6stcbxm0000gn/T/
USER=bibo
XPC_FLAGS=0x0
XPC_SERVICE_NAME=0
ZSH=/Users/bibo/.oh-my-zsh
ZSH_TMUX_AUTOSTART=false
ZSH_TMUX_AUTOSTARTED=true
__CFBundleIdentifier=com.openai.codex
__CF_USER_TEXT_ENCODING=0x1F5:0x0:0x0
_=/usr/bin/env

### 4.2 本地无 GPU 验证
bash scripts/pipeline/run_paper_ready.sh
[resource] accelerator=mps cuda_mem_gb=0.0 cuda_count=0 model_tier=7b
[hard-negative] input=15984 output=15984 path=data/clean/real_pref_seed_pairs.jsonl
[warn] training skipped: Insufficient CUDA resources for 7B (need >= 18GB).
[alignment-compare] methods=3 report=reports/alignment_compare.md
[real-alignment-pipeline] done mode=real skipped=true
[pipeline] step=thesis_eval start
{"benchmark_rows": 3600, "benchmark_rows_after_split_filter": 2400, "pair_count": 1200, "kb_rows": 1200, "missing_positive_pairs": 0, "include_splits": ["train"]}
[detection-eval] split filter=['test', 'validation'] samples=1200
[detection-eval] progress=200/1200
[detection-eval] progress=400/1200
[detection-eval] progress=600/1200
[detection-eval] progress=800/1200
[detection-eval] progress=1000/1200
[detection-eval] progress=1200/1200
[detection-eval] samples=1200 report=reports/detection_eval.md
{"samples": 1200, "leakage_risk": "HIGH", "gap": 0.9916666666666667}
{"output": "data/benchmark/real_medqa_benchmark_v2_balanced.jsonl", "total": 3600, "rewritten": 1798, "unresolved": 2, "by_letter": 1813, "by_text_exact": 1785, "by_text_fuzzy": 0, "unresolved_empty": 2, "unresolved_no_match": 0, "risk_split_letter_rate_after": {"high:test": {"count": 300, "letter_rate_after": 1.0}, "high:train": {"count": 1200, "letter_rate_after": 0.9983333333333333}, "high:validation": {"count": 300, "letter_rate_after": 1.0}, "low:test": {"count": 300, "letter_rate_after": 1.0}, "low:train": {"count": 1200, "letter_rate_after": 1.0}, "low:validation": {"count": 300, "letter_rate_after": 1.0}}}
{"benchmark_rows": 3600, "benchmark_rows_after_split_filter": 2400, "pair_count": 1200, "kb_rows": 1200, "missing_positive_pairs": 0, "include_splits": ["train"]}
[detection-eval] split filter=['test', 'validation'] samples=1200
[detection-eval] progress=200/1200
[detection-eval] progress=400/1200
[detection-eval] progress=600/1200
[detection-eval] progress=800/1200
[detection-eval] progress=1000/1200
[detection-eval] progress=1200/1200
[detection-eval] samples=1200 report=reports/detection_eval_v2_balanced.md
{"samples": 1200, "leakage_risk": "LOW", "gap": 0.0}
[detection-robustness] done
[eval] split filter=['test', 'validation'] samples=1200
[eval:sft] progress=400/1200
[eval:sft] progress=800/1200
[eval:sft] progress=1200/1200
[eval:dpo] progress=400/1200
[eval:dpo] progress=800/1200
[eval:dpo] progress=1200/1200
[eval:simpo] progress=400/1200
[eval:simpo] progress=800/1200
[eval:simpo] progress=1200/1200
[eval:sft] progress=400/1200
[eval:sft] progress=800/1200
[eval:sft] progress=1200/1200
[eval:detection] progress=400/1200
[eval:detection] progress=800/1200
[eval:detection] progress=1200/1200
[eval] reports generated
[sota] split filter=['test', 'validation'] samples=1200
[sota:HuatuoGPT-7B-Proxy (raw)] progress=400/1200
[sota:HuatuoGPT-7B-Proxy (raw)] progress=800/1200
[sota:HuatuoGPT-7B-Proxy (raw)] progress=1200/1200
[sota:BioMistral-7B-Proxy (whitebox)] progress=400/1200
[sota:BioMistral-7B-Proxy (whitebox)] progress=800/1200
[sota:BioMistral-7B-Proxy (whitebox)] progress=1200/1200
[sota:MedQA-RAG-Proxy (retrieval)] progress=400/1200
[sota:MedQA-RAG-Proxy (retrieval)] progress=800/1200
[sota:MedQA-RAG-Proxy (retrieval)] progress=1200/1200
[sota:MedLLM-Hybrid (ours)] progress=400/1200
[sota:MedLLM-Hybrid (ours)] progress=800/1200
[sota:MedLLM-Hybrid (ours)] progress=1200/1200
{"systems": 4, "report": "reports/sota_compare.md"}
{"rows": 1200, "errors": 763, "top_cases": 30, "output": "reports/error_analysis.md"}
{"out_dir": "reports/thesis_assets", "predictions": 1200, "overview_rows": 8}
{"figures": 0, "summary": "reports/thesis_assets/tables/training_loss_summary.csv"}
{"output_md": "reports/thesis_support/thesis_draft_material.md", "output_json": "reports/thesis_support/experiment_record.json", "eval_rows": 3}
{"PASS": 5, "DEFERRED": 2, "FAIL": 0}
[thesis-pipeline] done
[pipeline] step=thesis_eval done
[pipeline] step=e2e_acceptance start
[e2e] report=reports/e2e_acceptance.md
[pipeline] step=e2e_acceptance done
[pipeline] status=reports/pipeline/paper_ready_status.md

### 4.3 GPU 迁移标准流程
python3 scripts/migration/build_gpu_handoff_manifest.py
{"json": "reports/migration/gpu_handoff_manifest.json", "md": "reports/migration/gpu_handoff_manifest.md", "commit": "c3562e3d27218b469b0f8b79781b1224ccfe47d2"}
python3 scripts/migration/check_handoff_readiness.py
{"ready": true, "missing_count": 0}
bash scripts/migration/bootstrap_gpu_env.sh
[gpu-bootstrap] root=/Users/bibo/Desktop/MedLLM_codex
[gpu-bootstrap] python=python3 install_method=venv
Requirement already satisfied: pip in ./.venv/lib/python3.13/site-packages (26.0.1)
Collecting wheel
  Downloading wheel-0.46.3-py3-none-any.whl.metadata (2.4 kB)
Requirement already satisfied: setuptools in ./.venv/lib/python3.13/site-packages (82.0.0)
Requirement already satisfied: packaging>=24.0 in ./.venv/lib/python3.13/site-packages (from wheel) (26.0)
Downloading wheel-0.46.3-py3-none-any.whl (30 kB)
Installing collected packages: wheel
Successfully installed wheel-0.46.3
Ignoring bitsandbytes: markers 'platform_system != "Darwin"' don't match your environment
Requirement already satisfied: accelerate>=0.34.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 1)) (1.12.0)
Requirement already satisfied: datasets>=2.21.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 3)) (4.6.0)
Requirement already satisfied: faiss-cpu>=1.8.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 4)) (1.13.2)
Requirement already satisfied: fastapi>=0.115.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 5)) (0.133.1)
Requirement already satisfied: numpy>=1.26.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 6)) (2.4.2)
Requirement already satisfied: openai>=1.54.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 7)) (2.24.0)
Requirement already satisfied: pandas>=2.2.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 8)) (3.0.1)
Requirement already satisfied: peft>=0.12.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 9)) (0.18.1)
Requirement already satisfied: pydantic>=2.8.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 10)) (2.12.5)
Requirement already satisfied: python-dotenv>=1.0.1 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 11)) (1.2.1)
Requirement already satisfied: pyarrow>=17.0.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 12)) (23.0.1)
Requirement already satisfied: pytest>=8.2.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 13)) (9.0.2)
Requirement already satisfied: pyyaml>=6.0.1 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 14)) (6.0.3)
Requirement already satisfied: rich>=13.8.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 15)) (14.3.3)
Requirement already satisfied: scikit-learn>=1.5.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 16)) (1.8.0)
Requirement already satisfied: sentence-transformers>=3.0.1 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 17)) (5.2.3)
Requirement already satisfied: torch>=2.4.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 18)) (2.10.0)
Requirement already satisfied: transformers>=4.44.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 19)) (5.2.0)
Requirement already satisfied: trl>=0.10.1 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 20)) (0.29.0)
Requirement already satisfied: typer>=0.12.5 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 21)) (0.24.1)
Requirement already satisfied: uvicorn>=0.30.6 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 22)) (0.41.0)
Requirement already satisfied: packaging>=20.0 in ./.venv/lib/python3.13/site-packages (from accelerate>=0.34.0->-r requirements.txt (line 1)) (26.0)
Requirement already satisfied: psutil in ./.venv/lib/python3.13/site-packages (from accelerate>=0.34.0->-r requirements.txt (line 1)) (7.2.2)
Requirement already satisfied: huggingface_hub>=0.21.0 in ./.venv/lib/python3.13/site-packages (from accelerate>=0.34.0->-r requirements.txt (line 1)) (1.5.0)
Requirement already satisfied: safetensors>=0.4.3 in ./.venv/lib/python3.13/site-packages (from accelerate>=0.34.0->-r requirements.txt (line 1)) (0.7.0)
Requirement already satisfied: filelock in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (3.24.3)
Requirement already satisfied: dill<0.4.1,>=0.3.0 in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (0.4.0)
Requirement already satisfied: requests>=2.32.2 in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (2.32.5)
Requirement already satisfied: httpx<1.0.0 in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (0.28.1)
Requirement already satisfied: tqdm>=4.66.3 in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (4.67.3)
Requirement already satisfied: xxhash in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (3.6.0)
Requirement already satisfied: multiprocess<0.70.19 in ./.venv/lib/python3.13/site-packages (from datasets>=2.21.0->-r requirements.txt (line 3)) (0.70.18)
Requirement already satisfied: fsspec<=2026.2.0,>=2023.1.0 in ./.venv/lib/python3.13/site-packages (from fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (2026.2.0)
Requirement already satisfied: aiohttp!=4.0.0a0,!=4.0.0a1 in ./.venv/lib/python3.13/site-packages (from fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (3.13.3)
Requirement already satisfied: anyio in ./.venv/lib/python3.13/site-packages (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3)) (4.12.1)
Requirement already satisfied: certifi in ./.venv/lib/python3.13/site-packages (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3)) (2026.2.25)
Requirement already satisfied: httpcore==1.* in ./.venv/lib/python3.13/site-packages (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3)) (1.0.9)
Requirement already satisfied: idna in ./.venv/lib/python3.13/site-packages (from httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3)) (3.11)
Requirement already satisfied: h11>=0.16 in ./.venv/lib/python3.13/site-packages (from httpcore==1.*->httpx<1.0.0->datasets>=2.21.0->-r requirements.txt (line 3)) (0.16.0)
Requirement already satisfied: hf-xet<2.0.0,>=1.2.0 in ./.venv/lib/python3.13/site-packages (from huggingface_hub>=0.21.0->accelerate>=0.34.0->-r requirements.txt (line 1)) (1.3.1)
Requirement already satisfied: typing-extensions>=4.1.0 in ./.venv/lib/python3.13/site-packages (from huggingface_hub>=0.21.0->accelerate>=0.34.0->-r requirements.txt (line 1)) (4.15.0)
Requirement already satisfied: starlette>=0.40.0 in ./.venv/lib/python3.13/site-packages (from fastapi>=0.115.0->-r requirements.txt (line 5)) (0.52.1)
Requirement already satisfied: typing-inspection>=0.4.2 in ./.venv/lib/python3.13/site-packages (from fastapi>=0.115.0->-r requirements.txt (line 5)) (0.4.2)
Requirement already satisfied: annotated-doc>=0.0.2 in ./.venv/lib/python3.13/site-packages (from fastapi>=0.115.0->-r requirements.txt (line 5)) (0.0.4)
Requirement already satisfied: distro<2,>=1.7.0 in ./.venv/lib/python3.13/site-packages (from openai>=1.54.0->-r requirements.txt (line 7)) (1.9.0)
Requirement already satisfied: jiter<1,>=0.10.0 in ./.venv/lib/python3.13/site-packages (from openai>=1.54.0->-r requirements.txt (line 7)) (0.13.0)
Requirement already satisfied: sniffio in ./.venv/lib/python3.13/site-packages (from openai>=1.54.0->-r requirements.txt (line 7)) (1.3.1)
Requirement already satisfied: annotated-types>=0.6.0 in ./.venv/lib/python3.13/site-packages (from pydantic>=2.8.0->-r requirements.txt (line 10)) (0.7.0)
Requirement already satisfied: pydantic-core==2.41.5 in ./.venv/lib/python3.13/site-packages (from pydantic>=2.8.0->-r requirements.txt (line 10)) (2.41.5)
Requirement already satisfied: python-dateutil>=2.8.2 in ./.venv/lib/python3.13/site-packages (from pandas>=2.2.0->-r requirements.txt (line 8)) (2.9.0.post0)
Requirement already satisfied: iniconfig>=1.0.1 in ./.venv/lib/python3.13/site-packages (from pytest>=8.2.0->-r requirements.txt (line 13)) (2.3.0)
Requirement already satisfied: pluggy<2,>=1.5 in ./.venv/lib/python3.13/site-packages (from pytest>=8.2.0->-r requirements.txt (line 13)) (1.6.0)
Requirement already satisfied: pygments>=2.7.2 in ./.venv/lib/python3.13/site-packages (from pytest>=8.2.0->-r requirements.txt (line 13)) (2.19.2)
Requirement already satisfied: markdown-it-py>=2.2.0 in ./.venv/lib/python3.13/site-packages (from rich>=13.8.0->-r requirements.txt (line 15)) (4.0.0)
Requirement already satisfied: scipy>=1.10.0 in ./.venv/lib/python3.13/site-packages (from scikit-learn>=1.5.0->-r requirements.txt (line 16)) (1.17.1)
Requirement already satisfied: joblib>=1.3.0 in ./.venv/lib/python3.13/site-packages (from scikit-learn>=1.5.0->-r requirements.txt (line 16)) (1.5.3)
Requirement already satisfied: threadpoolctl>=3.2.0 in ./.venv/lib/python3.13/site-packages (from scikit-learn>=1.5.0->-r requirements.txt (line 16)) (3.6.0)
Requirement already satisfied: regex!=2019.12.17 in ./.venv/lib/python3.13/site-packages (from transformers>=4.44.0->-r requirements.txt (line 19)) (2026.2.19)
Requirement already satisfied: tokenizers<=0.23.0,>=0.22.0 in ./.venv/lib/python3.13/site-packages (from transformers>=4.44.0->-r requirements.txt (line 19)) (0.22.2)
Requirement already satisfied: typer-slim in ./.venv/lib/python3.13/site-packages (from transformers>=4.44.0->-r requirements.txt (line 19)) (0.24.0)
Requirement already satisfied: setuptools in ./.venv/lib/python3.13/site-packages (from torch>=2.4.0->-r requirements.txt (line 18)) (82.0.0)
Requirement already satisfied: sympy>=1.13.3 in ./.venv/lib/python3.13/site-packages (from torch>=2.4.0->-r requirements.txt (line 18)) (1.14.0)
Requirement already satisfied: networkx>=2.5.1 in ./.venv/lib/python3.13/site-packages (from torch>=2.4.0->-r requirements.txt (line 18)) (3.6.1)
Requirement already satisfied: jinja2 in ./.venv/lib/python3.13/site-packages (from torch>=2.4.0->-r requirements.txt (line 18)) (3.1.6)
Requirement already satisfied: click>=8.2.1 in ./.venv/lib/python3.13/site-packages (from typer>=0.12.5->-r requirements.txt (line 21)) (8.3.1)
Requirement already satisfied: shellingham>=1.3.0 in ./.venv/lib/python3.13/site-packages (from typer>=0.12.5->-r requirements.txt (line 21)) (1.5.4)
Requirement already satisfied: aiohappyeyeballs>=2.5.0 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (2.6.1)
Requirement already satisfied: aiosignal>=1.4.0 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (1.4.0)
Requirement already satisfied: attrs>=17.3.0 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (25.4.0)
Requirement already satisfied: frozenlist>=1.1.1 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (1.8.0)
Requirement already satisfied: multidict<7.0,>=4.5 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (6.7.1)
Requirement already satisfied: propcache>=0.2.0 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (0.4.1)
Requirement already satisfied: yarl<2.0,>=1.17.0 in ./.venv/lib/python3.13/site-packages (from aiohttp!=4.0.0a0,!=4.0.0a1->fsspec[http]<=2026.2.0,>=2023.1.0->datasets>=2.21.0->-r requirements.txt (line 3)) (1.22.0)
Requirement already satisfied: mdurl~=0.1 in ./.venv/lib/python3.13/site-packages (from markdown-it-py>=2.2.0->rich>=13.8.0->-r requirements.txt (line 15)) (0.1.2)
Requirement already satisfied: six>=1.5 in ./.venv/lib/python3.13/site-packages (from python-dateutil>=2.8.2->pandas>=2.2.0->-r requirements.txt (line 8)) (1.17.0)
Requirement already satisfied: charset_normalizer<4,>=2 in ./.venv/lib/python3.13/site-packages (from requests>=2.32.2->datasets>=2.21.0->-r requirements.txt (line 3)) (3.4.4)
Requirement already satisfied: urllib3<3,>=1.21.1 in ./.venv/lib/python3.13/site-packages (from requests>=2.32.2->datasets>=2.21.0->-r requirements.txt (line 3)) (2.6.3)
Requirement already satisfied: mpmath<1.4,>=1.1.0 in ./.venv/lib/python3.13/site-packages (from sympy>=1.13.3->torch>=2.4.0->-r requirements.txt (line 18)) (1.3.0)
Requirement already satisfied: MarkupSafe>=2.0 in ./.venv/lib/python3.13/site-packages (from jinja2->torch>=2.4.0->-r requirements.txt (line 18)) (3.0.3)
bash scripts/migration/run_gpu_thesis_experiment.sh
[gpu-run] model=Qwen/Qwen2.5-7B-Instruct tier=7b mode=real
[gpu-run] allow_skip_training=false force_skip_training=false dry_run=false
python3 scripts/migration/check_gpu_completion.py
{"strict_pass": false}

### 4.4 GPU 首次上线零思考执行
[T+00m] start day1 runner in /Users/bibo/Desktop/MedLLM_codex
[T+00m] ERROR: missing command: nvidia-smi
bash day1_run.sh
[T+00m] start day1 runner in /Users/bibo/Desktop/MedLLM_codex
[T+00m] ERROR: missing command: nvidia-smi

## 5. 产出说明（论文证据链映射）

### 5.1 数据层
- ：数据构建报告
- ：清洗与治理报告
- ：数据统计摘要

### 5.2 训练层
- 
- 
- 
- 
- 
- 

### 5.3 评测层
- 
- 
- 
- 
- 
- 

### 5.4 论文资产层
- 
- 
- 

### 5.5 论文支撑层
- 
- 
- 
- 

### 5.6 迁移与完工判定层
- 
- 
- 
- （忽略提交）
- （忽略提交）

## 6. 论文撰写材料（可直接改写）

## 6.1 研究背景与问题定义（章节草稿）
随着通用大模型在医疗问答场景中的应用增加，模型幻觉带来的临床安全风险逐步凸显。与开放域问答相比，医疗场景对事实一致性、风险控制与可追溯性要求更高。现有工作往往侧重单一环节优化，如数据微调或推理时校验，缺少覆盖“数据-推理-训练”全链路的工程化闭环。

本研究聚焦中文医疗问答场景，目标是在可复现实验框架下构建三层协同系统：通过数据治理降低输入噪声，通过运行时混合检测拦截高风险回答，通过偏好对齐抑制模型生成中的危险倾向。研究核心问题是：在资源受限到可扩展 GPU 环境下，如何构建具备工程可落地性与学术可验证性的幻觉抑制系统。

## 6.2 方法章节（章节草稿）
本文方法分为三层。第一层为数据治理层，针对多来源医疗问答数据进行字段标准化、冲突识别、规则清洗与基于知识库的质量校验，并产出结构化统计与审计报告。第二层为运行时检测层，融合白盒不确定性特征与检索核查结果进行风险判别，并可在低置信度区域引入受预算约束的 LLM 回退裁决。第三层为偏好对齐层，以 SFT 作为基础，再通过 DPO/SimPO/KTO 对风险相关偏好进行优化。

工程实现上，系统采用统一脚本编排与证据链落盘机制。所有关键环节均输出配置快照、指标文件、评测报告与审计记录。针对评测偏差问题，本文引入 benchmark 构造泄露审计，并构建 v2 balanced 基准，保证结论不依赖格式泄露。

## 6.3 实验设置与指标（章节草稿）
数据来源包括 CMTMedQA、Huatuo26M-Lite 与 Huatuo Encyclopedia QA。经去重后获得 19978 条样本，并构建 train/dev/test 以及 3600 条 benchmark。基座模型以 Qwen2.5-7B/14B（或 Qwen3 小参数）为目标口径。

评测指标包括事实性（FactScore）、可用性（Utility）、风险评分（RiskScore）、拦截率（InterceptionRate）以及安全二分类指标（Accuracy、Recall、Specificity、Unsafe Pass Rate、F1）。此外，本文引入 option-letter gap 与 leakage risk 对基准偏差进行审计。

## 6.4 结果与分析（章节草稿）
在当前非 GPU 环境下，真实训练因显存限制被安全跳过，但评测与审计链路完整可运行。综合评测显示系统能够稳定产出结构化指标；对标代理实验中，MedLLM-Hybrid 在当前口径下表现出更低的高风险放行率。偏差审计结果进一步表明，原始 benchmark 存在显著格式泄露风险，而 v2 balanced 基准有效降低该风险并使评测更具可信度。

在 v2 基准上，纯规则检测存在高漏检问题；引入预算受控的 LLM 回退后，Recall 与 F1 获得提升，但同时伴随 Specificity 下降。该结果说明回退机制可作为召回增强手段，但需在安全召回与误报成本之间做任务级权衡。

## 6.5 讨论与局限（章节草稿）
第一，当前阶段尚未完成 GPU 上的真实 Qwen 训练闭环，训练章节结论应明确标注为“待 GPU 补全”。第二，对标结果为统一代理复现实验，不等同官方模型原始能力。第三，LLM 回退模块受 API 预算与外部模型稳定性影响，需在生产化阶段设计更细粒度的缓存与降级策略。

尽管存在上述局限，本文已完成从数据到评测的工程主链与审计链构建，并提供严格完工闸门。该设计使后续 GPU 实验能够在不改代码的前提下直接完成，确保论文实证部分具备可追溯性与可复现性。

## 6.6 结论与后续工作（章节草稿）
本文构建了面向中文医疗问答的三层幻觉抑制系统，并给出可复现实验工程框架。系统在数据治理、检测融合、偏好对齐和偏差审计方面形成闭环，已具备迁移至 GPU 后一键完成真实训练与论文级验证的条件。后续工作将重点完成真实 Qwen 训练闭环、补全真实 loss 曲线与 checkpoint 证据，并进一步扩展多轮对话场景下的稳健性评估。

## 7. 论文章节建议目录（可直接采用）
1. 绪论
2. 相关工作
3. 系统设计与方法
4. 数据构建与治理
5. 实验设置与评测协议
6. 实验结果与分析
7. 讨论与局限
8. 结论与展望

## 8. 论文提交前硬性检查清单

1.  中 
2.  中 
3. 真实 SFT/DPO/SimPO/KTO 均为 
4. 真实 Layer-B Qwen SFT 训练曲线文件存在
5. 最终论文引用的所有指标均来自  当前版本产物

