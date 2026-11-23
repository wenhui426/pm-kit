#!/usr/bin/env python3
"""Discover, validate, index, and scaffold pm-kit catalog packages.

规则分工（这条分工是刻意的，改动前请先读）：

- 字段、类型、枚举、长度：一律由 ``catalog/_schemas/<kind>.schema.json`` 判定。
  本脚本不再重复写一遍，否则脚本和 schema 会各自演化、互相漂移。
- 脚本只补 schema 表达不了的关系：目录归属、id 与目录是否一致、``files`` 是否真实存在、
  ``extends`` 指向是否存在且同类、id 是否重复、定稿资源的必填项是否留空。

所以新增一种资源类型时，主要工作是写一份 schema；脚本这边只需要在 ``KINDS`` 里登记
它的容器目录和脚手架文件。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - 取决于运行环境
    jsonschema = None


SKILL_ROOT = Path(__file__).resolve().parent.parent

# 每类资源的容器目录与脚手架文件。
# 场景包的 6 个文件与「使用说明与扩展指南.md」第 8.3 节的目录示例保持一致：
# 用户照文档核对时，脚手架造出来的东西必须对得上。
KINDS = {
    "scenario": {
        "container": "scenarios",
        "starter_files": [
            "overview.md",
            "roles.md",
            "workflow.md",
            "states.md",
            "risks.md",
            "validation.md",
        ],
    },
    "component-library": {
        "container": "component-libraries",
        "starter_files": [
            "component-map.md",
            "tokens.md",
            "setup.md",
            "constraints.md",
            "validation.md",
        ],
    },
    "template": {
        "container": "templates",
        "starter_files": ["template.md", "field-rules.md", "example.md", "validation.md"],
    },
    "case": {
        "container": "cases",
        "starter_files": ["case.md", "reusable-patterns.md"],
    },
}

STATUSES = {"draft", "reviewed", "active", "deprecated"}
# 定稿状态不允许留空必填项；draft 阶段本来就该允许边写边填。
FINAL_STATUSES = {"reviewed", "active"}
ID_RE = re.compile(r"^(built-in|local):[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def harden_stdout() -> None:
    """Windows 控制台默认代码页表示不了中文，直接 print 会抛 UnicodeEncodeError。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def relative(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict:
    # utf-8-sig 同时兼容带 BOM 和不带 BOM 的 UTF-8：Windows 编辑器另存过的文件会带 BOM。
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def manifest_paths(root: Path) -> list[Path]:
    catalog = root / "catalog"
    found: list[Path] = []
    for namespace in ("built-in", "local"):
        base = catalog / namespace
        if base.exists():
            found.extend(base.rglob("manifest.json"))
    return sorted(found)


def load_schema(root: Path, kind: str | None) -> dict | None:
    if not isinstance(kind, str) or not kind:
        return None
    path = root / "catalog" / "_schemas" / f"{kind}.schema.json"
    if not path.is_file():
        return None
    try:
        return load_json(path)
    except (OSError, ValueError):
        return None


def make_validator(schema: dict):
    """按 schema 声明的 draft 选校验器，老版本 jsonschema 没有 2020-12 时退到 Draft7。"""
    cls = getattr(jsonschema, "Draft202012Validator", None)
    if cls is None:
        cls = getattr(jsonschema, "Draft7Validator", None)
    if cls is None:  # 极老版本
        cls = jsonschema.validators.validator_for(schema)
    return cls(schema)


def dedupe(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def collect(root: Path) -> list[dict]:
    """读取全部 manifest，每个条目带上读取结果或读取错误。只读盘一次。"""
    entries: list[dict] = []
    for path in manifest_paths(root):
        rel = relative(root, path)
        try:
            data = load_json(path)
        except (OSError, ValueError) as exc:
            entries.append({"path": path, "rel": rel, "data": None, "read_error": f"{rel}: cannot read manifest: {exc}"})
            continue
        entries.append({"path": path, "rel": rel, "data": data, "read_error": None})
    return entries


def index_by_id(entries: list[dict]) -> tuple[dict[str, tuple[str, str, Path]], list[str]]:
    """建立 id 索引，同时报出重复 id（重复 id 会让 extends 指向哪个变得不确定）。"""
    by_id: dict[str, tuple[str, str, Path]] = {}
    errors: list[str] = []
    for entry in entries:
        data = entry["data"]
        if not isinstance(data, dict):
            continue
        resource_id = data.get("id")
        if not isinstance(resource_id, str) or not resource_id:
            continue
        if resource_id in by_id:
            errors.append(f"{entry['rel']}: duplicate id {resource_id!r} also used by {by_id[resource_id][0]}")
        else:
            by_id[resource_id] = (entry["rel"], str(data.get("kind")), entry["path"])
    return by_id, errors


def structural_errors(rel: str, data: dict, kind: str | None, schema: dict | None) -> list[str]:
    if schema is None:
        return [f"{rel}: no schema at catalog/_schemas/{kind}.schema.json"]
    if jsonschema is None:
        # 缺失依赖由命令层统一提示，这里不重复刷屏。
        return []
    validator = make_validator(schema)
    out: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
        location = "/".join(str(p) for p in err.absolute_path) or "(root)"
        out.append(f"{rel}: {location}: {err.message}")
    return out


def semantic_errors(
    root: Path,
    path: Path,
    rel: str,
    data: dict,
    by_id: dict[str, tuple[str, str, Path]],
    schema: dict | None,
) -> list[str]:
    errors: list[str] = []

    kind = data.get("kind")
    if kind not in KINDS:
        return [f"{rel}: unsupported kind {kind!r}; expected one of {sorted(KINDS)}"]

    try:
        relative_parts = path.relative_to(root / "catalog").parts
        namespace = relative_parts[0]
    except ValueError:
        return [f"{rel}: manifest is outside catalog/"]

    slug = path.parent.name
    if KINDS[kind]["container"] not in relative_parts:
        errors.append(f"{rel}: kind {kind!r} must live under {KINDS[kind]['container']}/")

    # id 由目录位置决定，命名空间和 slug 必须和目录一致，否则索引与实现会对不上。
    resource_id = data.get("id")
    expected_id = f"{namespace}:{slug}"
    if not isinstance(resource_id, str) or not ID_RE.fullmatch(resource_id):
        errors.append(f"{rel}: id must look like built-in:slug or local:slug")
    elif resource_id != expected_id:
        errors.append(f"{rel}: id must be {expected_id!r} to match its directory")

    if data.get("status") not in STATUSES:
        errors.append(f"{rel}: status must be one of {sorted(STATUSES)}")

    version = data.get("version")
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        errors.append(f"{rel}: version must use major.minor.patch")

    # schema 表达不了「同样合法、但定稿阶段不该为空」这类条件约束。
    if data.get("status") in FINAL_STATUSES:
        for field in (schema or {}).get("required", []):
            value = data.get(field)
            if isinstance(value, (list, str, dict)) and len(value) == 0:
                errors.append(f"{rel}: {field!r} cannot be empty when status is {data.get('status')!r}")

    files = data.get("files")
    if isinstance(files, dict):
        resolved_root = root.resolve()
        for label, target_rel in files.items():
            if not isinstance(target_rel, str) or not target_rel:
                continue
            target = (path.parent / target_rel).resolve()
            if target != resolved_root and resolved_root not in target.parents:
                errors.append(f"{rel}: files.{label} escapes the skill root")
            elif not target.is_file():
                errors.append(f"{rel}: files.{label} not found: {target_rel}")

    # extends 是用户扩展继承内置资源的唯一机制，必须真的可解析。
    extends = data.get("extends")
    if isinstance(extends, list):
        for parent_id in extends:
            if not isinstance(parent_id, str):
                continue
            found = by_id.get(parent_id)
            if found is None:
                errors.append(f"{rel}: extends target {parent_id!r} not found in catalog")
                continue
            _, parent_kind, parent_path = found
            if parent_path == path:
                errors.append(f"{rel}: extends cannot reference itself")
            elif parent_kind != kind:
                errors.append(f"{rel}: extends target {parent_id!r} is a {parent_kind}, not {kind}")
    return errors


def cycle_errors(entries: list[dict]) -> list[str]:
    """资源最多继承一个父资源，因此 extends 构成森林；沿父链走一遍即可发现环。"""
    id_to_rel: dict[str, str] = {}
    parents: dict[str, str] = {}
    for entry in entries:
        data = entry["data"]
        if not isinstance(data, dict):
            continue
        resource_id = data.get("id")
        if not isinstance(resource_id, str):
            continue
        id_to_rel[resource_id] = entry["rel"]
        extends = data.get("extends")
        if isinstance(extends, list):
            for parent_id in extends:
                if isinstance(parent_id, str):
                    parents[resource_id] = parent_id
                    break

    out: list[str] = []
    reported: set[tuple[str, ...]] = set()
    for start in parents:
        chain = [start]
        current = parents.get(start)
        while current is not None:
            if current in chain:
                loop = chain[chain.index(current) :]
                key = tuple(sorted(set(loop)))
                if key not in reported:
                    reported.add(key)
                    path_text = " -> ".join(loop + [current])
                    out.append(f"{id_to_rel.get(start, start)}: extends cycle {path_text}")
                break
            chain.append(current)
            current = parents.get(current)
    return out


def listing(root: Path, entries: list[dict]) -> list[dict]:
    """discover 的用途是「看看现在有哪些资源」，不做校验，也不带 valid 字段。"""
    del root
    items: list[dict] = []
    for entry in entries:
        data = entry["data"]
        if not isinstance(data, dict):
            items.append({"manifest": entry["rel"], "readable": False})
            continue
        triggers = data.get("triggers")
        items.append(
            {
                "manifest": entry["rel"],
                "readable": True,
                "id": data.get("id"),
                "kind": data.get("kind"),
                "name": data.get("name"),
                "version": data.get("version"),
                "status": data.get("status"),
                "triggers": triggers if isinstance(triggers, list) else [],
            }
        )
    items.sort(key=lambda item: (str(item.get("kind")), str(item.get("id"))))
    return items


def evaluate(root: Path, entries: list[dict]) -> tuple[list[dict], list[str]]:
    by_id, id_errors = index_by_id(entries)
    problems: list[str] = list(id_errors)
    reports: list[dict] = []

    for entry in entries:
        data = entry["data"]
        if not isinstance(data, dict):
            problems.append(entry["read_error"])
            reports.append(
                {
                    "manifest": entry["rel"],
                    "id": None,
                    "kind": None,
                    "name": None,
                    "version": None,
                    "status": None,
                    "triggers": [],
                    "valid": False,
                }
            )
            continue

        kind = data.get("kind")
        schema = load_schema(root, kind)
        found = dedupe(
            structural_errors(entry["rel"], data, kind, schema)
            + semantic_errors(root, entry["path"], entry["rel"], data, by_id, schema)
        )
        problems.extend(found)
        triggers = data.get("triggers")
        reports.append(
            {
                "manifest": entry["rel"],
                "id": data.get("id"),
                "kind": kind,
                "name": data.get("name"),
                "version": data.get("version"),
                "status": data.get("status"),
                "triggers": triggers if isinstance(triggers, list) else [],
                # 没有 jsonschema 时结构检查整个没跑，不能声称 valid——用 null 表示"未知"
                "valid": None if jsonschema is None else not found,
            }
        )

    problems.extend(cycle_errors(entries))
    reports.sort(key=lambda item: (str(item.get("kind")), str(item.get("id"))))
    return reports, dedupe(problems)


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_discover(root: Path) -> int:
    entries = collect(root)
    items = listing(root, entries)
    print_json({"count": len(items), "resources": items})
    return 0


def command_validate(root: Path) -> int:
    if jsonschema is None:
        print(
            "cannot validate: python package 'jsonschema' is not installed. "
            "Run: python -m pip install jsonschema",
            file=sys.stderr,
        )
        return 2
    entries = collect(root)
    reports, problems = evaluate(root, entries)
    print_json({"count": len(reports), "resources": reports, "errors": problems})
    return 1 if problems else 0


def command_rebuild_index(root: Path) -> int:
    entries = collect(root)
    reports, problems = evaluate(root, entries)
    if jsonschema is None:
        print(
            "warning: python package 'jsonschema' is not installed; "
            "structural schema checks were skipped. The index is marked "
            "schema_validated=false and every resource's valid field is null (unknown), not true.",
            file=sys.stderr,
        )

    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_validated": jsonschema is not None,
        "count": len(reports),
        "resources": reports,
        "errors": problems,
    }
    index_path = root / "catalog" / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    local_resources = [item for item in reports if str(item.get("id", "")).startswith("local:")]
    local_payload = {
        "schema_version": "1.0",
        "generated_at": payload["generated_at"],
        "description": "使用者创建的场景、组件库、模板和案例。技能升级不得覆盖此目录。",
        "count": len(local_resources),
        "resources": local_resources,
    }
    local_index_path = root / "catalog" / "local" / "index.json"
    local_index_path.parent.mkdir(parents=True, exist_ok=True)
    local_index_path.write_text(
        json.dumps(local_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 索引始终写出：draft 资源本来就允许边写边填，不能因为一条错误就让整个索引停更。
    print(
        f"wrote {relative(root, index_path)} with {len(reports)} resources; "
        f"wrote {relative(root, local_index_path)} with {len(local_resources)} local resources"
    )
    if problems:
        print(f"index written, but {len(problems)} problem(s) remain:", file=sys.stderr)
        for item in problems:
            print(f"  - {item}", file=sys.stderr)
        return 1
    return 0


def starter_manifest(kind: str, slug: str, name: str) -> dict:
    files = {Path(filename).stem.replace("-", "_"): filename for filename in KINDS[kind]["starter_files"]}
    base = {
        "kind": kind,
        "id": f"local:{slug}",
        "name": name,
        "version": "0.1.0",
        "status": "draft",
        "extends": [],
        "triggers": [name],
        "files": files,
    }
    if kind == "scenario":
        base.update({"platforms": ["web"], "capabilities": ["待用户确认的场景能力"]})
    elif kind == "component-library":
        base.update(
            {
                "platforms": ["web"],
                "frameworks": ["custom"],
                "package_names": [],
                "capabilities": ["待用户确认的组件能力"],
            }
        )
    elif kind == "template":
        base.update(
            {
                "output_type": "document",
                "formats": ["md"],
                "applies_to": ["待用户确认的适用场景"],
                "required_fields": [],
            }
        )
    elif kind == "case":
        base.update(
            {
                "summary": "待用户确认的脱敏案例摘要",
                "applicable_scenarios": [],
                "modes": ["analysis"],
                "inputs_summary": [],
                "decisions": [],
                "deliverables": ["待用户确认的交付物"],
                "reusable_patterns": [],
                "sensitive_data_removed": True,
            }
        )
    return base


def command_scaffold(root: Path, kind: str, slug: str, name: str) -> int:
    if not SLUG_RE.fullmatch(slug):
        print("slug must use lowercase letters, digits, and single hyphens", file=sys.stderr)
        return 2
    target = root / "catalog" / "local" / KINDS[kind]["container"] / slug
    if target.exists():
        print(f"target already exists: {target}", file=sys.stderr)
        return 2
    try:
        target.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"target already exists: {target}", file=sys.stderr)
        return 2

    manifest = starter_manifest(kind, slug, name)
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for filename in KINDS[kind]["starter_files"]:
        title = filename.rsplit(".", 1)[0].replace("-", " ").title()
        (target / filename).write_text(f"# {name} · {title}\n\n请在用户确认归档内容后填写。\n", encoding="utf-8")
    print(f"created draft {kind} package: {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=SKILL_ROOT, help="pm-kit skill root")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover", help="list catalog resources without validating them")
    sub.add_parser("validate", help="validate every manifest against its schema and report problems")
    sub.add_parser("rebuild-index", help="write catalog/index.json from the current manifests")
    create = sub.add_parser("scaffold", help="create a draft resource package under catalog/local")
    create.add_argument("kind", choices=sorted(KINDS))
    create.add_argument("slug")
    create.add_argument("--name", required=True)
    return parser


def main() -> int:
    harden_stdout()
    args = build_parser().parse_args()
    root = args.root.resolve()

    if args.command == "discover":
        return command_discover(root)
    if args.command == "validate":
        return command_validate(root)
    if args.command == "rebuild-index":
        return command_rebuild_index(root)
    if args.command == "scaffold":
        return command_scaffold(root, args.kind, args.slug, args.name)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
