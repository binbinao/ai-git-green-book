#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archify 图渲染管线 v2（修正「16:9 截断」）。

v1（render_figure.py）用固定 `--window-size=1100,620` 截图，高于 620 CSS px 的图
会被**直接截掉下半部分**（14 张全部中招，缺的正是图底部的内容）。
v2 改成：
    1) 用一个足够高的视口（默认 1100×2600）截图 → 内容完整
    2) PIL 自动裁掉四周白边（保留 6px padding）→ 图幅贴合内容
    3) 去点阵底纹

用法：
    build/.venv/bin/python build/render_figure2.py <out_dir> [slug ...]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 优先用当初出图的那份 archify（skill 版校验更严，这批 spec 过不了）
ARCHIFY = (Path('/tmp/archify/archify/bin/archify.mjs')
           if Path('/tmp/archify/archify/bin/archify.mjs').exists()
           else Path.home() / '.workbuddy/skills/archify/bin/archify.mjs')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
NODE = Path.home() / '.workbuddy/binaries/node/versions/22.22.2-6/bin/node'
DPR = 3
WIN_W = 1100
WIN_H = 2600
PAD = 6


def render(json_path, out_png):
    json_path = Path(json_path).resolve()
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        html = Path(td) / (json_path.stem + '.html')
        subprocess.run([str(NODE), str(ARCHIFY), 'render', 'architecture',
                        str(json_path), str(html), '--quality', 'showcase'],
                       check=True, capture_output=True)
        raw = out_png.with_name(out_png.stem + '-raw.png')
        url = f'file://{html}?theme=light&embed=1&present=1'
        subprocess.run([CHROME, '--headless', '--no-sandbox', '--disable-gpu',
                        '--hide-scrollbars',
                        f'--force-device-scale-factor={DPR}',
                        f'--screenshot={raw}',
                        f'--window-size={WIN_W},{WIN_H}', url],
                       check=True, capture_output=True)

    from PIL import Image, ImageChops
    import numpy as np
    im = Image.open(raw).convert('RGB')
    # 去底纹：archify 画布底色是 244–247 的浅灰渐变（不是纯白），还带极淡点阵。
    # 判定「背景」= 近中性色（max-min 很小）且足够亮；置为纯白。
    # 注意阈值要留出余量，别把图例里的浅灰方块（≈229,231,235）一起抹掉。
    a = np.asarray(im).copy()
    mx = a.max(axis=2).astype(np.int16)
    mn = a.min(axis=2).astype(np.int16)
    mask = (mx - mn <= 14) & (mn >= 238)
    a[mask] = 255
    im = Image.fromarray(a)
    # 自动裁白边
    bbox = ImageChops.difference(im, Image.new('RGB', im.size, (255, 255, 255))).getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        x0, y0 = max(0, x0 - PAD), max(0, y0 - PAD)
        x1, y1 = min(im.size[0], x1 + PAD), min(im.size[1], y1 + PAD)
        im = im.crop((x0, y0, x1, y1))
    im.save(out_png, optimize=True)
    raw.unlink()
    return im.size


if __name__ == '__main__':
    out_dir = Path(sys.argv[1])
    slugs = sys.argv[2:] or [p.stem for p in sorted((ROOT / 'build/figures').glob('*.json'))]
    for slug in slugs:
        spec = ROOT / 'build/figures' / f'{slug}.json'
        if not spec.exists():
            print(f'  跳过（无 spec）: {slug}')
            continue
        size = render(spec, out_dir / f'{slug}.png')
        print(f'  {slug:40s} {size[0]:5d} x {size[1]:5d}  ratio {size[0]/size[1]:.2f}')
