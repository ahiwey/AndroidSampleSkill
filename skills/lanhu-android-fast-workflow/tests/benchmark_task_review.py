"""Measure a synthetic transcript projection; not an agent or Token benchmark."""
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time


SCRIPT = Path(__file__).parents[1] / "scripts/task_review.py"
SPEC = importlib.util.spec_from_file_location("task_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture():
    return {
        "thread": {"title": "Synthetic shared component review", "id": "synthetic"},
        "page": {"order": "newest_first", "hasMore": False},
        "turns": [
            {"id": "latest", "status": "interrupted", "items": []},
            {"id": "historical", "status": "completed", "items": [
                {"type": "userMessage", "text": "背景仍不连续，请检查公共组件。"},
                *[{"type": "commandExecution", "command": "synthetic command " + "x" * 1800,
                   "output": "synthetic output " + "y" * 1800, "exitCode": 0} for _ in range(160)],
                {"type": "agentMessage", "phase": "final_answer", "text": "是否继续真机验证？"},
                {"type": "agentMessage", "phase": "final_answer",
                 "text": "已完成静态检查；新 APK 尚未安装，运行效果未验证。"},
            ]},
        ],
    }


def run():
    source = json.dumps(fixture(), ensure_ascii=False, separators=(",", ":"))
    def raw_output():
        return json.dumps(json.loads(source), ensure_ascii=False, separators=(",", ":"))
    def projection():
        return json.dumps(MODULE.summarize(json.loads(source)), ensure_ascii=False, separators=(",", ":"))
    outputs, medians = {}, {}
    for name, operation in (("raw", raw_output), ("projected", projection)):
        operation()
        elapsed = []
        for _ in range(30):
            start = time.perf_counter()
            outputs[name] = operation()
            elapsed.append((time.perf_counter() - start) * 1000)
        medians[name] = round(statistics.median(elapsed), 3)
    result = json.loads(outputs["projected"])
    assert result["latest_evidence_gap"]
    assert result["turns"][1]["scope"] == "historical"
    assert "尚未安装" in result["turns"][1]["agent_report"]["text"]
    assert result["turns"][1]["user_messages"][0]["text"] == "背景仍不连续，请检查公共组件。"
    assert result["turns"][1]["commands"] == 160
    start = time.perf_counter()
    process = subprocess.run([sys.executable, "-B", "-X", "utf8", str(SCRIPT)],
                             input=source, text=True, encoding="utf-8", capture_output=True, check=True)
    cold_ms = round((time.perf_counter() - start) * 1000, 3)
    assert json.loads(process.stdout) == result
    print(json.dumps({"input_sha256": hashlib.sha256(source.encode()).hexdigest(),
                      "python": platform.python_version(), "system": platform.system(),
                      "warm_runs": 30, "median_ms": medians, "new_cli_cold_ms": cold_ms,
                      "output_chars": {k: len(v) for k, v in outputs.items()},
                      "invariants": "passed", "token_usage": "unavailable",
                      "scope": "synthetic JSON projection only; not App/agent speed or quality"},
                     ensure_ascii=False))


if __name__ == "__main__":
    run()
