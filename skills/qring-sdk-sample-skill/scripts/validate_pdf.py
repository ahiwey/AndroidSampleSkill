#!/usr/bin/env python3
"""Detect missing headings, source code, table cells and empty PDF pages."""
import argparse
import html
import json
from pathlib import Path
import re

from pypdf import PdfReader


def normalize(text):
    return re.sub(r'\s+', '', text)


def plain_inline(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    return html.unescape(text.replace('`', '').replace('**', '').replace('\\|', '|')).strip()


def validate_pdf(source, pdf):
    source = Path(source).read_text(encoding='utf-8-sig')
    reader = PdfReader(pdf)
    pages = [page.extract_text() or '' for page in reader.pages]
    text = '\n'.join(re.sub(r'QRing Android SDK\s+\d+\s*/\s*\d+', '', page) for page in pages)
    flat = normalize(text)
    blocks, body, buffer, fence = [], [], [], None
    for line in source.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                blocks.append('\n'.join(buffer))
                buffer, fence = [], None
            else:
                buffer.append(line)
        elif marker:
            fence = marker[1]
        else:
            body.append(line)
    if fence:
        raise ValueError('Source Markdown contains an unterminated code fence.')
    headings = [plain_inline(match[1]) for line in body if (match := re.match(r'^#{1,6}\s+(.+)$', line))]
    cells = []
    for line in body:
        if not line.lstrip().startswith('|') or re.fullmatch(r'[|:\-\s]+', line):
            continue
        protected = re.sub(r'(`+)(.*?)\1', lambda match: match.group().replace('|', '\x00'), line.strip())
        for cell in re.split(r'(?<!\\)\|', protected.strip('|')):
            cell = plain_inline(cell.replace('\x00', '|'))
            if cell:
                cells.append(cell)
    missing = {kind: [index + 1 for index, item in enumerate(items) if normalize(item) not in flat]
               for kind, items in [('code_blocks', blocks), ('headings', headings), ('table_cells', cells)]}
    blank_pages = [index + 1 for index, page in enumerate(pages) if len(page.strip()) < 35]
    if not pages or any(missing.values()) or blank_pages or '\ufffd' in text:
        raise ValueError(f'PDF content validation failed: missing={missing}, blank_pages={blank_pages}, replacement_glyphs={text.count(chr(0xfffd))}')
    return {'pages': len(pages), 'code_blocks': len(blocks), 'headings': len(headings), 'table_cells': len(cells), 'missing': missing}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--pdf', required=True)
    args = parser.parse_args()
    print(json.dumps(validate_pdf(args.source, args.pdf), ensure_ascii=False, indent=2))
