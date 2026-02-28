#!/usr/bin/env python3
"""Audit task completion status against deliverable paths."""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path
from typing import Any


TASK_ROW_RE = re.compile(r"^\|\s*(T\d+)\s*\|")
CODE_PATH_RE = re.compile(r"`([^`]+)`")
PATH_TOKEN_RE = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")

DELIVERABLE_ALIASES: dict[str, list[str]] = {
    # Real dataset naming is the canonical runtime path.
    "data/clean/sft_train.jsonl": ["data/clean/real_sft_train.jsonl"],
    "data/clean/sft_dev.jsonl": ["data/clean/real_sft_dev.jsonl"],
    "data/clean/pref_seed_pairs.jsonl": ["data/clean/real_pref_seed_pairs.jsonl"],
    # KG triples may be materialized as the merged core KB.
    "data/kg/triples/*.jsonl": ["data/kg/cm3kg_core_kb.jsonl", "data/kg/real_medqa_reference_kb_merged.jsonl"],
}


def parse_task_rows(markdown: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in markdown.splitlines():
        if not TASK_ROW_RE.match(line):
            continue
        cols = [c.strip() for c in line.strip().split("|")[1:-1]]
        if len(cols) < 7:
            continue
        rows.append(
            {
                "id": cols[0],
                "task": cols[1],
                "deliverables": cols[2],
                "dod": cols[3],
                "deps": cols[4],
                "priority": cols[5],
                "status": cols[6],
            }
        )
    return rows


def extract_paths(raw: str) -> list[str]:
    paths = []
    for hit in CODE_PATH_RE.findall(raw):
        token = hit.strip()
        if "/" in token:
            paths.append(token)
    if not paths:
        for token in PATH_TOKEN_RE.findall(raw):
            if "/" in token:
                paths.append(token.strip())
    dedup = []
    seen = set()
    for p in paths:
        if p not in seen:
            seen.add(p)
            dedup.append(p)
    return dedup


def expand_brace_path(path: str) -> list[str]:
    m = re.match(r"^(.*)\{([^}]+)\}(.*)$", path)
    if not m:
        return [path]
    prefix, options, suffix = m.groups()
    parts = [x.strip() for x in options.split(",") if x.strip()]
    if not parts:
        return [path]
    return [f"{prefix}{opt}{suffix}" for opt in parts]


def path_exists(repo: Path, rel_item: str) -> bool:
    if "*" in rel_item:
        return len(glob.glob(str(repo / rel_item))) > 0
    return (repo / rel_item).exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit task completion")
    parser.add_argument("--tasks", default="docs/EXECUTION_TASKS.md")
    parser.add_argument("--report", default="reports/task_audit.md")
    parser.add_argument("--json", default="reports/task_audit.json")
    args = parser.parse_args()

    repo = Path.cwd()
    tasks_path = repo / args.tasks
    text = tasks_path.read_text(encoding="utf-8")
    tasks = parse_task_rows(text)

    done_count = sum(1 for t in tasks if t["status"] == "DONE")
    todo_count = sum(1 for t in tasks if t["status"] == "TODO")
    blocked_count = sum(1 for t in tasks if t["status"] == "BLOCKED")

    audit_rows = []
    for t in tasks:
        paths = extract_paths(t["deliverables"])
        checks = []
        for rel in paths:
            expanded = expand_brace_path(rel)
            for rel_item in expanded:
                exists = path_exists(repo, rel_item)
                alias_used = None
                if not exists:
                    for alt in DELIVERABLE_ALIASES.get(rel_item, []):
                        if path_exists(repo, alt):
                            exists = True
                            alias_used = alt
                            break
                checks.append({"path": rel_item, "exists": exists, "alias_used": alias_used})
        missing = [c["path"] for c in checks if not c["exists"]]
        alias_hits = [c["alias_used"] for c in checks if c.get("alias_used")]
        audit_rows.append(
            {
                "id": t["id"],
                "task": t["task"],
                "status": t["status"],
                "deliverable_paths": paths,
                "missing_paths": missing,
                "alias_hits": alias_hits,
                "all_paths_exist": len(missing) == 0,
            }
        )

    done_missing = [r for r in audit_rows if r["status"] == "DONE" and not r["all_paths_exist"]]
    todo_with_paths = [r for r in audit_rows if r["status"] == "TODO"]

    report_lines = [
        "# 开题任务完成度审计报告",
        "",
        f"- 任务总数: {len(tasks)}",
        f"- DONE: {done_count}",
        f"- TODO: {todo_count}",
        f"- BLOCKED: {blocked_count}",
        f"- 已标记 DONE 但交付物缺失: {len(done_missing)}",
        "",
        "## DONE 任务交付物缺失项",
    ]
    if done_missing:
        for row in done_missing:
            report_lines.append(f"- {row['id']} {row['task']}: {', '.join(row['missing_paths'])}")
    else:
        report_lines.append("- 无")

    report_lines.extend(["", "## 待完成任务", "| ID | 任务 | 状态 |", "|---|---|---|"])
    if todo_with_paths:
        for row in todo_with_paths:
            report_lines.append(f"| {row['id']} | {row['task']} | {row['status']} |")
    else:
        report_lines.append("| - | 无 | - |")

    report_path = repo / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    json_path = repo / args.json
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "summary": {
                    "total": len(tasks),
                    "done": done_count,
                    "todo": todo_count,
                    "blocked": blocked_count,
                    "done_missing": len(done_missing),
                },
                "rows": audit_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "total": len(tasks),
                "done": done_count,
                "todo": todo_count,
                "done_missing": len(done_missing),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
