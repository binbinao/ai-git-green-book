#!/usr/bin/env python3
"""编译后收尾：配帖补页（P1-15）+ 把页数/体积/日期写回 build/README.md（P1-14）。

用法：python3 build/finalize.py
须在 build/build.sh 的第 4 步（typst compile）之后运行。
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / 'output' / 'git-concept-map-full.pdf'
BUILD_README = ROOT / 'build' / 'README.md'
TPL = ROOT / 'build' / 'book.typ'

if not PDF.exists():
    sys.exit(f'找不到 {PDF}，请先运行 build/build.sh 的第 4 步。')

doc = pymupdf.open(PDF)
before = doc.page_count

# ---- P1-15：配帖页数须为 4 的倍数（胶订） ----
# 172×248mm 属常规 16 开装订体系，印厂配帖要求总页数是 4 的倍数。
# 不足时在全文末尾（附录 D 之后）补空白页，不设页码、不加书眉。
pad = (-before) % 4
if pad:
    rect = doc[0].rect
    for _ in range(pad):
        doc.new_page(pno=-1, width=rect.width, height=rect.height)
    # PyMuPDF 不允许就地全量重写，先落临时文件再替换
    tmp = PDF.with_suffix('.pdf.tmp')
    doc.save(tmp, deflate=True, garbage=3)
    doc.close()
    tmp.replace(PDF)
    doc = pymupdf.open(PDF)
after = doc.page_count

# ---- 元数据校验（P1-10） ----
md = doc.metadata or {}
doc.close()

size_mb = PDF.stat().st_size / 1024 / 1024

# ---- P1-14：把实测页数/体积/日期写回 build/README.md ----
tpl_head = TPL.read_text(encoding='utf-8')
m = re.search(r'#let meta = \((.*?)\n\)', tpl_head, re.S)
def meta_val(key, default=''):
    if not m:
        return default
    mm = re.search(key + r':\s*"([^"]*)"', m.group(1))
    return mm.group(1) if mm else default

edition = meta_val('edition', '')
date = meta_val('date', '') or datetime.now().strftime('%Y-%m-%d')

line = f'- {edition} · **{after} 页** · {size_mb:.1f} MB · 书稿 {date}（本行由 build/finalize.py 自动写回）'

text = BUILD_README.read_text(encoding='utf-8')
new_text, n = re.subn(r'(?m)^- .*页.*由 build/finalize\.py 自动写回.*$', line, text)
if n == 0:
    # 首次：在「## 版本」小节下插入
    new_text, n = re.subn(r'(## 版本\n\n)', r'\1' + line + '\n', text)
if n:
    BUILD_README.write_text(new_text, encoding='utf-8')

print(f'  配帖补页：{before} -> {after} 页（补 {pad} 页空白）')
print(f'  体积：{size_mb:.1f} MB')
print(f'  元数据：title={md.get("title")!r} author={md.get("author")!r}')
print(f'  build/README.md 版本行已更新：{line}')
if after % 4 != 0:
    sys.exit(f'警告：总页数 {after} 仍不是 4 的倍数')
