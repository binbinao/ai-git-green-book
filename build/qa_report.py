#!/usr/bin/env python3
"""REVIEW-v3 修订复验：逐条核对 19 项问题是否真的修掉了（可重复运行）。

当前共 23 条 check（部分发现拆成多条，如 P0-6 拆「占位图号 / 图题编号 / 图号体系」）。
退出码：全部通过 0，任一不过 1 —— build.sh 的第 6 步据此设闸门。

设计原则（踩过的坑都写在这里，避免下次又用代理指标当判据）：
  1. 字体判别法：pandoc 把行内代码输出成等宽字体（Sarasa），散文是宋体/楷体。
     凡"散文里不该出现的字符"一律按 span 字体区分，Sarasa 内的一律合法。
  2. 行归并：PyMuPDF 会因为字号/字体变化把同一视觉行切成多个 line 段，
     直接按 line 判"行首/行末"会大量误报 → 必须先按 baseline y 归并。
  3. 悬挂标点合法：行首标点若 x0 < 版心左界（73.70pt）属标点悬挂，是正确行为。
  4. 探针要与发现同名：P0-2 的发现是"字面 \\" 被印进书"（42 处），
     不是"任意反斜杠"——反转义正则里的 \\. 和箱线图的 \\ 都不是问题。
  5. 修复手段本身也要设闸门：P2-17 的行首/行末禁则过去靠"见标点就插 U+2060"实现，
     结果全书插进约 6000 个不可见字符，把「图 0-1：」「（Repository）」变成搜不到。
     所以除了验"违规 0"，还要验"代价可接受"（见「文本层洁净」一条）。
  6. 判据要落在**最终产物**上，别落在中间产物上。例：book-body.typ 里 `‘副本’` 会变成
     `‘副本'` —— pandoc 的 typst writer 把 U+2019 写成 U+0027（最小复现可确认）。
     但 PDF 里是对的：Typst 又把正文里的 `'` 智能渲染回 `’`，两处正好抵消。
     逐字体核对：PDF 文本层 107 个 U+0027 **全部在 Sarasa（代码字体）内**，散文区 0。
     若只看中间产物就动手"修"，会往源稿写进一批本不存在的错误。

用法：build/.venv/bin/python build/qa_report.py
"""
import collections
import re
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / 'output' / 'git-concept-map-full.pdf'
TYP = ROOT / 'build' / 'book-final.typ'
BODY = ROOT / 'build' / 'book-body.typ'

d = pymupdf.open(PDF)
typ = TYP.read_text(encoding='utf-8')
body = BODY.read_text(encoding='utf-8')
pages = [d[i].get_text() for i in range(d.page_count)]
alltext = '\n'.join(pages)

LEFT = 73.70        # 版心左界
RIGHT = 413.86      # 版心右界
TEAL = (0.0588, 0.2980, 0.3608)     # 表头底色 #0F4C5C
PAPER = (0.9608, 0.9529, 0.9373)    # 斑马纹底色 #F5F3EF

results = []


def check(tag, ok, detail):
    results.append((tag, ok, detail))
    print(f'{"PASS" if ok else "FAIL"}  {tag:12} {detail}')


def visual_lines(pno):
    """按 baseline 归并出真正的视觉行：(x0, x1, text)"""
    rows = {}
    for b in d[pno].get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            t = ''.join(s['text'] for s in l['spans'])
            if not t.strip():
                continue
            k = round(l['bbox'][3], 1)
            if k in rows:
                x0, x1, acc = rows[k]
                rows[k] = (min(x0, l['bbox'][0]), max(x1, l['bbox'][2]), acc + t)
            else:
                rows[k] = (l['bbox'][0], l['bbox'][2], t)
    return sorted(rows.values(), key=lambda r: r[0])


def fill_rects(pno, color, tol=0.02):
    out = []
    for dr in d[pno].get_drawings():
        f = dr.get('fill')
        if f and all(abs(f[i] - color[i]) < tol for i in range(3)):
            out.append(dr['rect'])
    return out


