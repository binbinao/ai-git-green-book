#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REVIEW-v5 落地 · 第二组：需要按显示宽度/作用域计算的修订。

三件事：
  1. 附录 C 术语表 13 处「书签」回归 → 分支语境改「名牌」，tag 语境改「标记」
  2. ch14 §14.3「全书总图」ASCII 框图右墙歪墙 → 按显示宽度重算填充
     （实证：成品 PDF p446–448 右墙最远偏 12.75pt ≈ 3 个字符宽）
  3. 散文层 18 处半角括号 → 全角括号（全书散文层全角 2060 处 : 半角 18 处）

安全设计同 revision_v5.py：先校验、后写入；半角括号与 ASCII 重排都做成
「幂等」的——重跑一次结果不变（用于验证）。
"""
import io
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / 'manuscript'


def disp(s):
    """显示宽度：东亚 W/F 记 2 列，其余 1 列。

    已用成品 PDF 反解验证：Sarasa 等宽字体下一列 = 4.25pt，
    该函数对 `·`（U+00B7，东亚宽度 A）记 1 列，与 Sarasa 实排一致。
    """
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)


# ---------------------------------------------------------------- 1. 附录 C 书签
def fix_glossary_shuqian():
    p = MS / 'appendix-c-glossary.md'
    s = io.open(p, encoding='utf-8').read()
    n = s.count('书签')
    if n == 0:
        print('SKIP 附录 C：无「书签」残留（本轮已应用或从未存在）')
        return
    if n != 13:
        raise SystemExit('中止：附录 C「书签」预期 13 处，实测 %d 处' % n)
    s = s.replace('书签', '名牌')
    # 唯一一处指的是 tag（附注标签/轻量标签），不能叫名牌
    old = '发布用**附注标签**，临时名牌用**轻量标签**'
    if s.count(old) != 1:
        raise SystemExit('中止：附录 C tag 语境修正未唯一命中')
    s = s.replace(old, '发布用**附注标签**，临时标记用**轻量标签**')
    if '书签' in s:
        raise SystemExit('中止：附录 C 仍有「书签」残留')
    io.open(p, 'w', encoding='utf-8').write(s)
    print('OK 附录 C：书签 → 名牌 12 处 + 标记 1 处（共 13）')


# ---------------------------------------------------------------- 2. ch14 ASCII
def fix_ascii_box():
    p = MS / 'ch14-copilot.md'
    lines = io.open(p, encoding='utf-8').read().split('\n')

    # 内层小框「档案馆」比它的上下边框宽 1 列，先修内容（已修过则跳过）
    inner_old = '  │                        │  档案馆  │                        │'
    inner_new = '  │                        │ 档案馆  │                        │'
    inner_done = 0
    if lines.count(inner_old) == 1:
        lines = [inner_new if l == inner_old else l for l in lines]
        inner_done = 1
    elif lines.count(inner_new) != 1:
        raise SystemExit('中止：ch14 内层「档案馆」行定位失败')

    # 两行是「内容本身超宽」，尾部空格不够抽，需先削字（语义不变）
    trims = [
        # 超 3 列：` · ` → `，`（省 1）+ ` = ` → `=`（省 2）
        ('  │   珠子不可变，项链可塑 · 重写 = 造新珠 + 挪名牌 + 旧珠进反射 │',
         '  │   珠子不可变，项链可塑，重写=造新珠 + 挪名牌 + 旧珠进反射 │'),
        # 超 2 列：图例标签「你亲手确认」→「亲手确认」，与同框其它标签同样简洁
        ('  │   黄 force push · reset --hard · 重写共享历史（你亲手确认） │',
         '  │   黄 force push · reset --hard · 重写共享历史（亲手确认） │'),
    ]
    trimmed = 0
    for old, new in trims:
        if lines.count(old) == 1:
            lines = [new if l == old else l for l in lines]
            trimmed += 1
        elif lines.count(new) != 1:
            raise SystemExit('中止：ch14 削字目标定位失败 —— %r' % old[:28])

    # 定位围栏块，并由顶边框推得框宽 W
    in_fence, start, end = False, None, None
    for i, l in enumerate(lines):
        if l.lstrip().startswith('```'):
            if not in_fence:
                in_fence, start = True, i
            else:
                in_fence, end = False, i
                break
    if start is None or end is None:
        raise SystemExit('中止：ch14 未找到全书总图的围栏块')
    # 该文件里 §14.3 的那块是含「全书总图」的那一段
    blk = lines[start:end]
    if not any('全书总图' in l for l in blk):
        raise SystemExit('中止：定位到的围栏块不是「全书总图」')

    borders = [l for l in blk if l.startswith('  ┌') and l.rstrip().endswith('┐')]
    if not borders:
        raise SystemExit('中止：未找到顶边框行')
    W = disp(borders[0])
    fixed = 0
    for i in range(start, end):
        l = lines[i]
        if not (l.startswith('  │') and l.rstrip().endswith('│')):
            continue
        core, w = l.rstrip(), disp(l.rstrip())
        if w == W:
            continue
        idx = core.rfind('│')
        head, tail = core[:idx], core[idx:]
        if w > W:                       # 多了空格：从 │ 前抽掉
            head2 = head.rstrip()
            slack = len(head) - len(head2)
            need = w - W
            if need > slack:
                raise SystemExit('中止：%d 行要抽 %d 列，但 │ 前只有 %d 个空格'
                                 % (i + 1, need, slack))
            core = head2 + ' ' * (slack - need) + tail
        else:                           # 少了空格：在 │ 前补上
            core = head + ' ' * (W - w) + tail
        if disp(core) != W:
            raise SystemExit('中止：%d 行重排后宽度仍为 %d（应 %d）'
                             % (i + 1, disp(core), W))
        lines[i] = core
        fixed += 1

    io.open(p, 'w', encoding='utf-8').write('\n'.join(lines))
    residual = [i + 1 for i in range(start, end)
                if lines[i].startswith('  │') and lines[i].rstrip().endswith('│')
                and disp(lines[i].rstrip()) != W]
    if residual:
        raise SystemExit('中止：ch14 重排后仍有非 %d 列的行 %s' % (W, residual[:5]))
    print('OK ch14 全书总图：框宽 %d 列，重排 %d 行（内层修 %d / 削字 %d）'
          % (W, fixed, inner_done, trimmed))


# ---------------------------------------------------------------- 3. 半角括号
PAREN = re.compile(r'([\u4e00-\u9fff]|[）])(\s*)\(([a-dA-D1-9])\)')
HALF = re.compile(r'[\u4e00-\u9fff]\s*\([a-dA-D1-9]\)')


def rewrite_prose_line(ln):
    """只改行内代码之外的片段；返回 (新行, 改动数)。"""
    parts = re.split(r'(`[^`]*`)', ln)
    n = 0
    for i in range(0, len(parts), 2):          # 偶数下标 = 非代码片段
        seg, prev = parts[i], None
        while prev != seg:                     # (a)(b)(c) 连排要迭代
            prev = seg
            seg, k = PAREN.subn(r'\1\2（\3）', seg)
            n += k
        parts[i] = seg
    return ''.join(parts), n


def prose_only(txt):
    """剥掉代码围栏后的散文层——围栏内半角标点本来就合规，不该算残留。"""
    out, inf = [], False
    for ln in txt.split('\n'):
        if ln.lstrip().startswith('```'):
            inf = not inf
            continue
        if not inf:
            out.append(ln)
    return '\n'.join(out)


def fix_halfwidth_parens():
    total, files = 0, []
    for p in sorted(MS.glob('*.md')):
        if p.name.startswith('REVIEW') or p.name == 'STYLE-NOTES.md':
            continue
        src = io.open(p, encoding='utf-8').read()
        out, in_fence, n = [], False, 0
        for ln in src.split('\n'):
            if ln.lstrip().startswith('```'):
                in_fence = not in_fence
                out.append(ln)
                continue
            if in_fence:
                out.append(ln)
                continue
            new, k = rewrite_prose_line(ln)
            n += k
            out.append(new)
        txt = '\n'.join(out)
        if txt == src:
            continue
        left = len(HALF.findall(prose_only(txt)))
        if left:
            raise SystemExit('中止：%s 散文层改写后仍残留 %d 处半角括号'
                             % (p.name, left))
        io.open(p, 'w', encoding='utf-8').write(txt)
        files.append((p.name, n))
        total += n
    print('OK 半角括号 → 全角：%d 个文件 / 共 %d 处（ASCII 图内保持半角）'
          % (len(files), total))
    for f, k in files:
        print('   - %-30s %d 处' % (f, k))


if __name__ == '__main__':
    fix_glossary_shuqian()
    fix_ascii_box()
    fix_halfwidth_parens()
