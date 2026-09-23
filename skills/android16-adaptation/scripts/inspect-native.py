"""Read-only AAR/JAR/APK/AAB/SO inventory. Exit 0: scoped static pass; 1: issue; 2: input error.

The default baseline checks 64-bit LOAD alignment. ARMv7/other 32-bit alignment
is inventory only. Release mode adds RELRO checks. Neither mode proves runtime,
APK ZIP alignment, AAB configuration, API compatibility, or Play approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile


def inspect_elf(data, name, mode="baseline"):
    if len(data) < 52 or data[:4] != b"\x7fELF" or data[4] not in (1, 2) or data[5] not in (1, 2):
        raise ValueError(f"Invalid ELF: {name}")
    wide = data[4] == 2
    endian = "<" if data[5] == 1 else ">"
    machine = struct.unpack_from(endian + "H", data, 18)[0]
    offset = struct.unpack_from(endian + ("Q" if wide else "I"), data, 32 if wide else 28)[0]
    size, count = struct.unpack_from(endian + "HH", data, 54 if wide else 42)
    if count == 0 or count == 65535 or size < (56 if wide else 32) or offset + size * count > len(data):
        raise ValueError(f"Missing, unsupported, or truncated ELF program headers: {name}")
    loads, relro = [], []
    for i in range(count):
        fields = struct.unpack_from(endian + ("IIQQQQQQ" if wide else "IIIIIIII"), data, offset + size * i)
        if wide:
            kind, flags, file_offset, address, physical, file_size, memory_size, alignment = fields
        else:
            kind, file_offset, address, physical, file_size, memory_size, flags, alignment = fields
        if kind == 1:
            loads.append(alignment)
        elif kind == 0x6474E552:
            relro.append((address + memory_size) % 16384)
    if not loads:
        raise ValueError(f"No LOAD segments: {name}")
    scoped = wide and machine in (183, 62)  # Android arm64-v8a and x86_64.
    issues = []
    if scoped and any(a < 16384 or a & (a - 1) for a in loads):
        issues.append("LOAD_ALIGNMENT")
    if scoped and mode == "release" and any(relro):
        issues.append("RELRO_ALIGNMENT")
    return {
        "path": name, "sha256": hashlib.sha256(data).hexdigest(),
        "bits": 64 if wide else 32, "machine": machine,
        "loadAlignments": loads, "relroEndRemainders16k": relro,
        "scope": "16K_64BIT" if scoped else "PRESERVE_LEGACY_ABI",
        "result": "FAIL" if issues else ("PASS_SCOPED_STATIC" if scoped else "INVENTORY_ONLY"),
        "issues": issues,
    }


def inspect_artifact(path, mode="baseline"):
    path = Path(path)
    data = path.read_bytes()
    rows, class_jars = [], {}
    if path.suffix.lower() == ".so":
        rows.append(inspect_elf(data, path.name, mode))
    else:
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                if name.endswith(".so"):
                    rows.append(inspect_elf(archive.read(name), name, mode))
                elif name == "classes.jar" or (name.startswith("libs/") and name.endswith(".jar")):
                    class_jars[name] = hashlib.sha256(archive.read(name)).hexdigest()
    return {"artifact": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
            "mode": mode, "libraries": rows, "classJarSha256": class_jars,
            "issues": [{"path": row["path"], "issues": row["issues"]} for row in rows if row["issues"]],
            "coverage": "Direct archive .so entries only; inspect embedded archives/resolved dependencies separately.",
            "nativeStatus": "INSPECTED" if rows else "NO_DIRECT_NATIVE_ENTRIES"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="+", type=Path)
    parser.add_argument("--mode", choices=("baseline", "release"), default="baseline")
    args = parser.parse_args()
    try:
        reports = [inspect_artifact(path, args.mode) for path in args.artifacts]
    except (OSError, ValueError, struct.error, zipfile.BadZipFile, RuntimeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(reports, indent=2, ensure_ascii=False))
    return int(any(report["issues"] for report in reports))


if __name__ == "__main__":
    raise SystemExit(main())
