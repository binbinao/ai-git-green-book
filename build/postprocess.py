#!/usr/bin/env python3
"""后处理：组装最终 typst 文件（前置页 + 正文）。"""
import re
from pathlib import Path

build = Path(__file__).parent
tpl = (build / 'book.typ').read_text(encoding='utf-8')
body = (build / 'book-body.typ').read_text(encoding='utf-8')
body = body.replace('#cite(<小李>, form: "prose")', '小李')
body = body.replace('#cite(<小王>, form: "prose")', '小王')
body = body.replace('#cite(<Bob>, form: "prose")', 'Bob')
body = re.sub(r'#cite\(<([^>]+)>, form: "prose"\)', r'\1', body)  # 兜底

# 变体选择符 U+FE0F（emoji presentation selector）：源稿里 `⚠️` 是 U+26A0 + U+FE0F。
# emoji 已由 book.typ 的 show rule 换成矢量/文字符号（P1-7），这个选择符只剩一个
# 无主字形，会让 `#show "⚠"` 的匹配落空并可能印出空框 —— 统一剥掉。
body = body.replace('\ufe0f', '')
body = body.replace('\u200d', '')   # 零宽连接符同理

# ---------------------------------------------------------------------------
# 行首禁则（P2-17）：破折号「——」不得落在行首
#
# 背景：源稿写的是 U+2014 ×2，pandoc 的 typst writer 把它转写成 Typst 的智能
# 破折号语法 `------`（每个 U+2014 → `---`），渲染仍是「——」，所以 PDF 里的
# 破折号本身没问题 —— 有问题的是它前后允许断行。
#
# 实测（/tmp 最小复现：6 种分隔符 × 22 个前缀长度样本，版心 74mm 逼出断行）：
#     分隔符            行首破折号
#     半角空格 ' '          4    ← 断
#     无分隔符  ''          2    ← 断（Typst 的 em dash 本身就带断行机会）
#     全角空格 U+3000       5    ← 断
#     NBSP U+00A0           0    ← 不断，但**有可见宽度**，会印进一个空格
#     WORD JOINER U+2060    0    ← 不断，且零宽度  ✅
# 可见：仅"删掉空格"不够（无分隔符照样断），必须显式绑定前字 —— 这也正是
# REVIEW 建议的「`——` 前加 no-break」。
#
# 只处理围栏代码块与行内代码之外的正文：WJ 虽不可见，但一旦混进命令里，
# 读者复制粘贴时就会带出一个不可见字符。
# ---------------------------------------------------------------------------
WJ = '\u2060'

# ---- 行首/行末禁则：只补「引擎管不到的那一类边界」 ----
# Typst 依 Unicode UAX#14 断行：LB13「不在收尾标点前断」保证 、。，；：？！」』 等不会
# 落到行首，LB14「不在开括号后断」保证 （《「 等不会落到行末。**纯中文语境下引擎
# 自己就排得对**（最小复现 /tmp/kinsoku_probe：29 变体 × 版心逼断 → 0 违规）。
#
# 引擎管不到的是**行内代码边界**：行内代码在 Typst 里是 `raw` 生成的原子盒
# （`box()` 装箱，见 book.typ 的 code-inline），盒子内部不参与断行，于是
# 「盒子 → 全角标点」这个接缝上的断行机会不受 UAX#14 约束。
#
# 实测（把 KINSOKU_HEAD/TAIL 全部清空后重建，QA 逐页归并行判定）：
#     全书只剩 3 处违规，**全部**是「行内代码紧邻全角标点」：
#       p261 行末「（」   .git/rebase-merge/（      ← 代码后接前括号
#       p499 行首「；」   ；（4）git add package-lock.json。
#       p528 行首「：」   ：只挪分支书签，工作区和暂存区不变；
# 反之，按之前"见标点就插"的写法，全书要插约 6000 个不可见 U+2060
# （其中「（」后 1943 处、「：」前 1205 处）——用 6000 个字符去堵 3 个洞，
# 代价是 PDF 文本层里「图 0-1␣：」「（Repository）」「分支␣：只是一张会移动的
# 名牌」全部变成**搜不到、复制带隐含字符**。
#
# 因此收窄判据：只有当标点的**前一字**是行内代码的收尾反引号或拉丁 token
# （即跨了「代码盒 / 拉丁 → 全角标点」这条接缝）时才插 WJ。
KINSOKU_HEAD = '；：…'      # 不得落行首
KINSOKU_TAIL = '（'          # 不得落行末