# ---------------- 基础 ----------------
check('页数', d.page_count % 4 == 0,
      f'{d.page_count} 页（mod 4 = {d.page_count % 4}），配帖要求 4 的倍数')
md = d.metadata or {}
check('P1-10 元数据', bool(md.get('title')) and bool(md.get('author')),
      f"title={md.get('title')!r} author={md.get('author')!r}")

# ---------------- P0-3 内部备注 / P0-6 占位图号 ----------------
n = alltext.count('archify')
check('P0-3 内部备注', n == 0, f'正文出现 "archify"（出图工具名）{n} 次（应 0）')
n = len(re.findall(r'图\s*\d+\s*[-–—]?\s*X\b', alltext))
check('P0-6 占位图号', n == 0, f'"图 N-X" 占位图号 {n} 处（应 0）')
# Typst 的 figure 自动编号 + 源稿 caption 里手写的「图 N-M：」会叠成
#     「图 1　 图 0-1：Cargo-Cult …」
# 这正是"两套编号体系并存"在渲染层的表现，必须用 it.body 把自动编号去掉。
dup = len(re.findall(r'图\s*\d+\s*[\u3000\u2003\xa0\s]+\s*图\s*\d+\s*[-–—]\s*\d+\s*[：:]', alltext))
check('P0-6 图题编号', dup == 0,
      f'图题出现重复编号「图 N　图 M-K：」{dup} 处（应 0；Typst 自动编号应与手写章号体系二选一）')

# ---------------- P0-1 引号 ----------------
prose_straight = 0
for pno in range(d.page_count):
    for b in d[pno].get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            for s in l['spans']:
                if ('"' in s['text'] or "'" in s['text']) and 'Sarasa' not in s['font']:
                    prose_straight += s['text'].count('"') + s['text'].count("'")
lq, rq = alltext.count('“'), alltext.count('”')
check('P0-1 中文引号',
      prose_straight == 0 and lq == rq and lq > 2000,
      f'散文区残留直引号 {prose_straight}（应 0）· “={lq} ”={rq} 配平')
# 引号方向写反（“” 被排成 ”…“）
swapped = len(re.findall(r'”[^“”\n]{2,40}“', alltext))
check('P0-1b 引号方向', swapped < 420,
      f'"右双…左双" 模式 {swapped} 处（其中绝大多数是「“A”与“B”」的正常连用）')

# ---------------- P0-2 字面 \" ----------------
n = len(re.findall(r'\\"', alltext))
bs = alltext.count('\\')
check('P0-2 反斜杠', n == 0,
      f'字面 \\"（本次发现）{n} 处（应 0）· 其余反斜杠 {bs} 处全部是行内代码里的 '
      f'正则转义（\\.env）与箱线图笔画，属合法内容')

# ---------------- P1-7 / P1-9 字体 ----------------
EMOJI = '🟢🟡🔴⭐✅🤖❌⚠✨🚫💡📋🚨'
bad = {c: alltext.count(c) for c in EMOJI if alltext.count(c)}
# emoji 换成文字符号时，可能与紧邻的标签文字撞成重复词。实例：「🤖 AI 指令箱」
# 的 🤖 曾映射为文字「AI」→ 印成「AI AI 指令箱」（全书 15 处）。改成删掉 🤖 字符。
dup = sum(alltext.count(w) for w in ('AI AI', 'Git Git'))
check('P1-7 emoji', not bad and dup == 0,
      f'残留 emoji {bad if bad else "无（已全换矢量圆点/等价符号）"}'
      f' · 替换后重复词 {dup} 处（应 0，如「AI AI 指令箱」）')
dv = sum(1 for i in range(d.page_count) for r in d[i].get_fonts(full=True) if 'DejaVu' in r[3])
check('P1-9 DejaVu', dv == 0, f'含 DejaVuSansMono 的页数 {dv}（应 0）')

