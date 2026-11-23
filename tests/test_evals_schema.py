#!/usr/bin/env python3
"""评测用例的格式与可判定性检查。

守两件事：
1. 根目录与内嵌模块共用 catalog/_schemas/evals.schema.json；新增模块评测自动纳入检查；
2. assertions 不能为空，且每条用例至少三条 —— 空断言的评测无法机器判定，等于没有评测。

运行：python -B -X utf8 tests/test_evals_schema.py
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TESTS_DIR.parent
SCHEMA = SKILL_ROOT / "catalog" / "_schemas" / "evals.schema.json"

EVAL_FILES = [
    SKILL_ROOT / "evals" / "evals.json",
] + sorted(SKILL_ROOT.glob("modules/*/evals/evals.json"))

MIN_ASSERTIONS = 3


class EvalsSchemaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8-sig"))

    @staticmethod
    def rel(path: Path) -> str:
        return path.relative_to(SKILL_ROOT).as_posix()

    def load(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"缺少评测文件：{path}")
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def test_discovered_eval_sets_exist(self):
        for path in EVAL_FILES:
            with self.subTest(evals=self.rel(path)):
                self.assertTrue(path.is_file(), f"缺少评测文件：{self.rel(path)}")

    @unittest.skipIf(importlib.util.find_spec("jsonschema") is None, "需要 jsonschema")
    def test_every_eval_file_matches_the_shared_schema(self):
        import jsonschema

        validator = jsonschema.Draft202012Validator(self.schema)
        for path in EVAL_FILES:
            with self.subTest(evals=self.rel(path)):
                found = sorted(validator.iter_errors(self.load(path)), key=lambda e: list(e.absolute_path))
                problems = [
                    f"{'/'.join(str(p) for p in err.absolute_path) or '(root)'}: {err.message}" for err in found
                ]
                self.assertEqual(problems, [])

    def test_ids_are_unique_and_start_at_one(self):
        for path in EVAL_FILES:
            with self.subTest(evals=self.rel(path)):
                ids = [item["id"] for item in self.load(path)["evals"]]
                self.assertEqual(len(ids), len(set(ids)), "评测 id 不能重复")
                self.assertEqual(min(ids), 1, "评测 id 从 1 开始，不用 0")

    def test_assertions_are_present_and_specific_enough(self):
        for path in EVAL_FILES:
            for item in self.load(path)["evals"]:
                with self.subTest(evals=self.rel(path), id=item.get("id")):
                    assertions = item.get("assertions") or []
                    self.assertGreaterEqual(
                        len(assertions),
                        MIN_ASSERTIONS,
                        f"评测 {item.get('id')} 的断言少于 {MIN_ASSERTIONS} 条，无法判定",
                    )
                    for text in assertions:
                        self.assertTrue(text.strip(), "断言内容不能为空")

    def test_names_are_unique_within_a_set(self):
        for path in EVAL_FILES:
            names = [item["name"] for item in self.load(path)["evals"] if "name" in item]
            with self.subTest(evals=self.rel(path)):
                self.assertEqual(len(names), len(set(names)), "同一套评测里的 name 不能重复")

    def test_referenced_files_exist(self):
        for path in EVAL_FILES:
            # <skill>/evals/ -> <skill>；<skill>/modules/<m>/evals/ -> <skill>/modules/<m>
            base = path.parent.parent
            for item in self.load(path)["evals"]:
                for rel in item.get("files", []):
                    with self.subTest(evals=self.rel(path), file=rel):
                        self.assertTrue((base / rel).is_file(), f"评测引用的文件不存在：{base / rel}")

    def test_scripts_are_covered_by_a_real_run_case(self):
        """两个最重要的脚本必须有用例要求“实际运行”，而不只是人工目检。"""
        text = json.dumps(self.load(SKILL_ROOT / "evals" / "evals.json"), ensure_ascii=False)
        for script in ("catalog_manager.py", "validate_records.py"):
            with self.subTest(script=script):
                self.assertIn(script, text, f"根级评测没有覆盖 {script} 的实际运行")

    def test_review_layout_and_directory_gates_are_actually_exercised(self):
        """prd-html 的两条强制门禁不能在 prompt 里被预先满足掉。

        对每条门禁分别断言：至少有一条用例**故意不给**它，并且那条用例必须断言 Agent 会先确认。
        早先的写法用 ``or`` 拼两个条件，而「生成目录已确认」这个字面量在任何 prompt 里都不存在，
        于是列表恒非空、断言永不失败——保护的恰是最核心的门禁，实际零保护。
        """
        evals = self.load(SKILL_ROOT / "modules" / "prd-html" / "evals" / "evals.json")["evals"]
        gates = {"生成目录": "目录", "设计规范选型": "规范"}
        for prompt_marker, assertion_marker in gates.items():
            with self.subTest(gate=prompt_marker):
                without_gate = [item for item in evals if prompt_marker not in item["prompt"]]
                self.assertTrue(
                    without_gate, f"没有一条用例故意不给{prompt_marker}，这条门禁从未被测试"
                )
                self.assertTrue(
                    any(
                        assertion_marker in text
                        for item in without_gate
                        for text in item["assertions"]
                    ),
                    f"不给{prompt_marker}的用例没有断言 Agent 会先确认它",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