def _need_bind(prev):
    """前一字是否处于「行内代码盒」的右端接缝。

    判据来自实测（见上方常量区注释）：清空禁则集合后全书只剩 3 处违规，
    3 处的**前一字全部是收尾反引号**（行内代码在 typ 源码里就是 `` `...` ``，
    这是 raw 原子盒的右边界）。
    **不要**把 `]` 或拉丁字符算进来：
      · `]` —— pandoc 把 `**粗体**` 输出成 `#strong[...]`，星号加粗的右边界也是
        `]`，但 strong 只改字重、不是原子盒，接缝处断行完全正常。早先误把 `]`
        计入，凭空多插 1205 个 WJ，既无用又污染文本层。
      · 拉丁字符 —— 「Latin → 全角标点」已由 UAX#14 与 cjk-latin-spacing: none
        共同覆盖（最小复现 B 组 29 个变体：0 违规），无需再绑。
    """
    return prev == '`'


def protect_kinsoku(text):
    out, infence = [], False
    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            infence = not infence
            out.append(line)
            continue
        if infence:
            out.append(line)
            continue
        keep = bytearray(len(line))              # 受保护区间掩码
        # ① 行内代码 `...`
        # ② Typst 标签 <...>（pandoc 由标题文本生成），里面出现 `---` 时
        #    若插进 WJ 会变成 `unclosed label` 编译错误
        for pat in (r'`[^`]*`', r'<[^<>\s]*>'):
            for m in re.finditer(pat, line):
                for i in range(m.start(), m.end()):
                    keep[i] = 1
        res = []
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            if not keep[i]:
                # 破折号序列（pandoc 把 U+2014 写成 `---`）：绑到前一个字上
                if ch == '-' and (i == 0 or line[i - 1] != '-'):
                    j = i
                    while j < n and line[j] == '-':
                        j += 1
                    if j - i >= 3 and not any(keep[i:j]):
                        res.append(WJ)
                        res.append(line[i:j])
                        i = j
                        continue
                # 行首禁则：把标点绑到前一个字上。
                # 只在「代码盒 / 拉丁 → 标点」的接缝上做：纯中文段落由 Typst 的
                # UAX#14 断行自己保证（见上方常量区注释）。
                # 注意不要检查 keep[i-1]：行内代码的掩码包含**闭合反引号**，而
                # 「`...package-lock.json`；（2）…」这种写法恰恰要求把 WJ 插在
                # 反引号与 `；` 之间 —— 检查 keep[i-1] 会让这一类全部漏掉
                # （实测 p255 的 `；` 就是这么漏下来的）。
                if ch in KINSOKU_HEAD and i > 0 \
                        and line[i - 1] not in ' \u2060' and _need_bind(line[i - 1]):
                    res.append(WJ)
                # 行末禁则：把标点绑到后一个字上（同样只在代码/拉丁接缝上做）
                elif ch in KINSOKU_TAIL and i + 1 < n and keep[i + 1] == 0 \
                        and line[i + 1] not in ' \u2060' \
                        and (i == 0 or line[i - 1] not in ' \u2060') \
                        and _need_bind(line[i - 1] if i > 0 else ''):
                    res.append(ch)
                    res.append(WJ)
                    i += 1
                    continue
            res.append(ch)
            i += 1
        out.append(''.join(res))
    return '\n'.join(out)


_dash_seq = len(re.findall(r'-{3,}', body))
body = protect_kinsoku(body)
_wj = body.count(WJ)
print(f'  行首/行末禁则：插入 U+2060 WORD JOINER {_wj} 处（破折号序列 {_dash_seq} 处一并覆盖）')

