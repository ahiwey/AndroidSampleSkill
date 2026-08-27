#!/usr/bin/env python3
"""Audit and safely order Android string resources without third-party packages."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any


UTF8_BOM = b"\xef\xbb\xbf"
UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")
STRING_BLOCK = re.compile(r"<string\b[^>]*>.*?</string\s*>", re.DOTALL)
NAME_ATTR = re.compile(r"\bname\s*=\s*(['\"])(.*?)\1", re.DOTALL)
FORMAT_TOKEN = re.compile(
    r"%(?:\d+\$)?[-#+0,(<]*\d*(?:\.\d+)?[bBhHsScCdoxXeEfgGaAtTn]|%%"
)
MOJIBAKE_PATTERNS = (
    "\ufffd",
    "Ã©",
    "Ã¨",
    "Ãª",
    "Ã¡",
    "Ã³",
    "Ãº",
    "Ã±",
    "Â°",
    "â€™",
    "â€œ",
    "â€",
    "ðŸ",
    "ï¿½",
    "锟斤拷",
)
COMMON_STABLE_TERMS = {
    "bpm",
    "min",
    "sec",
    "kg",
    "ms",
    "km",
    "kcal",
    "mmhg",
    "°c",
    "°f",
    "12h",
    "24h",
    "ecg",
    "hrv",
    "gps",
    "ok",
}


class AuditError(RuntimeError):
    """Raised when a resource file cannot be safely processed."""


def configure_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure:
        reconfigure(encoding="utf-8", errors="backslashreplace")


def read_utf8(path: pathlib.Path) -> tuple[str, dict[str, Any]]:
    raw = path.read_bytes()
    if raw.startswith(UTF16_BOMS):
        raise AuditError(f"UTF-16 is not supported: {path}")
    has_bom = raw.startswith(UTF8_BOM)
    payload = raw[len(UTF8_BOM) :] if has_bom else raw
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AuditError(f"Invalid UTF-8 in {path}: {exc}") from exc
    crlf = payload.count(b"\r\n")
    lf_only = payload.count(b"\n") - crlf
    cr_only = payload.count(b"\r") - crlf
    if crlf and not lf_only and not cr_only:
        newline = "CRLF"
    elif lf_only and not crlf and not cr_only:
        newline = "LF"
    elif cr_only and not crlf and not lf_only:
        newline = "CR"
    elif not crlf and not lf_only and not cr_only:
        newline = "none"
    else:
        newline = "mixed"
    return text, {
        "has_utf8_bom": has_bom,
        "newline": newline,
        "crlf_count": crlf,
        "lf_only_count": lf_only,
        "cr_only_count": cr_only,
        "raw": raw,
    }


def parse_xml(path: pathlib.Path, text: str) -> ET.Element:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise AuditError(f"Malformed XML in {path}: {exc}") from exc
    if root.tag != "resources":
        raise AuditError(f"Expected <resources> root in {path}, found <{root.tag}>")
    return root


def direct_strings(root: ET.Element) -> list[ET.Element]:
    return [child for child in root if child.tag == "string"]


def element_text(element: ET.Element) -> str:
    return "".join(element.itertext())


def duplicate_names(elements: list[ET.Element]) -> list[str]:
    names = [element.attrib.get("name", "") for element in elements]
    return sorted(name for name, count in collections.Counter(names).items() if count > 1)


def nested_string_names(root: ET.Element) -> list[str]:
    direct_ids = {id(element) for element in direct_strings(root)}
    return sorted(
        element.attrib.get("name", "<missing-name>")
        for element in root.iter("string")
        if id(element) not in direct_ids
    )


def placeholders(element: ET.Element) -> list[str]:
    if element.attrib.get("formatted", "true").lower() == "false":
        return []
    return sorted(FORMAT_TOKEN.findall(element_text(element)))


def suspicious_mojibake(text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        patterns = [pattern for pattern in MOJIBAKE_PATTERNS if pattern in line]
        if patterns:
            hits.append(
                {
                    "line": line_number,
                    "patterns": patterns,
                    "snippet": line.strip()[:240],
                }
            )
    return hits


def is_stable_same_value(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return True
    lowered = normalized.lower()
    if lowered in COMMON_STABLE_TERMS:
        return True
    without_formats = FORMAT_TOKEN.sub("", normalized).strip(" -–—_:/.,()%")
    if not without_formats:
        return True
    if without_formats.lower() in COMMON_STABLE_TERMS:
        return True
    if not re.search(r"[A-Za-z]", without_formats):
        return True
    if any(operator in without_formats for operator in ("*", "+", "/", "=")) and re.fullmatch(
        r"[A-Za-z0-9*+./=_-]{1,16}", without_formats
    ):
        return True
    if re.fullmatch(r"[A-Z0-9*+._/-]{1,10}", without_formats):
        return True
    return False


def resource_files(res_dir: pathlib.Path, base_path: pathlib.Path) -> list[pathlib.Path]:
    files = sorted(res_dir.glob("values*/strings.xml"))
    return [path.resolve() for path in files if path.resolve() != base_path]


def resolve_base(res_dir: pathlib.Path, base: str) -> pathlib.Path:
    base_path = pathlib.Path(base)
    if not base_path.is_absolute():
        base_path = res_dir / base_path
    if not base_path.is_file():
        raise AuditError(f"Default strings file does not exist: {base_path}")
    return base_path.resolve()


def audit_resources(res_dir: pathlib.Path, base_path: pathlib.Path) -> dict[str, Any]:
    base_text, base_encoding = read_utf8(base_path)
    base_root = parse_xml(base_path, base_text)
    base_items = direct_strings(base_root)
    base_names = [item.attrib.get("name", "") for item in base_items]
    base_by_name = {item.attrib.get("name", ""): item for item in base_items}
    translatable_names = [
        item.attrib.get("name", "")
        for item in base_items
        if item.attrib.get("translatable", "true").lower() != "false"
    ]

    same_summary: dict[str, dict[str, Any]] = {}
    locales: dict[str, dict[str, Any]] = {}
    for path in resource_files(res_dir, base_path):
        text, encoding = read_utf8(path)
        root = parse_xml(path, text)
        items = direct_strings(root)
        names = [item.attrib.get("name", "") for item in items]
        by_name = {item.attrib.get("name", ""): item for item in items}
        name_set = set(names)
        base_set = set(base_names)
        missing = [name for name in translatable_names if name not in name_set]
        extras = [name for name in names if name not in base_set]
        expected_order = [name for name in base_names if name in name_set]
        actual_order = [name for name in names if name in base_set]
        placeholder_mismatches = []
        for name in expected_order:
            base_tokens = placeholders(base_by_name[name])
            locale_tokens = placeholders(by_name[name])
            if base_tokens != locale_tokens:
                placeholder_mismatches.append(
                    {"name": name, "base": base_tokens, "locale": locale_tokens}
                )
        same_candidates = []
        same_stable = []
        for name in translatable_names:
            if name not in by_name:
                continue
            base_value = element_text(base_by_name[name]).strip()
            locale_value = element_text(by_name[name]).strip()
            if locale_value != base_value:
                continue
            stable = is_stable_same_value(base_value)
            (same_stable if stable else same_candidates).append(name)
            summary = same_summary.setdefault(
                name,
                {"value": base_value, "locales": [], "stable": stable},
            )
            summary["locales"].append(path.parent.name)
        non_string_children = [
            child.tag for child in root if isinstance(child.tag, str) and child.tag != "string"
        ]
        locales[path.parent.name] = {
            "path": str(path),
            "string_count": len(items),
            "missing": missing,
            "extra": extras,
            "duplicates": duplicate_names(items),
            "nested_strings": nested_string_names(root),
            "non_string_children": non_string_children,
            "ordered_like_default": actual_order == expected_order,
            "placeholder_mismatches": placeholder_mismatches,
            "same_as_default_candidates": same_candidates,
            "same_as_default_stable": same_stable,
            "mojibake": suspicious_mojibake(text),
            "encoding": {key: value for key, value in encoding.items() if key != "raw"},
        }

    grouped_same = [
        {
            "name": name,
            "value": data["value"],
            "locale_count": len(data["locales"]),
            "locales": data["locales"],
            "stable": data["stable"],
        }
        for name, data in same_summary.items()
    ]
    grouped_same.sort(key=lambda item: (-item["locale_count"], item["name"]))
    return {
        "res_dir": str(res_dir),
        "default": {
            "path": str(base_path),
            "string_count": len(base_items),
            "translatable_count": len(translatable_names),
            "translatable_false_count": len(base_items) - len(translatable_names),
            "duplicates": duplicate_names(base_items),
            "nested_strings": nested_string_names(base_root),
            "non_string_children": [
                child.tag
                for child in base_root
                if isinstance(child.tag, str) and child.tag != "string"
            ],
            "mojibake": suspicious_mojibake(base_text),
            "encoding": {key: value for key, value in base_encoding.items() if key != "raw"},
        },
        "locale_count": len(locales),
        "locales": locales,
        "same_as_default": grouped_same,
    }


def report_failures(report: dict[str, Any]) -> list[str]:
    failures = []
    default = report["default"]
    for field in ("duplicates", "nested_strings", "non_string_children", "mojibake"):
        if default[field]:
            failures.append(f"default:{field}={len(default[field])}")
    if default["encoding"]["newline"] == "mixed":
        failures.append("default:mixed-newlines")
    for locale, data in report["locales"].items():
        for field in (
            "missing",
            "duplicates",
            "nested_strings",
            "placeholder_mismatches",
            "mojibake",
        ):
            if data[field]:
                failures.append(f"{locale}:{field}={len(data[field])}")
        if not data["ordered_like_default"]:
            failures.append(f"{locale}:order")
        if data["encoding"]["newline"] == "mixed":
            failures.append(f"{locale}:mixed-newlines")
    return failures


def print_human_report(report: dict[str, Any]) -> None:
    default = report["default"]
    print(
        "default_strings={string_count} translatable={translatable_count} "
        "translatable_false={translatable_false_count} locales={locale_count}".format(
            locale_count=report["locale_count"], **default
        )
    )
    print(
        "locale                         strings missing dup nested order placeholders "
        "same? mojibake newline"
    )
    for locale, data in report["locales"].items():
        print(
            f"{locale:<30} {data['string_count']:>7} {len(data['missing']):>7} "
            f"{len(data['duplicates']):>3} {len(data['nested_strings']):>6} "
            f"{str(data['ordered_like_default']):>5} "
            f"{len(data['placeholder_mismatches']):>12} "
            f"{len(data['same_as_default_candidates']):>5} "
            f"{len(data['mojibake']):>8} {data['encoding']['newline']}"
        )
    candidates = [item for item in report["same_as_default"] if not item["stable"]]
    if candidates:
        print("\nTop same-as-default translation candidates:")
        for item in candidates[:40]:
            value = item["value"].replace("\n", "\\n")
            print(f"  {item['name']} locales={item['locale_count']}: {value[:140]}")
    failures = report_failures(report)
    print(f"\nstrict_failures={len(failures)}")
    for failure in failures[:80]:
        print(f"  {failure}")


def ensure_sortable(path: pathlib.Path, text: str, root: ET.Element) -> None:
    items = direct_strings(root)
    nested = nested_string_names(root)
    duplicates = duplicate_names(items)
    non_string = [
        child.tag for child in root if isinstance(child.tag, str) and child.tag != "string"
    ]
    blocks = list(STRING_BLOCK.finditer(text))
    problems = []
    if nested:
        problems.append(f"nested strings: {nested}")
    if duplicates:
        problems.append(f"duplicate strings: {duplicates}")
    if non_string:
        problems.append(f"non-string children: {non_string}")
    if len(blocks) != len(items):
        problems.append(f"raw blocks={len(blocks)} xml strings={len(items)}")
    if problems:
        raise AuditError(f"Refusing to sort {path}: {'; '.join(problems)}")


def sorted_bytes(path: pathlib.Path, base_order: dict[str, int]) -> bytes:
    text, encoding = read_utf8(path)
    root = parse_xml(path, text)
    ensure_sortable(path, text, root)
    matches = list(STRING_BLOCK.finditer(text))
    if not matches:
        return encoding["raw"]
    prefix = text[: matches[0].start()]
    suffix = text[matches[-1].end() :]
    previous_end = matches[0].start()
    units: list[tuple[str, int, str]] = []
    for position, match in enumerate(matches):
        leading = text[previous_end : match.start()]
        block = match.group(0)
        name_match = NAME_ATTR.search(block)
        if not name_match:
            raise AuditError(f"Missing name attribute in {path}: {block[:100]}")
        units.append((name_match.group(2), position, leading + block))
        previous_end = match.end()
    units.sort(key=lambda item: (base_order.get(item[0], len(base_order)), item[1]))
    updated = prefix + "".join(unit for _, _, unit in units) + suffix
    payload = updated.encode("utf-8")
    return (UTF8_BOM if encoding["has_utf8_bom"] else b"") + payload


def sort_resources(
    res_dir: pathlib.Path, base_path: pathlib.Path, write: bool
) -> tuple[list[str], list[str]]:
    base_text, _ = read_utf8(base_path)
    base_root = parse_xml(base_path, base_text)
    ensure_sortable(base_path, base_text, base_root)
    base_names = [item.attrib.get("name", "") for item in direct_strings(base_root)]
    base_order = {name: index for index, name in enumerate(base_names)}
    changed = []
    unchanged = []
    planned: list[tuple[pathlib.Path, bytes]] = []
    for path in resource_files(res_dir, base_path):
        updated = sorted_bytes(path, base_order)
        if updated == path.read_bytes():
            unchanged.append(path.parent.name)
        else:
            changed.append(path.parent.name)
            planned.append((path, updated))
    if write:
        for path, updated in planned:
            path.write_bytes(updated)
    return changed, unchanged


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit and safely order Android values*/strings.xml files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("audit", "sort"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("res_dir", type=pathlib.Path)
        subparser.add_argument(
            "--base",
            default="values/strings.xml",
            help="Default strings path, relative to res_dir unless absolute.",
        )
        if command == "audit":
            subparser.add_argument("--json", action="store_true")
            subparser.add_argument(
                "--strict",
                action="store_true",
                help="Exit 1 when structural/order/encoding/placeholder failures exist.",
            )
        else:
            subparser.add_argument(
                "--write",
                action="store_true",
                help="Apply ordering changes. Without this flag, only preview.",
            )
    return parser


def main() -> int:
    configure_stdout()
    args = build_parser().parse_args()
    res_dir = args.res_dir.resolve()
    if not res_dir.is_dir():
        print(f"error: resource directory does not exist: {res_dir}", file=sys.stderr)
        return 2
    try:
        base_path = resolve_base(res_dir, args.base)
        if args.command == "audit":
            report = audit_resources(res_dir, base_path)
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print_human_report(report)
            return 1 if args.strict and report_failures(report) else 0
        changed, unchanged = sort_resources(res_dir, base_path, args.write)
        mode = "written" if args.write else "preview"
        print(f"mode={mode} changed={len(changed)} unchanged={len(unchanged)}")
        for locale in changed:
            print(f"  {locale}")
        if not args.write and changed:
            print("Rerun with --write to apply these ordering changes.")
        return 0
    except (AuditError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
