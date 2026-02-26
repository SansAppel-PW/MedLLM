# Balanced Detection Benchmark v2 Report

- Output: `data/benchmark/real_medqa_benchmark_v2_balanced.jsonl`
- Total rows: 3600
- Rewritten rows: 1798
- Unresolved rows: 2

## Rewrite Modes
- by_letter: 1813
- by_text_exact: 1785
- by_text_fuzzy: 0
- unresolved_empty: 2
- unresolved_no_match: 0

## Option-Letter Rate After Rewrite
| risk:split | count | option_letter_rate_after |
|---|---:|---:|
| high:test | 300 | 1.0000 |
| high:train | 1200 | 0.9983 |
| high:validation | 300 | 1.0000 |
| low:test | 300 | 1.0000 |
| low:train | 1200 | 1.0000 |
| low:validation | 300 | 1.0000 |