# 表格列宽改写：pandoc 等宽百分比列 → 类型感知 fr 权重
# fr 保证表格永不横向溢出版心；权重按表头语义分配：
#   透视表（你说的话…）：短引语 / 命令 / 长说明 = 1.15 / 1.15 / 1.7
#   命令表（命令…）：emoji+命令 / 概念语义 / 口语 = auto / 1.5 / 1.7
#   其余三列表：auto 首列 + 均衡权重
def rewrite_tables(text):
    text = text.replace('columns: (33.33%, 33.33%, 33.33%)', 'columns: (1.15fr, 1.15fr, 1.7fr)')
    text = text.replace('columns: (25%, 25%, 25%, 25%)', 'columns: (1fr, 1fr, 1.2fr, 1.3fr)')
    text = text.replace('columns: (20%, 20%, 20%, 20%, 20%)', 'columns: (1fr, 1fr, 1fr, 1fr, 1fr)')
    text = text.replace('columns: (50%, 50%)', 'columns: (1fr, 1fr)')
    return text

body = rewrite_tables(body)

# 剥掉表格的 figure 壳与 center 包裹（figure 不可跨页致页尾重叠；align(center) 让列宽错误收缩）
body = body.replace('#figure(\n  align(center)[#table(', '#table(\n ')
body = re.sub(r'\n  \)\]\n  , kind: table\n  \)', '\n  )', body)

# 三列表按表头细分：命令表首列放命令、语义列放说明，权重略调。
# ⚠ 这个函数只允许返回 `columns: (...)` 这一小段 —— 调用方是
#      lambda m: retbl3(m) + m.group(1)
#   group(1) 是「columns 之后直到 table.header(...) 为止」的尾巴。若这里返回
#   m.group(0)（整个匹配，含尾巴），结果就会变成 [columns+尾巴] + [尾巴]，
#   于是 typst 源码里出现重复的 `align: (...), table.header(...),` 与多余的
#   逗号（`),,`），编译直接报 unexpected comma / duplicate argument: align。
def retbl3(m):
    head = m.group(1)
    # 判据必须是「表头第一格就是命令列」——否则像
    #   table.header([你说的话（或执行的命令）], [命令], [文件系统/仓库里的真实变化])
    # 这种透视表也会被误判（它的第二格才含「命令」二字）。
    if 'table.header([命令' in head:
        return 'columns: (1.2fr, 1.4fr, 1.4fr)'
    return 'columns: (1.15fr, 1.15fr, 1.7fr)'

body = re.sub(
    r'columns: \(1\.15fr, 1\.15fr, 1\.7fr\)(.{0,400}?table\.header\((.*?)\)\,)',
    lambda m: retbl3(m) + m.group(1),
    body, flags=re.S)


# ============================================================
# 列宽按内容重分配（REVIEW-v4 §6.3 问题 A）
# ------------------------------------------------------------
# 上面的 rewrite_tables / retbl3 是按「表头语义」写死的固定比例族：
#     (1.15, 1.15, 1.7) / (1.2, 1.4, 1.4) / (1, 1, 1.2, 1.3) / (1, 1, 1, 1, 1)
# 同一族里所有表共用一个比例，于是内容短的第一列白占宽度、内容长的列被挤窄，
# 实测有 8 张表的最窄列只有 24–26.7mm，把命令与术语折断
# （`git reset --soft C` 折 2 行、`Trunk-Based` 折成 `Trunk-`/`Based`、
#   `add/rm/rename` 折成 `add/rm/`/`rename`）。
#
# 两个量缺一不可：
#   need = 该列最长**不可断词元**（按空格切）的 pt 宽度 —— 硬下界，决定"词元不许被劈开"
#   want = 该列最长单元格整宽的约一半 —— 目标宽，决定"长句不至于折成 4–5 行"
# 只做**转移**：从有余量的列搬到有缺口的列，且捐赠列
#   ① 最多让出自身宽度的 15%，② **永不低于自身 need × 1.15**
# 于是"含长命令/长路径的列"天然只当受赠方、不当捐赠方 → P1-13 不会退化。
# 这条约束是实测买来的：早先"只按字符数加权"的版本把代码列抽薄，
# P1-13（表内 token 断在 "-"）从 0 行回退到 16 行。
# fr 单位保证表格永不横向溢出版心。
# ============================================================
PT_PER_UNIT = 4.5        # 9pt 正文下 1 显示单位 ≈ 4.5pt
TABLE_PT = 340.16        # 版心宽 120mm = 340.16pt
MIN_COL_PT = 32 / 25.4 * 72   # 32mm —— 只对"最窄列 < 32mm"的表动手
CELL_INSET = 12.0        # 单元格左右各 6pt
SAFE_MARGIN = 1.15       # 列宽硬下界系数
MAX_DONATE = 0.15        # 单列最多让出的自身宽度比例
WANT_SHARE = 0.5         # 目标宽 = 最长单元格宽 × 0.5（约容两行）
MAX_RATIO = 2.6


