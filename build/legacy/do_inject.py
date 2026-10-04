#!/usr/bin/env python3
"""直接修改 build/book-final.typ：在 ch10 决策树 ASCII 围栏前注入 archify 优化图。"""
from pathlib import Path
import re
p = Path('build/book-final.typ')
body = p.read_text()

# 锚点：``` + 第一问 在同一行 fence
# 实际：第一问的 \`\`\` 在上方 13 行（围栏起点）
pat = re.compile(r'```\n([\s\S]*?│  第一问[\s\S]*?```)', re.S)
m = pat.search(body)
if not m:
    print('未匹配到 ch10 决策树围栏起点')
    raise SystemExit(1)

start = m.start()
inject = '''#block(width: 100%, stroke: 0.5pt + rgb("#cccccc"), inset: 6pt, radius: 4pt)[
  #image("figures/ch10-decision-tree.architecture.png", width: 100%)
]
#v(0.6em)
#align(center)[
  #text(size: 8.5pt, fill: rgb("#666"))[*图 10-X：事故恢复决策树（archify 优化版）· 90% 事故停在最左路径*]
]
#v(1em)
'''
out = body[:start] + inject + body[start:]
p.write_text(out)
print(f'INJECTED at {start}')
