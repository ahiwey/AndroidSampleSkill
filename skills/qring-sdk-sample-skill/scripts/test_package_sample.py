#!/usr/bin/env python3
"""Focused behavioral tests; synthetic files stay under an explicit work directory."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import package_sample as pack

TEST_ROOT = None


def aar(path):
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('AndroidManifest.xml', '<manifest/>')
        archive.writestr('classes.jar', b'fixture')


class PackagingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='case-', dir=TEST_ROOT)
        self.root = Path(self.temp.name)
        self.project = self.root / '示例 Sample'
        self.project.mkdir()
        for name in pack.ITEMS:
            if name in ('app', 'gradle'):
                (self.project / name).mkdir()
            else:
                (self.project / name).write_text(f'fixture {name}', encoding='utf-8')
        (self.project / 'app/libs').mkdir()
        (self.project / 'app/build.gradle').write_text("dependencies { implementation(name: 'qring_sdk_1.0.0.9', ext: 'aar') }", encoding='utf-8')
        (self.project / 'gradle/wrapper').mkdir()
        (self.project / 'gradle/wrapper/gradle-wrapper.properties').write_text('fixture', encoding='utf-8')
        aar(self.project / 'app/libs/qring_sdk_1.0.0.9.aar')
        (self.project / 'docs').mkdir()
        for name in pack.DOCS:
            (self.project / 'docs' / name).write_text('# 中英文文档\nKeep source unchanged.\n', encoding='utf-8')
        self.env = patch.dict(os.environ, {'QRING_SAMPLE_CONFIG': str(self.root / 'preferences/config.json')})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def args(self, *extra):
        return pack.parser().parse_args(['pack', '--project', str(self.project), *extra])

    def test_current_version_wins_even_if_newer_exists(self):
        aar(self.project / 'app/libs/qring_sdk_1.0.0.10.aar')
        self.assertEqual(pack.select_aar(self.project)['version'], '1.0.0.9')

    def test_fallback_compares_numbers_not_time_or_text(self):
        build = self.project / 'app/build.gradle'
        build.write_text("implementation(name: 'qring_sdk_1.0.0.8', ext: 'aar')", encoding='utf-8')
        aar(self.project / 'app/libs/qring_sdk_1.0.0.10.aar')
        os.utime(self.project / 'app/libs/qring_sdk_1.0.0.9.aar', (2000000000, 2000000000))
        selected = pack.select_aar(self.project)
        self.assertEqual(selected['version'], '1.0.0.10')
        self.assertIn('not rewritten', selected['warning'])
        self.assertIn('1.0.0.8', build.read_text())

    def test_comments_and_app_version_are_not_sdk_references(self):
        with (self.project / 'app/build.gradle').open('a', encoding='utf-8') as stream:
            stream.write('\n// qring_sdk_9.9.9.9\n/* implementation("qring_sdk_8.8.8.8") */\nversionName "5.0.0"\n')
        self.assertEqual(pack.select_aar(self.project)['version'], '1.0.0.9')

    def test_multiple_dependencies_stop(self):
        with (self.project / 'app/build.gradle').open('a') as stream:
            stream.write('\nimplementation("qring_sdk_8.8.8.8")')
        with self.assertRaisesRegex(ValueError, 'Multiple'):
            pack.select_aar(self.project)

    def test_missing_and_corrupt_aar_stop(self):
        file = self.project / 'app/libs/qring_sdk_1.0.0.9.aar'
        file.write_bytes(b'not an aar')
        with self.assertRaises(zipfile.BadZipFile):
            pack.select_aar(self.project)
        file.unlink()
        with self.assertRaisesRegex(ValueError, 'No qring'):
            pack.select_aar(self.project)

    def test_zip_has_exact_eight_roots_and_preserves_local_file(self):
        (self.project / '.git').mkdir()
        (self.project / '.git/private').write_text('must not export')
        target = self.root / 'sample.zip'
        pack.create_sample_zip(self.project, target)
        with zipfile.ZipFile(target) as archive:
            self.assertEqual({name.split('/')[1] for name in archive.namelist()}, set(pack.ITEMS))
            self.assertEqual(archive.read(f'{self.project.name}/local.properties'), (self.project / 'local.properties').read_bytes())
            self.assertFalse(any('/docs/' in name or '/.git/' in name for name in archive.namelist()))

    def test_config_survives_new_process_without_packaging(self):
        target = self.root / '蓝牙 SDK'
        result = subprocess.run([sys.executable, str(pack.SCRIPTS / 'package_sample.py'), 'config', '--output-root', str(target)], capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)['output_root'], str(target))
        self.assertFalse(target.exists())
        result = subprocess.run([sys.executable, str(pack.SCRIPTS / 'package_sample.py'), 'plan', '--project', str(self.project)], capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)['output_root'], str(target))
        pack.configure(pack.parser().parse_args(['config', '--reset']))
        self.assertEqual(pack.make_plan(self.args())['output_root'], str(self.project))

    def test_output_inside_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inside'):
            pack.make_plan(self.args('--output-root', str(self.project / 'app/packages')))

    def test_plan_does_not_write_outputs(self):
        before = set(self.root.rglob('*'))
        pack.make_plan(self.args())
        self.assertEqual(before, set(self.root.rglob('*')))

    def test_publish_keeps_previous_package(self):
        staging = self.root / 'staging'
        staging.mkdir()
        folder = staging / 'QRing_Android_SDK_1.0.0.9'
        folder.mkdir()
        (folder / 'new').write_text('new')
        outer = staging / (folder.name + '.zip')
        outer.write_bytes(b'new zip')
        output = self.root / 'output'
        output.mkdir()
        (output / folder.name).mkdir()
        (output / folder.name / 'old').write_text('old')
        (output / outer.name).write_bytes(b'old zip')
        history = Path(pack.publish(folder, outer, output))
        self.assertEqual((history / folder.name / 'old').read_text(), 'old')
        self.assertEqual((history / outer.name).read_bytes(), b'old zip')
        self.assertEqual((output / folder.name / 'new').read_text(), 'new')

    def test_clean_failure_does_not_publish(self):
        with patch.object(pack, 'renderer_args', return_value=['node']), patch.object(pack, 'run', return_value='probe'), patch.object(pack, 'clean_project', side_effect=RuntimeError('clean failed')), patch('sys.stdout', io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'clean failed'):
                pack.package(self.args())
        self.assertFalse(list(self.project.glob('QRing_Android_SDK*')))

    def test_pdf_failure_preserves_markdown_and_cleans_staging(self):
        before = {name: (self.project / 'docs' / name).read_bytes() for name in pack.DOCS}
        with patch.object(pack, 'renderer_args', return_value=['node']), patch.object(pack, 'run', side_effect=['probe', RuntimeError('PDF failed')]), patch.object(pack, 'clean_project'), patch('sys.stdout', io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'PDF failed'):
                pack.package(self.args())
        self.assertFalse(list(self.project.glob('.qring-staging-*')))
        self.assertFalse(list(self.project.glob('QRing_Android_SDK*')))
        self.assertEqual(before, {name: (self.project / 'docs' / name).read_bytes() for name in pack.DOCS})


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('--work-dir', required=True)
    args = cli.parse_args()
    TEST_ROOT = Path(args.work_dir).resolve()
    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    unittest.main(argv=[sys.argv[0]], verbosity=2)
