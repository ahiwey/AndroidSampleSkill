"""Reproduce the recorded Duktape 1.2.0 baseline; not a universal 16 KB release fix.

ARM64 is retained and its RELRO/runtime remain unverified. Legacy ABI rebuilds here
reproduce the historical case, not the default ARMv7 support requirement.

Requires SDK packages cmake;3.22.1, ndk;29.0.13599879 and ndk;16.1.4479499.
The legacy NDK preserves ARMv5 and non-NEON ARMv7 support. Sources/licenses and
provenance are embedded in the resulting AAR. No ELF alignment is binary-patched.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import zipfile

COMMIT = "93d6b86cae63f0dd020bdea1f24f07119cbdec25"
ORIGINAL_SHA256 = "0391c309957be03b27a7805bba6f978f07258ec49093c8ddee2e4215e9cf8ec2"
REBUILD = {"armeabi": "16.1.4479499", "armeabi-v7a": "16.1.4479499",
           "x86": "29.0.13599879", "x86_64": "29.0.13599879"}
HEADER = "duktape/src/main/jni/duktape/duk_custom.h"
DECLARATIONS = '''#ifdef __cplusplus
extern "C" {
#endif
duk_int_t android__get_local_tzoffset(duk_double_t time);
duk_bool_t android__date_parse_string(duk_context* ctx, const char* str);
#ifdef __cplusplus
}
#endif

'''


def run(command, log):
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run([str(x) for x in command], stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed; see {log}\n" +
                           log.read_text(encoding="utf-8", errors="replace")[-5000:])


def load_alignments(data):
    if data[:4] != b"\x7fELF":
        raise ValueError("Expected ELF")
    endian = "<" if data[5] == 1 else ">"
    wide = data[4] == 2
    offset = struct.unpack_from(endian + ("Q" if wide else "I"), data, 32 if wide else 28)[0]
    size, count = struct.unpack_from(endian + "HH", data, 54 if wide else 42)
    return [struct.unpack_from(endian + ("Q" if wide else "I"), data,
                               offset + i * size + (48 if wide else 28))[0]
            for i in range(count)
            if struct.unpack_from(endian + "I", data, offset + i * size)[0] == 1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", required=True, type=Path)
    parser.add_argument("--original-aar", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reproduce-case", required=True, action="store_true")
    args = parser.parse_args()
    if hashlib.sha256(args.original_aar.read_bytes()).hexdigest() != ORIGINAL_SHA256:
        raise ValueError("Original AAR is not the verified Maven 1.2.0 artifact")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    source = args.work_dir / "duktape-source"
    if not source.exists():
        run(["git", "clone", "--depth", "1", "--branch", "duktape-android-1.2.0",
             "https://github.com/cashapp/duktape-android.git", source],
            args.work_dir / "duktape-source-fetch.log")
    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(source), *arguments], text=True).strip()
    if git("rev-parse", "HEAD") != COMMIT:
        raise ValueError("Unexpected upstream commit")
    changes = git("diff", "--name-only").splitlines()
    if any(path != HEADER for path in changes) or git("ls-files", "--others", "--exclude-standard"):
        raise ValueError("Source checkout contains unexpected changes")
    original_header = git("show", f"HEAD:{HEADER}") + "\n"
    patched_header = DECLARATIONS + original_header
    if (source / HEADER).read_text().strip() not in (original_header.strip(), patched_header.strip()):
        raise ValueError("Unexpected custom header contents")
    (source / HEADER).write_text(patched_header, encoding="utf-8")

    suffix = ".exe" if os.name == "nt" else ""
    cmake_dir = args.sdk_root / "cmake/3.22.1/bin"
    cmake, ninja = cmake_dir / ("cmake" + suffix), cmake_dir / ("ninja" + suffix)
    host = "windows-x86_64" if os.name == "nt" else "linux-x86_64"
    strip = args.sdk_root / f"ndk/29.0.13599879/toolchains/llvm/prebuilt/{host}/bin/llvm-strip{suffix}"
    outputs = {}
    for abi, ndk in REBUILD.items():
        build = args.work_dir / "duktape-rebuild" / abi
        command = [cmake, "-S", source / "duktape/src/main/jni", "-B", build, "-G", "Ninja",
                   f"-DCMAKE_MAKE_PROGRAM={ninja}",
                   f"-DCMAKE_TOOLCHAIN_FILE={args.sdk_root / 'ndk' / ndk / 'build/cmake/android.toolchain.cmake'}",
                   f"-DANDROID_ABI={abi}", "-DANDROID_PLATFORM=android-26", "-DANDROID_STL=c++_static",
                   "-DANDROID_TOOLCHAIN=clang", "-DCMAKE_BUILD_TYPE=Release",
                   "-DCMAKE_C_FLAGS=-std=c99 -fstrict-aliasing -DDUK_OPT_HAVE_CUSTOM_H -fvisibility=hidden",
                   "-DCMAKE_CXX_FLAGS=-std=c++11 -fstrict-aliasing -fexceptions -fvisibility=hidden",
                   "-DCMAKE_C_FLAGS_RELEASE=-Os -DNDEBUG -fomit-frame-pointer",
                   "-DCMAKE_CXX_FLAGS_RELEASE=-Os -DNDEBUG -fomit-frame-pointer",
                   "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384,-z,common-page-size=16384"]
        if abi.startswith("armeabi"):
            command.append("-DANDROID_ARM_NEON=FALSE")
        run(command, args.work_dir / f"duktape-configure-{abi}.log")
        run([cmake, "--build", build, "--parallel", "1"], args.work_dir / f"duktape-build-{abi}.log")
        library = build / "libduktape.so"
        run([strip, "--strip-debug", library], args.work_dir / f"duktape-strip-{abi}.log")
        outputs[f"jni/{abi}/libduktape.so"] = library.read_bytes()
        print(f"Rebuilt {abi}: {len(outputs[f'jni/{abi}/libduktape.so'])} bytes", flush=True)

    metadata = {"upstream": "https://github.com/cashapp/duktape-android", "commit": COMMIT,
                "originalAarSha256": ORIGINAL_SHA256, "nativeApi": 26, "ndkByRebuiltAbi": REBUILD,
                "patch": "Declare the two existing Android date hooks for modern C99 compilers.",
                "linkerFlags": "-Wl,-z,max-page-size=16384,-z,common-page-size=16384",
                "unchanged": "Java classes and all original ABI directories are retained.", "libraries": []}
    with zipfile.ZipFile(args.original_aar) as original:
        entries = {entry.filename: original.read(entry) for entry in original.infolist()}
        for name in (name for name in entries if name.endswith(".so")):
            data = outputs.get(name, entries[name])
            alignments = load_alignments(data)
            if not alignments or min(alignments) < 16384:
                raise ValueError(f"{name} still fails 16 KB LOAD alignment: {alignments}")
            metadata["libraries"].append({"path": name, "loadAlignments": alignments,
                "sha256": hashlib.sha256(data).hexdigest(), "rebuilt": name in outputs})
        entries.update(outputs)
        entries["AndroidManifest.xml"] = entries["AndroidManifest.xml"].replace(
            b'android:minSdkVersion="12"', b'android:minSdkVersion="26"')
        entries["META-INF/duktape-rebuild/provenance.json"] = json.dumps(metadata, indent=2).encode()
        entries["META-INF/duktape-rebuild/LICENSE"] = (source / "LICENSE").read_bytes()
        native = source / "duktape/src/main/jni"
        for file in native.rglob("*"):
            if file.is_file():
                entries["META-INF/duktape-rebuild/source/" + file.relative_to(native).as_posix()] = file.read_bytes()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for name, data in sorted(entries.items()):
                info = zipfile.ZipInfo(name)
                info.compress_type = zipfile.ZIP_DEFLATED
                output.writestr(info, data)
    print(f"Wrote {args.output}: all {len(metadata['libraries'])} original ABIs pass static ELF checks")


if __name__ == "__main__":
    main()
