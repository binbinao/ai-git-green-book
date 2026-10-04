#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REVIEW-v3 的 P0-5 / P0-6：删掉与位图重复的 ASCII 图，换成位图引用 + 统一图号。

用法：
    build/.venv/bin/python build/apply_v3_figures.py            # dry-run
    build/.venv/bin/python build/apply_v3_figures.py --apply    # 写入

决策依据（用户已确认）：**保留位图，删掉内容重复的 ASCII 图**。
配对关系由 build/figures/<slug>.json 的组件标签与 ASCII 图正文做关键词重合度匹配，
再逐张人工核对位图内容确定（见 build/figures/figures.yaml 的 note 字段）。

图号统一为章号体系 `图 <章>-<序>`；已存在的图号（1-1/2-1/3-1/4-1/9-1/10-1/11-1/12-1/12-2）
原样保留，只给此前没有图号的图补号。
"""
import re
import sys
from pathlib import Path

APPLY = '--apply' in sys.argv
ROOT = Path(__file__).resolve().parent.parent
M = ROOT / 'manuscript'

FENCE_RE = re.compile(r'^```[^\n]*\n(.*?)^```', re.M | re.S)

# (章节, 该章第几个围栏块) -> (slug, 完整中文图题)
# 块序号按 FENCE_RE 的匹配顺序，从 0 开始。
REPLACE = {
    ('ch00', 0): ('ch00-cargo-cult',
                  '图 0-1：Cargo-Cult Git 负循环——遇到问题就搜命令，命令失灵后更慌，'
                  '于是抄更多命令，离理解越来越远。'),
    ('ch00', 3): ('ch00-mini-map',
                  '图 0-2：本章小地图——先诊断 cargo cult，再依次摊开五张概念地图。'),
    ('ch01', 1): ('ch01-clone',
                  '图 1-1：clone 复制的是整个 `.git/`，工作区里那堆文件只是从中读出来的“当前视图”。'),
    ('ch02', 1): ('ch02-three-areas',
                  '图 2-1：三区模型。add 是“搬上入库台”，commit 是“入库”。'),
    ('ch03', 2): ('ch03-branch-chain',
                  '图 3-1：两张名牌挂在同一条项链的不同珠子上。这就是分支的全部。'),
    ('ch04', 8): ('ch04-remote-fork',
                  '图 4-1：Fork 工作流的三层结构。origin 是你自己那份、upstream 是官方那份、'
                  'local 是你笔记本上的。'),
    ('ch05', 5): ('ch05-merge-before-new',
                  '图 5-1：合并前两条分支分叉——main 与 feature 在共同祖先 A 之后并行。'),
    ('ch07', 1): ('ch07-branching-strategy',
                  '图 7-1：分支策略选择决策树——拿不准就用 GitHub Flow，再视复杂度升级或降级。'),
    ('ch08', 0): ('ch08-worktree',
                  '图 8-1：worktree 把同一个 `.git/` 铺开成多张工作台，各自站在不同分支上，'
                  '对象库与引用完全共享。'),
    ('ch09', 2): ('ch09-three-way-merge',
                  '图 9-1：三方合并的机械视角。B 是祖先，两条分支各自演化出不同的版本，'
                  'Git 把两个后代摆到一起，请你仲裁。'),
    ('ch10', 3): ('ch10-decision-tree.architecture',
                  '图 10-1：事故恢复决策树的第一问和第二问。90% 的事故都停在最左边那个绿色的框里。'),
    ('ch12', 1): ('ch12-three-gates',
                  '图 12-2：一个 secret 从“贴进代码”到“上公网”要经过三道闸。每一道都能拦。'
                  '少配一道，事故的概率就翻一倍。'),
    ('ch13', 1): ('ch13-cherry-pick',
                  '图 13-1：cherry-pick 从 feature 摘一颗珠子到 main——新珠子 Y′ 的内容与 Y 相同，'
                  '但 SHA 不同；feature 原样保留。'),
    ('ch14', 1): ('ch14-knowledge-map',
                  '图 14-1：全书总图——5 张概念地图 + 6 个场景 + 1 道防线 + 8 条小路 + 3 件产出。'),
}

# 位图注入位置需要一张配图说明；此处只做“删除 ASCII + 换成位图引用”。
CAP_RE = re.compile(r'^\*图\s*[0-9]+\s*[-–—]\s*[0-9]+\s*[：:].*\*\s*$')

files = {p.name.split('-')[0]: p for p in M.glob('ch*.md')}
assert len(files) == 15, f'expect 15 chapters, got {len(files)}'


def process(chapter, text):
    blocks = list(FENCE_RE.finditer(text))
    edits = []
    for idx, m in enumerate(blocks):
        key = (chapter, idx)
        if key not in REPLACE:
            continue
        slug, caption = REPLACE[key]
        img = f'![{caption}](figures/{slug}.png)'
        # 顺带吞掉紧随其后、原本手写的图题行（现在由图注承担）
        tail = text[m.end():]
        t = re.match(r'(\s*\n)(\*图\s*[0-9]+\s*[-–—]\s*[0-9]+\s*[：:][^\n]*\*[ \t]*)', tail)
        end = m.end() + (t.end() if t else 0)
        edits.append((m.start(), end, img, slug, len(m.group(1).split('\n'))))
    return edits


total = 0
for chapter in sorted({k[0] for k in REPLACE}):
    path = files[chapter]
    text = path.read_text(encoding='utf-8')
    edits = process(chapter, text)
    for start, end, img, slug, nlines in sorted(edits, reverse=True):
        text = text[:start] + img + text[end:]
        total += 1
        print(f'  {path.name}: {slug}  ← 删除 {nlines} 行 ASCII 图')
    if edits and APPLY:
        path.write_text(text, encoding='utf-8')

print(f'\n替换 {total} 处（应为 14）')
print('模式:', 'APPLY（已写入）' if APPLY else 'DRY-RUN（未写入）')

# 校验：位图是否都存在
missing = [s for s, _ in REPLACE.values()
           if not (ROOT / 'build' / 'figures' / f'{s}.png').exists()]
print('缺图:', missing if missing else '无 ✓')
