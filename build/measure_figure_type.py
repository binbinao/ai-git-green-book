#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测量图内文字的实际落版字号（px → pt）。

原理
------------------------------------------------
图 PNG 由 SVG 铺满 1100 CSS px 视口、DPR=3 截得（3300 设备 px），再裁白边。
落到书上时又缩放版心宽 120mm = 340.16pt。所以**不管原画布多宽**：

    1 PNG px = 340.16 / 3300 pt = 0.10308 pt

即「同一个字在 PNG 里多高」直接决定它在纸上的字号 —— 这正是 REVIEW-v4 口径。

做法：按行统计深色墨迹像素，取连续有墨的行段作为「文字行」，
段高（含笔画，≈ 字高）换算成 pt；节点边框只有 ~13px、节点框 ~640px，
用 20–160px 窗口滤掉，剩下的就是文字行。

用法：
    build/.venv/bin/python build/measure_figure_type.py <png目录> [...]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PT_PER_PX = 340.16 / 3300.0
MIN_H, MAX_H = 20, 160           # 文字行高窗口（PNG px）


def measure(png):
    im = Image.open(png).convert('L')
    a = np.asarray(im)
    ink = a < 150                              # 深色文字（浅填充/底纹不会进来）
    rows = ink.sum(axis=1)
    heights = []
    y, n = 0, len(rows)
    while y < n:
        if rows[y] > 0:
            y0 = y
            while y < n and rows[y] > 0:
                y += 1
            h = y - y0
            if MIN_H <= h <= MAX_H:
                heights.append(h)
        else:
            y += 1
    if not heights:
        return 0, 0, []
    heights.sort()
    med = heights[len(heights) // 2] * PT_PER_PX
    top = heights[int(len(heights) * 0.9)] * PT_PER_PX
    return med, top, heights


if __name__ == '__main__':
    for d in sys.argv[1:]:
        d = Path(d)
        print(f'=== {d} ===')
        print(f"{'图':34s}{'行数':>5s}{'中位 pt':>9s}{'P90 pt':>9s}{'最大 pt':>9s}")
        for f in sorted(d.glob('*.png')):
            med, top, hs = measure(f)
            if not hs:
                print(f'{f.stem:34s}  （未测到文字行）')
                continue
            mx = hs[-1] * PT_PER_PX
            print(f'{f.stem:34s}{len(hs):5d}{med:9.2f}{top:9.2f}{mx:9.2f}')
