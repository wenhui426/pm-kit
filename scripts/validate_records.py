#!/usr/bin/env python3
"""Read-only validation of pm-kit cross-round project records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError:
    print(
        "缺少 jsonschema：请在运行环境安装 Python 包 jsonschema（4.18 以上，提供 Draft202012Validator）。",
        file=sys.stderr,
    )
    raise SystemExit(2)


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = SKILL_ROOT / "catalog" / "_schemas" / "project-records.schema.json"
REGISTRY = SKILL_ROOT / "capabilities" / "registry.json"


def harden_streams() -> None:
    """stdout 和 stderr 都要加固。

    Windows 控制台默认代码页表示不了中文，而本脚本恰恰在出错路径上打印中文——
    不加固的话报错路径自己会抛 UnicodeEncodeError，把真实的校验结果吞掉。
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def load_capability_ids() -> set[str]:
    """读包内的能力清单，用于判断记录里引用的能力 ID 是否真实存在。

    读不到时返回空集合，调用方据此跳过这项检查——包自身的问题不该让记录校验失败。
    """
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return set()
    items = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return set()
    return {
        item["id"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


CAPABILITY_IDS = load_capability_ids()


# 有结构错误而被整体跳过的记录。跳过意味着这个文件的跨文件检查本轮没跑，
# 所以必须在结尾说出来——否则用户修完一批、再跑一次才发现还有下一批。
SKIPPED_RECORDS: list[str] = []


def read_record(path: Path, kind: str, schema: dict, errors: list[str]) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: 无法读取 JSON：{exc}")
        SKIPPED_RECORDS.append(str(path))
        return None
    defs = schema.get("$defs", {}) if isinstance(schema, dict) else {}
    validator = Draft202012Validator(
        {"$ref": f"#/$defs/{kind}", "$defs": defs},
        format_checker=FormatChecker(),
    )
    issues = sorted(validator.iter_errors(data), key=lambda item: str(item.absolute_path))
    for error in issues:
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{path}:{location}: {error.message}")
    if not isinstance(data, dict) or issues:
        SKIPPED_RECORDS.append(str(path))
        return None
    return data


def unique_keys(items: list[dict], fields: tuple[str, ...], label: str, errors: list[str]) -> None:
    seen: set[tuple] = set()
    for item in items:
        if not isinstance(item, dict) or any(field not in item for field in fields):
            continue
        key = tuple(item[field] for field in fields)
        if key in seen:
            errors.append(f"{label}: 重复编号 {key}")
        seen.add(key)


def record_if_present(path: Path, kind: str, schema: dict, errors: list[str]) -> dict | None:
    return read_record(path, kind, schema, errors) if path.is_file() else None


def validate_project(project_dir: Path, schema: dict, errors: list[str]) -> str | None:
    project_file = project_dir / "project.json"
    if not project_file.is_file():
        errors.append(f"{project_file}: 缺少项目记录")
        return None
    project = read_record(project_file, "project", schema, errors)
    if not project or not isinstance(project.get("project_id"), str):
        return None
    project_id = project["project_id"]
    project_rules = record_if_present(project_dir / "business-rules.json", "businessRules", schema, errors)
    artifact_index = record_if_present(project_dir / "artifact-index.json", "artifactIndex", schema, errors)
    if project_rules:
        if project_rules.get("project_id") != project_id or project_rules.get("task_id") is not None:
            errors.append(f"{project_dir / 'business-rules.json'}: 项目或任务归属不符")

    rule_keys: set[tuple[str, int]] = set()
    rule_records: list[tuple[dict, str | None]] = []
    if project_rules and isinstance(project_rules.get("rules"), list):
        rule_records.extend((item, None) for item in project_rules["rules"])

    tasks_dir = project_dir / "tasks"
    task_ids: set[str] = set()
    run_records: list[tuple[Path, dict]] = []
    if tasks_dir.is_dir():
        for task_dir in sorted(path for path in tasks_dir.iterdir() if path.is_dir()):
            task_file = task_dir / "task.json"
            if not task_file.is_file():
                errors.append(f"{task_file}: 任务目录缺少任务记录")
                continue
            task = read_record(task_file, "task", schema, errors)
            if not task or not isinstance(task.get("task_id"), str):
                continue
            task_id = task["task_id"]
            if task_dir.name != task_id:
                errors.append(f"{task_file}: task_id 与任务目录名不符")
            if task.get("project_id") != project_id:
                errors.append(f"{task_file}: project_id 与项目记录不符")
            if task_id in task_ids:
                errors.append(f"{task_file}: 重复 task_id {task_id!r}")
            task_ids.add(task_id)
            if task.get("baseline_version", 0) > project.get("baseline_version", 0):
                errors.append(f"{task_file}: baseline_version 超过项目当前版本")
            task_rules_file = task_dir / "business-rules.json"
            task_rules = record_if_present(task_rules_file, "businessRules", schema, errors)
            if task_rules:
                if task_rules.get("project_id") != project_id or task_rules.get("task_id") != task_id:
                    errors.append(f"{task_rules_file}: 项目或任务归属不符")
                if isinstance(task_rules.get("rules"), list):
                    rule_records.extend((item, task_id) for item in task_rules["rules"])
            runs_dir = task_dir / "runs"
            run_ids: set[str] = set()
            if runs_dir.is_dir():
                for run_file in sorted(runs_dir.glob("*.json")):
                    run = read_record(run_file, "run", schema, errors)
                    if not run:
                        continue
                    run_records.append((run_file, run))
                    run_id = run.get("run_id")
                    if run.get("project_id") != project_id or run.get("task_id") != task_id:
                        errors.append(f"{run_file}: 项目或任务归属不符")
                    if run_id != run_file.stem:
                        errors.append(f"{run_file}: run_id 与文件名不符")
                    if isinstance(run_id, str):
                        run_ids.add(run_id)
                    capabilities = run.get("capabilities")
                    if CAPABILITY_IDS and isinstance(capabilities, list):
                        for capability_id in capabilities:
                            if capability_id not in CAPABILITY_IDS:
                                errors.append(
                                    f"{run_file}: 引用了能力清单里没有的能力 {capability_id!r}"
                                )
                    if run.get("baseline_version", 0) > project.get("baseline_version", 0):
                        errors.append(f"{run_file}: baseline_version 超过项目当前版本")
            latest = task.get("latest_run_id")
            if latest is not None and latest not in run_ids:
                errors.append(f"{task_file}: latest_run_id 找不到对应轮次文件")

    all_rules = [item for item, _ in rule_records]
    unique_keys(all_rules, ("rule_id", "revision"), f"{project_dir}: 业务规则", errors)
    rule_by_key: dict[tuple[str, int], dict] = {}
    rule_owner_by_key: dict[tuple[str, int], str | None] = {}
    latest_confirmed: dict[str, int] = {}
    for rule, owner in rule_records:
        if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str) and type(rule.get("revision")) is int:
            key = (rule["rule_id"], rule["revision"])
            rule_keys.add(key)
            rule_by_key[key] = rule
            rule_owner_by_key[key] = owner
            if rule.get("status") == "confirmed":
                latest_confirmed[rule["rule_id"]] = max(
                    latest_confirmed.get(rule["rule_id"], 0), rule["revision"]
                )
    for rule in all_rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("supersedes"), dict):
            continue
        previous = rule["supersedes"]
        key = (previous.get("rule_id"), previous.get("revision"))
        if key not in rule_keys:
            errors.append(f"{project_dir}: 规则 {rule.get('rule_id')}@{rule.get('revision')} 的 supersedes 找不到旧版")
        elif previous.get("rule_id") != rule.get("rule_id") or previous.get("revision", 0) >= rule.get("revision", 0):
            errors.append(f"{project_dir}: 规则 {rule.get('rule_id')}@{rule.get('revision')} 的 supersedes 必须指向同一规则的较早版本")

    artifact_keys: set[tuple[str, int]] = set()
    artifact_by_key: dict[tuple[str, int], dict] = {}
    artifacts = artifact_index.get("artifacts", []) if artifact_index else []
    if artifact_index and artifact_index.get("project_id") != project_id:
        errors.append(f"{project_dir / 'artifact-index.json'}: project_id 与项目记录不符")
    if isinstance(artifacts, list):
        unique_keys(artifacts, ("artifact_id", "version"), f"{project_dir}: 产物", errors)
        for artifact in artifacts:
            if isinstance(artifact, dict) and isinstance(artifact.get("artifact_id"), str) and type(artifact.get("version")) is int:
                key = (artifact["artifact_id"], artifact["version"])
                artifact_keys.add(key)
                artifact_by_key[key] = artifact
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            if artifact.get("task_id") not in task_ids:
                errors.append(f"{project_dir}: 产物 {artifact.get('artifact_id')} 所属 task_id 不存在")
            for ref in artifact.get("depends_on_rules", []):
                if not isinstance(ref, dict):
                    continue
                rule_key = (ref.get("rule_id"), ref.get("revision"))
                if rule_key not in rule_keys:
                    errors.append(f"{project_dir}: 产物 {artifact.get('artifact_id')} 引用了不存在的规则版本 {ref}")
                elif rule_owner_by_key[rule_key] is not None and rule_owner_by_key[rule_key] != artifact.get("task_id"):
                    errors.append(f"{project_dir}: 产物 {artifact.get('artifact_id')} 不得直接依赖其他任务的规则 {ref}")
            for ref in artifact.get("depends_on_artifacts", []):
                if isinstance(ref, dict) and (ref.get("artifact_id"), ref.get("version")) not in artifact_keys:
                    errors.append(f"{project_dir}: 产物 {artifact.get('artifact_id')} 引用了不存在的上游产物版本 {ref}")
                elif isinstance(ref, dict) and ref.get("artifact_id") == artifact.get("artifact_id") and ref.get("version") == artifact.get("version"):
                    errors.append(f"{project_dir}: 产物 {artifact.get('artifact_id')} 不能依赖自身版本")
        required_review: set[tuple[str, int]] = set()
        for key, artifact in artifact_by_key.items():
            if artifact.get("status") == "superseded":
                continue
            for ref in artifact.get("depends_on_rules", []):
                if not isinstance(ref, dict):
                    continue
                rule_key = (ref.get("rule_id"), ref.get("revision"))
                rule = rule_by_key.get(rule_key)
                if rule and (
                    rule.get("status") == "superseded"
                    or latest_confirmed.get(rule_key[0], 0) > rule_key[1]
                ):
                    required_review.add(key)
        changed = True
        while changed:
            changed = False
            for key, artifact in artifact_by_key.items():
                if artifact.get("status") == "superseded" or key in required_review:
                    continue
                for ref in artifact.get("depends_on_artifacts", []):
                    if not isinstance(ref, dict):
                        continue
                    upstream_key = (ref.get("artifact_id"), ref.get("version"))
                    upstream = artifact_by_key.get(upstream_key)
                    if upstream_key in required_review or (upstream and upstream.get("freshness") == "needs_review"):
                        required_review.add(key)
                        changed = True
                        break
        for key in sorted(required_review):
            if artifact_by_key[key].get("freshness") != "needs_review":
                errors.append(f"{project_dir}: 产物 {key[0]}@{key[1]} 依据已变化，必须标记 needs_review")
    for run_file, run in run_records:
        for ref in run.get("input_artifacts", []):
            if isinstance(ref, dict) and (ref.get("artifact_id"), ref.get("version")) not in artifact_keys:
                errors.append(f"{run_file}: 输入产物版本不存在：{ref}")
    return project_id


