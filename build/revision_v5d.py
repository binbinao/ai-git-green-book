#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四批修订（合规补注）：为时效性论断补出处，并更正一处事实错误。

边界说明（严格守界）：
  ✓ 本批只做「补来源标注」与「事实更正」——属本轮拍板的无争议项。
  ✗ 不动语气、不做数值降级（如 ch11「80% 不在 diff 里」、ch12「≈99% / 覆盖 80%」
    这类示意数值），那些属改语气，只出 Before→After 示范。

每条均先全校验唯一命中，任一不唯一即中止、不落盘。幂等。

用法：
    python build/revision_v5d.py --check
    python build/revision_v5d.py
"""
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MS = ROOT / 'manuscript'

EDITS = [
    # ---------- 1. Cursor Undo 事故：更正不可考的版本号，改为可考事实 ----------
    ('ch08-worktree.md', 'Cursor 版本号不可考 → 官方论坛可查的事实描述',
     '- **想让多个 AI 并行干活**：`Cursor 2.0 Composer` 多 agent 并行时曾出过“Undo 删档”事故——官方论坛可查的至少两起：2.0.34 的 undo checkpoint 不区分 agent（在 A agent 里 undo 会撤掉所有 agent 的改动）、2.0.77 的 undo apply 会删掉未提交的工作文件——一部分根因就是多 agent 在同一工作目录上互相踩踏。',
     '- **想让多个 AI 并行干活**：**Cursor Agent** 曾出过“Undo 删档”事故——Cursor 官方论坛自 2025 年 7 月起有多起用户报告（涉及 1.3.0、2.4.31、2.4.37 等版本）：点了 Undo 之后，不属于本次改动的文件被一并从磁盘删除，未提交的改动也随之消失；官方 2026 年 1 月回复称根因是 **Agent Review Tab 与文件编辑之间的冲突**，属已知问题。多 agent 在同一工作目录上互相踩踏，会把这类事故的后果放大。'),

    ('ch08-worktree.md', '同上，交叉引用处的版本号同步更正',
     '**Cursor 2.0 Composer 多 agent 并行时曾出过 Undo 操作误删用户工作文件的事故**（官方论坛 2.0.34、2.0.77 两起事故帖，见上文）。',
     '**Cursor Agent 曾出过 Undo 操作误删用户工作文件的事故**（Cursor 官方论坛多起报告，见上文；官方归因为 Agent Review Tab 与文件编辑冲突）。'),

    # ---------- 2. Replit 事件：点名主体 + 给报道出处 ----------
    ('ch00-breaking-the-spell.md', '匿名「一家创业公司」→ 点名主体 + 报道出处',
     '2025 年一家创业公司的 AI 代理在用户明确宣布“代码冻结”之后仍然执行了破坏性操作、抹掉了生产数据库',
     '2025 年 7 月，SaaStr 创始人 Jason Lemkin 公开记录了自己亲历的一次事故：Replit 的 AI 代理在他明确宣布“代码冻结”之后仍然执行了破坏性操作，抹掉了生产数据库（据 Fortune 2025-07-23 报道）'),

    # ---------- 3. ch12 威胁清单：逐个补 CVE 元信息与研究出处 ----------
    ('ch12-security.md', 'CVE-2022-24765 补影响版本与披露日期',
     '**CVE-2022-24765 就是利用了 Windows 上的 `.git/config` 会被 parent 目录的 shared owner 触发**',
     '**CVE-2022-24765（Git for Windows < 2.35.2，2022-04-12 披露）就是利用了 Windows 上的 `.git/config` 会被 parent 目录的 shared owner 触发**'),

    ('ch12-security.md', 'CVE-2025-54135 补影响版本、披露日期与 CVSS',
     '- **Cursor RCE CVE-2025-54135**：恶意仓库的某个文件里的提示注入让 Cursor Agent 执行任意代码。',
     '- **Cursor RCE CVE-2025-54135**（影响 < 1.3.9，2025-08-05 披露，CVSS 3.1 = 8.6）：恶意仓库的某个文件里的提示注入让 Cursor Agent 执行任意代码。'),

    ('ch12-security.md', 'Agentjacking 补披露方与研究出处',
     '- **Agentjacking**：攻击者往公开的 DSN（如 Sentry 的错误上报端点）注入伪“解决方案”，AI coding agent 经 MCP 读到它并照着执行',
     '- **Agentjacking**（Tenet Security 披露，Cloud Security Alliance 2026-06 研究简报；实测命中 2,388 家 DSN 暴露的组织）：攻击者往公开的 DSN（如 Sentry 的错误上报端点）注入伪“解决方案”，AI coding agent 经 MCP 读到它并照着执行'),

    ('ch12-security.md', 'Aurora 事件补时间窗、受害规模与报告出处',
     '- **Aurora 勒索团伙武器化 Cursor Agent（2026-04）**：至少 10 家跨国企业遭入侵——凭证窃取、ESXi 勒索落地',
     '- **Aurora 勒索团伙武器化 Cursor Agent（2026-04 至 05，共 10 家受害组织）**：据 Gambit Security 2026-08 报告，该团伙用 Cursor Agent（运行 Claude Sonnet）做内网侦察与凭证窃取，并落地了 ESXi 勒索加密器'),
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
        print('SKIP %-26s 已应用  %s' % (f, lab))
    if not pending:
        print('无待写入条目（全部已应用）')
        return
    if check_only:
        print('校验通过：%d 条待写入（未写入）' % len(pending))
        return

    for f, lab, old, new in pending:
        contents[f] = contents[f].replace(old, new, 1)
        print('OK   %-26s %s' % (f, lab))
    for f in sorted(contents):
        io.open(MS / f, 'w', encoding='utf-8').write(contents[f])
    print('DONE %d edits across %d files' % (len(pending), len(set(f for f, _, _, _ in pending))))


if __name__ == '__main__':
    main()
