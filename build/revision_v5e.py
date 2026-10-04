#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第五批修订：修 ch14「全书总图」3 行丢列（成品级可见缺陷）。

背景（实证，非推测）：
  Typst + Sarasa Fixed SC 下，全角右括号「）」紧接中点「·」时，该行会少渲染
  1 列。ch14 §14.3 全书总图里有 3 行是「（第 N 章）· 正文」结构，因此在成品
  PDF 里右墙比其余行内缩一格（pp.446–447 肉眼可见）。
  隔离样本已复现：`）·` → 该行窄 1 列；`）——`、行尾`）` 均正常。

修法：
  把章号引用移到行尾，变成「… · 正文（第 N 章）」——
  既消除 `）·` 邻接，又保持整行显示宽度严格 63 列，
  且与全书既有的「地图 1 · 仓库（第 1 章）」体例一致。

脚本在写入前会断言：每行替换后显示宽度仍等于原宽度。

用法：
    python build/revision_v5e.py --check
    python build/revision_v5e.py
"""
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MS = ROOT / 'manuscript'


def dw(c):
    o = ord(c)
    return 2 if (0x1100 <= o <= 0x115f or 0x2e80 <= o <= 0xa4cf
                 or 0xac00 <= o <= 0xd7a3 or 0xf900 <= o <= 0xfaff
                 or 0xfe30 <= o <= 0xfe6f or 0xff00 <= o <= 0xff60
                 or 0xffe0 <= o <= 0xffe6) else 1


def disp(s):
    return sum(dw(c) for c in s)


# (文件, 标签, 旧整行, 新内容)
# 新行的填充由脚本按「整行必须 63 列」重算，避免手工数字符出错。
EDITS = [
    ('ch14-copilot.md', '六个场景：章号移到行尾，消除 ）· 邻接',
     '  │             六个场景（第 6–11 章）· 判断在你脑里          │',
     '六个场景 · 判断在你脑里（第 6–11 章）'),

    ('ch14-copilot.md', '一道防线：章号移到行尾，消除 ）· 邻接',
     '  │              一道防线（第 12 章）· 红黄绿边界             │',
     '一道防线 · 红黄绿边界（第 12 章）'),

    ('ch14-copilot.md', '八条小路：章号移到行尾，消除 ）· 邻接',
     '  │             八条小路 · 十个工具（第 13 章）· 都不是新原理 │',
     '八条小路 · 十个工具 · 都不是新原理（第 13 章）'),
]

LINE_W = 63


def rebuild(old_line, new_content):
    """保留原行前导空格数，重算尾随空格，使整行严格 LINE_W 列。"""
    lead = len(old_line[3:]) - len(old_line[3:].lstrip(' '))
    inner = LINE_W - 4                       # 2 前导空格 + 2 个 │
    tail = inner - lead - disp(new_content)
    if tail < 0:
        raise SystemExit('宽度校验失败：新内容过宽，缺 %d 列' % -tail)
    return '  │' + ' ' * lead + new_content + ' ' * tail + '│'


def main():
    check_only = '--check' in sys.argv
    plans = []
    for f, lab, old, new_content in EDITS:
        new = rebuild(old, new_content)
        if disp(old) != LINE_W:
            raise SystemExit('宽度校验失败：%s —— 旧串 %d 列，应为 %d'
                             % (lab, disp(old), LINE_W))
        if disp(new) != LINE_W:
            raise SystemExit('宽度校验失败：%s —— 新串 %d 列，应为 %d'
                             % (lab, disp(new), LINE_W))
        if '）·' in new or '）·' in old.replace(new_content, ''):
            pass
        if '）·' in new:
            raise SystemExit('宽度校验失败：%s —— 新串仍含「）·」邻接' % lab)
        plans.append((f, lab, old, new))

    contents, pending, done, bad = {}, [], [], []
    for f, lab, old, new in plans:
        p = MS / f
        if f not in contents:
            contents[f] = io.open(p, encoding='utf-8').read()
        s = contents[f]
        if s.count(old) == 1:
            pending.append((f, lab, old, new))
        elif s.count(old) == 0 and s.count(new) >= 1:
            done.append((f, lab))
        else:
            bad.append((f, lab, s.count(old)))

    if bad:
        for f, lab, c in bad:
            print('中止：%s / %s —— 旧串命中 %d 次（应为 1）' % (f, lab, c))
        raise SystemExit('校验失败，未写入任何文件')

    for f, lab in done:
        print('SKIP %-22s 已应用  %s' % (f, lab))
    if not pending:
        print('无待写入条目（全部已应用）')
        return
    if check_only:
        print('校验通过：%d 条待写入（新旧均 %d 列，无「）·」，未写入）'
              % (len(pending), LINE_W))
        return

    for f, lab, old, new in pending:
        contents[f] = contents[f].replace(old, new, 1)
        print('OK   %-22s disp %d→%d  %s' % (f, disp(old), disp(new), lab))
        print('     %s' % new)
    for f in sorted(contents):
        io.open(MS / f, 'w', encoding='utf-8').write(contents[f])
    print('DONE %d edits across %d files' % (len(pending), len(set(f for f, _, _, _ in pending))))


if __name__ == '__main__':
    main()