def _units(s):
    """显示宽度：全角/中日韩 = 2，其余 = 1（与 archify textUnits 同口径）。"""
    n = 0
    for ch in s:
        cp = ord(ch)
        n += 2 if (0x2E80 <= cp <= 0xA4CF or 0xAC00 <= cp <= 0xD7A3
                   or 0xF900 <= cp <= 0xFAFF or 0xFE30 <= cp <= 0xFE4F
                   or 0xFF00 <= cp <= 0xFF60 or 0xFFE0 <= cp <= 0xFFE6
                   or 0x3000 <= cp <= 0x303F) else 1
    return n


def _visible(cell):
    """把 typst 单元格源码还原成肉眼可见文本，用于量宽。"""
    s = re.sub(r'#[A-Za-z][\w.]*(\([^()]*\))?', ' ', cell)   # 去掉 #strong / #link(...) 之类
    s = s.replace('[', ' ').replace(']', ' ')
    s = re.sub(r'[*_`\\]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def _split_top(s, sep=','):
    """按顶层分隔符切分，忽略 () [] {} 内部的分隔符。"""
    out, depth, cur = [], 0, []
    for ch in s:
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        if ch == sep and depth == 0:
            out.append(''.join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append(''.join(cur))
    return out


def _table_bounds(text):
    for m in re.finditer(r'#table\(', text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield m.start(), m.end() - 1, i + 1


SKIP = re.compile(r'^(columns|align|stroke|gutter|inset|column-gutter|row-gutter)\s*:')


def redistribute_columns(text):
    out, prev, changed, skipped = [], 0, 0, 0
    for _s, inner_s, inner_e in _table_bounds(text):
        inner = text[inner_s + 1:inner_e - 1]
        args = _split_top(inner)
        ncol = None
        old = None
        cells, head = [], []
        for a in args:
            t = a.strip()
            if t.startswith('columns:'):
                old = t
                ncol = len(_split_top(t[len('columns:'):].strip().strip('()')))
            elif SKIP.match(t) or t.startswith('table.hline') or t == '':
                continue
            elif t.startswith('table.header'):
                head = [c for c in _split_top(t[t.index('(') + 1:t.rindex(')')]) if c.strip()]
            elif t.startswith('['):
                cells.append(t)
        if not ncol or not cells:
            skipped += 1
            continue
        rows = [cells[i:i + ncol] for i in range(0, len(cells), ncol)]
        need, want = [], []
        for j in range(ncol):
            col = [r[j] for r in rows if j < len(r)] + ([head[j]] if j < len(head) else [])
            tok = cellmax = 1
            for c in col:
                vis = _visible(c)
                cellmax = max(cellmax, _units(vis))
                for piece in vis.split(' '):
                    tok = max(tok, _units(piece))
            need.append(tok * PT_PER_UNIT * SAFE_MARGIN + CELL_INSET)
            want.append(cellmax * PT_PER_UNIT * WANT_SHARE + CELL_INSET)

        vals = [float(x) for x in re.findall(r'([\d.]+)fr', old or '')] or [1.0] * ncol
        if len(vals) != ncol:
            vals = [1.0] * ncol
        base_w = [v / sum(vals) * TABLE_PT for v in vals]
        # 只动 REVIEW-v4 §6.3 点名的那一类表：**存在 <32mm 窄列**的表。
        # 34.5mm 以上的列本来就有 40mm 上下，不存在"被折断"的问题；
        # 去动它们只会白改列比、让文本重排，实测就是这样在别处挤出 1 处
        # 「行尾断在 '-'」（p78 那张 3 列表，问题词元在**变宽**的列里，
        #  与抽薄无关，纯粹是断行点漂移）。缩小改动面 = 缩小回归面。
        if min(base_w) >= MIN_COL_PT:
            skipped += 1
            continue
        w = list(base_w)
        # 捐赠上限：既受 15% 约束，也受「不低于自身 need×1.15」约束
        floor = [max(need[j] * 1.15, base_w[j] * (1 - MAX_DONATE)) for j in range(ncol)]
        for _step in range(ncol * 3):
            surplus = [w[j] - floor[j] for j in range(ncol)]
            deficit = [min(want[j], need[j] * 1.8) - w[j] for j in range(ncol)]
            d_i = max(range(ncol), key=lambda j: deficit[j])
            s_i = max(range(ncol), key=lambda j: surplus[j])
            amount = min(surplus[s_i], deficit[d_i])
            if amount <= 0.5 or deficit[d_i] <= 0.5:
                break
            w[s_i] -= amount
            w[d_i] += amount

        mean = sum(w) / ncol
        w = [min(x, mean * MAX_RATIO) for x in w]
        if all(abs(w[j] - base_w[j]) < 1.0 for j in range(ncol)):
            continue                     # 无需改动（多数表走到这里 → 零风险）
        new = 'columns: (' + ', '.join(f'{x:.2f}fr' for x in w) + ')'
        if old.strip() == new:
            continue
        out.append(text[prev:inner_s + 1])
        out.append(inner.replace(old, new, 1))
        prev = inner_e - 1
        changed += 1
    out.append(text[prev:])
    print(f'  表格列宽按内容重分配：改写 {changed} 张，'
          f'跳过 {skipped} 张（最窄列已 ≥32mm，无需动）')
    return ''.join(out)


# 开关：实测第一版（只按字符数加权）会让代码列变窄，P1-13 从 0 行回退到 16 行；
# 改成"带 need 下界 + 单列最多让 15%"的转移版后，代码列只会受赠不会捐赠 → 可开。
APPLY_COLUMN_REDISTRIBUTION = True
if APPLY_COLUMN_REDISTRIBUTION:
    body = redistribute_columns(body)

# h1 结构化：章号/类型预解析（typst 字符串 API 按字节切中文易错，数据准备归 Python）
CH_RE = re.compile(r'^= (第\s*([0-9]+)\s*章)[　\s]+(.+)$')
AP_RE = re.compile(r'^= (附录)\s*([A-D])[　\s·]+(.+)$')

def parse_h1(line):
    m = CH_RE.match(line)
    if m:
        return f'#chapter-open(num: "{m.group(2)}", label: "{m.group(1)}", title: "{m.group(3)}", kind: "ch")'
    m = AP_RE.match(line)
    if m:
        return f'#chapter-open(num: "{m.group(2)}", label: "{m.group(1)} {m.group(2)}", title: "{m.group(3)}", kind: "ap")'
    return line



# ---------------------------------------------------------------------------
# 表头保留（P1-11 根因修复）
# 旧实现是一行「去重」：
#     body = re.sub(r',\s*align: \([^)]+\),\s*table\.header\([^)]*\),', ',', body)
# 它实测命中全部 44 张表 —— pandoc 对每个 pipe table 只输出一个 table.header()，
# 本来就不存在"重复"可去。该正则把 table.header([...]) 连同表头文字整段删掉，
# 于是书里每张表都"没有表头行"（表头单元格被删，不是没上底色）。
# 后果：列义丢失，且 book.typ 里 `#show table.cell` 的 y==0 深青表头样式失去作用对象。
# 结论：直接不删。表头由 book.typ 的 y==0 规则自动上深青底 + 白字。
# ---------------------------------------------------------------------------
body = re.sub(r'^= .+$', lambda m: parse_h1(m.group(0)), body, flags=re.M)

# ---------------------------------------------------------------------------
# 单一版本源（P1-14）：版本/日期只在 book.typ 的 `meta` 里定义一次，
# 封面、扉页、版权页全部从它取值，避免四处各写一份互相对不上。
# ---------------------------------------------------------------------------
_meta_block = re.search(r'#let meta = \((.*?)\n\)', tpl, re.S)
def _meta_val(key, default=''):
    if not _meta_block:
        return default
    mm = re.search(key + r':\s*"([^"]*)"', _meta_block.group(1))
    return mm.group(1) if mm else default

META_TITLE   = _meta_val('title',   'Git 的概念地图')
META_SUB     = _meta_val('subtitle', '用自然语言驾驭版本控制')
META_AUTHOR  = _meta_val('author',  'binbinao')
META_EDITION = _meta_val('edition', '')
META_DATE    = _meta_val('date',    '')
META_YM      = META_DATE[:7]                    # 2026-10
META_YM_CN   = META_YM.replace('-0', ' 年 ').replace('-1', ' 年 1') + ' 月' if META_YM else ''
# 上面这行对 10-12 月是准确的；直接用手写映射更稳妥：
META_YM_CN = f'{META_DATE[0:4]} 年 {int(META_DATE[5:7])} 月' if len(META_DATE) >= 7 else ''

front = f'''
// ============ 封面：全出血深青底 + 珠链分叉图形 ============
// P0-4：封面书名是最高优先级视觉资产，不接受自动折行摆布 —— 因此
//   1) 关掉全局的 first-line-indent（2em 在 42pt 下就是 84pt，正是把「图」挤下行的元凶）
//   2) 关掉两端对齐（断行后首行会被拉伸，副标题曾经因此出现大空档）
//   3) 主标题包 box（box 内部不可断行），字号与字重下调到 42pt / 700
//      （900 字重时「图」的「囗」部笔画糊成一个反白方块，读者看到的是"补丁"）
//   4) 副标题在「——」处主动断行，「Git 书」做 no-break 绑定
#page(margin: 0mm, header: none, footer: none, fill: rgb("#0F4C5C"))[
  #set align(left)
  #set par(first-line-indent: 0em, justify: false)
  #set text(hyphenate: false, cjk-latin-spacing: none)
  #v(30mm)
  #box(width: 100%, inset: (x: 22mm))[
    // 顶部：品牌标识行
    #box(width: 2.6em, height: 0.55em, fill: rgb("#E8A13D"), outset: (y: 0.3em))
    #h(0.9em)
    #text(font: ("Alibaba PuHuiTi 3.0",), size: 12pt, weight: 600, fill: rgb("#BFD7DD"), tracking: 0.1em)[VERSION CONTROL, CONCEPT-FIRST]
  ]
  #v(1fr)
  // 中部：巨型书名（单行不可断）+ 副题（在 —— 处主动断行）
  #box(width: 100%, inset: (x: 22mm))[
    #text(font: ("Alibaba PuHuiTi 3.0",), size: 42pt, weight: 700, fill: white, tracking: 0.01em)[#box[{META_TITLE}]]
    #v(6mm)
    #box(width: 30%, height: 2.8pt, fill: rgb("#E8A13D"))
    #v(6mm)
    #text(font: ("Songti SC",), size: 16pt, fill: rgb("#DCE9ED"))[用自然语言驾驭版本控制]#linebreak()
    #text(font: ("Songti SC",), size: 16pt, fill: rgb("#DCE9ED"))[—— 一本不背命令的 #box[Git 书]]
  ]
  #v(1fr)
  // 底部：珠链分叉图形（珠子=提交，分叉=分支）
  #box(width: 100%, inset: (x: 22mm))[
    #block(width: 128mm)[
      #v(2mm)
      #grid(
        columns: (1fr,),
        rows: (auto,),
        align(center)[
          #box(width: 128mm, height: 30mm)[
            // 珠链图：主链横穿，一支向上分出
            #place(dx: 0mm, dy: 13mm)[#box(width: 128mm, height: 0.8pt, fill: rgb("#5E8794"))]
            #place(dx: 40mm, dy: 13mm)[#box(width: 0.8pt, height: 9mm, fill: rgb("#5E8794"))]
            #place(dx: 40mm, dy: 4mm)[#box(width: 46mm, height: 0.8pt, fill: rgb("#5E8794"))]
            #place(dx: 86mm, dy: 4mm)[#box(width: 0.8pt, height: 9mm, fill: rgb("#5E8794"))]
            #place(dx: 86mm, dy: 13mm)[#box(width: 0.8pt, height: 0pt)]
            // 珠子：主链 5 颗（琥珀色高亮当前提交）
            #place(dx: 8mm, dy: 13mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
            #place(dx: 26mm, dy: 13mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
            #place(dx: 54mm, dy: 13mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
            #place(dx: 68mm, dy: 13mm - 1.6mm)[#circle(radius: 2.2mm, fill: rgb("#E8A13D"))]
            #place(dx: 96mm, dy: 13mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
            #place(dx: 112mm, dy: 13mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
            // 分支珠子 2 颗
            #place(dx: 40mm, dy: 4mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
            #place(dx: 86mm, dy: 4mm - 1.6mm)[#circle(radius: 1.6mm, fill: white)]
          ]
        ]
      )
    ]
    #v(9mm)
  ]
  #v(6mm)
  // 底部作者行改用 place 绝对定位（封面自查时新发现的问题）。
  // 原先它排在流末尾、前面靠 `#v(1fr)` 撑高：实测两个 1fr 会把"剩余高度"
  // 全部吃光，于是末尾那个 `#v(6mm)` 被挤出页面 —— 作者行的 baseline 精确落在
  // 702.99pt（= 页高 248mm），字形整个沉到页外，渲染出来是被裁掉一半。
  // 定位后它不再参与 fr 分配，距底边固定 15mm。
  #place(bottom + center, dy: -15mm, box(width: 172mm, inset: (x: 22mm))[
    #text(font: ("Songti SC",), size: 12pt, fill: rgb("#BFD7DD"))[{META_AUTHOR}　著]
    #h(1fr)
    #text(font: ("Alibaba PuHuiTi 3.0",), size: 11pt, fill: rgb("#8FB3BD"))[{META_DATE[:4]}-{META_DATE[5:7]}]
  ])
]


// ============ 扉页 ============
#pagebreak()
#align(center)[
  #set par(first-line-indent: 0em, justify: false)
  #v(10em)
  #text(font: hei, size: 28pt, weight: "bold")[#box[{META_TITLE}]]
  #v(0.8em)
  #text(font: song, size: 13pt, fill: rgb("#444444"))[{META_SUB}]
  #v(16em)
  #text(font: song, size: 12pt)[{META_AUTHOR}　著]
  #v(1em)
  #text(font: song, size: 11pt)[{META_EDITION}· {META_DATE}]
]

// ============ 版权页 ============
#pagebreak()
#align(center)[
  #set par(first-line-indent: 0em)
  #v(20em)
  #text(font: song, size: 10pt, fill: rgb("#666666"))[
    《{META_TITLE}》\\
    {META_AUTHOR} 著\\
    #v(0.5em)
    本作品采用 CC BY-NC-SA 4.0 许可（署名-非商业性-相同方式共享）\\
    转载请注明出处，商用需授权\\
    #v(1em)
    {META_YM_CN} · {META_EDITION}\\
    电子版由本书书稿源文件直接生成
  ]
]

// ============ 目录 ============
#make-toc()

// ============ 正文 ============
'''

out = tpl + '\n' + front + '\n' + '#in-body.update(true)\n\n' + body
(build / 'book-final.typ').write_text(out, encoding='utf-8')
# ---------------------------------------------------------------------------
# 已删除 ch10「archify 优化版」硬注入（P0-3 / P0-6）
# 旧代码把一段自带 caption 的 #image(...) 直接插进第 10 章，caption 是
#     图 10-X：事故恢复决策树（archify 优化版）· 90% 事故停在最左路径
# 三重问题：① 「archify 优化版」是内部制作备注；② 图号写死成 `10-X`，
# 与全书 `图 <章>-<序>` 体系冲突；③ 与源稿里 `![图 10-1：…](figures/…)`
# 正常引入的同一张图重复。ch10 的决策树现由源稿的图片引用统一承担。
# ---------------------------------------------------------------------------

print(f'book-final.typ: {len(out)} chars')
