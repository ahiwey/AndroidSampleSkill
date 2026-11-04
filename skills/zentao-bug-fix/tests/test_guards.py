import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from workflow_guard import acceptance, creation_action, schedule, writeback_action
from workspace_guard import capture, compare


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.state = {
            "code": "done", "checks": {"static": "passed", "paparazzi": "passed"},
            "behavior": {"status": "not_run"},
            "writeback": {"requested": True, "authorized": True, "observation": "unchanged"},
        }

    def test_default_checks_allow_confirmation_but_not_behavior_claim(self):
        result = acceptance(self.state)
        self.assertTrue(result["ready_for_writeback"])
        self.assertEqual("needs_regression", result["behavior"])
        self.assertEqual("pending", result["flow"])

    def test_display_only_success_remains_limited_after_writeback(self):
        self.state["behavior"] = {"status": "passed", "coverage": "component_only", "evidence": "image.png"}
        self.state["writeback"]["observation"] = "matches"
        self.assertEqual({"flow": "complete", "behavior": "needs_regression", "next": "already_matches", "ready_for_writeback": False}, acceptance(self.state))

    def test_actual_defect_path_requires_evidence(self):
        self.state["behavior"] = {"status": "passed", "coverage": "defect_path"}
        self.assertEqual("needs_regression", acceptance(self.state)["behavior"])
        self.state["behavior"]["evidence"] = "red-green.log"
        self.assertEqual("verified", acceptance(self.state)["behavior"])

    def test_known_behavior_or_required_check_failure_blocks_write(self):
        for failing in ("behavior", "static", "paparazzi"):
            state = copy.deepcopy(self.state)
            if failing == "behavior":
                state["behavior"]["status"] = "failed"
            else:
                state["checks"][failing] = "failed"
            self.assertEqual("failed", acceptance(state)["flow"])
            self.assertEqual("do_not_write", acceptance(state)["next"])

    def test_missing_check_and_missing_handoff_do_not_finish(self):
        del self.state["checks"]["paparazzi"]
        self.assertEqual("pending", acceptance(self.state)["flow"])
        self.state["checks"]["paparazzi"] = "passed"
        self.state["code"] = "pending"
        self.assertEqual("do_not_write", acceptance(self.state)["next"])

    def test_extra_required_check_cannot_be_ignored(self):
        self.state["checks"]["compile"] = "pending"
        self.assertEqual("do_not_write", acceptance(self.state)["next"])
        self.state["checks"]["compile"] = "passed"
        self.assertTrue(acceptance(self.state)["ready_for_writeback"])

    def test_no_ui_requires_reason_and_alternative_check(self):
        self.state["checks"]["paparazzi"] = "not_applicable"
        with self.assertRaises(ValueError):
            acceptance(self.state)
        self.state["no_ui_reason"] = "Pure data parser without visual output"
        self.assertEqual("pending", acceptance(self.state)["flow"])
        self.state["checks"]["non_visual"] = "passed"
        self.assertTrue(acceptance(self.state)["ready_for_writeback"])

    def test_override_needs_explicit_authorization(self):
        self.state["validation_override"] = {"required": ["static"], "reason": "User chose static only"}
        with self.assertRaises(ValueError):
            acceptance(self.state)
        self.state["validation_override"]["authorized"] = True
        del self.state["checks"]["paparazzi"]
        self.assertTrue(acceptance(self.state)["ready_for_writeback"])

    def test_timeout_reads_back_and_never_blindly_repeats(self):
        state = {"authorized": True, "attempted": True, "observation": "unknown"}
        self.assertEqual("readback_first", writeback_action(state))
        state["observation"] = "matches"
        self.assertEqual("already_matches", writeback_action(state))
        state["observation"] = "unchanged"
        self.assertEqual("retry_once", writeback_action(state))
        state["retry_count"] = 1
        self.assertEqual("needs_attention", writeback_action(state))

    def test_no_authorization_no_write_and_conflict_does_not_overwrite(self):
        self.assertEqual("needs_authorization", writeback_action({"observation": "unchanged"}))
        self.assertEqual("not_requested", writeback_action({"requested": False}))
        self.assertEqual("needs_attention", writeback_action({"authorized": True, "observation": "conflict"}))
        self.state["writeback"]["failed"] = True
        self.assertEqual("failed", acceptance(self.state)["flow"])

    def test_creation_timeout_does_not_duplicate(self):
        self.assertEqual("lookup_first", creation_action({}))
        self.assertEqual("reuse", creation_action({"observation": "exists"}))
        self.assertEqual("create", creation_action({"observation": "absent"}))

    def test_file_conflict_unknown_scope_and_dependency_are_deferred(self):
        result = schedule({"tasks": [
            {"id": "p:1", "files": ["app/A.kt"]},
            {"id": "p:2", "files": ["app\\a.kt"]},
            {"id": "p:3", "files": ["B.kt"], "depends_on": ["p:1"]},
            {"id": "p:4", "files": []},
            {"id": "p:5", "files": ["C.kt"]},
        ]})
        self.assertEqual(["p:1", "p:5"], result["selected"])
        self.assertEqual(["p:2", "p:3", "p:4"], result["deferred"])

    def test_cli_reports_limited_completion(self):
        self.state["writeback"]["observation"] = "matches"
        with tempfile.TemporaryDirectory(prefix="zentao-guard-") as folder:
            fixture = Path(folder) / "acceptance.json"
            fixture.write_text(json.dumps(self.state), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "workflow_guard.py"), "acceptance", str(fixture)], capture_output=True, check=True)
            self.assertEqual("needs_regression", json.loads(result.stdout)["behavior"])


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="zentao-workspace-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Local Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.repo / "existing.txt").write_text("original\n", encoding="utf-8")
        self.git("add", "existing.txt")
        self.git("commit", "-qm", "fixture")
        self.name = "已有文件 空格.md"
        (self.repo / self.name).write_text("staged\n", encoding="utf-8")
        self.git("add", self.name)
        (self.repo / self.name).write_text("staged plus unstaged\n", encoding="utf-8")
        self.before = capture(self.repo)

    def git(self, *args):
        return subprocess.run(["git", "-c", "safe.directory=" + self.repo.as_posix(), "-C", str(self.repo), *args], capture_output=True, check=True)

    def test_unicode_and_staged_unstaged_states_roundtrip(self):
        self.assertEqual("AM", self.before["files"][self.name]["status"])
        self.assertTrue(compare(self.before, capture(self.repo))["ok"])

    def test_unrelated_edit_and_staging_are_detected(self):
        (self.repo / self.name).write_text("overwritten", encoding="utf-8")
        result = compare(self.before, capture(self.repo))
        self.assertEqual([self.name], result["changed_existing"])
        self.git("add", self.name)
        self.assertIn("index_sha256", compare(self.before, capture(self.repo))["changed_metadata"])

    def test_only_declared_new_changes_are_accepted(self):
        (self.repo / "fix.kt").write_text("fix", encoding="utf-8")
        self.assertFalse(compare(self.before, capture(self.repo))["ok"])
        self.assertTrue(compare(self.before, capture(self.repo), ["fix.kt"])["ok"])

    def test_rename_and_delete_are_parsed(self):
        self.git("mv", "existing.txt", "renamed file.txt")
        current = capture(self.repo)
        self.assertEqual("existing.txt", current["files"]["renamed file.txt"]["original_path"])
        (self.repo / "renamed file.txt").unlink()
        self.assertEqual("missing", capture(self.repo)["files"]["renamed file.txt"]["kind"])

    def test_capture_cli_refuses_to_replace_baseline(self):
        output = self.root / "baseline.json"
        command = [sys.executable, "-B", str(SCRIPTS / "workspace_guard.py"), "capture", "--repo", str(self.repo), "--output", str(output)]
        self.assertEqual(0, subprocess.run(command, capture_output=True).returncode)
        original = output.read_bytes()
        self.assertEqual(2, subprocess.run(command, capture_output=True).returncode)
        self.assertEqual(original, output.read_bytes())
        check = subprocess.run([sys.executable, "-B", str(SCRIPTS / "workspace_guard.py"), "check", "--repo", str(self.repo), "--baseline", str(output)], capture_output=True)
        self.assertEqual(0, check.returncode)
        self.assertTrue(json.loads(check.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
