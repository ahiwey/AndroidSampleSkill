import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/inspect-native.py"
spec = importlib.util.spec_from_file_location("native_inspector", SCRIPT)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def elf(wide=True, alignment=16384, relro_end=16384):
    header_size, ph_size = (64, 56) if wide else (52, 32)
    data = bytearray(header_size + 2 * ph_size)
    data[:7] = b"\x7fELF" + bytes((2 if wide else 1, 1, 1))
    struct.pack_into("<H", data, 18, 183 if wide else 40)
    struct.pack_into("<Q" if wide else "<I", data, 32 if wide else 28, header_size)
    struct.pack_into("<HH", data, 54 if wide else 42, ph_size, 2)
    for i, (kind, size, align) in enumerate(((1, 0x8000, alignment), (0x6474E552, relro_end, 1))):
        fields = (kind, 6, 0, 0, 0, size, size, align) if wide else (kind, 0, 0, 0, size, size, 6, align)
        struct.pack_into("<IIQQQQQQ" if wide else "<IIIIIIII", data, header_size + i * ph_size, *fields)
    return bytes(data)


class NativeInspectionTests(unittest.TestCase):
    def test_armv7_4k_has_no_warning_or_failure_in_either_mode(self):
        for mode in ("baseline", "release"):
            row = inspector.inspect_elf(elf(False, 4096, 4096), "jni/armeabi-v7a/lib.so", mode)
            self.assertEqual(row["issues"], [])
            self.assertEqual(row["result"], "INVENTORY_ONLY")
            self.assertEqual(row["loadAlignments"], [4096])

    def test_bad_arm64_cannot_hide_behind_armv7_filename(self):
        row = inspector.inspect_elf(elf(True, 4096), "jni/armeabi-v7a/lib.so")
        self.assertEqual(row["issues"], ["LOAD_ALIGNMENT"])

    def test_relro_measurement_is_preserved_and_release_detects_risk(self):
        data = elf(relro_end=4096)
        baseline = inspector.inspect_elf(data, "lib.so")
        release = inspector.inspect_elf(data, "lib.so", "release")
        self.assertEqual(baseline["issues"], [])
        self.assertEqual(baseline["relroEndRemainders16k"], [4096])
        self.assertEqual(release["issues"], ["RELRO_ALIGNMENT"])

    def test_complete_alignment_passes(self):
        self.assertEqual(inspector.inspect_elf(elf(), "lib.so", "release")["issues"], [])

    def test_malformed_and_truncated_inputs_fail_closed(self):
        for data in (b"not ELF", elf()[:-1]):
            with self.assertRaises(ValueError):
                inspector.inspect_elf(data, "lib.so")

    def test_java_only_jar_needs_no_native_replacement(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            p = Path(folder) / "plain.jar"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("Example.class", b"example")
            row = inspector.inspect_artifact(p)
            self.assertEqual(row["nativeStatus"], "NO_DIRECT_NATIVE_ENTRIES")
            self.assertEqual(row["issues"], [])

    def test_cli_mixed_archive_fails_only_for_bad_64bit(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            p = Path(folder) / "mixed.aar"
            for align, exit_code in ((4096, 1), (16384, 0)):
                with zipfile.ZipFile(p, "w") as z:
                    z.writestr("jni/armeabi-v7a/legacy.so", elf(False, 4096, 4096))
                    z.writestr("jni/arm64-v8a/current.so", elf(True, align))
                run = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
                self.assertEqual(run.returncode, exit_code, run.stderr)
                report = json.loads(run.stdout)[0]
                self.assertEqual(len(report["issues"]), exit_code)
                self.assertFalse(any("armeabi-v7a" in x["path"] for x in report["issues"]))

    def test_bundled_candidate_matches_catalog_and_exposes_limits(self):
        catalog = json.loads((ROOT / "references/library-catalog.json").read_text(encoding="utf-8"))
        entry = catalog["entries"][0]
        p = ROOT / entry["asset"]
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), entry["sha256"])
        with zipfile.ZipFile(p) as z:
            self.assertEqual(hashlib.sha256(z.read("classes.jar")).hexdigest(), entry["classesJarSha256"])
            self.assertTrue(z.read("META-INF/duktape-rebuild/LICENSE"))
            self.assertIn(b"Copyright", z.read("META-INF/duktape-rebuild/source/duktape/duktape.c"))
        baseline = inspector.inspect_artifact(p)
        release = inspector.inspect_artifact(p, "release")
        self.assertEqual(baseline["issues"], [])
        self.assertEqual(len(baseline["libraries"]), 7)
        self.assertTrue(any(x["path"] == "jni/arm64-v8a/libduktape.so" and
                            "RELRO_ALIGNMENT" in x["issues"] for x in release["issues"]))

    def test_reproduction_recipe_requires_explicit_paths_and_case_selection(self):
        script = ROOT / "scripts/reproduce-duktape-case.py"
        run = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn("--work-dir", run.stderr)
        self.assertIn("--reproduce-case", run.stderr)


if __name__ == "__main__":
    unittest.main()
