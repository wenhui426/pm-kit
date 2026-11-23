"""Focused checks for the read-only cross-round record validator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_records.py"
STAMP = "2026-10-11T10:00:00+08:00"


class RecordValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project_dir = self.root / "alpha"
        self.task_dir = self.project_dir / "tasks" / "task-a"
        self.write(self.root / "projects.json", {
            "schema_version": "1.0",
            "projects": [{"project_id": "alpha", "name": "甲项目", "path": "alpha"}],
        })
        self.write(self.project_dir / "project.json", {
            "schema_version": "1.0", "project_id": "alpha", "name": "甲项目",
            "baseline_version": 1, "status": "active", "updated_at": STAMP,
        })
        self.write(self.project_dir / "business-rules.json", {
            "schema_version": "1.0", "project_id": "alpha", "task_id": None,
            "rules": [{
                "rule_id": "REFUND-07", "revision": 1, "kind": "requirement",
                "statement": "驳回后可重新提交", "scope": "项目退款流程",
                "source": {"type": "user", "detail": "用户确认"}, "status": "confirmed",
                "confirmed_by": "user", "confirmed_at": STAMP, "supersedes": None,
            }],
        })
        self.write(self.task_dir / "task.json", {
            "schema_version": "1.0", "project_id": "alpha", "task_id": "task-a",
            "goal": "完成 PRD", "baseline_version": 1, "status": "in_progress",
            "current_stage": "write-prd", "confirmed_decisions": [], "open_questions": [],
            "latest_run_id": "run-1",
        })
        self.write(self.task_dir / "runs" / "run-1.json", {
            "schema_version": "1.0", "project_id": "alpha", "task_id": "task-a",
            "run_id": "run-1", "goal": "编写 PRD", "baseline_version": 1,
            "input_artifacts": [], "capabilities": ["write-prd"], "decisions": [],
            "changed_files": [], "checks": [], "open_questions": [],
            "current_stage": "write-prd", "next_step": "review",
        })
        self.write(self.project_dir / "artifact-index.json", {
            "schema_version": "1.0", "project_id": "alpha",
            "artifacts": [{
                "artifact_id": "prd", "task_id": "task-a", "type": "markdown",
                "path": "tasks/task-a/artifacts/prd.md", "version": 1,
                "status": "draft", "freshness": "current",
                "depends_on_rules": [{"rule_id": "REFUND-07", "revision": 1}],
                "depends_on_artifacts": [], "checks": [], "updated_at": STAMP,
            }],
        })

    @staticmethod
    def write(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def read(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def validate(self, path: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(path or self.root)],
            capture_output=True,
            check=False,
            # 显式指定编码：子进程输出 UTF-8，而 Windows 默认按本地代码页解码，
            # 会在读取线程里抛 UnicodeDecodeError，把真实的失败输出吞掉。
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def assert_rejected_cleanly(
        self, result: subprocess.CompletedProcess[str], contains: str | None = None
    ) -> None:
        """应当报错退出，但不应当抛栈——校验器崩掉会把真正的问题埋进 traceback。"""
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("ERROR", result.stdout)
        if contains is not None:
            self.assertIn(contains, result.stdout)

    def test_valid_root_and_single_project_are_read_only(self) -> None:
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*.json")}
        self.assertEqual(self.validate().returncode, 0)
        self.assertEqual(self.validate(self.project_dir).returncode, 0)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*.json")}
        self.assertEqual(before, after)

    def test_missing_required_field_fails(self) -> None:
        path = self.task_dir / "task.json"
        data = self.read(path)
        del data["goal"]
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 1)

    def test_unknown_capability_id_fails(self) -> None:
        """轮次记录引用的能力 ID 必须真实存在于能力清单里。

        只校验「是非空字符串数组」会放过打错的能力名，编排计划会指向不存在的能力。
        """
        path = self.task_dir / "runs" / "run-1.json"
        data = self.read(path)
        data["capabilities"] = ["write-prd-typo"]
        self.write(path, data)
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("能力清单", result.stdout, "错误信息应当指出能力 ID 不存在")

    def test_known_capability_id_passes(self) -> None:
        path = self.task_dir / "runs" / "run-1.json"
        data = self.read(path)
        data["capabilities"] = ["make-prd", "review-validate"]
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 0)

    def test_task_directory_name_mismatch_fails(self) -> None:
        data = self.read(self.task_dir / "task.json")
        data["task_id"] = "task-b"
        self.write(self.task_dir / "task.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="task_id 与任务目录名不符")

    def test_task_baseline_above_project_fails(self) -> None:
        data = self.read(self.task_dir / "task.json")
        data["baseline_version"] = 9
        self.write(self.task_dir / "task.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="baseline_version 超过项目当前版本")

    def test_run_id_mismatch_fails(self) -> None:
        data = self.read(self.task_dir / "runs" / "run-1.json")
        data["run_id"] = "run-2"
        self.write(self.task_dir / "runs" / "run-1.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="run_id 与文件名不符")

    def test_artifact_cannot_depend_on_itself(self) -> None:
        data = self.read(self.project_dir / "artifact-index.json")
        data["artifacts"][0]["depends_on_artifacts"] = [{"artifact_id": "prd", "version": 1}]
        self.write(self.project_dir / "artifact-index.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="不能依赖自身版本")

    def test_supersedes_pointing_nowhere_fails(self) -> None:
        data = self.read(self.project_dir / "business-rules.json")
        data["rules"][0]["supersedes"] = {"rule_id": "REFUND-99", "revision": 1}
        self.write(self.project_dir / "business-rules.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="supersedes 找不到旧版")

    def test_artifact_index_project_mismatch_fails(self) -> None:
        data = self.read(self.project_dir / "artifact-index.json")
        data["project_id"] = "beta"
        self.write(self.project_dir / "artifact-index.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="project_id 与项目记录不符")

    def test_index_path_pointing_to_another_project_fails(self) -> None:
        data = self.read(self.root / "projects.json")
        data["projects"][0]["project_id"] = "gamma"
        self.write(self.root / "projects.json", data)
        self.assert_rejected_cleanly(self.validate(), contains="索引路径指向")

    def test_schema_gate_prevents_cross_file_type_errors(self) -> None:
        """结构错误会让整份记录被跳过，跨文件比较因此拿不到错误类型。

        审计曾担心 `baseline_version` 写成字符串会让 `>` 比较抛 TypeError。
        实际不可达：`read_record` 只要发现任何结构问题就整份丢弃，
        所以走到比较那一步的记录一定是 schema 合法的。这条测试把这个前提钉住——
        一旦有人改成"带错继续比较"，这里就会看到 traceback。
        """
        data = self.read(self.task_dir / "task.json")
        data["baseline_version"] = "2"
        self.write(self.task_dir / "task.json", data)
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("SKIPPED", result.stdout, "被跳过的记录应当被明确报出来")

    def test_skipped_records_are_announced(self) -> None:
        """有结构错误的文件会被整体跳过，必须说出来。

        否则它的跨文件检查静默不跑，用户修完一批、再跑一次才发现还有下一批。
        """
        data = self.read(self.task_dir / "runs" / "run-1.json")
        del data["goal"]
        self.write(self.task_dir / "runs" / "run-1.json", data)
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SKIPPED", result.stdout)
        self.assertIn("本轮没有执行", result.stdout)

    def test_wrong_project_ownership_fails(self) -> None:
        path = self.task_dir / "task.json"
        data = self.read(path)
        data["project_id"] = "beta"
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 1)

    def test_dangling_rule_dependency_fails(self) -> None:
        path = self.project_dir / "artifact-index.json"
        data = self.read(path)
        data["artifacts"][0]["depends_on_rules"][0]["revision"] = 2
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 1)

    def test_unknown_schema_version_fails(self) -> None:
        path = self.project_dir / "project.json"
        data = self.read(path)
        data["schema_version"] = "2.0"
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 1)

    def test_missing_latest_run_fails(self) -> None:
        path = self.task_dir / "task.json"
        data = self.read(path)
        data["latest_run_id"] = "run-2"
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 1)

    def test_confirmed_rule_requires_confirmer(self) -> None:
        path = self.project_dir / "business-rules.json"
        data = self.read(path)
        data["rules"][0]["confirmed_by"] = None
        self.write(path, data)
        self.assertEqual(self.validate().returncode, 1)

    def test_new_project_needs_no_empty_task_or_rule_files(self) -> None:
        new_root = self.root / "new-project"
        self.write(new_root / "project.json", {
            "schema_version": "1.0", "project_id": "new-project", "name": "新项目",
            "baseline_version": 1, "status": "active", "updated_at": STAMP,
        })
        self.assertEqual(self.validate(new_root).returncode, 0)

    def test_confirmed_rule_change_requires_downstream_review(self) -> None:
        rules_path = self.project_dir / "business-rules.json"
        rules = self.read(rules_path)
        rules["rules"][0]["status"] = "superseded"
        newer = dict(rules["rules"][0])
        newer.update({
            "revision": 2, "statement": "驳回后不可重新提交",
            "status": "confirmed", "supersedes": {"rule_id": "REFUND-07", "revision": 1},
        })
        rules["rules"].append(newer)
        self.write(rules_path, rules)
        project_path = self.project_dir / "project.json"
        project = self.read(project_path)
        project["baseline_version"] = 2
        self.write(project_path, project)
        index_path = self.project_dir / "artifact-index.json"
        index = self.read(index_path)
        index["artifacts"].append({
            "artifact_id": "prototype", "task_id": "task-a", "type": "html",
            "path": "tasks/task-a/artifacts/prototype.html", "version": 1,
            "status": "reviewed", "freshness": "current", "depends_on_rules": [],
            "depends_on_artifacts": [{"artifact_id": "prd", "version": 1}],
            "checks": [], "updated_at": STAMP,
        })
        self.write(index_path, index)
        self.assertEqual(self.validate().returncode, 1)
        index["artifacts"][0]["freshness"] = "needs_review"
        self.write(index_path, index)
        self.assertEqual(self.validate().returncode, 1)
        index["artifacts"][1]["freshness"] = "needs_review"
        self.write(index_path, index)
        self.assertEqual(self.validate().returncode, 0)

    def test_unconfirmed_new_rule_does_not_invalidate_confirmed_old_rule(self) -> None:
        path = self.project_dir / "business-rules.json"
        rules = self.read(path)
        proposed = dict(rules["rules"][0])
        proposed.update({
            "revision": 2, "statement": "拟取消重新提交",
            "status": "unconfirmed", "confirmed_by": None, "confirmed_at": None,
            "supersedes": {"rule_id": "REFUND-07", "revision": 1},
        })
        rules["rules"].append(proposed)
        self.write(path, rules)
        self.assertEqual(self.validate().returncode, 0)

    def test_other_task_cannot_use_task_local_rule(self) -> None:
        rules_path = self.task_dir / "business-rules.json"
        self.write(rules_path, {
            "schema_version": "1.0", "project_id": "alpha", "task_id": "task-a",
            "rules": [{
                "rule_id": "LOCAL-A", "revision": 1, "kind": "assumption",
                "statement": "仅 A 任务尝试的交互", "scope": "A 任务",
                "source": {"type": "user", "detail": "模拟讨论"},
                "status": "unconfirmed", "confirmed_by": None,
                "confirmed_at": None, "supersedes": None,
            }],
        })
        self.write(self.project_dir / "tasks" / "task-b" / "task.json", {
            "schema_version": "1.0", "project_id": "alpha", "task_id": "task-b",
            "goal": "设计订单列表", "baseline_version": 1, "status": "planned",
            "current_stage": None, "confirmed_decisions": [],
            "open_questions": [], "latest_run_id": None,
        })
        index_path = self.project_dir / "artifact-index.json"
        index = self.read(index_path)
        index["artifacts"].append({
            "artifact_id": "order-list", "task_id": "task-b", "type": "markdown",
            "path": "tasks/task-b/artifacts/order-list.md", "version": 1,
            "status": "draft", "freshness": "current",
            "depends_on_rules": [{"rule_id": "LOCAL-A", "revision": 1}],
            "depends_on_artifacts": [], "checks": [], "updated_at": STAMP,
        })
        self.write(index_path, index)
        self.assertEqual(self.validate().returncode, 1)


if __name__ == "__main__":
    unittest.main()