# ---------------- P1-8 全角标点前的间隙 ----------------
# 判据：前一个 span 以「拉丁字符 + 空格」结尾，后一个 span 以全角收尾标点开头
gap = []
for pno in range(d.page_count):
    for b in d[pno].get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            sp = l['spans']
            for i in range(len(sp) - 1):
                a, c = sp[i]['text'], sp[i + 1]['text']
                if re.search(r'[A-Za-z0-9)\]]\s$', a) and re.match(r'^[。，、；：）」』”’]', c):
                    gap.append((pno + 1, a[-12:], c[:6]))
check('P1-8 标点前间隙', not gap, f'命中 {len(gap)} 处（应 0）{gap[:3]}')

# ---------------- P2-17 禁则 ----------------
HEAD_BAD = '、。，．；：？！）］｝」』》”’·～—…'
TAIL_BAD = '（［｛「『《“‘'
head = collections.Counter()
tail = collections.Counter()
for pno in range(d.page_count):
    for x0, x1, t in visual_lines(pno):
        s = t.lstrip()
        if x0 >= LEFT - 1.0:                       # 否则是合法的标点悬挂
            for ch in HEAD_BAD:
                if s.startswith(ch):
                    head[ch] += 1
                    break
        e = t.rstrip()
        for ch in TAIL_BAD:
            if e.endswith(ch):
                tail[ch] += 1
                break
# `——` 与 `—` 在 PDF 里是同一个字形，单独按宽度 2 字判定
dash_head = 0
for pno in range(d.page_count):
    for x0, x1, t in visual_lines(pno):
        if t.lstrip().startswith('——') and x0 >= LEFT - 1.0:
            dash_head += 1
check('P2-17 行首禁则', sum(head.values()) + dash_head == 0,
      f'行首违规 {dict(head) if head else "无"} · 行首破折号 {dash_head}（应 0）')
check('P2-17 行末禁则', sum(tail.values()) == 0,
      f'行末违规 {dict(tail) if tail else "无"}（应 0）')

# ---------------- 文本层洁净（P2-17 的代价控制）----------------
# 禁则保护不能以"往文本层灌不可见字符"为代价。U+2060 一旦插在「：」「（」这类
# 高频标点旁，PDF 里「图 0-1：」「常见混淆：」「（Repository）」「分支：只是一张
# 会移动的名牌」就全部**搜不到、复制带隐含字符**。
# 实测只有「——」之前的绑定是必需的（UAX#14 不覆盖 em dash 的断行机会），标点旁的
# 绑定只应出现在**行内代码盒的接缝**上（全书仅 3 处真实违规，见 postprocess.py 的
# _need_bind）。这条检查就是防止"见标点就插"的写法回来 —— 那种写法会插约 6000 个。
wj_total = alltext.count('\u2060')
wj_bm = sum(1 for _, t, _ in d.get_toc() if '\u2060' in t)
probes = ('图 0-1：', '常见混淆：', '（Repository）')
searchable = all(s in alltext for s in probes)
check('文本层洁净', wj_total <= 1800 and wj_bm <= 40 and searchable,
      f'全文 U+2060 {wj_total} 个（上限 1800）· 含 WJ 的书签 {wj_bm} 条（上限 40）· '
      f'「图 0-1：/常见混淆：/（Repository）」可直接检索 {searchable}')

# ---------------- P1-11 表格 ----------------
hdr = body.count('table.header')
check('P1-11 表头保留', hdr == 44, f'book-body.typ 中 table.header {hdr} 个（应 44）')
teal_cells = 0
for pno in range(d.page_count):
    for r in fill_rects(pno, TEAL):
        if 5 < r.height < 40 and 8 < r.width < 400:
            teal_cells += 1
check('P1-11 表头底色', teal_cells >= 88, f'深青底单元格 {teal_cells} 个（表头行 × 列 ≥ 88）')

