#!/usr/bin/env python3
"""把 build/figures/ 下的所有 PNG 自动注入到 book-final.typ 对应章节位置。

策略：扫描每张 PNG 的来源章节（如 ch10-decision-tree 来自 ch10），
在 chapter-open 之后 + 第一个 ASCII 围栏之前插入 typst image 调用。
"""
import re
from pathlib import Path

# PNG 文件名 → 章节号 + 原围栏前缀
FIG_TO_CH = {
    'ch00-cargo-cult': 'ch00',
    'ch01-clone': 'ch01',
    'ch02-three-areas': 'ch02',
    'ch03-branch-chain': 'ch03',
    'ch04-remote-fork': 'ch04',
    'ch05-merge-before-new': 'ch05',
    'ch07-branching-strategy': 'ch07',
    'ch08-worktree': 'ch08',
    'ch09-three-way-merge': 'ch09',
    'ch10-decision-tree.architecture': 'ch10',
    'ch12-three-gates': 'ch12',
    'ch13-cherry-pick': 'ch13',
    'ch14-knowledge-map': 'ch14',
}

p = Path('build/book-final.typ')
body = p.read_text()

# 确保 images 目录可访问
n = 0
for fig_name, ch in FIG_TO_CH.items():
    png = f'figures/{fig_name}.png'
    block_marker = f'#chapter-open(num: "{ch.replace("ch","").lstrip("0") or "0"}"'
    # ch00 chapter-open 特殊: num: "0"
    if ch == 'ch00':
        block_marker = '#chapter-open(num: "0"'

    # 找 chapter-open 位置
    co_match = re.search(re.escape(block_marker) + r'.*?\n', body)
    if not co_match:
        print(f'  {fig_name}: no chapter-open match ({ch})')
        continue

    # 找该 chapter 内下一个 ASCII 围栏
    rest = body[co_match.end():]
    # 找下一个 chapter-open 或文件末尾
    next_chap = re.search(r'#chapter-open\(num: "', rest)
    chap_end = next_chap.start() if next_chap else len(rest)
    chapter_content = rest[:chap_end]

    # 找第一个 ASCII ``` 围栏
    fence_match = re.search(r'```\n', chapter_content)
    if not fence_match:
        print(f'  {fig_name}: no fence in {ch}')
        continue

    # 插入位置 = chapter-open 后 + 第一个围栏前
    insert_pos = co_match.end() + fence_match.start()

    # 章节号 → 显示编号
    ch_num = ch.replace('ch', '').lstrip('0') or '0'

    inject = (
        f'\n// archify 优化版图：{ch}（{fig_name}）\n'
        f'#block(width: 100%, stroke: 0.5pt + rgb("#cccccc"), inset: 6pt, radius: 4pt)[\n'
        f'  #image("{png}", width: 100%)\n'
        f']\n'
        f'#v(0.6em)\n'
        f'#align(center)[\n'
        f'  #text(size: 8.5pt, fill: rgb("#666"))[*图 {ch}-{ch_num}-{fig_name.split("-",1)[1]}（archify 优化版，与原 ASCII 图内容相同）*]\n'
        f']\n'
        f'#v(1em)\n'
    )

    body = body[:insert_pos] + inject + body[insert_pos:]
    print(f'  ✓ {fig_name} injected at {ch}')
    n += 1

p.write_text(body)
print(f'\n{n} figures injected into book-final.typ')
