#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三批修订（收尾）：清掉散文层残留的 4 处半角括号 / 括号错配。

所有条目均为「唯一命中」校验通过后才写入，任何一条不唯一立即中止、不落盘。
幂等：已修过的条目再次运行会被识别为「已应用」并跳过。

用法：
    python build/revision_v5c.py --check   # 只校验
    python build/revision_v5c.py           # 校验并写入
"""
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MS = ROOT / 'manuscript'

# (文件, 标签, 旧串, 新串)
EDITS = [
    ('ch06-commit-craft.md', '提示词内半角括号→全角（与附录 B.2.12 归一）',
     '> “把最近 10 颗提交 (`git log -10 --pretty=fuller --stat`) 拿去审阅。对每一颗告诉我：',
     '> “把最近 10 颗提交（`git log -10 --pretty=fuller --stat`）拿去审阅。对每一颗告诉我：'),

    ('ch13-advanced.md', '半角左括号配全角右括号（错配）',
     '- 「当前 HEAD 距离最近的 tag 有多少颗 commit？(`git describe` 的语义)。如果我现在打 tag，按语义化版本推断，下一个版本号应该是什么？」',
     '- 「当前 HEAD 距离最近的 tag 有多少颗 commit？（`git describe` 的语义）。如果我现在打 tag，按语义化版本推断，下一个版本号应该是什么？」'),

    ('ch05-history.md', '(b) 半角，与前半句（a）错配；顺带去掉全角括号两侧空格',
     '假设 （a） 这条分支只有我一个人：用什么撤销？为什么？(b) 这条分支已经推到远端',
     '假设（a）这条分支只有我一个人：用什么撤销？为什么？（b）这条分支已经推到远端'),

    ('appendix-c-glossary.md', '术语条目内 (1)(2) 半角序号→全角',
     '看语境——(1) 分支的“上游跟踪目标”，即 `branch.<name>.remote` + `branch.<name>.merge`；(2) fork 场景下',
     '看语境——（1）分支的“上游跟踪目标”，即 `branch.<name>.remote` + `branch.<name>.merge`；（2）fork 场景下'),
]


def main():
    check_only = '--check' in sys.argv
    contents, pending, done, bad = {}, [], [], []
    for f, lab, old, new in EDITS:
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
        print('SKIP %-28s 已应用' % f, lab)
    if not pending:
        print('无待写入条目（全部已应用）')
        return
    if check_only:
        print('校验通过：%d 条待写入（未写入）' % len(pending))
        return

    for f, lab, old, new in pending:
        contents[f] = contents[f].replace(old, new, 1)
        print('OK   %-28s %s' % (f, lab))
    for f in sorted(contents):
        io.open(MS / f, 'w', encoding='utf-8').write(contents[f])
    print('DONE %d edits across %d files' % (len(pending), len(set(f for f, _, _, _ in pending))))


if __name__ == '__main__':
    main()
