#!/usr/bin/env python3
"""Audit one-click pipeline interface consistency for GPU migration."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"


@dataclass
class CheckResult:
    id: str
    requirement: str
    status: str
    detail: str
    evidence: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pipeline interface consistency")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out-md", default="reports/interface_consistency_audit.md")
    parser.add_argument("--out-json", default="reports/interface_consistency_audit.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    results: list[CheckResult] = []

    key_scripts = [
        "scripts/train/run_gpu_thesis_mainline.sh",
        "scripts/train/run_real_alignment_pipeline.sh",
        "scripts/train/run_layer_b_real_sft.sh",
        "scripts/eval/run_thesis_pipeline.sh",
        "scripts/eval/run_eval.sh",
        "scripts/data/ensure_real_dataset.sh",
    ]
    missing_key = [x for x in key_scripts if not (root / x).exists()]
    results.append(
        CheckResult(
            id="C01",
            requirement="GPU 主链关键脚本存在",
            status=PASS if not missing_key else FAIL,
            detail="关键脚本齐全。" if not missing_key else f"缺失关键脚本: {', '.join(missing_key)}",
            evidence=key_scripts,
        )
    )

    makefile = root / "Makefile"
    make_text = read_text(makefile)
    make_refs = sorted(set(re.findall(r"scripts/[A-Za-z0-9_./-]+\\.(?:sh|py)", make_text)))
    missing_make_refs = [x for x in make_refs if not (root / x).exists()]
    results.append(
        CheckResult(
            id="C02",
            requirement="Makefile 引用的脚本路径有效",
            status=PASS if not missing_make_refs else FAIL,
            detail="Makefile 脚本引用路径均存在。"
            if not missing_make_refs
            else f"Makefile 存在无效脚本引用: {', '.join(missing_make_refs)}",
            evidence=["Makefile"],
        )
    )

    hardcode_targets = [
        "scripts/train/run_gpu_thesis_mainline.sh",
        "scripts/train/run_real_alignment_pipeline.sh",
        "scripts/train/run_layer_b_real_sft.sh",
        "scripts/eval/run_thesis_pipeline.sh",
        "scripts/eval/run_eval.sh",
    ]
    hardcode_hits: list[str] = []
    for rel in hardcode_targets:
        text = read_text(root / rel)
        if re.search(r"(^|\\s)python3(\\s|$)", text):
            hardcode_hits.append(rel)
    results.append(
        CheckResult(
            id="C03",
            requirement="关键流水线脚本不得硬编码 python3",
            status=PASS if not hardcode_hits else FAIL,
            detail="关键流水线脚本均通过 PYTHON_BIN 调用 Python。"
            if not hardcode_hits
            else f"发现硬编码 python3: {', '.join(hardcode_hits)}",
            evidence=hardcode_targets,
        )
    )

    gpu_mainline = read_text(root / "scripts/train/run_gpu_thesis_mainline.sh")
    gpu_has_alignment_pybin = "PYTHON_BIN=\"${PYTHON_BIN}\"" in gpu_mainline and "bash scripts/train/run_real_alignment_pipeline.sh" in gpu_mainline
    gpu_has_eval_pybin = "PYTHON_BIN=\"${PYTHON_BIN}\"" in gpu_mainline and "bash scripts/eval/run_thesis_pipeline.sh" in gpu_mainline
    c04_ok = gpu_has_alignment_pybin and gpu_has_eval_pybin
    results.append(
        CheckResult(
            id="C04",
            requirement="gpu-mainline 向子流水线透传 PYTHON_BIN",
            status=PASS if c04_ok else FAIL,
            detail="已向 alignment 与 thesis eval 子流水线透传 PYTHON_BIN。"
            if c04_ok
            else "未检测到对 alignment/eval 子流水线的 PYTHON_BIN 透传。",
            evidence=["scripts/train/run_gpu_thesis_mainline.sh"],
        )
    )

    alignment_text = read_text(root / "scripts/train/run_real_alignment_pipeline.sh")
    c05_ok = (
        "PYTHON_BIN=\"${PYTHON_BIN}\"" in alignment_text
        and "bash scripts/train/run_layer_b_real_sft.sh" in alignment_text
    )
    results.append(
        CheckResult(
            id="C05",
            requirement="real-alignment 调用 Layer-B SFT 时透传 PYTHON_BIN",
            status=PASS if c05_ok else FAIL,
            detail="Layer-B SFT 子脚本透传 PYTHON_BIN 已配置。"
            if c05_ok
            else "未检测到 Layer-B SFT 子脚本的 PYTHON_BIN 透传。",
            evidence=["scripts/train/run_real_alignment_pipeline.sh", "scripts/train/run_layer_b_real_sft.sh"],
        )
    )

    required_targets = ["gpu-mainline:", "gpu-mainline-dryrun:", "gpu-readiness:", "gpu-closure:"]
    missing_targets = [x for x in required_targets if x not in make_text]
    results.append(
        CheckResult(
            id="C06",
            requirement="Makefile 提供 GPU 一键主链入口与验收入口",
            status=PASS if not missing_targets else FAIL,
            detail="GPU 一键执行与验收目标齐全。"
            if not missing_targets
            else f"缺失 Makefile 目标: {', '.join(missing_targets)}",
            evidence=["Makefile"],
        )
    )

    summary = {
        "total": len(results),
        "pass": sum(1 for x in results if x.status == PASS),
        "fail": sum(1 for x in results if x.status == FAIL),
    }

    out_json = root / args.out_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps({"summary": summary, "checks": [x.__dict__ for x in results]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Pipeline Interface Consistency Audit",
        "",
        f"- PASS: {summary['pass']}",
        f"- FAIL: {summary['fail']}",
        "",
        "| ID | Requirement | Status | Detail | Evidence |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row.id} | {row.requirement} | {row.status} | {row.detail} | {'<br>'.join(row.evidence)} |"
        )

    out_md = root / args.out_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
