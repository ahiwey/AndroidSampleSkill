"""Inventory local Lanhu exports without network access or Android resource writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import tempfile
import unittest
import zipfile
import zlib

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}
MAX_FILE = 50 * 1024 * 1024
MAX_TOTAL = 500 * 1024 * 1024


def png_metadata(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    offset, width, height, alpha, ended = 8, None, None, False, False
    while offset + 12 <= len(data):
        size = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        if offset + size + 12 > len(data):
            raise ValueError('truncated_png')
        checksum = struct.unpack('>I', data[offset + 8 + size:offset + 12 + size])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != checksum:
            raise ValueError('png_crc_mismatch')
        if offset == 8 and (kind != b'IHDR' or size != 13):
            raise ValueError('invalid_png_header')
        if kind == b'IHDR':
            width, height = struct.unpack('>II', payload[:8])
            alpha = payload[9] in (4, 6)
        elif kind == b'tRNS':
            alpha = True
        elif kind == b'IEND':
            ended = True
            break
        offset += size + 12
    if not ended or not width or not height:
        raise ValueError('incomplete_png')
    return {'width': width, 'height': height, 'has_alpha_channel': alpha,
            'inspection': 'png_chunks_checked_not_pixel_decode'}


def safe_member(info):
    name = info.filename.replace('\\', '/')
    p = PurePosixPath(name)
    return (not p.is_absolute() and '..' not in p.parts and ':' not in name
            and not stat.S_ISLNK(info.external_attr >> 16))


def raster_metadata(data, suffix):
    if suffix == '.png':
        result = png_metadata(data)
        if result is None:
            raise ValueError('invalid_png_signature')
        return result
    width = height = 0
    alpha = False
    if suffix in ('.jpg', '.jpeg'):
        if data[:2] != b'\xff\xd8':
            raise ValueError('invalid_jpeg_signature')
        offset = 2
        while offset < len(data):
            if data[offset] != 255:
                raise ValueError('invalid_jpeg_marker')
            while offset < len(data) and data[offset] == 255:
                offset += 1
            if offset >= len(data):
                break
            marker = data[offset]; offset += 1
            if marker in (0xDA, 0xD9):
                break
            if marker == 0x01 or 0xD0 <= marker <= 0xD7:
                continue
            if offset + 2 > len(data):
                raise ValueError('truncated_jpeg')
            size = int.from_bytes(data[offset:offset + 2], 'big')
            if size < 2 or offset + size > len(data):
                raise ValueError('truncated_jpeg_segment')
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                if size < 8:
                    raise ValueError('invalid_jpeg_frame')
                height, width = struct.unpack('>HH', data[offset + 3:offset + 7])
                break
            offset += size
    elif suffix == '.webp':
        if data[:4] != b'RIFF' or data[8:12] != b'WEBP':
            raise ValueError('invalid_webp_signature')
        end = int.from_bytes(data[4:8], 'little') + 8
        if end != len(data):
            raise ValueError('invalid_webp_length')
        offset = 12
        while offset + 8 <= end:
            kind = data[offset:offset + 4]
            size = int.from_bytes(data[offset + 4:offset + 8], 'little')
            payload = data[offset + 8:offset + 8 + size]
            if offset + 8 + size + size % 2 > end:
                raise ValueError('truncated_webp_chunk')
            if kind == b'VP8X':
                if size != 10:
                    raise ValueError('invalid_webp_extended_header')
                width = int.from_bytes(payload[4:7], 'little') + 1
                height = int.from_bytes(payload[7:10], 'little') + 1
                alpha = bool(payload[0] & 0x10)
                break
            if kind == b'VP8L':
                if size < 5 or payload[0] != 0x2f:
                    raise ValueError('invalid_webp_lossless_header')
                bits = int.from_bytes(payload[1:5], 'little')
                width, height = (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
                alpha = bool(bits & (1 << 28))
                break
            if kind == b'VP8 ':
                if size < 10 or payload[3:6] != b'\x9d\x01\x2a':
                    raise ValueError('invalid_webp_lossy_header')
                width, height = (v & 0x3fff for v in struct.unpack('<HH', payload[6:10]))
                break
            offset += 8 + size + size % 2
    else:
        return None
    if not width or not height:
        raise ValueError('missing_raster_dimensions')
    return {'width': width, 'height': height, 'has_alpha_channel': alpha,
            'inspection': 'header_only_not_pixel_decode_or_exif_rotation'}


def prepare(source, designs, output, density=None):
    output = Path(output).resolve()
    inputs = [(Path(source).resolve(), 'slices')]
    if designs:
        inputs.append((Path(designs).resolve(), 'designs'))
    for src, _ in inputs:
        if src == output or (src.is_dir() and output.is_relative_to(src)):
            raise ValueError('output_must_not_be_inside_input')
    output.mkdir(parents=True, exist_ok=True)
    rows, issues, seen, total = [], [], set(), 0

    def consume(name, data, category):
        digest = hashlib.sha256(data).hexdigest()
        suffix = PurePosixPath(name).suffix.lower()
        meta = raster_metadata(data, suffix)
        target = output / category / (digest + suffix)
        target.parent.mkdir(exist_ok=True)
        reused = target.exists()
        if reused and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('existing_output_hash_conflict')
        if not reused:
            target.write_bytes(data)
        path_density = re.search(r'(?i)(?:^|[/_\-])(xxxhdpi|xxhdpi|xhdpi|hdpi|mdpi)(?:[/_\-.]|$)', name)
        detected = path_density.group(1).lower() if path_density else density
        row = {'source': name, 'category': category, 'sha256': digest,
               'output': str(target), 'bytes': len(data), 'reused': reused,
               'duplicate': (category, digest) in seen,
               'density': detected if category == 'slices' else None,
               'density_evidence': ('path' if path_density else 'caller_declaration') if detected else 'unknown',
               'status': 'prepared' if meta else 'dimensions_unverified'}
        row.update(meta or {})
        rows.append(row)
        seen.add((category, digest))
        if meta is None:
            issues.append({'source': name, 'reason': 'unsupported_dimension_inspection'})
        if category == 'slices' and detected != 'xxhdpi':
            issues.append({'source': name, 'reason': 'density_not_verified_xxhdpi'})

    for src, category in inputs:
        if src.is_file() and src.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(src) as archive:
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        name = info.filename.replace('\\', '/')
                        if not safe_member(info):
                            issues.append({'source': name, 'reason': 'unsafe_archive_member'})
                            continue
                        if PurePosixPath(name).suffix.lower() not in IMAGE_EXTENSIONS:
                            continue
                        total += info.file_size
                        if info.file_size > MAX_FILE or total > MAX_TOTAL:
                            issues.append({'source': name, 'reason': 'size_limit'})
                            continue
                        try:
                            consume(name, archive.read(info), category)
                        except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as error:
                            issues.append({'source': name, 'reason': type(error).__name__, 'detail': str(error)[:120]})
            except (OSError, zipfile.BadZipFile) as error:
                issues.append({'source': src.name, 'reason': type(error).__name__})
        elif src.is_dir():
            for directory, dirs, names in os.walk(src, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
                for name in sorted(names):
                    file = Path(directory) / name
                    if file.is_symlink() or file.suffix.lower() not in IMAGE_EXTENSIONS:
                        continue
                    rel = file.relative_to(src).as_posix()
                    try:
                        size = file.stat().st_size
                        total += size
                        if size > MAX_FILE or total > MAX_TOTAL:
                            issues.append({'source': rel, 'reason': 'size_limit'})
                            continue
                        consume(rel, file.read_bytes(), category)
                    except (ValueError, OSError) as error:
                        issues.append({'source': rel, 'reason': type(error).__name__, 'detail': str(error)[:120]})
        else:
            issues.append({'source': src.name, 'reason': 'missing_input_or_not_zip_directory'})
    report = {'schema_version': 1, 'scope': 'Local export inventory; no network, resizing, res import, or completeness claim.',
              'summary': {'files': len(rows), 'unique_contents': len(seen),
                          'reused': sum(r['reused'] for r in rows),
                          'duplicates': sum(r['duplicate'] for r in rows), 'issues': len(issues)},
              'files': rows, 'issues': issues}
    (output / 'local-assets.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def fixture_png():
    def chunk(kind, content):
        return struct.pack('>I', len(content)) + kind + content + struct.pack('>I', zlib.crc32(kind + content) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\x00\xff\x00\x00\xff')) + chunk(b'IEND', b''))


def self_test(work_dir):
    class Checks(unittest.TestCase):
        def test_jpeg_webp_headers(self):
            for marker in (0xC0, 0xC2):
                jpeg = b'\xff\xd8\xff' + bytes([marker]) + struct.pack('>HBHHB', 8, 8, 19, 31, 1)
                self.assertEqual(raster_metadata(jpeg, '.jpg')['width'], 31)
                self.assertEqual(raster_metadata(jpeg, '.jpg')['height'], 19)
                with self.assertRaises(ValueError):
                    raster_metadata(jpeg[:-1], '.jpg')
            def webp(kind, content):
                chunk = kind + struct.pack('<I', len(content)) + content + b'\0' * (len(content) % 2)
                return b'RIFF' + struct.pack('<I', len(chunk) + 4) + b'WEBP' + chunk
            extended = bytes([0x10, 0, 0, 0]) + (30).to_bytes(3, 'little') + (18).to_bytes(3, 'little')
            lossless = b'\x2f' + (30 | (18 << 14) | (1 << 28)).to_bytes(4, 'little')
            lossy = b'\x00\x00\x00\x9d\x01\x2a' + struct.pack('<HH', 31, 19)
            for kind, payload, alpha in [(b'VP8X', extended, True), (b'VP8L', lossless, True), (b'VP8 ', lossy, False)]:
                data = webp(kind, payload)
                meta = raster_metadata(data, '.webp')
                self.assertEqual((meta['width'], meta['height'], meta['has_alpha_channel']), (31, 19, alpha))
                with self.assertRaises(ValueError):
                    raster_metadata(data[:-1], '.webp')
            with self.assertRaises(ValueError):
                raster_metadata(fixture_png(), '.jpg')

        def test_exports(self):
            with tempfile.TemporaryDirectory(prefix='local-assets-test-', dir=work_dir) as folder:
                root = Path(folder)
                archive = root / 'slices.zip'
                with zipfile.ZipFile(archive, 'w') as z:
                    z.writestr('drawable-xxhdpi/icon.png', fixture_png())
                    z.writestr('drawable-xxhdpi/copy.png', fixture_png())
                    z.writestr('../escape.png', fixture_png())
                    z.writestr('broken.png', b'broken')
                    z.writestr('unknown.svg', '<svg/>')
                first = prepare(archive, None, root / 'out')
                self.assertEqual(first['summary']['files'], 3)
                self.assertEqual(first['summary']['duplicates'], 1)
                self.assertFalse((root / 'escape.png').exists())
                self.assertTrue(any(x['reason'] == 'unsafe_archive_member' for x in first['issues']))
                self.assertTrue(any(x.get('detail') == 'invalid_png_signature' for x in first['issues']))
                self.assertTrue(any(x['reason'] == 'density_not_verified_xxhdpi' for x in first['issues']))
                second = prepare(archive, None, root / 'out')
                self.assertEqual(second['summary']['reused'], 3)
                target = Path(second['files'][0]['output'])
                target.write_bytes(b'conflict')
                conflict = prepare(archive, None, root / 'out')
                self.assertTrue(any(x.get('detail') == 'existing_output_hash_conflict' for x in conflict['issues']))
                self.assertEqual(target.read_bytes(), b'conflict')
        def test_paths_and_crc(self):
            with tempfile.TemporaryDirectory(prefix='local-assets-test-', dir=work_dir) as folder:
                root = Path(folder)
                with self.assertRaises(ValueError):
                    prepare(root, None, root / 'output')
                bad = bytearray(fixture_png()); bad[20] ^= 1
                with self.assertRaises(ValueError):
                    png_metadata(bad)
                src = root / 'input'; src.mkdir(); (src / 'icon.png').write_bytes(fixture_png())
                report = prepare(src, None, root / 'out', 'xxhdpi')
                self.assertEqual(report['summary']['issues'], 0)
                self.assertTrue(report['files'][0]['has_alpha_channel'])
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input')
    parser.add_argument('--designs')
    parser.add_argument('--output')
    parser.add_argument('--density', choices=['xxhdpi'])
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--work-dir')
    args = parser.parse_args()
    if args.self_test:
        if not args.work_dir or not Path(args.work_dir).is_dir():
            parser.error('--self-test requires an existing --work-dir')
        self_test(args.work_dir)
        print(json.dumps({'status': 'ok', 'test': 'local_assets'}))
    else:
        if not args.input or not args.output:
            parser.error('--input and --output are required')
        report = prepare(args.input, args.designs, args.output, args.density)
        print(json.dumps(report['summary']))
