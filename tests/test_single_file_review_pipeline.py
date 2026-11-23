#!/usr/bin/env python3
"""两个 html-prd 脚本必须彼此相容。

`build_single_file_review.py` 生成的是本模块的默认交付模式（单文件评审版），
`validate_outputs.py` 负责校验产物结构。如果生成出来的东西过不了自家校验，
默认交付模式就是自相矛盾的——这条测试就是为了让这种矛盾无法悄悄存在。

运行：python -B -X utf8 tests/test_single_file_review_pipeline.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TESTS_DIR.parent
HTML_PRD = SKILL_ROOT / "modules" / "html-prd"
SCRIPTS = HTML_PRD / "scripts"
FIXTURE = HTML_PRD / "evals" / "files" / "sample-prototype.html"

LAYOUT_FILES = {
    "并列可调": "PRD评审版-并列可调.html",
    "聚焦抽屉": "PRD评审版-聚焦抽屉.html",
}


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        # -B：不把 .pyc 写回技能包目录，避免测试运行本身污染包内容
        [sys.executable, "-B", *args],
        capture_output=True,
        check=False,
        # 子进程输出 UTF-8，显式指定编码，避免 Windows 下按本地代码页解码报错
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class SingleFileReviewPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not FIXTURE.is_file():
            raise unittest.SkipTest(f"缺少 fixture：{FIXTURE}")

    def build(self, out: Path) -> subprocess.CompletedProcess[str]:
        (out / "P01.md").write_text(
            "**页面目标**\n\n| 字段 | 说明 |\n| --- | --- |\n| 单号 | 工单编号 |\n", encoding="utf-8"
        )
        (out / "P02.md").write_text("**页面目标**\n\n- 展示工单详情\n- 可返回列表\n", encoding="utf-8")
        pages = out / "review-pages.json"
        pages.write_text(
            json.dumps(
                {
                    "pages": [
                        {"id": "P01", "name": "工单列表", "match": "#list", "note": "P01.md"},
                        {"id": "P02", "name": "工单详情", "match": "#detail", "note": "P02.md"},
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return run(
            [
                str(SCRIPTS / "build_single_file_review.py"),
                "--source",
                str(FIXTURE),
                "--pages",
                str(pages),
                "--output-dir",
                str(out),
                "--layout",
                "both",
            ]
        )

    def test_generated_single_file_passes_the_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            built = self.build(out)
            self.assertEqual(built.returncode, 0, f"生成失败：\n{built.stdout}\n{built.stderr}")

            for layout, filename in LAYOUT_FILES.items():
                with self.subTest(layout=layout):
                    target = out / filename
                    self.assertTrue(target.is_file(), f"没有生成 {filename}")
                    checked = run(
                        [
                            str(SCRIPTS / "validate_outputs.py"),
                            "check",
                            "--source",
                            str(FIXTURE),
                            "--output-dir",
                            str(out),
                            "--mode",
                            "html",
                            "--review-name",
                            filename,
                        ]
                    )
                    self.assertEqual(
                        checked.returncode,
                        0,
                        f"{filename} 未通过自家校验：\n{checked.stdout}\n{checked.stderr}",
                    )

    def test_generated_single_file_is_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertEqual(self.build(out).returncode, 0)
            html = (out / LAYOUT_FILES["并列可调"]).read_text(encoding="utf-8-sig")
            self.assertIn("srcdoc=", html, "单文件版应把原型内联进 srcdoc，而不是引用外部文件")
            self.assertNotIn("{{", html, "产物里不应残留模板占位符")
            self.assertNotIn("{{FIRST_PAGE_SOURCE}}", html)

    def test_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertEqual(self.build(out).returncode, 0)
            second = self.build(out)
            self.assertNotEqual(second.returncode, 0, "已存在同名产物时应拒绝覆盖")

    def test_refuses_when_source_has_external_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            page = out / "P01.md"
            page.write_text("**目标**\n", encoding="utf-8")
            pages = out / "review-pages.json"
            pages.write_text(
                json.dumps({"pages": [{"id": "P01", "name": "首页", "match": "#home", "note": "P01.md"}]}, ensure_ascii=False),
                encoding="utf-8",
            )
            source = out / "with-cdn.html"
            source.write_text(
                "<!DOCTYPE html><html><head><title>x</title></head><body>"
                '<script src="https://cdn.example.com/app.js"></script></body></html>',
                encoding="utf-8",
            )
            built = run(
                [
                    str(SCRIPTS / "build_single_file_review.py"),
                    "--source",
                    str(source),
                    "--pages",
                    str(pages),
                    "--output-dir",
                    str(out),
                    "--layout",
                    "parallel",
                ]
            )
            self.assertNotEqual(built.returncode, 0, "原型含外部资源时不应产出半成品")
            self.assertIn("外部资源", built.stdout + built.stderr)


    def test_missing_source_is_reported_and_written_to_the_report(self):
        """源文件不存在时直接出报告，不要空跑到底再写一份 source 指向不存在路径的报告。"""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = out / "validation-report.json"
            checked = run(
                [
                    str(SCRIPTS / "validate_outputs.py"),
                    "check",
                    "--source",
                    str(out / "does-not-exist"),
                    "--output-dir",
                    str(out),
                    "--mode",
                    "html",
                    "--review-name",
                    "PRD评审版.html",
                    "--report",
                    str(report),
                ]
            )
            self.assertEqual(checked.returncode, 1)
            self.assertIn("输入路径不存在", checked.stdout)
            self.assertNotIn("Traceback", checked.stderr)
            payload = json.loads(report.read_text(encoding="utf-8-sig"))
            self.assertFalse(payload["ok"])
            self.assertTrue(any("输入路径不存在" in item for item in payload["errors"]))

    def test_output_dir_inside_source_warns_about_missing_exclusions(self):
        """输出在输入之内时源文件保护范围为空，必须说出来，否则下一轮会误报新源文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src"
            out = source / "out"
            out.mkdir(parents=True)
            (source / "index.html").write_text("<html><body>原型</body></html>", encoding="utf-8")
            (out / "PRD评审版.html").write_text("<html><body>评审版</body></html>", encoding="utf-8")
            checked = run(
                [
                    str(SCRIPTS / "validate_outputs.py"),
                    "check",
                    "--source",
                    str(source),
                    "--output-dir",
                    str(out),
                    "--mode",
                    "html",
                ]
            )
            self.assertIn("输出目录位于输入目录之内", checked.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
