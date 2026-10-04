#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三审三校 · 编校机械扫描器（出版合规 + 差错率估算）

设计要点
------------------------------------------------
正文与代码必须分开统计：STYLE-NOTES 规定「散文全角标点 / 代码围栏内半角」，
所以直引号 `"`、半角逗号 `,` 出现在代码里是**正确**的，出现在散文里才是差错。
本脚本先切出「散文层」（去掉 ``` 围栏与 `行内代码`、去掉 ASCII 图块），
再在散文层上做标点 / 数字 / 违禁词检查。

用法：
    build/.venv/bin/python build/qa_compliance.py            # 全部检查
    build/.venv/bin/python build/qa_compliance.py quotes     # 只看引号
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MS = ROOT / 'manuscript'

# 评审报告本身不是书稿正文，排除
SKIP_FILES = {'STYLE-NOTES.md'}
SKIP_PREFIX = ('REVIEW',)

CJK = r'\u4e00-\u9fff'


def book_files():
    out = []
    for p in sorted(MS.glob('*.md')):
        if p.name in SKIP_FILES or p.name.startswith(SKIP_PREFIX):
            continue
        out.append(p)
    return out


def layers(text):
    """把 markdown 切成 (散文层, 代码层) 两个字符串。

    散文层：正文 + 表格文字 + 标题，去掉了代码围栏、行内代码、ASCII 图块。
    代码层：代码围栏 + 行内代码的内容（用于代码内半角标点抽查）。
    """
    prose, code = [], []
    in_fence = False
    for ln in text.split('\n'):
        s = ln.rstrip()
        if s.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            code.append(s)
            continue
        # 行内代码取出
        for m in re.finditer(r'`([^`]*)`', s):
            code.append(m.group(1))
        prose.append(re.sub(r'`[^`]*`', '\x00', s))
    return '\n'.join(prose), '\n'.join(code)


def line_of(text, pos):
    return text.count('\n', 0, pos) + 1


def snippet(text, pos, w=26):
    a = max(0, pos - w)
    return text[a:pos + w].replace('\n', ' ⏎ ')


# ---------------------------------------------------------------- 检查项

def chk_quotes(files):
    """散文层出现直引号 / 直单引号 = 标点未转中文弯引号。"""
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        for ch, name in (('"', '直双引号'), ("'", '直单引号')):
            for m in re.finditer(re.escape(ch), prose):
                hits.append((p.name, line_of(prose, m.start()), name,
                             snippet(prose, m.start())))
    return hits


def chk_halfwidth_punct(files):
    """散文层中夹在汉字之间的半角逗号/句号/冒号/问号/感叹号。"""
    pat = re.compile(f'[{CJK}]\\s*([,.;:?!])\\s*[{CJK}]')
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        for m in pat.finditer(prose):
            hits.append((p.name, line_of(prose, m.start()),
                         f'半角 {m.group(1)}', snippet(prose, m.start())))
    return hits


def chk_numbers(files):
    """GB/T 15835 数字用法。

    注意：**「第 9、11、12、13 章」这类序号并列是合法用法**（序号、编号用阿拉伯数字），
    早期版本把它误判为"并列概数"，已剔除。真正违规的是**概数用阿拉伯数字**：
    「10 多个人」应作「十多个人」，「3、4 个」表约数时应作「三四个」。
    故此处只保留「数字 + 多」这一无争议规则，避免制造假阳性。
    """
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        pat = re.compile(r'\d+\s*多(?=[个条次天年月人倍分秒页行])')
        for m in pat.finditer(prose):
            hits.append((p.name, line_of(prose, m.start()), '概数应用汉字',
                         snippet(prose, m.start())))
    return hits


def chk_dupe_punct(files):
    """重复标点：`。。` `，，` `！！` `？？` `：：`。"""
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        for m in re.finditer(r'([。，、；：！？])\1+', prose):
            hits.append((p.name, line_of(prose, m.start()), f'重复标点 {m.group(0)}',
                         snippet(prose, m.start())))
    return hits


BANNED = [
    '最好的', '最佳', '最强', '最快', '最权威', '最全', '唯一', '独一无二',
    '绝无仅有', '史无前例', '史上最', '天下第一', '第一品牌', '顶尖', '顶级',
    '国家级', '国家认证', '国家推荐', '永久', '终身', '100%', '百分之百',
    '零风险', '稳赚', '保证成功', '包过', '万能', '绝对不会', '永远不会出错',
]

# 语境豁免：命中这些邻域即不算广告宣传性绝对化用语
EXEMPT_NEG = re.compile(r'不是|并非|无法|没能|不可能|没有|别指望|不保证|≠')
EXEMPT_FACT = re.compile(
    r'对象|SHA|哈希|指纹|id\b|ID\b|物理|机制|语义|定义|身份证|唯一标识|'
    r'唯一路径|唯一入口|唯一出口|唯一合法|父的|指称')
SELF_REF = re.compile(r'本书|全书|本章|这份表|附录|全书共')


def classify_banned(word, ctx):
    """把命中分为 3 档：豁免 / 自指 / 风险。"""
    if EXEMPT_NEG.search(ctx):
        return '豁免·否定式'
    if word in ('永久', '唯一', '万能') and EXEMPT_FACT.search(ctx):
        return '豁免·技术事实'
    if SELF_REF.search(ctx):
        return '自指·建议改写避险'
    return '★风险·评价性绝对化'


def chk_banned(files, all_hits=False):
    """广告法绝对化用语 / 收益承诺。

    关键：**不能只看词，要看语境**。「唯一身份证」是 SHA 的技术事实，
    「不是万能保险」是否定式警告，「全书唯一集中命令参考」是自指结构描述——
    这三类都不是对商品/服务的绝对化宣传。真正需要处理的是**评价第三方**的
    绝对化用语（如「Pro Git 是最全的中文资源」「唯一权威」），它同时踩
    广告法风险与「表述不可复核」两条线。
    """
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        for w in BANNED:
            for m in re.finditer(re.escape(w), prose):
                ctx = prose[max(0, m.start() - 26):m.start() + 26].replace('\n', ' ')
                kind = classify_banned(w, ctx)
                if all_hits or kind.startswith('★'):
                    hits.append((p.name, line_of(prose, m.start()),
                                 f'{kind}「{w}」', ctx))
    return hits


def banned_breakdown(files):
    from collections import Counter
    c = Counter()
    risky = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        for w in BANNED:
            for m in re.finditer(re.escape(w), prose):
                ctx = prose[max(0, m.start() - 26):m.start() + 26].replace('\n', ' ')
                k = classify_banned(w, ctx)
                c[k] += 1
                if k.startswith('★'):
                    risky.append((p.name, line_of(prose, m.start()), w, ctx))
    return c, risky


def no_fence(text):
    """去掉代码围栏，但**保留行内代码**。

    术语判据要的是语境线索，而 `refs/tags/` 这类线索就写在行内代码里。
    早先这里用的 `layers()` 会把行内代码替换成 \\x00，于是 "tags" 被抹掉、
    附录 C「refs/tags/ 放标签」被误报——度量本身出了错。
    """
    out = []
    in_fence = False
    for ln in text.split('\n'):
        s = ln.rstrip()
        if s.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append(s)
    return '\n'.join(out)


def chk_term(files):
    """术语口径：'标签' 只允许指 git tag；指代分支/引用时应为「名牌」。

    判 OK 的依据必须就近可见：附近 45 字内出现 tag / 附注 / 轻量 / 签名 等 tag 语境线索。
    其余一律标为「待判」并打印完整上下文，由审校人裁决——不做猜测性自动判错。
    """
    hits = []
    for p in files:
        text = no_fence(p.read_text(encoding='utf-8'))
        for m in re.finditer('标签', text):
            ctx = text[max(0, m.start() - 45):m.start() + 45].replace('\n', ' ')
            if re.search(r'tag|附注|轻量|签名|打标签|标签页|标签云', ctx, re.I):
                continue
            hits.append((p.name, line_of(text, m.start()),
                         '「标签」无 tag 语境线索，待判是否应为名牌', ctx))
    return hits


# ---- 三校 · 体例一致性（跨文件）------------------------------------

CH_TITLE = re.compile(r'^#\s*第\s*(\d+)\s*章[　\s]*(.*)$')
APP_TITLE = re.compile(r'^#\s*附录\s*([A-D])[　\s]*(.*)$')


def chapter_titles(files):
    """返回 {('ch', n): 标题} / {('app', 'A'): 标题}。"""
    out = {}
    for p in files:
        for ln in p.read_text(encoding='utf-8').split('\n'):
            m = CH_TITLE.match(ln.strip())
            if m:
                out[('ch', int(m.group(1)))] = m.group(2).strip()
                continue
            m = APP_TITLE.match(ln.strip())
            if m:
                out[('app', m.group(1))] = m.group(2).strip()
    return out


def chk_preview(files):
    """下一章预告里引用的章标题，必须等于下一章的实际标题。

    只在「下一章预告」栏目区块内比对，且只取 `第 N 章《…》` 这种显式引用——
    早期版本用全文正则，会把「第 2 章讲的…」这类顺带提及全部误判为标题不符。
    """
    titles = chapter_titles(files)
    hits = []
    for p in files:
        lines = p.read_text(encoding='utf-8').split('\n')
        starts = [i for i, l in enumerate(lines)
                  if re.match(r'^#{2,4}.*下一章预告', l)]
        for start in starts:
            end = len(lines)
            for j in range(start + 1, len(lines)):
                if re.match(r'^#{2,4} ', lines[j]):
                    end = j
                    break
            body = '\n'.join(lines[start:end])
            for m in re.finditer(r'第\s*(\d+)\s*章\s*《([^》]+)》', body):
                nn = int(m.group(1))
                cited = m.group(2).strip()
                real = titles.get(('ch', nn))
                if real and real != cited:
                    hits.append((p.name, start + 1,
                                 f'预告第 {nn} 章标题与正文不符',
                                 f'预告「{cited}」 / 正文「{real}」'))
    return hits


def chk_xrefs(files):
    """交叉引用解析：第 N 章 / 附录 X 是否存在；附录 B.n.m 的 n 是否在 1–13。"""
    titles = chapter_titles(files)
    hits = []
    for p in files:
        text = p.read_text(encoding='utf-8')
        for m in re.finditer(r'第\s*(\d+)\s*章', text):
            n = int(m.group(1))
            if ('ch', n) not in titles:
                hits.append((p.name, line_of(text, m.start()),
                             f'引用了不存在的第 {n} 章', snippet(text, m.start())))
        for m in re.finditer(r'附录\s*([A-D])', text):
            if ('app', m.group(1)) not in titles:
                hits.append((p.name, line_of(text, m.start()),
                             f'引用了不存在的附录 {m.group(1)}',
                             snippet(text, m.start())))
        for m in re.finditer(r'B\.(\d+)\.(\d+)', text):
            if not 1 <= int(m.group(1)) <= 13:
                hits.append((p.name, line_of(text, m.start()),
                             f'附录 B 分组号越界 B.{m.group(1)}',
                             snippet(text, m.start())))
    return hits


# PDF 构建期会把这些 emoji 替换成矢量圆点/等价符号（见 qa_report.py P1-7）。
# 出现在这个白名单之外的 emoji，构建期不会被替换 → 会在 PDF 里印成缺字方框。
MAPPED_EMOJI = set('🟢🟡🔴⭐✅🤖❌⚠✨🚫💡📋🚨')


def pdf_text_set(pdf_path):
    """成品 PDF 文本层出现的字符集合。

    用来回答「这个符号到底渲染出来了吗」——判据落在最终产物上，
    而不是靠维护一张「猜测哪些符号会被替换」的白名单。
    """
    import pymupdf as fitz
    doc = fitz.open(str(pdf_path))
    chars = set()
    for pg in doc:
        chars |= set(pg.get_text())
    doc.close()
    return chars


def chk_unmapped_emoji(files, pdf_path=None):
    """源稿里出现、但成品 PDF 文本层查无此字的符号。

    两类不算问题：
      (a) MAPPED_EMOJI —— 构建期刻意换成矢量圆点／等价符号，本就不进文本层；
      (b) 成品文本层实测存在 —— 渲染正常（如 → ← ├ ─ 等框线箭头，实测均正常）。
    只有「不在 (a) 也不在 (b)」才是会变成缺字方框的真问题。
    """
    present = pdf_text_set(pdf_path) if pdf_path and pdf_path.exists() else None
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        for m in re.finditer(r'[\U0001F000-\U0001FAFF\u2190-\u21FF\u2600-\u27BF]',
                             prose):
            ch = m.group(0)
            if ch in MAPPED_EMOJI:
                continue
            if present is not None and ch in present:
                continue
            why = ('构建期不替换' if present is None
                   else f'不在替换表、成品文本层也查不到（共 {len(present)} 字）')
            hits.append((p.name, line_of(prose, m.start()),
                         f'未映射符号 {ch}（{why}，成品会缺字）',
                         snippet(prose, m.start())))
    return hits


def chk_halfwidth_paren(files):
    """散文层中的半角左括号。

    两类都要抓：
      (a) 左括号前是汉字或中文标点 —— 中文语境误用半角；
      (b) 左括号是半角、配对的右括号却是全角 —— 括号错配（如 `(语义)。`）。
    仅靠 `[CJK]\\s*\\(` 会漏掉 `？(` 这类前置为标点的情况（ch13 实测漏报）。
    """
    left = re.compile(f'[{CJK}。，、；：！？）】」》…—]\\s*[\\(]')
    hits = []
    for p in files:
        prose, _ = layers(p.read_text(encoding='utf-8'))
        seen = set()
        for m in left.finditer(prose):
            i = m.end() - 1          # points at the '('
            kind = '半角左括号'
            close = prose.find(')', i)
            fw = prose.find('）', i)
            if fw != -1 and (close == -1 or fw < close):
                kind = '半角左括号配全角右括号（错配）'
            if (i, kind) in seen:
                continue
            seen.add((i, kind))
            hits.append((p.name, line_of(prose, i), kind, snippet(prose, i)))
    return hits


BOX = '┌┐└┘├┤│┬┴┼─'


def chk_ascii_art(files):
    """ASCII 框线图不变量：同一连续框图内，竖线 │ 必须列对齐。

    早期版本比较「整行显示宽度是否一致」，但 ASCII 图天然有长短不齐的行
    （箭头、旁注、孤立标签），会产生大量假阳性。真正的不变量是：
    一个由 ┌ 起、┘ 终的连续框图里，所有含 │ 的行，其 │ 的列位置必须相同。
    这里用「连续框图段内 │ 列位置集合的众数覆盖度」判定。
    """
    hits = []
    for p in files:
        text = p.read_text(encoding='utf-8')
        in_fence, block, start = False, [], 0
        for i, ln in enumerate(text.split('\n'), 1):
            if ln.lstrip().startswith('```'):
                if block:
                    hits += _check_block(p.name, start, block)
                    block = []
                in_fence = not in_fence
                continue
            if not in_fence:
                continue
            if any(c in ln for c in '│┌┐└┘├┤'):
                if not block:
                    start = i
                block.append(ln)
            else:
                if block:
                    hits += _check_block(p.name, start, block)
                    block = []
        if block:
            hits += _check_block(p.name, start, block)
    return hits


def _check_block(fname, start, block):
    """框图段内比对 ⟂ 竖线列位置（按显示宽度计）。"""
    import unicodedata

    def disp(s):
        return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in s)

    rows = []
    for ln in block:
        if '│' not in ln:
            continue
        pos, col = [], 0
        for ch in ln:
            if ch == '│':
                pos.append(col)
            col += 2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if pos:
            rows.append(tuple(pos))
    if len(rows) < 2:
        return []
    from collections import Counter
    modal, cnt = Counter(rows).most_common(1)[0]
    if cnt >= len(rows) - 1 or cnt / len(rows) > 0.85:
        return []          # 允许 1 行例外（常是注释行）
    odd = sorted(set(rows) - {modal})[:2]
    return [(fname, start, 'ASCII 框图竖线未列对齐',
             f'众数列位 {modal}（{cnt}/{len(rows)} 行）；异常列位 {odd}')]


BORDER_CH = '│┌┐└┘├┤┬┴┼─'
WALL_CH = '│┐┘'          # 右墙的候选字符


def _pdf_rows(page):
    """抽取一页里所有「框线行」：返回 (baseline_y, 最右墙x, 行文本, 最左墙x, 各墙x列表)。

    关键：**必须把边框行也算进来**。`┌───┐` / `└───┘` 不含 `│`，
    若只收 `│` 行，框的"正确宽度"就不在样本里，比较立刻失效（踩过）。
    """
    rows = []
    for b in page.get_text('rawdict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if 'Sarasa' not in s['font']:
                    continue
                t = ''.join(c['c'] for c in s['chars'])
                if not any(ch in t for ch in BORDER_CH):
                    continue
                walls = [c['bbox'][0] for c in s['chars'] if c['c'] in WALL_CH]
                if not walls:
                    continue
                rows.append((round(l['bbox'][1], 1), round(max(walls), 2), t,
                             round(min(walls), 2), walls))
    rows.sort()
    return rows


def chk_boxes_pdf(pdf_path):
    """产物级判据：成品 PDF 里 ASCII 方框的右墙是否落在同一列。

    ASCII 图在成品里排 Sarasa 等宽字体，一个显示列 = 4.25pt（CJK = 8.5pt）。
    做法：把连续的框线行并成一段（**同一框的行距 21.1pt，跨框空行 42pt**，
    故阈值取 30pt），要求该段含真正的边框（┌ 与 └/┘）以排除树形/扇形图，
    然后把「最右墙 x」分簇；**簇数 ≥2 即为歪墙**——因为一个方框的墙只能有一个 x。

    为什么必须量成品（不量源稿）：`·`（U+00B7，东亚宽度 A）占 1 列还是 2 列
    取决于字体，按源稿字符数算宽度会得出与实际印刷不符的结论。
    """
    import pymupdf
    d = pymupdf.open(pdf_path)
    hits = []
    for pno in range(d.page_count):
        rows = _pdf_rows(d[pno])
        run = []
        for r in rows:
            if run and r[0] - run[-1][0] > 30:
                hits += _judge_run(pno + 1, run)
                run = []
            run.append(r)
        if run:
            hits += _judge_run(pno + 1, run)
    return hits


def _judge_run(page, run):
    """一段连续框线行内，找出「同属于同一个外框」的行的右墙是否一致。

    不能直接拿所有行的最右墙比：框与框之间的**连接线**（如 `│  装着`）
    只有一个竖线，天然不在外框的右墙列上，会被误判成歪墙（踩过）。
    故先定出外框左墙（众数最小墙位），只比较**含外框左墙**的行。
    """
    joined = ''.join(r[2] for r in run)
    if '┌' not in joined or not ('└' in joined or '┘' in joined):
        return []                      # 不是方框（树形图/扇形图），不适用
    if len(run) < 3:
        return []

    # 外框左墙：所有行里出现次数最多的「最小墙位」
    from collections import Counter
    lefts = Counter(r[3] for r in run)
    box_left = None
    for x, c in lefts.most_common():
        if c >= 2:
            box_left = x
            break
    if box_left is None:
        return []

    members = [r for r in run if any(abs(w - box_left) <= 4.25 for w in r[4])]
    if len(members) < 3:
        return []
    rights = [r[1] for r in members]
    mode = Counter(rights).most_common(1)[0][0]
    bad = [r for r in members if abs(r[1] - mode) > 4.25]
    if not bad:
        return []
    worst = max(bad, key=lambda r: abs(r[1] - mode))
    return [(f'PDF p{page}', 0,
             f'ASCII 外框右墙歪：{len(bad)}/{len(members)} 行偏离',
             f'正确右墙 x={mode:.2f}（{rights.count(mode)} 行）· 最差行 x={worst[1]:.2f}'
             f'（偏 {abs(worst[1] - mode):.2f}pt ≈ {abs(worst[1] - mode) / 4.25:.1f} 字符）'
             f'· 示例「{worst[2][:34]}」')]


def chk_boxes_pdf_strict(pdf_path):
    """同上，但返回每条偏离行的明细（供报告逐行列示）。"""
    import pymupdf
    d = pymupdf.open(pdf_path)
    out = []
    for pno in range(d.page_count):
        rows = []
        for b in d[pno].get_text('rawdict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    t = ''.join(c['c'] for c in s['chars'])
                    if '│' not in t or 'Sarasa' not in s['font']:
                        continue
                    xs = [c['bbox'][0] for c in s['chars'] if c['c'] == '│']
                    rows.append((round(l['bbox'][1], 1), min(xs), max(xs), t))
        rows.sort()
        for r in rows:
            if abs(r[2] - 347.2) > 4.25 and r[2] != r[1]:
                out.append((pno + 1, r[0], r[2], r[3][:40]))
    return out


def wordcount(files):
    cjk = 0
    for p in files:
        cjk += len(re.findall(f'[{CJK}]', p.read_text(encoding='utf-8')))
    return cjk


# ---------------------------------------------------------------- 主流程

def report(title, hits, limit=12):
    print(f'\n### {title}：{len(hits)} 处')
    for h in hits[:limit]:
        f, ln, kind, ctx = h
        print(f'  {f}:{ln}  {kind}')
        if ctx:
            print(f'        …{ctx}…')
    if len(hits) > limit:
        print(f'  （另有 {len(hits) - limit} 处未列出）')


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    files = book_files()
    n = wordcount(files)
    print(f'扫描书稿 {len(files)} 个文件，汉字 {n} 字')

    checks = [
        ('quotes', '一校 · 散文层引号未转中文', chk_quotes),
        ('punct', '一校 · 散文层半角标点', chk_halfwidth_punct),
        ('paren', '一校 · 散文层半角括号', chk_halfwidth_paren),
        ('dupe', '一校 · 重复标点', chk_dupe_punct),
        ('num', '二校 · 数字用法（GB/T 15835）', chk_numbers),
        ('term', '二校 · 术语口径（待判清单，需人工裁决，不计入差错率）', chk_term),
        ('xref', '二校 · 交叉引用解析', chk_xrefs),
        ('preview', '二校 · 下一章预告标题对齐', chk_preview),
        ('tiers', '二校 · 未映射符号（成品会缺字）', chk_unmapped_emoji),
        ('art', '三校 · ASCII 框图竖线（源稿定位，可能有假阳性）', chk_ascii_art),
        ('boxes', '三校 · ASCII 框图歪墙（成品级，权威判据）', chk_boxes_pdf),
        ('banned', '终审 · 广告法违禁词（已分语境）', chk_banned),
    ]
    total = 0
    # 违禁词属合规红线（另表统计）；art 为定位用、有假阳性；
    # term 是「待判清单」——该判据明确不做猜测性自动判错，命中不等于差错，
    # 必须由审校人逐条裁决后才计入（本轮 5 处已裁决为 git tag 正当用法）。
    not_counted = {'banned', 'art', 'term'}
    pdf = ROOT / 'output' / 'git-concept-map-full.pdf'
    for key, title, fn in checks:
        if only and key != only:
            continue
        if key == 'boxes':
            hits = fn(pdf) if pdf.exists() else []
        elif key == 'tiers':
            hits = chk_unmapped_emoji(files, pdf if pdf.exists() else None)
        else:
            hits = fn(files)
        if key not in not_counted:
            total += len(hits)
        report(title, hits)

    if not only:
        brk, risky = banned_breakdown(files)
        print(f'\n### 终审 · 广告法红线分语境归类：共 {sum(brk.values())} 处命中')
        for k in sorted(brk, key=lambda x: -brk[x]):
            print(f'  {k:<22}{brk[k]:>4} 处')
        print(f'\n  其中「★风险」需处理 {len(risky)} 处：')
        for f, ln, w, ctx in risky:
            print(f'    {f}:{ln}  「{w}」  …{ctx}…')

        print(f'\n===== 汇总 =====')
        print(f'编校类差错（不含违禁词分类）合计 {total} 处')
        print(f'估算编校差错率 = {total} ÷ {n} 字 = {total / n * 10000:.2f}/10000'
              f'  （合格线 ≤1.00/10000）')


if __name__ == '__main__':
    main()
