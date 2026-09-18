"""Summarize explicitly selected local evidence; never execute validation."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def summarize(reports=(), snapshots=(), previous=None):
    result = {"scope": "existing_files_only", "source_freshness": "unverified",
              "visual_review": "not_established", "runtime": "not_established",
              "reports": [], "snapshots": [], "issues": [],
              "totals": dict(tests=0, failures=0, errors=0, skipped=0)}
    old = {item["path"]: item.get("sha256") for item in (previous or {}).get("snapshots", [])}
    for value in dict.fromkeys(str(Path(p).resolve()) for p in reports):
        try:
            root = ET.parse(value).getroot()
            cases = list(root.iter("testcase"))
            if root.tag not in ("testsuite", "testsuites") or not cases:
                raise ValueError("No testcase evidence; summary-only/empty report is not accepted")
            for suite in root.iter():
                if suite.tag in ("testsuite", "testsuites") and suite.get("tests") is not None:
                    if int(suite.get("tests")) != len(list(suite.iter("testcase"))):
                        raise ValueError("Declared test count differs from testcase evidence")
            counts = dict(tests=len(cases), failures=0, errors=0, skipped=0)
            failures = []
            for case in cases:
                for kind in ("failure", "error", "skipped"):
                    node = case.find(kind)
                    if node is not None:
                        counts[{"failure": "failures", "error": "errors", "skipped": "skipped"}[kind]] += 1
                        if kind != "skipped" and len(failures) < 3:
                            failures.append({"test": case.get("name", ""), "kind": kind,
                                             "message": (node.get("message") or node.text or "")[:400]})
            result["reports"].append({"path": value, "counts": counts,
                                      "timestamp": root.get("timestamp"), "first_failures": failures})
            for key in counts:
                result["totals"][key] += counts[key]
        except (OSError, ET.ParseError, ValueError) as exc:
            result["issues"].append({"path": value, "error": str(exc)[:400]})
    for value in dict.fromkeys(str(Path(p).resolve()) for p in snapshots):
        try:
            path = Path(value)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result["snapshots"].append({"path": value, "sha256": digest,
                "change": "unknown" if value not in old else "unchanged" if old[value] == digest else "changed"})
        except OSError as exc:
            result["issues"].append({"path": value, "error": str(exc)[:400]})
    totals = result["totals"]
    result["report_result"] = ("incomplete" if result["issues"] or not totals["tests"] else
        "failed" if totals["failures"] or totals["errors"] else
        "passed_with_skips" if totals["skipped"] else "passed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="append", default=[], help="Exact JUnit XML path; repeatable")
    parser.add_argument("--snapshot", action="append", default=[], help="Exact snapshot path; repeatable")
    parser.add_argument("--previous", help="Previously saved summary JSON; read only")
    args = parser.parse_args()
    try:
        previous = json.loads(Path(args.previous).read_text(encoding="utf-8-sig")) if args.previous else None
        if previous is not None and (not isinstance(previous, dict) or
                not isinstance(previous.get("snapshots", []), list) or
                any(not isinstance(item, dict) or "path" not in item for item in previous.get("snapshots", []))):
            raise ValueError("Invalid previous summary")
        result = summarize(args.report, args.snapshot, previous)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["report_result"] in ("passed", "passed_with_skips") else 1


if __name__ == "__main__":
    raise SystemExit(main())
