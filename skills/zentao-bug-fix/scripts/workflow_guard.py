#!/usr/bin/env python3
"""Local decision checks only. Never calls a browser, creates a chat or changes a Bug."""
import argparse
import json
import posixpath
import sys
from pathlib import Path


def writeback_action(state):
    if state.get("requested", True) is False:
        return "not_requested"
    if state.get("authorized") is not True:
        return "needs_authorization"
    if state.get("failed") is True:
        return "writeback_failed"
    observation = state.get("observation", "unknown")
    if observation == "matches":
        return "already_matches"
    if observation == "unknown":
        return "readback_first"
    if observation == "conflict":
        return "needs_attention"
    if observation != "unchanged":
        raise ValueError("Invalid writeback observation")
    if not state.get("attempted", False):
        return "write_once"
    return "retry_once" if state.get("retry_count", 0) == 0 else "needs_attention"


def acceptance(state):
    code = state.get("code", "pending")
    if code not in {"pending", "done", "failed", "skipped"}:
        raise ValueError("Invalid code status")
    checks = state.get("checks", {})
    if any(v not in {"passed", "failed", "pending", "not_applicable"} for v in checks.values()):
        raise ValueError("Invalid check status")
    behavior = state.get("behavior", {})
    behavior_status = behavior.get("status", "not_run")
    if behavior_status not in {"passed", "failed", "not_run"}:
        raise ValueError("Invalid behavior status")
    if code == "skipped":
        return {"flow": "skipped", "behavior": "not_run", "next": "do_not_write"}
    if code == "failed" or "failed" in checks.values() or behavior_status == "failed":
        return {"flow": "failed", "behavior": behavior_status, "next": "do_not_write"}
    required = ["static", "paparazzi"]
    override = state.get("validation_override")
    if override:
        if override.get("authorized") is not True or not override.get("reason") or not override.get("required"):
            raise ValueError("Validation override needs explicit authorization, reason and checks")
        required = override["required"]
    elif checks.get("paparazzi") == "not_applicable":
        if not state.get("no_ui_reason"):
            raise ValueError("Paparazzi not applicable requires a no-UI reason, not a missing framework")
        required = ["static", "non_visual"]
    # Any additional recorded check is required; optional uncovered behavior belongs in behavior.
    required = set(required) | {name for name in checks if name != "paparazzi" or checks[name] != "not_applicable"}
    if code != "done" or any(checks.get(name) != "passed" for name in required):
        return {"flow": "pending", "behavior": behavior_status, "next": "do_not_write"}
    covered = behavior_status == "passed" and behavior.get("coverage") == "defect_path" and bool(behavior.get("evidence"))
    action = writeback_action(state.get("writeback", {}))
    complete = action in {"already_matches", "not_requested"}
    return {
        "flow": "failed" if action == "writeback_failed" else "complete" if complete else "pending",
        "behavior": "verified" if covered else "needs_regression",
        "next": action,
        "ready_for_writeback": action in {"write_once", "retry_once"},
    }


def schedule(state):
    limit = state.get("limit", 3)
    if type(limit) is not int or limit < 1:
        raise ValueError("Concurrency must be a positive integer")
    tasks = state["tasks"]
    if len({task["id"] for task in tasks}) != len(tasks):
        raise ValueError("Duplicate task identity; use project + Bug ID")
    completed = set(state.get("completed", []))
    occupied, selected, deferred = set(), [], []
    for task in tasks:
        if task["id"] in completed:
            continue
        paths = {posixpath.normpath(p.replace("\\", "/")) for p in task.get("files", [])}
        if not state.get("case_sensitive", False):
            paths = {p.casefold() for p in paths}
        dependencies = set(task.get("depends_on", []))
        if not paths or not dependencies <= completed or paths & occupied or len(selected) >= limit:
            deferred.append(task["id"])
        else:
            selected.append(task["id"])
            occupied.update(paths)
    return {"selected": selected, "deferred": deferred}


def creation_action(state):
    return {"exists": "reuse", "absent": "create", "unknown": "lookup_first"}[state.get("observation", "unknown")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["acceptance", "writeback", "schedule", "creation"])
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    state = json.loads(args.input.read_text(encoding="utf-8-sig"))
    handler = {"acceptance": acceptance, "writeback": writeback_action, "schedule": schedule, "creation": creation_action}[args.kind]
    print(json.dumps(handler(state), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
