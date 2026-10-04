#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 archify 渲染出的 HTML 里抠出「连线标签矩形」与「节点矩形」，逐对判重叠。

做法：HTML 内嵌 SVG，两类 rect 用 rx 区分——
    节点矩形   rx="6"  （renderComponent）
    标签面膜   rx="3" height="14"（renderConnectionLabel，紧跟着 font-size="8" 的 text）
两者都是 class="c-mask"。把 `<g data-detail="context" ...>…<rect rx="3"…/><text font-size="8">…`
配对读出即可。这是在**不依赖校验器**的前提下拿到的图内真实几何。

用法：
    build/.venv/bin/python build/check_labels.py /tmp/figs-new
"""
import re
import sys
from pathlib import Path

RECT = re.compile(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="(\d+)"')
EDGE_LABEL = re.compile(
    r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="14" rx="3"[^>]*/>\s*'
    r'<text x="[-\d.]+" y="[-\d.]+" class="[^"]*" font-size="8"[^>]*>([^<]*)</text>')


def rects(html, rx):
    out = []
    for m in RECT.finditer(html):
        x, y, w, h, r = m.groups()
        if int(r) != rx:
            continue
        out.append((float(x), float(y), float(w), float(h)))
    return out


def overlap(a, b, tol=2.0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ox = min(ax + aw, bx + bw) - max(ax, bx)
    oy = min(ay + ah, by + bh) - max(ay, by)
    return ox > tol and oy > tol, max(0.0, ox), max(0.0, oy)


def check(path):
    html = Path(path).read_text(encoding='utf-8')
    nodes = rects(html, 6)
    labels = [(float(m.group(1)), float(m.group(2)), float(m.group(3)), 14.0, m.group(4))
              for m in EDGE_LABEL.finditer(html)]
    vb = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', html)
    problems = []
    for lx, ly, lw, lh, text in labels:
        for nx, ny, nw, nh in nodes:
            hit, ox, oy = overlap((lx, ly, lw, lh), (nx, ny, nw, nh))
            if hit:
                problems.append(
                    f'标签「{text}」压住节点 [{nx:.0f},{ny:.0f},{nw:.0f},{nh:.0f}] '
                    f'重叠 {ox:.0f}×{oy:.0f}px（标签 [{lx:.0f},{ly:.0f},{lw:.0f},{lh:.0f}]）')
        if vb:
            vx, vy, vw, vh = (float(g) for g in vb.groups())
            if lx < vx - 0.5 or ly < vy - 0.5 or lx + lw > vw + 0.5 or ly + lh > vh + 0.5:
                problems.append(f'标签「{text}」越出画布 viewBox {vw:.0f}x{vh:.0f}'
                                f'（标签 [{lx:.0f},{ly:.0f},{lw:.0f},{lh:.0f}]）')
    return len(nodes), len(labels), problems


if __name__ == '__main__':
    d = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/figs-new')
    total = 0
    for f in sorted(d.glob('*.html')):
        if f.name.endswith('.loose.html'):
            continue
        n, m, probs = check(f)
        tag = 'ok  ' if not probs else 'BAD '
        print(f'{tag}{f.stem:36s} 节点 {n:2d}  连线标签 {m:2d}')
        for p in probs:
            print(f'        {p}')
            total += 1
    print(f'\n合计 {total} 处标签缺陷')
