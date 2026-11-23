#!/usr/bin/env python3
"""Regression tests for the html-prd module scripts.

守的是脚本与文档承诺一致：数据源引用怎么判定、说明正文怎么渲染、坏文件怎么报错。
所有 fixture 建在临时目录里，不触碰模块内任何文件。

运行：python -B -X utf8 tests/test_html_prd_scripts.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = TESTS_DIR.parent
SCRIPTS = SKILL_ROOT / "modules" / "html-prd" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate_outputs = load_module("validate_outputs", SCRIPTS / "validate_outputs.py")
build_review = load_module("build_single_file_review", SCRIPTS / "build_single_file_review.py")


class LocalTargetTest(unittest.TestCase):
    """只有空 scheme 和 file: 算本地；其余 scheme 不能报成本地页面缺失。"""

    REVIEW = Path("out/PRD评审版.html")

    def test_non_local_schemes_are_skipped(self):
        for value in (
            "about:blank",
            "blob:https://example.com/abc",
            "mailto:a@b.c",
            "tel:123456",
            "javascript:void(0)",
            "https://example.com/x",
            "data:text/css,a{}",
        ):
            with self.subTest(value=value):
                self.assertIsNone(validate_outputs.local_target(self.REVIEW, value))

    def test_local_references_are_resolved(self):
        for value in ("page.html", "../pages/page.html", "./x/y.html"):
            with self.subTest(value=value):
                self.assertIsNotNone(validate_outputs.local_target(self.REVIEW, value))

    def test_fragment_only_reference_has_no_local_file(self):
        """纯锚点没有对应文件可核对，应跳过而不是解析成目录。"""
        self.assertIsNone(validate_outputs.local_target(self.REVIEW, "#p01"))

    def test_windows_file_url_keeps_the_drive(self):
        target = validate_outputs.local_target(self.REVIEW, "file:///E:/proj/page.html")
        self.assertIsNotNone(target)
        self.assertEqual(target.name, "page.html")

    def test_remote_file_url_is_skipped(self):
        self.assertIsNone(validate_outputs.local_target(self.REVIEW, "file://server/share/page.html"))


class DependencyScannerTest(unittest.TestCase):
    """已内联和不可导航的引用不构成外部依赖，否则会误报。"""

    def scan(self, markup: str) -> list[str]:
        scanner = build_review.DependencyScanner()
        scanner.feed(markup)
        return scanner.dependencies

    def test_inlined_and_inert_references_are_not_dependencies(self):
        markup = (
            '<link rel="stylesheet" href="data:text/css,a{}">'
            '<a href="mailto:a@b.c">mail</a>'
            '<a href="tel:123">call</a>'
            '<a href="#p01">jump</a>'
            '<img src="data:image/png;base64,AAAA">'
        )
        self.assertEqual(self.scan(markup), [])

    def test_real_references_are_still_dependencies(self):
        markup = (
            '<link rel="stylesheet" href="style.css">'
            '<a href="page.html">next</a>'
            '<script src="https://cdn.example.com/x.js"></script>'
        )
        self.assertEqual(len(self.scan(markup)), 3)


class NoteHtmlTest(unittest.TestCase):
    """说明正文里的表格和有序列表要渲染成真结构，不能变成一堆裸竖线。"""

    def test_pipe_table_becomes_a_table(self):
        html = build_review.note_html("| 字段 | 类型 |\n| --- | --- |\n| 名称 | 文本 |\n", "P01")
        self.assertIn("<table>", html)
        self.assertIn("<th>字段</th>", html)
        self.assertIn("<td>名称</td>", html)
        self.assertNotIn("| --- |", html)

    def test_ordered_list_becomes_ol(self):
        html = build_review.note_html("1. 第一项\n2. 第二项\n", "P01")
        self.assertIn("<ol>", html)
        self.assertIn("<li>第一项</li>", html)

    def test_unordered_list_still_works(self):
        html = build_review.note_html("- 甲\n- 乙\n", "P01")
        self.assertIn("<ul>", html)
        self.assertIn("<li>甲</li>", html)

    def test_page_heading_is_dropped_and_bold_line_becomes_heading(self):
        html = build_review.note_html("### P01 工作台\n**1. 功能目标**\n", "P01")
        self.assertNotIn("P01 工作台", html)
        self.assertIn("<h3>1. 功能目标</h3>", html)


class ReadPagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_map(self, payload: dict) -> Path:
        path = self.dir / "review-pages.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_navigate_null_falls_back_to_match(self):
        (self.dir / "P01.md").write_text("**目标**\n", encoding="utf-8")
        path = self.write_map(
            {"pages": [{"id": "P01", "name": "工作台", "match": "#overview", "navigate": None, "note": "P01.md"}]}
        )
        pages = build_review.read_pages(path)
        self.assertEqual(pages[0]["navigate"], "#overview")
        self.assertNotEqual(pages[0]["navigate"], "None")

    def test_gbk_note_is_reported_instead_of_crashing(self):
        (self.dir / "P01.md").write_bytes("**目标**\n".encode("gbk"))
        path = self.write_map({"pages": [{"id": "P01", "name": "工作台", "match": "#overview", "note": "P01.md"}]})
        with self.assertRaises(ValueError) as ctx:
            build_review.read_pages(path)
        self.assertIn("UTF-8", str(ctx.exception))

    def test_missing_pages_list_is_reported(self):
        path = self.write_map({"items": []})
        with self.assertRaises(ValueError):
            build_review.read_pages(path)

    def test_note_outside_the_map_directory_is_rejected(self):
        """note 只能指向映射文件所在目录之内，否则一个 ../.. 就能读到任意位置。"""
        sub = self.dir / "过程记录"
        sub.mkdir()
        (self.dir / "P01.md").write_text("**目标**\n", encoding="utf-8")
        path = sub / "review-pages.json"
        path.write_text(
            json.dumps(
                {"pages": [{"id": "P01", "name": "工作台", "match": "#a", "note": "../P01.md"}]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError) as ctx:
            build_review.read_pages(path)
        self.assertIn("之内", str(ctx.exception))

    def test_broken_json_is_reported(self):
        path = self.dir / "review-pages.json"
        path.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_review.read_pages(path)


class ValidateTextFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_gbk_file_is_reported_instead_of_crashing(self):
        path = self.dir / "PRD.md"
        path.write_bytes("# 标题\n".encode("gbk"))
        errors: list[str] = []
        validate_outputs.validate_text_file(path, errors)
        self.assertTrue(errors, "非 UTF-8 文件应报错，而不是抛出未捕获异常")
        self.assertIn("UTF-8", errors[0])

    def test_lowercase_placeholder_is_detected(self):
        path = self.dir / "PRD.md"
        path.write_text("# 标题\n{{page_title}}\n", encoding="utf-8")
        errors: list[str] = []
        validate_outputs.validate_text_file(path, errors)
        self.assertTrue(any("占位符" in item for item in errors))

    def test_clean_file_has_no_errors(self):
        path = self.dir / "PRD.md"
        path.write_text("# 标题\n\nP01 工作台\n", encoding="utf-8")
        errors: list[str] = []
        validate_outputs.validate_text_file(path, errors)
        self.assertEqual(errors, [])


class VerifyManifestTest(unittest.TestCase):
    """只核对清单里的文件不够，事后新增的源文件同样会改变产物依据。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "src"
        self.dir.mkdir()
        (self.dir / "index.html").write_text("<html></html>", encoding="utf-8")
        self.manifest = Path(self._tmp.name) / "source-hashes.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def snapshot(self) -> None:
        args = argparse.Namespace(source=self.dir, manifest=self.manifest, exclude=[])
        self.assertEqual(validate_outputs.snapshot(args), 0)

    def test_unchanged_tree_passes(self):
        self.snapshot()
        errors: list[str] = []
        validate_outputs.verify_manifest(self.manifest, self.dir, errors)
        self.assertEqual(errors, [])

    def test_new_source_file_is_reported(self):
        self.snapshot()
        (self.dir / "extra.css").write_text("body{}", encoding="utf-8")
        errors: list[str] = []
        validate_outputs.verify_manifest(self.manifest, self.dir, errors)
        self.assertTrue(any("新源文件" in item for item in errors), errors)

    def test_modified_source_file_is_reported(self):
        self.snapshot()
        (self.dir / "index.html").write_text("<html>changed</html>", encoding="utf-8")
        errors: list[str] = []
        validate_outputs.verify_manifest(self.manifest, self.dir, errors)
        self.assertTrue(any("发生变化" in item for item in errors), errors)

    def test_missing_source_file_is_reported(self):
        self.snapshot()
        (self.dir / "index.html").unlink()
        errors: list[str] = []
        validate_outputs.verify_manifest(self.manifest, self.dir, errors)
        self.assertTrue(any("已缺失" in item for item in errors), errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
