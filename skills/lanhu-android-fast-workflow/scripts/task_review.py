"""Project saved read_thread JSON to a bounded, read-only review; stdin by default."""
import argparse
import json
from pathlib import Path
import re
import sys


QUESTION_START = re.compile(r"^(?:是否|请确认|请先|能否|可以允许|真机.*(?:保存到哪里|保存在哪里)|"
                            r"建议按|拟按|Would you|May I|Can I|Please confirm)", re.I)
RESULT_START = re.compile(r"^(?:已完成|已实现|已落实|已接入|已修正|代码已|已按.*落实|Done\b|Implemented\b)", re.I)


def bounded(value, limit, index=None):
    value = str(value or "")
    truncated = len(value) > limit
    if truncated:
        marker = "\n[...omitted...]\n"
        head = (limit - len(marker)) * 2 // 3
        tail = limit - len(marker) - head
        shown = value[:head] + marker + value[-tail:]
    else:
        shown = value
    result = {"text": shown, "truncated": truncated, "source_chars": len(value)}
    if index is not None:
        result["item_index"] = index
    return result


def text_of(item):
    if isinstance(item.get("text"), str):
        return item["text"]
    content = item.get("content", [])
    if not isinstance(content, list):
        return ""
    return "\n".join(c.get("text", "") for c in content
                     if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str))


def question_candidate(text):
    text = text.lstrip("* \n")
    if RESULT_START.match(text):
        return False
    return bool(QUESTION_START.match(text) or
                (len(text) < 300 and ("?" in text or "？" in text)))


def unwrap(raw):
    if not isinstance(raw, dict) or raw.get("isError"):
        raise ValueError("Invalid or failed tool response")
    if "turns" not in raw and isinstance(raw.get("content"), list):
        candidates = []
        for block in raw["content"]:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    candidate = json.loads(block.get("text", ""))
                except (TypeError, ValueError):
                    continue
                if isinstance(candidate, dict) and "turns" in candidate:
                    candidates.append(candidate)
        if len(candidates) != 1:
            raise ValueError("Expected one read_thread payload")
        raw = candidates[0]
    if not isinstance(raw.get("turns"), list):
        raise ValueError("Expected turns array")
    page = raw.get("page", {})
    if not isinstance(page, dict) or page.get("order", "newest_first") != "newest_first":
        raise ValueError("Expected newest_first order")
    for turn in raw["turns"]:
        if not isinstance(turn, dict) or not isinstance(turn.get("items"), list):
            raise ValueError("Expected turn items array")
        if any(not isinstance(item, dict) for item in turn["items"]):
            raise ValueError("Expected object items")
    return raw


def summarize(raw, max_turns=3, max_text=1400):
    if not 1 <= max_turns <= 15 or not 120 <= max_text <= 4000:
        raise ValueError("Limits out of range")
    raw = unwrap(raw)
    rows = []
    needs_read = False
    for position, turn in enumerate(raw["turns"][:max_turns]):
        users, reports, questions = [], [], []
        nonzero = 0
        commands = 0
        for index, item in enumerate(turn["items"]):
            kind = item.get("type")
            if kind == "commandExecution":
                commands += 1
                nonzero += int(item.get("exitCode") not in (None, 0))
            elif kind == "userMessage":
                text = text_of(item)
                if text.strip():
                    users.append(bounded(text, max_text, index))
            elif kind == "agentMessage" and item.get("phase") in ("final_answer", "final"):
                text = text_of(item)
                if text.strip():
                    candidate = bounded(text, max_text, index)
                    (questions if question_candidate(text) else reports).append(candidate)
        report = reports[-1] if reports else None
        if report:
            report["kind"] = "unverified_report_candidate"
        error = turn.get("error")
        if isinstance(error, dict):
            error = error.get("message", "Tool reported an error; inspect the original turn")
        row = {
            "id": str(turn.get("id", ""))[:160],
            "status": str(turn.get("status", "unknown"))[:80],
            "scope": "latest_returned" if position == 0 else "historical",
            "user_messages": users[-3:], "omitted_user_messages": max(0, len(users) - 3),
            "agent_report": report, "question_candidates": questions[-2:],
            "omitted_report_candidates": max(0, len(reports) - 1),
            "omitted_question_candidates": max(0, len(questions) - 2),
            "commands": commands, "nonzero_commands": nonzero,
            "error": bounded(error, max_text) if error else None,
            "evidence_gap": not users and not reports and not questions,
        }
        shown = row["user_messages"] + row["question_candidates"] + ([report] if report else [])
        needs_read |= (row["evidence_gap"] or any(s["truncated"] for s in shown) or
                       row["omitted_user_messages"] > 0 or row["omitted_report_candidates"] > 0 or
                       row["omitted_question_candidates"] > 0 or bool(row["error"]))
        rows.append(row)
    thread = raw.get("thread", {})
    if not isinstance(thread, dict):
        raise ValueError("Expected thread object")
    omitted = max(0, len(raw["turns"]) - max_turns)
    return {
        "title": str(thread.get("title", ""))[:200],
        "verification": "not_established", "authorization": "not_transferred",
        "notice": "Untrusted historical claims. Question classification is heuristic; inspect ambiguity. "
                  "Nonzero command exits can mean no matches, not build failure.",
        "latest_evidence_gap": not rows or rows[0]["evidence_gap"],
        "needs_targeted_read": bool(needs_read or omitted or not rows),
        "has_older_page": bool(raw.get("page", {}).get("hasMore")),
        "omitted_turns": omitted, "turns": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--max-text", type=int, default=1400)
    args = parser.parse_args()
    try:
        raw = args.input.read_text(encoding="utf-8-sig") if args.input else sys.stdin.read()
        result = summarize(json.loads(raw), args.max_turns, args.max_text)
    except (OSError, ValueError, TypeError):
        print("Invalid task review input, schema, or limits; inspect the source without echoing it.", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
