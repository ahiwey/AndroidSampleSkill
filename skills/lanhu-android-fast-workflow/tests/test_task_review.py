import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts/task_review.py"
SPEC = importlib.util.spec_from_file_location("task_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def message(text, kind="agentMessage", phase="final_answer"):
    return {"type": kind, "text": text, "phase": phase}


def page(*turns):
    return {"thread": {"title": "Synthetic task", "id": "fixture"},
            "page": {"order": "newest_first", "hasMore": False}, "turns": list(turns)}


def turn(*items, status="completed", ident="latest"):
    return {"id": ident, "status": status, "items": list(items)}


class TaskReviewTests(unittest.TestCase):
    def test_question_tagged_as_final_does_not_replace_delivery(self):
        result = MODULE.summarize(page(turn(
            message("是否继续真机验证？\n- 允许\n- 暂不"),
            message("已完成代码和静态检查；新版尚未安装。是否符合预期？"))))
        item = result["turns"][0]
        self.assertIn("尚未安装", item["agent_report"]["text"])
        self.assertEqual(item["question_candidates"][0]["item_index"], 0)
        self.assertEqual(item["agent_report"]["item_index"], 1)

    def test_question_after_result_is_not_selected_as_delivery(self):
        item = MODULE.summarize(page(turn(message("已实现布局，未运行设备。"),
                                         message("是否允许操作设备？"))))["turns"][0]
        self.assertIn("已实现", item["agent_report"]["text"])

    def test_proposal_and_unknown_prose_never_become_verified_completion(self):
        result = MODULE.summarize(page(turn(message("建议按以下方案实施。确认后继续。"))))
        self.assertIsNone(result["turns"][0]["agent_report"])
        self.assertEqual(result["verification"], "not_established")
        unknown = MODULE.summarize(page(turn(message("Some opaque prose."))))
        self.assertEqual(unknown["verification"], "not_established")
        self.assertEqual(unknown["turns"][0]["agent_report"]["kind"], "unverified_report_candidate")

    def test_empty_latest_turn_retains_gap_and_historical_result(self):
        result = MODULE.summarize(page(turn(), turn(message("已完成真机验收。"), ident="older")))
        self.assertTrue(result["latest_evidence_gap"])
        self.assertIsNone(result["turns"][0]["agent_report"])
        self.assertEqual(result["turns"][1]["scope"], "historical")

    def test_interrupted_turn_is_not_promoted_by_old_success(self):
        result = MODULE.summarize(page(turn(status="interrupted"), turn(message("Done."), ident="old")))
        self.assertEqual(result["turns"][0]["status"], "interrupted")
        self.assertTrue(result["latest_evidence_gap"])

    def test_user_correction_kept_and_commands_never_echoed(self):
        command = {"type": "commandExecution", "command": "DO_NOT_ECHO " + "x" * 100000,
                   "output": "PRIVATE_TOOL_OUTPUT", "exitCode": 1}
        result = MODULE.summarize(page(turn(command, message("还是不对，背景有断层", "userMessage"))))
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertIn("背景有断层", encoded)
        self.assertNotIn("DO_NOT_ECHO", encoded)
        self.assertNotIn("PRIVATE_TOOL_OUTPUT", encoded)
        self.assertEqual(result["turns"][0]["nonzero_commands"], 1)

    def test_wrapped_mcp_response_and_content_blocks(self):
        raw = page(turn({"type": "userMessage", "content": [{"type": "text", "text": "继续"}]},
                        message("已完成静态检查。")))
        result = MODULE.summarize({"content": [{"type": "text", "text": json.dumps(raw)}]})
        self.assertEqual(result["turns"][0]["user_messages"][0]["text"], "继续")

    def test_bounds_keep_head_tail_and_expose_omissions(self):
        text = "已完成布局。" + "a" * 2000 + "设备验证尚未完成。"
        result = MODULE.summarize(page(turn(message(text)), turn(message("old"))), max_turns=1, max_text=120)
        report = result["turns"][0]["agent_report"]
        self.assertLessEqual(len(report["text"]), 120)
        self.assertTrue(report["truncated"])
        self.assertTrue(report["text"].endswith("设备验证尚未完成。"))
        self.assertEqual(result["omitted_turns"], 1)
        self.assertTrue(result["needs_targeted_read"])

    def test_cli_malformed_json_fails_without_echo(self):
        run = subprocess.run([sys.executable, "-B", str(SCRIPT)], input="SECRET invalid json",
                             capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn("SECRET", run.stdout + run.stderr)

    def test_invalid_schema_and_order_are_not_silently_accepted(self):
        for raw in ({}, {"turns": "bad"}, page({"items": "bad"}), {"isError": True}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                MODULE.summarize(raw)
        raw = page(turn())
        raw["page"]["order"] = "oldest_first"
        with self.assertRaises(ValueError):
            MODULE.summarize(raw)

    def test_original_input_is_unchanged_and_error_detail_bounded(self):
        raw = page(turn(message("已完成静态检查。")))
        raw["turns"][0]["error"] = {"message": "e" * 4000}
        before = json.dumps(raw)
        result = MODULE.summarize(raw, max_text=120)
        self.assertEqual(json.dumps(raw), before)
        self.assertLessEqual(len(result["turns"][0]["error"]["text"]), 120)

    def test_empty_response_does_not_prove_success(self):
        result = MODULE.summarize(page())
        self.assertTrue(result["latest_evidence_gap"])
        self.assertEqual(result["verification"], "not_established")

    def test_blank_message_is_still_a_retrieval_gap(self):
        result = MODULE.summarize(page(turn(message("  ", "userMessage"), message("\n"))))
        self.assertTrue(result["latest_evidence_gap"])


if __name__ == "__main__":
    unittest.main()