def validate_root(root: Path, schema: dict, errors: list[str]) -> None:
    if (root / "project.json").is_file():
        validate_project(root, schema, errors)
        return
    index_path = root / "projects.json"
    if not index_path.is_file():
        errors.append(f"{root}: 需要项目目录中的 project.json，或项目集合目录中的 projects.json")
        return
    index = read_record(index_path, "projects", schema, errors)
    if not index or not isinstance(index.get("projects"), list):
        return
    unique_keys(index["projects"], ("project_id",), str(index_path), errors)
    unique_keys(index["projects"], ("path",), str(index_path), errors)
    for entry in index["projects"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            continue
        location = Path(entry["path"])
        project_dir = location if location.is_absolute() else root / location
        actual_id = validate_project(project_dir, schema, errors)
        if actual_id and actual_id != entry.get("project_id"):
            errors.append(f"{index_path}: {entry.get('project_id')} 的索引路径指向 {actual_id}")


def main() -> int:
    harden_streams()
    parser = argparse.ArgumentParser(description="只读校验 pm-kit 跨轮记录")
    parser.add_argument("record_root", type=Path, help="项目集合目录或单个项目目录")
    args = parser.parse_args()
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, SchemaError) as exc:
        print(f"Schema 无法加载：{exc}", file=sys.stderr)
        return 2
    errors: list[str] = []
    SKIPPED_RECORDS.clear()
    try:
        validate_root(args.record_root, schema, errors)
    except Exception as exc:  # 兜底：先交出已经发现的问题，再说明校验器自身出错
        for error in errors:
            print(f"ERROR {error}")
        print(f"校验器内部出错：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        if SKIPPED_RECORDS:
            print("注意：以下记录有结构错误，已整体跳过，它们的跨文件检查本轮没有执行：")
            for path in SKIPPED_RECORDS:
                print(f"  SKIPPED {path}")
        print(f"校验失败：{len(errors)} 个问题")
        return 1
    print("校验通过：记录结构与已登记引用一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
