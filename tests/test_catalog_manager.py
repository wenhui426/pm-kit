#!/usr/bin/env python3
"""Regression tests for scripts/catalog_manager.py.

这些测试守的是「扩展契约」：用户新增资源时，脚手架造出来的东西必须和文档一致，
校验器必须真的能拦住坏资源。所有 fixture 都建在临时目录里，不会碰到 catalog/ 本身。

运行：python -B -X utf8 tests/test_catalog_manager.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TESTS_DIR.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "catalog_manager.py"
SCHEMA_SRC = SKILL_ROOT / "catalog" / "_schemas"


def load_module():
    spec = importlib.util.spec_from_file_location("catalog_manager", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


cm = load_module()

# 文档「使用说明与扩展指南.md」第 8.3 节给出的场景包目录示例。
DOCUMENTED_SCENARIO_FILES = ["overview.md", "roles.md", "workflow.md", "states.md", "risks.md", "validation.md"]


def scenario_manifest(resource_id: str, **overrides) -> dict:
    data = {
        "kind": "scenario",
        "id": resource_id,
        "name": "测试场景",
        "version": "1.0.0",
        "status": "active",
        "extends": [],
        "triggers": ["测试"],
        "platforms": ["web"],
        "capabilities": ["测试能力"],
        "files": {"overview": "overview.md"},
    }
    data.update(overrides)
    return data


class CatalogManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "pm-kit"
        (self.root / "catalog" / "built-in").mkdir(parents=True)
        (self.root / "catalog" / "local").mkdir(parents=True)
        shutil.copytree(SCHEMA_SRC, self.root / "catalog" / "_schemas")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- helpers ---------------------------------------------------------

    def write_manifest(self, relative_dir: str, data: dict, encoding: str = "utf-8") -> Path:
        target = self.root / "catalog" / relative_dir
        target.mkdir(parents=True, exist_ok=True)
        path = target / "manifest.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding=encoding)
        return path

    def write_referenced_files(self, relative_dir: str, names: list[str]) -> None:
        target = self.root / "catalog" / relative_dir
        target.mkdir(parents=True, exist_ok=True)
        for name in names:
            (target / name).write_text("# stub\n", encoding="utf-8")

    def run_command(self, func, *args):
        """运行命令并捕获 stdout/stderr，返回 (exit_code, stdout, stderr)。"""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = func(*args)
        return code, out.getvalue(), err.getvalue()

    def errors_text(self) -> str:
        code, out, _ = self.run_command(cm.command_validate, self.root)
        payload = json.loads(out)
        return " | ".join(payload["errors"])

    # --- A2: 脚手架必须和文档一致 -----------------------------------------

    def test_scaffold_creates_the_documented_scenario_files(self):
        code, _, _ = self.run_command(cm.command_scaffold, self.root, "scenario", "store-inspection", "门店巡检")
        self.assertEqual(code, 0)

        package = self.root / "catalog" / "local" / "scenarios" / "store-inspection"
        on_disk = sorted(p.name for p in package.iterdir() if p.suffix == ".md")
        self.assertEqual(on_disk, sorted(DOCUMENTED_SCENARIO_FILES))

        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8-sig"))
        expected_keys = {Path(name).stem.replace("-", "_") for name in DOCUMENTED_SCENARIO_FILES}
        self.assertEqual(set(manifest["files"].keys()), expected_keys)
        for name in DOCUMENTED_SCENARIO_FILES:
            self.assertTrue((package / name).is_file(), f"{name} 未生成")

    def test_scaffolded_draft_passes_validation(self):
        self.run_command(cm.command_scaffold, self.root, "scenario", "store-inspection", "门店巡检")
        code, out, _ = self.run_command(cm.command_validate, self.root)
        self.assertEqual(code, 0, f"新建的 draft 资源不应报错：{out}")

    def test_scaffold_refuses_existing_target(self):
        self.run_command(cm.command_scaffold, self.root, "template", "team-prd", "团队 PRD")
        code, _, _ = self.run_command(cm.command_scaffold, self.root, "template", "team-prd", "团队 PRD")
        self.assertEqual(code, 2)

    def test_scaffold_rejects_bad_slug(self):
        code, _, _ = self.run_command(cm.command_scaffold, self.root, "template", "Bad_Slug", "x")
        self.assertEqual(code, 2)

    # --- A3: extends 必须真的被校验 ---------------------------------------

    def test_extends_to_missing_parent_is_reported(self):
        self.write_referenced_files("local/scenarios/child", ["overview.md"])
        self.write_manifest("local/scenarios/child", scenario_manifest("local:child", extends=["built-in:does-not-exist"]))
        self.assertIn("not found in catalog", self.errors_text())

    def test_extends_to_different_kind_is_reported(self):
        self.write_referenced_files("built-in/templates/base", ["template.md"])
        self.write_manifest(
            "built-in/templates/base",
            {
                "kind": "template",
                "id": "built-in:base",
                "name": "基础模板",
                "version": "1.0.0",
                "status": "active",
                "extends": [],
                "triggers": ["模板"],
                "output_type": "document",
                "formats": ["md"],
                "applies_to": ["测试"],
                "required_fields": ["字段"],
                "files": {"template": "template.md"},
            },
        )
        self.write_referenced_files("local/scenarios/child", ["overview.md"])
        self.write_manifest("local/scenarios/child", scenario_manifest("local:child", extends=["built-in:base"]))
        self.assertIn("is a template, not scenario", self.errors_text())

    def test_extends_self_reference_is_reported(self):
        self.write_referenced_files("local/scenarios/selfish", ["overview.md"])
        self.write_manifest("local/scenarios/selfish", scenario_manifest("local:selfish", extends=["local:selfish"]))
        self.assertIn("cannot reference itself", self.errors_text())

    def test_extends_cycle_is_reported(self):
        self.write_referenced_files("local/scenarios/alpha", ["overview.md"])
        self.write_referenced_files("local/scenarios/beta", ["overview.md"])
        self.write_manifest("local/scenarios/alpha", scenario_manifest("local:alpha", extends=["local:beta"]))
        self.write_manifest("local/scenarios/beta", scenario_manifest("local:beta", extends=["local:alpha"]))
        self.assertIn("extends cycle", self.errors_text())

    def test_extends_more_than_one_parent_is_rejected_by_schema(self):
        self.write_referenced_files("local/scenarios/greedy", ["overview.md"])
        self.write_manifest(
            "local/scenarios/greedy",
            scenario_manifest("local:greedy", extends=["built-in:a", "built-in:b"]),
        )
        errors = self.errors_text()
        self.assertIn("extends", errors)
        self.assertIn("too long", errors.lower())

    def test_valid_extends_chain_passes(self):
        self.write_referenced_files("built-in/scenarios/base", ["overview.md"])
        self.write_manifest("built-in/scenarios/base", scenario_manifest("built-in:base"))
        self.write_referenced_files("local/scenarios/child", ["overview.md"])
        self.write_manifest("local/scenarios/child", scenario_manifest("local:child", extends=["built-in:base"]))
        code, out, _ = self.run_command(cm.command_validate, self.root)
        self.assertEqual(code, 0, out)

    # --- 其它语义检查 -----------------------------------------------------

    def test_duplicate_id_is_reported(self):
        self.write_referenced_files("built-in/scenarios/one", ["overview.md"])
        self.write_referenced_files("local/scenarios/two", ["overview.md"])
        self.write_manifest("built-in/scenarios/one", scenario_manifest("built-in:dupe"))
        self.write_manifest("local/scenarios/two", scenario_manifest("built-in:dupe"))
        self.assertIn("duplicate id", self.errors_text())

    def test_id_must_match_directory(self):
        self.write_referenced_files("local/scenarios/mismatch", ["overview.md"])
        self.write_manifest("local/scenarios/mismatch", scenario_manifest("local:something-else"))
        self.assertIn("to match its directory", self.errors_text())

    def test_missing_referenced_file_is_reported(self):
        self.write_manifest("local/scenarios/broken", scenario_manifest("local:broken"))
        self.assertIn("not found", self.errors_text())

    def test_final_status_rejects_empty_required_list(self):
        self.write_referenced_files("local/scenarios/empty", ["overview.md"])
        self.write_manifest(
            "local/scenarios/empty",
            scenario_manifest("local:empty", status="active", capabilities=[]),
        )
        self.assertIn("cannot be empty", self.errors_text())

    def test_draft_may_still_be_incomplete(self):
        self.write_referenced_files("local/scenarios/wip", ["overview.md"])
        self.write_manifest(
            "local/scenarios/wip",
            scenario_manifest("local:wip", status="draft", capabilities=[], platforms=["web"]),
        )
        code, out, _ = self.run_command(cm.command_validate, self.root)
        self.assertEqual(code, 0, out)

    def test_triggers_must_never_be_empty(self):
        """triggers 是资源被匹配到的唯一入口，draft 阶段也必须写，不适用「定稿才要求完整」。"""
        self.write_referenced_files("local/scenarios/notrigger", ["overview.md"])
        self.write_manifest(
            "local/scenarios/notrigger",
            scenario_manifest("local:notrigger", status="draft", triggers=[]),
        )
        self.assertIn("triggers", self.errors_text())

    # --- A6: Windows 编码 -------------------------------------------------

    def test_manifest_with_bom_is_readable(self):
        self.write_referenced_files("local/scenarios/bom", ["overview.md"])
        self.write_manifest("local/scenarios/bom", scenario_manifest("local:bom"), encoding="utf-8-sig")
        code, out, _ = self.run_command(cm.command_validate, self.root)
        self.assertEqual(code, 0, f"带 BOM 的 manifest 不应被判为非法：{out}")

    # --- A4 / A5: 命令语义 ------------------------------------------------

    def test_discover_lists_without_validating(self):
        self.write_manifest("local/scenarios/weird", {"kind": "not-a-kind", "id": "local:weird"})
        code, out, _ = self.run_command(cm.command_discover, self.root)
        self.assertEqual(code, 0, "discover 只列资源，不该因资源有问题而失败")
        payload = json.loads(out)
        self.assertEqual(payload["count"], 1)
        self.assertNotIn("valid", payload["resources"][0])

        code, _, _ = self.run_command(cm.command_validate, self.root)
        self.assertEqual(code, 1, "validate 必须报出不受支持的 kind")

    def test_rebuild_index_writes_even_when_a_resource_is_broken(self):
        self.write_manifest("local/scenarios/weird", {"kind": "not-a-kind", "id": "local:weird"})
        code, out, err = self.run_command(cm.command_rebuild_index, self.root)
        self.assertEqual(code, 1, "有问题的资源应让退出码非零")
        index = self.root / "catalog" / "index.json"
        self.assertTrue(index.is_file(), "索引必须照样写出，否则 draft 期索引永远停更")
        payload = json.loads(index.read_text(encoding="utf-8-sig"))
        self.assertTrue(payload["schema_validated"])
        self.assertTrue(payload["errors"])
        self.assertIn("index written", err)

    def test_rebuild_index_reports_local_resources_separately(self):
        self.run_command(cm.command_scaffold, self.root, "case", "sample-case", "示例案例")
        code, _, _ = self.run_command(cm.command_rebuild_index, self.root)
        self.assertEqual(code, 0)
        local_index = json.loads((self.root / "catalog" / "local" / "index.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(local_index["count"], 1)
        self.assertEqual(local_index["resources"][0]["id"], "local:sample-case")


@unittest.skipIf(cm.jsonschema is None, "需要 jsonschema 才能校验结构")
class SchemaRequiredToBeUsedTest(unittest.TestCase):
    """确认 schema 真的在生效：改坏 schema 必须让资源失败。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "pm-kit"
        (self.root / "catalog" / "built-in").mkdir(parents=True)
        (self.root / "catalog" / "local").mkdir(parents=True)
        shutil.copytree(SCHEMA_SRC, self.root / "catalog" / "_schemas")
        package = self.root / "catalog" / "local" / "scenarios" / "subject"
        package.mkdir(parents=True)
        (package / "overview.md").write_text("# stub\n", encoding="utf-8")
        manifest = {
            "kind": "scenario",
            "id": "local:subject",
            "name": "主题",
            "version": "1.0.0",
            "status": "active",
            "extends": [],
            "triggers": ["测试"],
            "platforms": ["web"],
            "capabilities": ["能力"],
            "files": {"overview": "overview.md"},
        }
        (package / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_removing_a_required_field_from_schema_relaxes_the_check(self):
        """schema 是唯一的结构事实源：去掉 required 后，缺字段的资源就不再报错。"""
        schema_path = self.root / "catalog" / "_schemas" / "scenario.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
        schema["required"] = [f for f in schema["required"] if f != "capabilities"]
        schema["properties"].pop("capabilities", None)
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

        package = self.root / "catalog" / "local" / "scenarios" / "subject"
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8-sig"))
        manifest.pop("capabilities")
        (package / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cm.command_validate(self.root)
        self.assertEqual(code, 0, f"schema 放宽后不应再报错，说明结构校验没有走 schema：{out.getvalue()}")

    def test_missing_schema_file_is_reported(self):
        (self.root / "catalog" / "_schemas" / "scenario.schema.json").unlink()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cm.command_validate(self.root)
        self.assertEqual(code, 1)
        self.assertIn("no schema", out.getvalue())


class RegistryContractTest(unittest.TestCase):
    """守入口契约：新增一种能力只要在 registry.json 登记正确，就不需要改 SKILL.md。"""

    def setUp(self) -> None:
        self.registry = json.loads((SKILL_ROOT / "capabilities" / "registry.json").read_text(encoding="utf-8-sig"))

    def test_every_capability_points_at_real_files(self):
        self.assertTrue(self.registry["capabilities"], "能力清单不能为空")
        for capability in self.registry["capabilities"]:
            with self.subTest(capability=capability.get("id")):
                self.assertIn("resource_base", capability, "每个能力都要声明 resource_base")
                instruction = SKILL_ROOT / capability["instruction"]
                self.assertTrue(instruction.is_file(), f"instruction 不存在：{capability['instruction']}")
                base = (SKILL_ROOT / capability["resource_base"]).resolve()
                self.assertTrue(base.is_dir(), f"resource_base 不存在：{capability['resource_base']}")
                self.assertIn(
                    SKILL_ROOT.resolve(),
                    [base, *base.parents],
                    "resource_base 必须落在技能包内",
                )

    def test_capability_ids_are_unique_and_documented(self):
        seen = set()
        for capability in self.registry["capabilities"]:
            with self.subTest(capability=capability.get("id")):
                self.assertNotIn(capability["id"], seen, "能力 id 不能重复")
                seen.add(capability["id"])
                for field in ("when", "accepts", "produces"):
                    self.assertTrue(capability.get(field), f"{capability['id']} 缺少 {field}")

    @unittest.skipIf(cm.jsonschema is None, "需要 jsonschema")
    def test_registry_matches_the_capability_schema(self):
        """能力清单本身也要有 schema：字段和取值不该只活在数据里。"""
        import jsonschema

        schema = json.loads(
            (SKILL_ROOT / "catalog" / "_schemas" / "capability.schema.json").read_text(encoding="utf-8-sig")
        )
        validator = jsonschema.Draft202012Validator(schema)
        found = sorted(validator.iter_errors(self.registry), key=lambda e: list(e.absolute_path))
        problems = [f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}" for e in found]
        self.assertEqual(problems, [])

    def test_every_bundled_module_has_the_required_pieces(self):
        """模块契约：内嵌模块至少要有 procedure.md 和 README.md。

        assets/ references/ design-specs/ scripts/ evals/ 都是可选的——现有三个模块
        各自带不同的可选部分，所以骨架必须写清哪些必需、哪些可选。
        """
        modules = [item for item in self.registry["capabilities"] if item["kind"] == "bundled-module"]
        self.assertTrue(modules, "能力清单里应当有内嵌模块")
        for capability in modules:
            base = SKILL_ROOT / capability["resource_base"]
            with self.subTest(module=capability["id"]):
                self.assertTrue((base / "procedure.md").is_file(), f"{capability['id']} 缺少 procedure.md")
                self.assertTrue((base / "README.md").is_file(), f"{capability['id']} 缺少 README.md")
                self.assertEqual(
                    (SKILL_ROOT / capability["instruction"]).resolve(),
                    (base / "procedure.md").resolve(),
                    "instruction 应当指向该模块的 procedure.md",
                )

    def test_skill_md_does_not_hardcode_capability_kinds(self):
        """入口正文写死分派规则的话，新增一种能力类型就必须改 SKILL.md。"""
        skill_md = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        self.assertNotIn("`internal-procedure` 读取本包参考文件", skill_md)
        self.assertIn("resource_base", skill_md)


class DocumentedLimitsMatchSchemaTest(unittest.TestCase):
    """`SKILL.md` 写的资源加载上限必须和 workflow-plan.schema.json 的 maxItems 一致。

    上限写错时不会有任何报错，只会让每次任务加载过多资源、规则互相冲突，
    所以用测试把文档和 schema 钉在一起；改上限就必须两边一起改。
    """

    NUMERALS = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4}
    FIELD_BY_WORD = {
        "场景": "scenarios",
        "组件库": "component_libraries",
        "主模板": "templates",
        "相似案例": "cases",
    }

    def test_skill_md_limits_match_schema(self):
        skill_md = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
        sentence = re.search(r"每次最多加载[^。]*。", skill_md)
        self.assertIsNotNone(sentence, "SKILL.md 应写清资源加载上限")

        documented: dict[str, int] = {}
        pattern = r"(一|两|二|三|四|\d+)个(场景|组件库|主模板|相似案例)"
        for count, word in re.findall(pattern, sentence.group(0)):
            documented[self.FIELD_BY_WORD[word]] = self.NUMERALS.get(count) or int(count)

        schema_path = SKILL_ROOT / "catalog" / "_schemas" / "workflow-plan.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
        limits = schema["properties"]["resources"]["properties"]

        self.assertEqual(set(documented), set(limits), "文档提到的资源类型应与 schema 一致")
        for field, spec in limits.items():
            with self.subTest(field=field):
                self.assertEqual(documented[field], spec["maxItems"])


class DocumentedTaskModeMatchesSchemaTest(unittest.TestCase):
    """`task_mode` 的取值只写在 schema 与 task-modes.md 两处，必须一致。

    只写 `type: string` 等于不校验：计划里填什么词都静默通过。
    """

    def test_task_mode_enum_matches_the_mode_document(self):
        import re

        schema = json.loads(
            (SKILL_ROOT / "catalog" / "_schemas" / "workflow-plan.schema.json").read_text(encoding="utf-8-sig")
        )
        enum = schema["properties"]["task_mode"]["enum"]
        self.assertEqual(len(enum), 9, "task-modes.md 声明的是九个取值")
        doc = (SKILL_ROOT / "references" / "task-modes.md").read_text(encoding="utf-8-sig")
        # 文档里的写法是 `analysis`（探索、材料分析），靠这个形状精确取值，不会误抓其他行内代码
        listed = set(re.findall(r"`([a-z]+)`(?=（)", doc))
        self.assertEqual(listed, set(enum), "task-modes.md 列的取值与 schema 枚举必须一致")


if __name__ == "__main__":
    unittest.main(verbosity=2)
