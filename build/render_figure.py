#!/usr/bin/env python3
"""archify 图渲染管线（端到端）：
JSON spec → render HTML → Chrome 4x 浅色主题截图 → 去点阵底纹 → 出版级 PNG
"""
import sys, subprocess, os
from pathlib import Path

ARCHIFY = '/tmp/archify/archify/bin/archify.mjs'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
DPR = 4  # 4x DPR = 印刷 300dpi

def render(json_path, out_png, theme='light'):
    json_path = Path(json_path).resolve()
    out_png = Path(out_png).resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)

    # 1) archify render HTML
    html_path = out_png.with_suffix('.html')
    subprocess.run(['node', ARCHIFY, 'render', 'architecture',
                    str(json_path), str(html_path),
                    '--quality', 'showcase'],
                   check=True, capture_output=True)
    print(f'  rendered: {html_path}')

    # 2) Chrome 截图（light theme + embed 模式）
    raw_png = out_png.with_name(out_png.stem + '-raw.png')
    # viewport：读 HTML meta 或 spec 里的 viewBox
    url = f'file://{html_path}?theme={theme}&embed=1&present=1'
    subprocess.run([CHROME, '--headless', '--no-sandbox', '--disable-gpu',
                    '--hide-scrollbars',
                    f'--force-device-scale-factor={DPR}',
                    f'--screenshot={raw_png}',
                    '--window-size=1100,620',
                    url],
                   check=True, capture_output=True)
    print(f'  screenshotted: {raw_png}')

    # 3) PIL 去点阵底纹
    from PIL import Image
    im = Image.open(raw_png).convert('RGB')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if abs(r-g) <= 2 and abs(g-b) <= 2 and 235 <= r <= 255:
                if 255 - r <= 12:
                    px[x, y] = (255, 255, 255)
    im.save(out_png)
    print(f'  cleaned: {out_png}')
    raw_png.unlink()

if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'light')