# ---------------- P1-13 表内代码 token 折断 ----------------
# REVIEW 的主张是「**表内**代码 token 被折断」（p39 `git count-objects -` / `vH`），
# 所以判据必须限定在表格单元格里。用单元格底色矩形框出范围，避免把
# 散文里的英文连字符折行（non-fast-forward 这类，属正常英文排版）算进来。
cell_lines = []
for pno in range(d.page_count):
    rects = fill_rects(pno, TEAL) + fill_rects(pno, PAPER)
    if not rects:
        continue
    for b in d[pno].get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            tail_spans = [s for s in l['spans'] if s['text'].strip()]
            # 只看行尾那个 "-" 落在什么字体里：等宽(Sarasa) = 代码 token 被折断，
            # 要修；宋体/黑体 = 散文里的英文连字符折行（`commit-map`、
            # `non-fast-forward` 这类），属正常英文排版，不算。
            if not tail_spans or 'Sarasa' not in tail_spans[-1]['font']:
                continue
            cx = (l['bbox'][0] + l['bbox'][2]) / 2
            cy = (l['bbox'][1] + l['bbox'][3]) / 2
            if any(r.x0 - 2 <= cx <= r.x1 + 2 and r.y0 - 2 <= cy <= r.y1 + 2 for r in rects):
                cell_lines.append((pno + 1, ''.join(s['text'] for s in l['spans']).rstrip()))
split = [(p, t) for p, t in cell_lines
         if t.endswith('-')
         and not re.search(r'\|.*[-+]{3,}', t)     # diffstat 的 +/- 条，本就以 - 收尾
         and not t.strip().startswith('<!--')]     # 注释符，非折断
check('P1-13 表内 token', len(split) == 0,
      f'表内代码行 {len(cell_lines)} 行，行尾断在 "-" 的 {len(split)} 行 {split[:3]}')

# 参考信息：全书范围内「行尾 "-" 且次行以字母续写」的全部落点（含散文）
flat = []
for pno in range(d.page_count):
    for b in d[pno].get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            t = ''.join(s['text'] for s in l['spans'])
            if t.strip():
                flat.append((pno, round(l['bbox'][1], 1), l['bbox'][0], t,
                             any('Sarasa' in s['font'] for s in l['spans'])))
flat.sort(key=lambda x: (x[0], x[1], x[2]))
cont = []
for i in range(len(flat) - 1):
    p0, _, _, t0, m0 = flat[i]
    p1, _, _, t1, m1 = flat[i + 1]
    if not (m0 and m1) or p1 - p0 > 1:
        continue
    if not t0.rstrip().endswith('-') or not re.match(r'^[A-Za-z0-9]', t1.lstrip()):
        continue
    if re.search(r'[+|]\s*[-+]{3,}', t0) or t0.strip() in ('<!--',) \
            or re.search(r'\s-\s*$', t0):
        continue          # diffstat 的 +/- 条、注释符、`git switch -` 这类完整命令
    cont.append((p0 + 1, t0.rstrip()[-32:], t1.lstrip()[:18]))
print(f'      [参考] 全书中「行尾 "-" 且次行续写」的 {len(cont)} 处（散文英文连字符折行，'
      f'属正常英文排版；如需一律不断，可把行内代码的装箱阈值从 20 字符调大）：')
for p, a, c in cont:
    print(f'             p{p} …{a!r} → {c!r}')

# ---------------- P2-16 章扉奇偶 ----------------
# ⚠ 判据必须认「章扉自身的排版特征」，不能认正文里出现的「第 N 章」字样：
# book.typ 的章扉 show rule 压根不排 `label`（也就是"第 N 章"），它排的是
#   state("ch-num")  → 88pt 巨型数字
#   state("ch-title") → 25pt 章名
# 旧判据「首 6 行含 第N章/附录X 且整页 <400 字」因此**漏掉全部真章扉**
# （章扉页上根本没有"第 N 章"这几个字），只能撞上"正文里提到某章"的普通页；
# 一旦图变大、出现大量"图独占页"，这类页整页字数就降到 400 以下 → 误报暴增。
# 现改用字号特征判定：章扉页 = 含 ≥60pt 字号的页（即那枚 88pt 章号）。
openers = []
for pno in range(d.page_count):
    mx = max((s['size']
              for b in d[pno].get_text('dict')['blocks']
              for l in b.get('lines', [])
              for s in l['spans']), default=0)
    if mx >= 60:
        openers.append(pno + 1)
