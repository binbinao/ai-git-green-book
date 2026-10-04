#!/usr/bin/env python3
"""扫描书稿所有 ASCII 图，输出 JSON 列表（含位置、内容、行数、绘图字符数）供后续 spec 编写参考。"""
import re, json, glob

order = sorted(glob.glob('manuscript/ch*.md')) + sorted(glob.glob('manuscript/appendix-*.md'))
DRAW = set('┌┐└┘├┤┬┴┼│─═║▶◀▲▼→←↑↓╭╮╯╰━─')

figures = []
for f in order:
    t = open(f, encoding='utf-8').read()
    blocks = list(re.finditer(r'^```[\w-]*\n(.*?)^```', t, re.M | re.S))
    for idx, m in enumerate(blocks):
        body = m.group(1)
        iface = sum(1 for c in body if c in DRAW)
        if iface >= 6:
            lines = body.splitlines()
            figures.append({
                'file': f, 'block_idx': idx,
                'lines': len(lines),
                'draw_chars': iface,
                'preview': lines[0][:50] if lines else '',
                'body': body,
            })

# 按形态分四类
def classify(fig):
    body = fig['body']
    has_arrow = '→' in body or '─▶' in body or '─→' in body
    has_decision = '├' in body or '└' in body or '◀' in body or '│' in body
    has_box = '┌' in body and '┐' in body
    has_dag = any(c in body for c in '○●◯()') and has_arrow
    if has_dag and not has_decision:
        return 'DAG'
    if has_decision and has_box:
        return 'TREE'
    if has_arrow and not has_decision:
        return 'FLOW'
    if '━' in body or '━━━' in body:
        return 'MAP'
    return 'OTHER'

for fig in figures:
    fig['class'] = classify(fig)

by_class = {}
for f in figures:
    by_class.setdefault(f['class'], []).append(f)
print(f'总计: {len(figures)} 张图')
for cls, fs in by_class.items():
    print(f'  {cls}: {len(fs)} 张')
    for f in fs[:5]:
        print(f"    {f['file'].split('/')[-1]}:blk{f['block_idx']} L{f['lines']} {f['preview'][:40]}")
    if len(fs) > 5:
        print(f"    ... ({len(fs)-5} more)")

json.dump(figures, open('build/figures.json', 'w'), ensure_ascii=False, indent=1)
print('saved build/figures.json')
