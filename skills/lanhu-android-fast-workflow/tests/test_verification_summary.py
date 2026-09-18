import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("summary", Path(__file__).parents[1] / "scripts/verification_summary.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerificationSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_nested_suites_do_not_double_count_and_duplicate_paths(self):
        p = self.file("report.xml", '<testsuites tests="2"><testsuite><testcase name="a"/><testcase name="b"/></testsuite></testsuites>')
        result = MODULE.summarize([p, p])
        self.assertEqual(result["totals"]["tests"], 2)
        self.assertEqual(result["report_result"], "passed")
        self.assertEqual(result["runtime"], "not_established")
        self.assertEqual(result["source_freshness"], "unverified")

    def test_failures_errors_and_skips(self):
        p = self.file("report.xml", '<testsuite><testcase><failure message="bad"/></testcase><testcase><error>broken</error></testcase><testcase><skipped/></testcase></testsuite>')
        result = MODULE.summarize([p])
        self.assertEqual(result["totals"], dict(tests=3, failures=1, errors=1, skipped=1))
        self.assertEqual(result["report_result"], "failed")
        self.assertEqual(len(result["reports"][0]["first_failures"]), 2)

    def test_missing_interrupted_report_is_not_pass(self):
        self.assertEqual(MODULE.summarize([self.root / "missing.xml"])["report_result"], "incomplete")
        self.assertEqual(MODULE.summarize()["report_result"], "incomplete")

    def test_empty_summary_only_or_malformed_is_not_pass(self):
        for content in ('<testsuite tests="8" failures="0"/>', '<testsuite tests="8"><testcase/></testsuite>', '<testsuite>', '<other><testcase/></other>'):
            with self.subTest(content=content):
                self.assertEqual(MODULE.summarize([self.file("report.xml", content)])["report_result"], "incomplete")

    def test_snapshot_hashes_and_read_only(self):
        p = self.file("image.png", "fixture")
        before = {x.name: x.read_bytes() for x in self.root.iterdir()}
        first = MODULE.summarize(snapshots=[p])
        self.assertEqual(first["snapshots"][0]["change"], "unknown")
        self.assertEqual(MODULE.summarize(snapshots=[p], previous=first)["snapshots"][0]["change"], "unchanged")
        self.assertEqual(before, {x.name: x.read_bytes() for x in self.root.iterdir()})
        p.write_text("changed", encoding="utf-8")
        result = MODULE.summarize(snapshots=[p], previous=first)
        self.assertEqual(result["snapshots"][0]["change"], "changed")
        self.assertEqual(result["visual_review"], "not_established")

    def test_skips_and_bounded_failure_details(self):
        p = self.file("report.xml", '<testsuite><testcase><skipped/></testcase></testsuite>')
        self.assertEqual(MODULE.summarize([p])["report_result"], "passed_with_skips")
        p = self.file("report.xml", '<testsuite>' + ('<testcase><failure>' + 'x' * 500 + '</failure></testcase>') * 10 + '</testsuite>')
        result = MODULE.summarize([p])
        self.assertEqual(result["totals"]["failures"], 10)
        self.assertEqual(len(result["reports"][0]["first_failures"]), 3)
        self.assertEqual(len(result["reports"][0]["first_failures"][0]["message"]), 400)
