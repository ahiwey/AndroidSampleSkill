import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('resource_usage', Path(__file__).resolve().parents[1] / 'scripts/resource_usage.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ResourceUsageTest(unittest.TestCase):
    def test_style_alias_parent_include_and_preview_evidence(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            for folder in ('values', 'layout'):
                (root / folder).mkdir()
            (root / 'values/ui.xml').write_text(
                '<resources><color name="named_orange">@color/actual</color>'
                '<color name="actual">#61B7FF</color>'
                '<style name="Base"><item name="android:orientation">horizontal</item></style>'
                '<style name="Score" parent="Base"><item name="android:gravity">end</item></style>'
                '<color name="cycle_a">@color/cycle_b</color><color name="cycle_b">@color/cycle_a</color></resources>')
            child = root / 'layout/child.xml'
            child.write_text('<TextView xmlns:android="http://schemas.android.com/apk/res/android" android:id="@+id/included"/>')
            layout = root / 'layout/card.xml'
            layout.write_text('<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" '
                              'xmlns:tools="http://schemas.android.com/tools" style="@style/Score">\n'
                              '<!-- @color/named_orange -->\n'
                              '<TextView android:id="@+id/score" android:textColor="@color/named_orange" tools:textColor="@color/named_orange"/>\n'
                              '<include layout="@layout/child"/></LinearLayout>')
            report = MODULE.inspect(['color/named_orange', 'color/cycle_a'], [layout], [root], node_id='score')
            color = report['resources'][0]
            self.assertEqual(color['reference_count'], 1)
            self.assertEqual(color['preview_reference_count'], 1)
            self.assertEqual(color['resolution']['candidates'][0]['alias']['candidates'][0]['value'], '#61B7FF')
            parent = report['layouts'][0]['ancestors'][0]
            self.assertEqual(parent['style_candidates'][0]['attributes']['orientation'], 'horizontal')
            self.assertEqual(parent['style_candidates'][0]['attributes']['gravity'], 'end')
            self.assertEqual(report['layouts'][0]['includes'][0]['candidates'][0]['path'], str(child.resolve()))
            self.assertIn('cycle', str(report['resources'][1]['resolution']))

    def test_external_and_commented_source_references_are_not_local_bindings(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            code = Path(directory) / 'Bind.kt'
            code.write_text('// R.color.metric\n/* R.color.metric */\nval external = android.R.color.metric\nval actual = R.color.metric\n')
            self.assertEqual(MODULE.inspect(['color/metric'], [code], [])['resources'][0]['reference_count'], 1)

    def test_ambiguous_style_and_alias_variants_are_not_active_values(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            for folder in ('values', 'values-night', 'layout'):
                (root / folder).mkdir()
            (root / 'values/ui.xml').write_text('<resources><color name="actual">#123456</color>'
                '<color name="alias">@color/actual</color>'
                '<style name="Base"><item name="android:orientation">horizontal</item></style>'
                '<style name="Derived" parent="Base"><item name="android:textColor">@color/alias</item></style></resources>')
            (root / 'values-night/ui.xml').write_text('<resources><color name="actual">#ABCDEF</color>'
                '<style name="Base"><item name="android:orientation">vertical</item></style></resources>')
            layout = root / 'layout/card.xml'
            layout.write_text('<TextView style="@style/Derived"/>')
            node = MODULE.inspect([], [layout], [root])['layouts'][0]['nodes'][0]
            candidate = node['style_candidates'][0]
            self.assertTrue(candidate['unresolved'])
            self.assertNotIn('orientation', candidate['attributes'])
            alias = candidate['attribute_resources']['textColor']['candidates'][0]['alias']
            self.assertEqual(alias['candidate_count'], 2)

    def test_variants_missing_mapping_and_layout_structure(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            for folder in ('res/values', 'res/values-night', 'res/layout', 'res/drawable-xxhdpi'):
                (root / folder).mkdir(parents=True)
            (root / 'res/values/colors.xml').write_text('<resources><color name="metric">#123456</color></resources>')
            (root / 'res/values-night/colors.xml').write_text('<resources><color name="metric">#ABCDEF</color></resources>')
            (root / 'res/drawable-xxhdpi/metric.png').write_bytes(b'fixture not decoded by reference scanner')
            layout = root / 'res/layout/card.xml'
            layout.write_text('<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" android:orientation="vertical">\n'
                              '<TextView android:textColor="@color/metric" android:text="87&#10;Me"/>\n</LinearLayout>')
            code = root / 'Binding.kt'
            code.write_text('val other = R.color.metric_extra\nval actual = R.color.metric\n')
            report = MODULE.inspect(['color/metric', 'drawable/metric'], [layout, code], [root / 'res'])
            color, icon = report['resources']
            self.assertEqual(color['definition_count'], 2)
            self.assertEqual(color['reference_count'], 2)
            self.assertEqual(color['references'][1]['line'], 2)
            self.assertEqual(icon['definition_count'], 1)
            self.assertEqual(icon['status'], 'not_found_in_scope')
            nodes = report['layouts'][0]['nodes']
            self.assertEqual(nodes[0]['attributes']['orientation'], 'vertical')
            self.assertEqual(nodes[1]['attributes']['text'], '87\nMe')
            self.assertIn('does not prove an unused resource', report['limitations'])
            limited = MODULE.inspect(['color/metric'], [layout, code], [root / 'res'], limit=1)
            self.assertEqual(len(limited['resources'][0]['references']), 1)
            self.assertEqual(limited['resources'][0]['reference_count'], 2)

    def test_bad_xml_and_missing_scope_are_not_silent(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'layout').mkdir()
            broken = root / 'layout/broken.xml'
            broken.write_text('<broken>')
            self.assertEqual(len(MODULE.inspect([], [broken], [])['issues']), 1)
            with self.assertRaises(FileNotFoundError):
                MODULE.inspect([], [root / 'missing.kt'], [])

    def test_preview_namespace_and_focused_subtree(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'layout').mkdir()
            layout = root / 'layout/page.xml'
            layout.write_text('<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android" '
                              'xmlns:tools="http://schemas.android.com/tools">'
                              '<TextView android:id="@+id/other"/>'
                              '<LinearLayout android:id="@+id/score" android:orientation="horizontal">'
                              '<TextView android:text="actual" tools:text="preview"/>'
                              '</LinearLayout></LinearLayout>')
            nodes = MODULE.inspect([], [layout], [], node_id='score')['layouts'][0]['nodes']
            self.assertEqual(len(nodes), 2)
            self.assertEqual(nodes[0]['attributes']['orientation'], 'horizontal')
            self.assertEqual(nodes[1]['attributes']['text'], 'actual')
            self.assertEqual(nodes[1]['attributes']['tools:text'], 'preview')


if __name__ == '__main__':
    unittest.main()
