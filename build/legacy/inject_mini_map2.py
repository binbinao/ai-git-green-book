#!/usr/bin/env python3
from pathlib import Path
p = Path('build/book-final.typ')
body = p.read_text()
inject_text = '''// archify 优化版图：ch00 小地图
#block(width: 100%, stroke: 0.5pt + rgb("#cccccc"), inset: 6pt, radius: 4pt)[
  #image("figures/ch00-mini-map.png", width: 100%)
]
#v(0.6em)
#align(center)[
  #text(size: 8.5pt, fill: rgb("#666"))[*图 0 mini-map（archify 优化版，本章导航）*]
]
#v(1em)

'''
marker = '// archify 优化版图：ch00（ch00-cargo-cult）'
if marker in body and 'ch00-mini-map.png' not in body:
    body = body.replace(marker, inject_text + marker)
    p.write_text(body)
    print('injected')
else:
    print('skipped')