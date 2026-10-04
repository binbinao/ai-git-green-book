#!/usr/bin/env python3
"""重组书稿：拼 19 个文件 + 剥离每章重复的脚手架（章头双行引 + 章首 ---）。

输出 build/book.md，供 pandoc 转 typst。
剥离规则（依据 manuscript/STYLE-NOTES.md 与 AGENTS.md 记录的固定模板）：
- 章标题 h1 保留
- 其后紧跟的「> 《Git 的概念地图》第 N 章 · …」双行块引（章位引言）剥离
- 块引后紧跟的 --- 分隔线剥离
- 每章末尾的「下一章预告」保留（出版级处理：转成章末装饰性隔断在 typst 后处理做）
"""
import re, glob, sys

order = sorted(glob.glob('manuscript/ch*.md')) + sorted(glob.glob('manuscript/appendix-*.md'))
assert len(order) == 19, f'expect 19 files, got {len(order)}'

EPGRAPH = re.compile(
    r'(^# .+$\n)\n'                       # h1
    r'((?:> [^\n]*\n)+)\n'                # 章位引言（任意 > 行，含附录头引）
    r'(?:---\n\n?)?'                      # 其后 ---
, re.M)

parts = []
for f in order:
    t = open(f, encoding='utf-8').read()
    m = EPGRAPH.match(t)
    stripped = 0
    if m:
        t = m.group(1) + t[m.end():]      # 保留 h1，剥掉章位引言与其后 ---
        stripped = 1
    parts.append(t.rstrip() + '\n\n')
    print(f'{f}: epigraph stripped={stripped}')

out = ''.join(parts)
open('build/book.md', 'w', encoding='utf-8').write(out)
print(f'--> build/book.md {len(out)} chars, {out.count(chr(10))} lines')
