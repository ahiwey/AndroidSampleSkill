#!/usr/bin/env python3
"""Read-only Git baseline capture/comparison; only the requested JSON output is written."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    result = subprocess.run(
        ["git", "-c", "safe.directory=" + repo.as_posix(), "-C", str(repo), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    return result.stdout


def file_hash(path):
    if path.is_symlink():
        return {"kind": "symlink", "sha256": digest(str(path.readlink()).encode("utf-8"))}
    if path.is_file():
        return {"kind": "file", "sha256": digest(path.read_bytes())}
    return {"kind": "directory" if path.is_dir() else "missing", "sha256": None}


def capture(repo):
    repo = repo.resolve()
    top = Path(git(repo, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve()
    if top != repo:
        raise ValueError("Use the repository root, not a subdirectory")
    entries = iter(git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").decode("utf-8").split("\0"))
    files = {}
    for entry in entries:
        if not entry:
            continue
        status, name = entry[:2], entry[3:]
        item = {"status": status, **file_hash(repo / name)}
        if "R" in status or "C" in status:
            item["original_path"] = next(entries)
        files[name] = item
    return {
        "version": 1, "repo": str(repo),
        "head": git(repo, "rev-parse", "HEAD").decode("ascii").strip(),
        "branch": git(repo, "rev-parse", "--abbrev-ref", "HEAD").decode("utf-8").strip(),
        "index_sha256": digest(git(repo, "ls-files", "--stage", "-z")),
        "files": files,
    }


def compare(before, after, allowed_new=()):
    if before.get("version") != 1 or before["repo"] != after["repo"]:
        raise ValueError("Baseline schema or repository mismatch")
    changed = sorted(p for p, record in before["files"].items() if after["files"].get(p) != record)
    new = sorted(set(after["files"]) - set(before["files"]))
    unexpected = sorted(set(new) - set(allowed_new))
    metadata = [key for key in ("head", "branch", "index_sha256") if before[key] != after[key]]
    return {
        "ok": not (changed or unexpected or metadata),
        "changed_existing": changed, "new_changes": new,
        "unexpected_new_changes": unexpected, "changed_metadata": metadata,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    snap = commands.add_parser("capture")
    snap.add_argument("--repo", type=Path, required=True)
    snap.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check")
    check.add_argument("--repo", type=Path, required=True)
    check.add_argument("--baseline", type=Path, required=True)
    check.add_argument("--allow-new", action="append", default=[])
    args = parser.parse_args()
    current = capture(args.repo)
    if args.command == "capture":
        # Refuse overwriting evidence of the original workspace.
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(current, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps({"captured": len(current["files"]), "output": str(args.output)}))
        return 0
    before = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
    result = compare(before, current, [p.replace("\\", "/") for p in args.allow_new])
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as error:
        print(error.stderr.decode("utf-8", errors="replace").strip(), file=sys.stderr)
        sys.exit(2)
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
