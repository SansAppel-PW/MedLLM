# Demo 部署与运行说明

## 1. 环境准备（Conda 推荐）
```bash
conda create -n medllm python=3.11 -y
conda activate medllm
pip install -r requirements.txt
```

## 2. 运行数据与评测流程
```bash
python scripts/data/run_data_governance_pipeline.py
python src/train/sft_train.py
python src/train/hard_negative_builder.py
python src/train/dpo_train.py
python src/train/simpo_train.py
python src/train/compare_alignment.py
bash scripts/eval/run_eval.sh
```

## 3. 启动 Demo
- CLI 演示：
```bash
scripts/deploy/run_demo.sh
```

- API 演示（FastAPI）：
```bash
scripts/deploy/run_demo.sh --api
```

- 打开静态页面：
```bash
scripts/deploy/run_demo.sh --web
# 浏览器访问 http://127.0.0.1:8080/demo/index.html
```

## 4. 端到端验收
```bash
python scripts/deploy/run_e2e_acceptance.py
```

输出：
- `reports/e2e_acceptance.md`
- `reports/e2e_acceptance_detail.json`
