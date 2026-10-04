#!/usr/bin/env python3
"""字体嵌入体检（P1-7 / P1-9）：列出 PDF 里每个字体及其 FontFile 嵌入状态。

用法：build/.venv/bin/python build/qa_fonts.py [pdf路径]
"""
import re
import sys
from pathlib import Path

import pymupdf

pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'output' / 'git-concept-map-full.pdf'


def fontfiles(doc, xref, depth=0, acc=None):
    acc = acc if acc is not None else []
    if depth > 4:
        return acc
    for key in ('DescendantFonts', 'FontDescriptor'):
        val = doc.xref_get_key(xref, key)
        if val and val[0] != 'null':
            for m in re.finditer(r'(\d+) 0 R', str(val[1])):
                fontfiles(doc, int(m.group(1)), depth + 1, acc)
    for key in ('FontFile', 'FontFile2', 'FontFile3'):
        val = doc.xref_get_key(xref, key)
        if val and val[0] != 'null':
            acc.append(key)
    return acc


doc = pymupdf.open(pdf)
seen = {}
for pno in range(doc.page_count):
    for row in doc[pno].get_fonts(full=True):
        xref, subtype, base = row[0], row[2], row[3]
        if base not in seen:
            seen[base] = (subtype, fontfiles(doc, xref))

bad = []
for base, (subtype, embedded) in sorted(seen.items()):
    tag = '嵌入 ' + ','.join(sorted(set(embedded))) if embedded else '★★ 未嵌入 ★★'
    if not embedded:
        bad.append(base)
    print(f'  {base[:42]:42} {str(subtype):8} {tag}')
print(f'\n字体数 {len(seen)}，未嵌入 {len(bad)}：{bad if bad else "无"}')
