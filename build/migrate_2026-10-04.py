#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-04 稿件层批量修订（REVIEW-v3 的 P0-1 / P0-2 / P1-8 / P2-19）。

用法：
    build/.venv/bin/python build/migrate_2026-10-04.py            # dry-run
    build/.venv/bin/python build/migrate_2026-10-04.py --apply    # 写入

规则
----
1) 围栏内：`\\"` -> `"`；若该行是散文/ASCII 图说明行（非 shell 命令行）且引号成对，
   转中文 `“ ”`；git/gh/echo 等命令行保持 ASCII。
2) 行内代码 `...`：只做 `\\"` -> `"`，引号保持 ASCII。
3) 散文：`\\"` -> `"`；成对 `"` -> `“ ”`，成对 `'` -> `‘ ’`（跳过英文撇号）。
   优先整块配对；整块奇数时退化为逐行配对，仍奇数则跳过并告警。
4) 散文里夹在中文/引号与中文之间的半角 `,` -> `，`。
5) 术语「标签」越界三处。
6) 三大典型误解：`**误解N：\"…\"**` 形态 -> `N. **\"…\"** ——驳斥`。
"""
import re
import sys
from pathlib import Path

APPLY = '--apply' in sys.argv
ROOT = Path(__file__).resolve().parent.parent
M = ROOT / 'manuscript'
FILES = sorted(M.glob('ch*.md')) + sorted(M.glob('appendix-*.md'))
assert len(FILES) == 19, f'expect 19, got {len(FILES)}'

FENCE = re.compile(r'^```([\w+#.\-]*)')

# 逐字保留语义的围栏语言：其内容属「文件/配置/源码原文」，引号必须保持 ASCII。
# 反例（本次核查发现）：ch04 ```` ```ini ```` 里 `[remote "origin"]` 是 .git/config
# 的真实内容，改成中文引号即为事实错误。
VERBATIM_LANG = {
    'ini', 'toml', 'yaml', 'yml', 'json', 'jsonc', 'xml', 'properties', 'gitconfig',
    'py', 'python', 'js', 'javascript', 'ts', 'typescript', 'tsx', 'jsx', 'rb', 'ruby',
    'php', 'go', 'rust', 'java', 'kt', 'c', 'cpp', 'c++', 'cs', 'swift', 'sh', 'bash',
    'zsh', 'fish', 'console', 'shell', 'diff', 'patch', 'html', 'css', 'scss', 'sql',
    'make', 'makefile', 'dockerfile', 'csv', 'tsv',
}

CMD_LINE = re.compile(
    r'^[\s│├└┌─┬┴┼•>*\-]*('
    r'git|gh|npm|npx|pnpm|yarn|python3?|pip|echo|curl|wget|ssh|gpg|openssl|'
    r'cat|ls|cd|mkdir|rm|mv|cp|chmod|node|export|jq|sed|awk|docker|brew|bash|sh|'
    r'pre-commit|husky|lefthook|gitleaks|trufflehog|gcloud|aws|kubectl)\b')
INLINE_CODE = re.compile(r'`[^`\n]*`')

rep = {k: 0 for k in ('fence_bs', 'fence_quote', 'fence_skip', 'fence_prime', 'inline_bs',
                      'prose_bs', 'dq', 'sq', 'prime', 'lit', 'comma', 'term', 'mis', 'block')}
samp = {k: [] for k in ('fence_quote', 'fence_skip', 'fence_prime', 'prime',
                        'lit', 'comma', 'mis', 'term', 'warn')}


def wide(s):
    """含 CJK / 全角字符即为「中文语境」行。"""
    return any(ord(c) > 0x2E80 for c in s)


PRIME = '\u2032'
# 成对引号（`‘…’` 或 `'…'`）——靠「左引号前面不是 ASCII 字母数字」来识别，先保护起来。
PAIR_HARD = re.compile(r"(?<![A-Za-z0-9])\u2018[^\u2018\u2019\n]*\u2019")
PAIR_SOFT = re.compile(r"(?<![A-Za-z0-9])'[^'\n]*'")
# 落到这里的就是「撇号 prime」：紧跟在 ASCII 字母数字后，且后面不再接 ASCII 字母数字。
# 例：X‘ / X’ / (X') / X1'-X3' 都是「X 的重放副本」；而 O'Reilly 的 ' 后面跟着 R，不匹配。
PRIME_CAND = re.compile(r"(?<=[A-Za-z0-9])['\u2018\u2019](?!\s*[A-Za-z0-9])")


def fix_primes(text):
    """把当作「重音符」用的引号统一成 U+2032 PRIME，返回 (新文本, 替换数)。"""
    spans = []

    def stash(m):
        spans.append(m.group(0))
        return f'\x01{len(spans) - 1}\x01'
    text = PAIR_HARD.sub(stash, text)
    text = PAIR_SOFT.sub(stash, text)
    text, n = PRIME_CAND.subn(PRIME, text)
    text = re.sub(r'\x01(\d+)\x01', lambda m: spans[int(m.group(1))], text)
    return text, n



def pair_q(s, q):
    left, right = ('“', '”') if q == '"' else ('‘', '’')
    out, n = [], 0
    for ch in s:
        if ch == q:
            out.append(left if n % 2 == 0 else right)
            n += 1
        else:
            out.append(ch)
    return ''.join(out), n


def single_ok(s):
    """单引号：只处理非英文撇号的那些，返回 (新串, 替换数)。"""
    res, i, n = [], 0, 0
    while i < len(s):
        c = s[i]
        if c == "'":
            prev = s[i - 1] if i > 0 else ' '
            nxt = s[i + 1] if i + 1 < len(s) else ' '
            if prev.isascii() and prev.isalnum() and nxt.isascii() and nxt.isalnum():
                res.append(c)
            else:
                res.append('‘' if n % 2 == 0 else '’')
                n += 1
        else:
            res.append(c)
        i += 1
    return ''.join(res), n


def convert_block(block):
    """返回 (新文本, 双引号替换数, 单引号替换数)。"""
    dq = block.count('"')
    if dq and dq % 2 == 0:
        block, n1 = pair_q(block, '"')
    else:
        n1 = 0
        if dq:
            lines = block.split('\n')
            for j, ln in enumerate(lines):
                if ln.count('"') and ln.count('"') % 2 == 0:
                    lines[j], k = pair_q(ln, '"')
                    n1 += k
                elif ln.count('"'):
                    samp['warn'].append(ln.strip()[:80])
            block = '\n'.join(lines)
    block, n2 = single_ok(block)
    return block, n1, n2


def convert_prose(text):
    text = text.replace('\\"', '"')
    text = text.replace("\\'", "'")
    parts = re.split(r'(\n\s*\n)', text)
    out = []
    for part in parts:
        if not part or re.fullmatch(r'\n\s*\n', part):
            out.append(part)
            continue
        part, n1, n2 = convert_block(part)
        rep['dq'] += n1
        rep['sq'] += n2
        out.append(part)
    text = ''.join(out)

    text, np = fix_primes(text)
    rep['prime'] += np

    def comma_fix(m):
        rep['comma'] += 1
        if len(samp['comma']) < 40:
            samp['comma'].append(m.group(0))
        return m.group(1) + '，' + m.group(2)
    return re.sub(r"([\u4e00-\u9fff'\"”’]),([\u4e00-\u9fff])", comma_fix, text)


def process(text):
    lines = text.split('\n')
    out, infence, flang, buf = [], False, '', []

    def flush():
        if not buf:
            return
        chunk = '\n'.join(buf)
        rep['prose_bs'] += chunk.count('\\"') + chunk.count("\\'")
        spans = []

        def stash(m):
            spans.append(m.group(0).replace('\\"', '"').replace("\\'", "'"))
            return f'\x00{len(spans) - 1}\x00'
        rep['inline_bs'] += sum(s.count('\\"') + s.count("\\'")
                                for s in INLINE_CODE.findall(chunk))
        masked = INLINE_CODE.sub(stash, chunk)
        masked = convert_prose(masked)
        out.append(re.sub(r'\x00(\d+)\x00', lambda m: spans[int(m.group(1))], masked))
        buf.clear()

    for line in lines:
        m = FENCE.match(line)
        if m:
            flush()
            if infence:
                infence, flang = False, ''
            else:
                infence, flang = True, m.group(1).lower()
            out.append(line)
            continue
        if infence:
            escaped = '\\"' in line or "\\'" in line
            if escaped:
                rep['fence_bs'] += line.count('\\"') + line.count("\\'")
                line = line.replace('\\"', '"').replace("\\'", "'")
            # 引号转中文的条件：本行是中文语境（或作者原本就写了转义引号），
            # 且所属围栏不是「配置/源码原文」语言，且不是 shell 命令行。
            if ('"' in line and line.count('"') % 2 == 0
                    and not CMD_LINE.match(line)
                    and (escaped or (wide(line) and flang not in VERBATIM_LANG))):
                line, n = pair_q(line, '"')
                rep['fence_quote'] += n
                if n and len(samp['fence_quote']) < 40:
                    samp['fence_quote'].append(line.strip()[:90])
            elif '"' in line and line.count('"') % 2 == 0 and not CMD_LINE.match(line):
                rep['fence_skip'] += 1
                if len(samp['fence_skip']) < 40:
                    samp['fence_skip'].append(f'[{flang or "-":8s}] {line.strip()[:76]}')
            # 围栏内的重音符（如 ASCII 图里的 (X') / (BC')）
            line, np = fix_primes(line)
            if np:
                rep['fence_prime'] += np
                if len(samp['fence_prime']) < 30:
                    samp['fence_prime'].append(line.strip()[:88])
            out.append(line)
        elif line.strip() == '':
            flush()
            out.append(line)
        else:
            buf.append(line)
    flush()
    return '\n'.join(out)


TERM_FIX = [
    ('**给 AI 的 PR 打标签**', '**给 AI 提交的 PR 加标记**'),
    ('两个 Chrome 标签页', '两个浏览器选项卡'),
    ('（both modified 之类的标签）', '（both modified 之类的状态标记）'),
]

# 一次性字面修正（都只有 1 处，逐条可回溯）
LITERAL_FIX = [
    # ch05 §5.x：`B‘、C'D’` 里的 ASCII 引号夹在两字母之间，被撇号规则跳过；补成全 PRIME。
    ("C'D\u2032", 'C\u2032D\u2032'),
    # 附录 D：O'Reilly 是品牌名，撇号本该是弯的（U+2019），不是重音符。
    ("O'Reilly", 'O\u2019Reilly'),
]

# 全稿唯一的引号不平衡块（ch04 §4.x 别名表）：删掉 origin 后那个多余的引号，
# 让该条与下一条同构（都是「整句引述」）。
BLOCK_FIX = [
    ('**"origin"这个别名，对应的 URL 是这个。',
     '**"origin 这个别名，对应的 URL 是这个。'),
]

MIS_RE = re.compile(r'^\*\*误解([一二三])：(.+?)\*\*\n((?:(?!\n\s*\n).)*)', re.M | re.S)
NUM = {'一': '1', '二': '2', '三': '3'}


def mis_sub(m):
    label, quote, body = m.group(1), m.group(2), m.group(3).strip()
    body = re.sub(r'^——\s*', '', body)
    rep['mis'] += 1
    if len(samp['mis']) < 30:
        samp['mis'].append(f'{NUM[label]}. **{quote[:30]}** ——{body[:24]}')
    return f'{NUM[label]}. **{quote}** ——{body}\n'


changed = []
for path in FILES:
    orig = path.read_text(encoding='utf-8')
    pre = orig
    for a, b in BLOCK_FIX:
        if a in pre:
            pre = pre.replace(a, b)
            rep['block'] += 1
    text = process(pre)
    for a, b in LITERAL_FIX:
        if a in text:
            text = text.replace(a, b)
            rep['lit'] += 1
            samp['lit'].append(f'{path.name}: {a}  ->  {b}')
    for a, b in TERM_FIX:
        if a in text:
            text = text.replace(a, b)
            rep['term'] += 1
            samp['term'].append(f'{path.name}: {a}  ->  {b}')
    text = MIS_RE.sub(mis_sub, text)
    if text != orig:
        changed.append(path.name)
        if APPLY:
            path.write_text(text, encoding='utf-8')

print('=========== 统计 ===========')
for k, v in rep.items():
    print(f'  {k:12s} {v}')
print(f'  改动文件数    {len(changed)}')
print('模式:', 'APPLY（已写入）' if APPLY else 'DRY-RUN（未写入）')
for k in ('fence_quote', 'fence_skip', 'fence_prime', 'prime', 'lit',
          'comma', 'mis', 'term', 'warn'):
    if samp[k]:
        print(f'\n--- {k}（{len(samp[k])}）---')
        for s in samp[k][:30]:
            print('   ', s)
