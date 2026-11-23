"""Build replayable pm-kit record scenarios without changing existing data."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_ROOT / "scripts" / "validate_records.py"
STAMP = "2026-10-11T10:00:00+08:00"


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rule(rule_id: str, statement: str, status: str = "confirmed", revision: int = 1) -> dict:
    return {
        "rule_id": rule_id, "revision": revision, "kind": "requirement",
        "statement": statement, "scope": "项目业务规则",
        "source": {"type": "user", "detail": "模拟用户确认"},
        "status": status, "confirmed_by": "user", "confirmed_at": STAMP,
        "supersedes": None,
    }


def task(project: str, task_id: str, goal: str, baseline: int = 1) -> dict:
    return {
        "schema_version": "1.0", "project_id": project, "task_id": task_id,
        "goal": goal, "baseline_version": baseline, "status": "in_progress",
        "current_stage": "review", "confirmed_decisions": [],
        "open_questions": [], "latest_run_id": "run-1",
    }


def run(project: str, task_id: str, goal: str) -> dict:
    return {
        "schema_version": "1.0", "project_id": project, "task_id": task_id,
        "run_id": "run-1", "goal": goal, "baseline_version": 1,
        "input_artifacts": [], "capabilities": ["write-prd"], "decisions": [],
        "changed_files": [], "checks": ["记录归属已核对"],
        "open_questions": [], "current_stage": "review", "next_step": "等待确认",
    }


def artifact(artifact_id: str, task_id: str, rule_id: str, upstream: str | None = None) -> dict:
    return {
        "artifact_id": artifact_id, "task_id": task_id, "type": "markdown",
        "path": f"tasks/{task_id}/artifacts/{artifact_id}.md", "version": 1,
        "status": "reviewed", "freshness": "current",
        "depends_on_rules": [] if upstream else [{"rule_id": rule_id, "revision": 1}],
        "depends_on_artifacts": (
            [{"artifact_id": upstream, "version": 1}] if upstream else []
        ),
        "checks": ["模拟内容检查"], "updated_at": STAMP,
    }


def add_task(project_dir: Path, task_id: str, goal: str) -> None:
    task_dir = project_dir / "tasks" / task_id
    write(task_dir / "task.json", task(project_dir.name, task_id, goal))
    write(task_dir / "business-rules.json", {
        "schema_version": "1.0", "project_id": project_dir.name,
        "task_id": task_id, "rules": [],
    })
    write(task_dir / "runs" / "run-1.json", run(project_dir.name, task_id, goal))


def build_same_project(root: Path) -> None:
    write(root / "projects.json", {
        "schema_version": "1.0",
        "projects": [{"project_id": "client-a", "name": "退款后台", "path": "client-a"}],
    })
    project_dir = root / "client-a"
    write(project_dir / "project.json", {
        "schema_version": "1.0", "project_id": "client-a", "name": "退款后台",
        "baseline_version": 1, "status": "active", "updated_at": STAMP,
    })
    write(project_dir / "business-rules.json", {
        "schema_version": "1.0", "project_id": "client-a", "task_id": None,
        "rules": [
            rule("REFUND-07", "驳回后允许重新提交"),
            rule("ORDER-01", "订单状态包含待支付、已支付、已关闭"),
        ],
    })
    add_task(project_dir, "refund-prd", "编写退款 PRD")
    add_task(project_dir, "order-list", "改版订单列表")
    task_rule = rule("A-DRAFT", "退款页尝试增加二次确认", "unconfirmed")
    task_rule["kind"] = "assumption"
    task_rule["confirmed_by"] = None
    task_rule["confirmed_at"] = None
    write(project_dir / "tasks" / "refund-prd" / "business-rules.json", {
        "schema_version": "1.0", "project_id": "client-a",
        "task_id": "refund-prd", "rules": [task_rule],
    })
    write(project_dir / "artifact-index.json", {
        "schema_version": "1.0", "project_id": "client-a",
        "artifacts": [
            artifact("refund-prd", "refund-prd", "REFUND-07"),
            artifact("refund-prototype", "refund-prd", "REFUND-07", "refund-prd"),
            artifact("refund-acceptance", "refund-prd", "REFUND-07", "refund-prototype"),
            artifact("order-list-spec", "order-list", "ORDER-01"),
        ],
    })


def validate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        # -B：不把 .pyc 写回包里。
        # 显式指定编码：子进程输出 UTF-8，而 Windows 默认按本地代码页解码，
        # 会在读取线程里抛 UnicodeDecodeError，把真实的校验结果吞掉。
        [sys.executable, "-B", str(VALIDATOR), str(root)],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="模拟 pm-kit 跨轮记录流转")
    parser.add_argument("output", type=Path, help="尚不存在的测试输出目录")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        print(f"拒绝覆盖现有目录：{output}", file=sys.stderr)
        return 2
    output.mkdir(parents=True)

    same = output / "01-same-project-new-task"
    same.mkdir()
    build_same_project(same)
    same_result = validate(same)
    a_draft = read(same / "client-a" / "tasks" / "refund-prd" / "business-rules.json")
    b_rules = read(same / "client-a" / "tasks" / "order-list" / "business-rules.json")
    same_pass = same_result.returncode == 0 and bool(a_draft["rules"]) and not b_rules["rules"]

    switched = output / "02-switch-project"
    shutil.copytree(same, switched)
    index = read(switched / "projects.json")
    index["projects"].append({"project_id": "client-b", "name": "退款后台", "path": "client-b"})
    write(switched / "projects.json", index)
    beta = switched / "client-b"
    write(beta / "project.json", {
        "schema_version": "1.0", "project_id": "client-b", "name": "退款后台",
        "baseline_version": 1, "status": "active", "updated_at": STAMP,
    })
    write(beta / "business-rules.json", {
        "schema_version": "1.0", "project_id": "client-b", "task_id": None,
        "rules": [rule("B-REFUND-01", "驳回后不可重新提交")],
    })
    add_task(beta, "refund-requirements", "梳理乙客户退款需求")
    write(beta / "artifact-index.json", {
        "schema_version": "1.0", "project_id": "client-b",
        "artifacts": [artifact("beta-requirements", "refund-requirements", "B-REFUND-01")],
    })
    switched_result = validate(switched)
    beta_rules = read(beta / "business-rules.json")["rules"]
    switch_pass = switched_result.returncode == 0 and all(
        item["rule_id"] != "REFUND-07" for item in beta_rules
    )

    changed = output / "03-rule-change"
    shutil.copytree(same, changed)
    alpha = changed / "client-a"
    project = read(alpha / "project.json")
    project["baseline_version"] = 2
    write(alpha / "project.json", project)
    rules_file = alpha / "business-rules.json"
    rules = read(rules_file)
    rules["rules"][0]["status"] = "superseded"
    revision_2 = rule("REFUND-07", "驳回后不可重新提交", revision=2)
    revision_2["supersedes"] = {"rule_id": "REFUND-07", "revision": 1}
    rules["rules"].append(revision_2)
    write(rules_file, rules)
    index_file = alpha / "artifact-index.json"
    artifacts = read(index_file)
    affected = []
    for item in artifacts["artifacts"]:
        if item["artifact_id"].startswith("refund-"):
            item["freshness"] = "needs_review"
            affected.append(item["artifact_id"])
    write(index_file, artifacts)
    change_result = validate(changed)
    order_artifact = next(item for item in artifacts["artifacts"] if item["artifact_id"] == "order-list-spec")
    change_pass = change_result.returncode == 0 and len(affected) == 3 and order_artifact["freshness"] == "current"

    missed = output / "04-unmarked-stale-negative-check"
    shutil.copytree(changed, missed)
    missed_index = missed / "client-a" / "artifact-index.json"
    stale = read(missed_index)
    for item in stale["artifacts"]:
        item["freshness"] = "current"
    write(missed_index, stale)
    missed_result = validate(missed)

    leaked = output / "05-task-rule-leak-negative-check"
    shutil.copytree(same, leaked)
    leaked_index = leaked / "client-a" / "artifact-index.json"
    leaked_artifacts = read(leaked_index)
    for item in leaked_artifacts["artifacts"]:
        if item["artifact_id"] == "order-list-spec":
            item["depends_on_rules"].append({"rule_id": "A-DRAFT", "revision": 1})
    write(leaked_index, leaked_artifacts)
    leaked_result = validate(leaked)

    result = {
        "same_project_new_task": {"passed": same_pass, "validator_exit": same_result.returncode},
        "switch_project": {"passed": switch_pass, "validator_exit": switched_result.returncode},
        "rule_change_manual_marking": {
            "passed": change_pass, "validator_exit": change_result.returncode,
            "affected": affected, "unaffected": order_artifact["artifact_id"],
        },
        "unmarked_stale_detected": missed_result.returncode != 0,
        "cross_task_draft_leak_detected": leaked_result.returncode != 0,
        "notes": "这是协议级记录模拟；未运行独立 AI Agent，也未生成真实 PRD/HTML。",
    }
    write(output / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all((
        same_pass, switch_pass, change_pass,
        result["unmarked_stale_detected"], result["cross_task_draft_leak_detected"],
    )) else 1


if __name__ == "__main__":
    raise SystemExit(main())