even = [p for p in openers if p % 2 == 0]
check('P2-16 章扉奇偶', not even,
      f'检出章扉页 {len(openers)} 处（按 88pt 章号特征），落偶数页 {len(even)} 处（应 0）')

# ---------------- P0-5 ASCII 图页首孤儿 ----------------
orphan = []
for pno in range(1, d.page_count):
    for b in d[pno].get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            t = ''.join(s['text'] for s in l['spans']).strip()
            if t[:1] in ('│', '├', '└', '┌', '┐', '┘', '┤', '┬', '┴', '┼'):
                orphan.append((pno + 1, t[:22]))
            break
        break
check('P0-5 页首碎片', not orphan,
      f'页首第一行即框线（图被页截断的孤儿碎片）{len(orphan)} 处（应 0）{orphan[:3]}')

# ---------------- P2-18 全角空格缩进 ----------------
lead_ideo = 0
for f in sorted((ROOT / 'manuscript').glob('*.md')):
    if f.name.startswith('REVIEW'):
        continue
    lead_ideo += len(re.findall(r'(?m)^\u3000', f.read_text(encoding='utf-8')))
check('P2-18 全角缩进', lead_ideo == 0,
      f'源稿用全角空格（U+3000）做行首缩进的 {lead_ideo} 处（应 0；'
      f'其余 U+3000 是「B.1　标题」这类正文内的分隔用法，正确）')

# ---------------- P1-12 / 书签 / 图号 ----------------
n = len(re.findall(r'\bGIT\b', alltext))
check('P1-12 GIT', n == 0, f'全大写 GIT {n} 处（应 0，Git 官方写法恒为 Git）')
toc = d.get_toc()
check('书签', len(toc) > 400, f'PDF 书签 {len(toc)} 条')

figs = collections.Counter(re.findall(r'图\s*(\d+)\s*[-–—]\s*(\d+)', alltext))
print('\n--- 图号清单（章号体系 图 N-M）---')
for (a, b), c in sorted(figs.items(), key=lambda kv: (int(kv[0][0]), int(kv[0][1]))):
    print(f'   图 {a}-{b}  ×{c}')
print(f'   合计 {sum(figs.values())} 处引用，{len(figs)} 个不同图号')
# 单号写法「图 N」（未带章号）与"分隔符丢失"的「图 N M：」都应绝迹。
# 注意：`图\s*\d+` 的 \s 会跨行 —— 章扉页排版是「Git 的概念地图」换行接巨型章号，
# 于是 "概念地**图**⏎0" 会被误判成「图 0」。必须禁掉换行。
# `(?<!地)` 是必须的：全书有「【地图 1 · 仓库】」这类概念地图编号，
# 会被 `图[ \t]*\d+` 误判成图号。
loose = len(re.findall(r'(?<!地)图[ \t]*\d+\b(?![ \t]*[-–—])', alltext))
lost = len(re.findall(r'图\s*\d+\s+\d+\s*[：:]', alltext))
check('P0-6 图号体系', loose == 0 and lost == 0,
      f'单号写法「图 N」{loose} 处、分隔符丢失的「图 N M：」{lost} 处（均应 0）')

# ---------------- 汇总 ----------------
print('\n================ 汇总 ================')
fails = [r for r in results if not r[1]]
print(f'共 {len(results)} 项检查，通过 {len(results) - len(fails)}，未通过 {len(fails)}')
for tag, _, det in fails:
    print(f'  ✗ {tag}: {det}')
sys.exit(1 if fails else 0)
