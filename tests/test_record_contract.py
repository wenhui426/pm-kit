#!/usr/bin/env python3
"""Keep the examples in references/record-contract.md executable.

契约文档最容易腐化的地方是示例：字段改了、示例没改，照着抄的人就会写出通不过的记录。
这里把文档里的每一段示例抽出来，建到临时目录里，再用真正的校验器跑一遍。

运行：python -B -X utf8 tests/test_record_contract.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TESTS_DIR.parent
CONTRACT = SKILL_ROOT / "references" / "record-contract.md"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_records.py"

# 示例用 **`路径`** 起头，紧跟着一段 json 代码块
LABEL_RE = re.compile(r"^\*\*`([^`]+)`\*\*")


def extract_examples(markdown_path: Path) -> list[tuple[str, str]]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    examples: list[tuple[str, str]] = []
    pending: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        label = LABEL_RE.match(line)
        if label:
            pending = label.group(1)
        if line.strip() == "```json" and pending:
            body: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                body.append(lines[index])
                index += 1
            examples.append((pending, "\n".join(body) + "\n"))
            pending = None
        index += 1
    return examples


class RecordContractExamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.examples = extract_examples(CONTRACT)

    def test_all_six_record_types_have_examples(self):
        labels = [label for label, _ in self.examples]
        self.assertGreaterEqual(len(labels), 6, f"契约文档应给出六类文件的示例，实际：{labels}")
        self.assertEqual(len(labels), len(set(labels)), "示例路径不能重复")
        joined = " ".join(labels)
        for expected in ("projects.json", "project.json", "task.json", "business-rules.json", "artifact-index.json", "runs/"):
            with self.subTest(record=expected):
                self.assertIn(expected, joined)

    def test_examples_are_valid_json(self):
        for label, body in self.examples:
            with self.subTest(example=label):
                json.loads(body)

    @unittest.skipIf(importlib.util.find_spec("jsonschema") is None, "需要 jsonschema 才能运行校验器")
    def test_documented_examples_pass_the_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, body in self.examples:
                target = root / label
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, f"文档示例未通过校验：\n{result.stdout}\n{result.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
