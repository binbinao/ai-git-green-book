#!/usr/bin/env python3
"""P1-7 续：把代码块（verbatim raw）内部的 emoji 换成等宽汉字标记。

为什么不能交给 book.typ 的 show rule：
    `#show "🟢": ...` 这类文本 show rule 只作用于正文与表格的 text 元素，
    代码块内部是逐字直排的 verbatim 内容，show rule 够不到。而 ASCII 箱线图
    的边框是靠列宽对齐的，替换字符必须与原 emoji 推进宽度完全一致。
实测（Sarasa Fixed SC, 8.5pt, lang zh）：
    AppleColorEmoji 的 emoji 推进宽度 = 8.5pt = 1em
    一个汉字 = 8.5pt = 1em        → 宽度完全一致 ✓
    `AI` = 2 个半角 = 8.5pt = 1em → 宽度完全一致 ✓
    （而 ● ★ ≡ 等"东亚歧义宽度"字符在该字体里只有 0.5em，会破坏边框对齐）
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (文件, 原字符, 替换字符, 代码块内期望命中次数)
EDITS = [
    ('ch06-commit-craft.md', '🟢', '绿', 2),   # release note 提示词块 + 红黄绿说明块
    ('ch06-commit-craft.md', '🟡', '黄', 1),
    ('ch06-commit-craft.md', '🔴', '红', 1),
    ('ch10-recovery.md', '📋', '单', 1),       # 事故第一小时便利贴
    ('ch10-recovery.md', '🚨', '警', 1),
    ('ch10-recovery.md', '🤖', 'AI', 1),
    ('ch12-security.md', '🟢', '绿', 1),       # AI 权限三档（红黄绿）
    ('ch12-security.md', '🟡', '黄', 1),
    ('ch12-security.md', '🔴', '红', 1),
    ('ch14-copilot.md', '🟢', '绿', 1),        # 一道防线 · 红黄绿边界
    ('ch14-copilot.md', '🟡', '黄', 1),
    ('ch14-copilot.md', '🔴', '红', 1),
]


def fence_spans(text):
    return [(m.start(), m.end()) for m in re.finditer(r'^```.*?^```', text, re.M | re.S)]


changed = {}
for fname, old, new, expect in EDITS:
    path = ROOT / 'manuscript' / fname
    text = path.read_text(encoding='utf-8')
    spans = fence_spans(text)
    hits = [m.start() for m in re.finditer(re.escape(old), text)
            if any(a <= m.start() < b for a, b in spans)]
    if len(hits) != expect:
        print(f'  ✗ {fname} {old!r}: 期望 {expect} 处，实得 {len(hits)} —— 跳过')
        continue
    for pos in reversed(hits):
        text = text[:pos] + new + text[pos + len(old):]
    path.write_text(text, encoding='utf-8')
    changed.setdefault(fname, []).append(f'{old}->{new} x{len(hits)}')

for fname, items in changed.items():
    print(f'  ok {fname}: ' + ', '.join(items))
print(f'共修改 {len(changed)} 个文件')
