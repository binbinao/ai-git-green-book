#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 archify 架构图重排成「窄画布」，使图内字号达标（对应 REVIEW-v4-figures-tables.md）。

为什么需要重排
------------------------------------------------
archify 的图内字号是**画布设计单位**里的固定值（节点主标签 11px、副标签 9px、
tag 7px、**连线标签 8px 硬编码**），不随画布尺寸变化。而 SVG 渲染时铺满视口宽、
再等比落到 120mm 版心 → 于是：

    落版 pt = 画布字号(px) × 340.16 ÷ canvas_W

要节点主标签 ≥7pt ⇒ **canvas_W ≤ 534**。原 14 张里 13 张超标（最大 1090），
根因是**节点副标签把节点撑宽 + archify 的标签间隙规则把画布撑宽**。

实测出的关键规则（/tmp/probe2.py 二分测得）
------------------------------------------------
archify 的 `composition/label-gap` 约束是：

    横向连线：所需间隙 = 24 + 8 × 标签字数   ← 标签必须横躺在两节点之间
    纵向连线：所需间隙 ≈ 36，**与标签长度无关** ← 标签竖躺在连线一侧

这正是原图不得不做宽的真正原因（例如「checkout/restore 回拉」横置要 192px）。

**因此本次重排的核心设计规则：带标签的连线一律走纵向。** 于是画布只需
≈ 节点宽 × 列数 + 小间隙，宽度立刻从 1090 降到 ~440，字号放大 ~2.5 倍。

坐标模型（实测标定）
    canvas_W ≈ 组件横向跨度 + 100   （左右各 30px 边界留白 + 各 20px 页边）
    canvas_H ≈ 组件纵向跨度 + 100 + 70×卡片数
约束：边界标签要组件距画布左/上边 ≥30px；节点宽 ≥ max(主标签 11px, 副标签 9px) 所需 + 8。

用法
    build/.venv/bin/python build/relayout_figures.py --dry-run   # 只算并报违规
    build/.venv/bin/python build/relayout_figures.py             # 写回 spec
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIGDIR = ROOT / 'build/figures'
# 原始（重排前）spec 的只读底本：每次都从它重建，保证反复运行幂等、可复现。
# 否则 drop_components / sub_override 会叠加到上一次的产物上。
PRISTINE = ROOT / '.backup-figures-prereflow'

MARGIN = 34
GAPX = 40
GAPY = 46
NODE_H = 72
BOUNDARY_PAD = 100


def text_units(t):
    """archify 的 textUnits：全角=2、半角=1（renderers/shared/utils.mjs）。"""
    if not t:
        return 0
    n = 0
    for ch in t:
        cp = ord(ch)
        n += 2 if (0x3000 <= cp <= 0x303F or 0xFF00 <= cp <= 0xFFEF
                   or 0x4E00 <= cp <= 0x9FFF) else 1
    return n


def label_cost_x(label):
    """横向放一个标签所需的最小节点间隙。

    源码（renderers/architecture/render-architecture.mjs::renderConnectionLabel）：
        w = max(30, textUnits(label) * 4.8 + 10)
    校验（同文件 composition/label-gap）：
        requiredGap = ceil(w + 16)
    → 取上整后等价于 max(46, ceil(units * 4.8 + 26))。
    三个实测样本精确吻合：「找结果」6→55、「父→子」5→50、「你这一侧代码块」14→94。
    """
    return max(46, int(-(-(text_units(label) * 4.8 + 26) // 1)))


def need_width(label, sublabel):
    return max(text_units(label) * 11 * 0.6 + 8, text_units(sublabel) * 9 * 0.6 + 8)


# ============================================================
# 布局表
#   rows: 行为单位，值为 [(组件id, 列号), ...]
#   drop_labels: 本图要删掉的冗余连线标签（内容不丢，语义已在节点/图题/正文里）
#   sub_override: 不得已需截短的副标签（保留全部技术词元）
#   force_w / gapx / gapy / floor: 覆盖默认几何
# ============================================================
LAYOUTS = {
    # Ch00 负循环：2 列 × 4 行蛇形。横向那 4 条只挂 2 字标签（「搜」「粘贴」…），
    # 正好卡在 GAPX=40 上；跨行的 3 条走纵向。
    'ch00-cargo-cult': dict(
        rows=[[('problem', 0), ('search', 1)],
              [('copy', 0), ('works', 1)],
              [('variant', 0), ('panic', 1)],
              [('more_copy', 0), ('far', 1)]],
        sub_override={'far': '离理解越来越远'},
    ),
    # Ch01 clone：左列 = 数据层级竖排，右列 = 命令贴在其作用的过渡旁
    'ch01-clone': dict(
        rows=[[('remote_server', 0)],
              [('remote_git', 0), ('git_clone', 1)],
              [('local_git', 0), ('checkout', 1)],
              [('working_tree', 0)]],
        sub_override={'remote_git': 'objects/ + refs/ 全量',
                      'local_git': 'objects/ + refs/ 全量拷贝',
                      'checkout': '从 objects 铺出 HEAD 的工作区'},
    ),
    # Ch02 三区：★★ 结构改动（对应 REVIEW-v4 §4.2「把命令节点降级为图外注释」）★★
    # 5 个命令节点扇入 3 个区，在窄画布里无论怎么排都会穿过中间节点（实测 8 条报错）。
    # 且它们与附录 A 命令速查表重复 → 移出画布，内容原样转成卡片，信息零丢失。
    # 剩下三区构成一个三角：working → staging（纵向）→ repo（横向）→ working（斜回）。
    'ch02-three-areas': dict(
        rows=[[('working', 0)],
              [('staging', 0), ('repo', 1)]],
        drop_components=['git_add', 'git_commit', 'git_restore',
                         'git_reset_soft', 'git_reset_hard'],
        card_title='五条命令：谁把数据推到哪一层',
        card_dot='cyan',
        sub_override={'working': '你编辑的文件',
                      'staging': '下一次 commit 的内容'},
    ),
    # Ch03 分支链：珠子必须横排成链；4 个「父→子」在每个环上完全相同，是纯噪声，删掉；
    # 两张名牌改为**挂在链上方**，于是「ref: …」长标签走纵向，不再吃横向间隙。
    'ch03-branch-chain': dict(
        rows=[[('main', 3), ('feature', 4)],
              [('C1', 0), ('C2', 1), ('C3', 2), ('C4', 3), ('C5', 4)]],
        drop_labels=['c1-c2', 'c2-c3', 'c3-c4', 'c4-c5'],
        pin_labels=True,
        gapx=28,
        floor=56,
        force_w={'C1': 52, 'C2': 52, 'C3': 52, 'C4': 52, 'C5': 52,
                 'main': 76, 'feature': 82},
    ),
    # Ch04 Fork 三层：三层竖排（左列）+ 命令竖排（右列）
    'ch04-remote-fork': dict(
        rows=[[('upstream', 0), ('pr', 1)],
              [('origin', 0), ('push_to_origin', 1)],
              [('local', 0), ('clone', 1)]],
        gapx=64,
        sub_override={'upstream': 'github.com/original/project',
                      'origin': 'github.com/<你>/project（fork）',
                      'local': 'refs/remotes/* 全量引用'},
    ),
    # Ch05 合并前分叉：两条链各占一列（main 链左 / feature 链右），名牌置底
    'ch05-merge-before-new': dict(
        rows=[[('root', 0), ('A', 1)],
              [('B', 0), ('D', 1)],
              [('C', 0), ('E', 1)],
              [('main', 0), ('feature', 1)]],
        gapx=56,
        floor=130,
        force_w={k: 130 for k in ('root', 'A', 'B', 'C', 'D', 'E', 'main', 'feature')},
    ),
    # Ch07 分支策略决策树：q1 → q2a/q2b → 四策略，全部连线纵向
    'ch07-branching-strategy': dict(
        rows=[[('q1', 0)],
              [('q2a', 0), ('q2b', 1)],
              [('gitflow', 0), ('trunk', 1)],
              [('simplified_gf', 0), ('github_flow', 1)]],
    ),
    # Ch08 worktree：.git/ 作横幅独占首行（它含 objects/ refs/ worktrees/ 一串路径，
    # 若按列宽计算会把左列顶到 155 宽），三张工作台 + 三条命令各成三列。
    # 这样 git→三张工作台、工作台→命令 全是相邻纵向，零穿线。
    'ch08-worktree': dict(
        banner='git',
        rows=[[('git', 0)],
              [('main_wt', 0), ('wt_a', 1), ('wt_b', 2)],
              [('wt_create', 0), ('wt_list', 1), ('wt_remove', 2)]],
        label_override={'wt_create': 'worktree add',
                        'wt_list': 'worktree list',
                        'wt_remove': 'worktree remove'},
        sub_override={'git': 'objects/ + refs/ + worktrees/',
                      'main_wt': '~/proj/ · main',
                      'wt_a': '~/proj-hot/ · hotfix',
                      'wt_b': '~/proj-rev/ · pr/42',
                      'wt_create': '新工作台 + 切分支',
                      'wt_list': '列出所有工作台',
                      'wt_remove': '删除工作台（分支保留）'},
        # 三条 git→工作台 的连线标签（HEAD → main / worktree/hotfix/HEAD …）
        # 与三张工作台的副标签完全重复，且挤在同一走廊 → 删掉，信息不丢。
        drop_labels=['git-main', 'git-wt_a', 'git-wt_b'],
    ),
    # Ch09 三方合并：B 顶 → ours/theirs 并排 → 算法 → 三个冲突标记纵排。
    # 冲突标记那两条连线标签极长（「你这一侧代码块」14 字 → 横向要 94px），
    # 竖排后标签贴在连线一侧，间隙需求与长度无关 → 画布从 680 收到 ~500。
    'ch09-three-way-merge': dict(
        rows=[[('base', 0)],
              [('ours', 0), ('theirs', 1)],
              [('git', 0)],
              [('marker_head', 0)],
              [('marker_mid', 0)],
              [('marker_end', 0)]],
        sub_override={'base': 'export async function fetchUser（原版）',
                      'marker_end': '>>>>>>> feature/user-refactor'},
        boundary_label=['冲突标记块'],
        pin_labels=True,
        gapy=38,
    ),
    # Ch10 恢复决策树：第一问 → 本地/第二问 → 三终策略（REVIEW-v4 的另一张 🔴）
    'ch10-decision-tree.architecture': dict(
        rows=[[('q1', 0)],
              [('local_branch', 0), ('q2', 1)],
              [('recover_local', 0), ('recover_merge', 1)],
              [('recover_forward', 0)]],
    ),
    # Ch12 三道闸：左侧流程竖排，右侧闸门竖排
    'ch12-three-gates': dict(
        rows=[[('developer', 0), ('gate1', 1)],
              [('git_push', 0), ('gate2', 1)],
              [('remote', 0), ('gate3', 1)],
              [('monitor', 0)]],
    ),
    # Ch13 cherry-pick：两条链各占一行（main 链 / feature 链），名牌置顶
    'ch13-cherry-pick': dict(
        rows=[[('main', 2), ('feature', 1)],
              [('A', 0), ('B', 1), ('C', 2)],
              [('X', 0), ('Y', 1), ('Z', 2)],
              [('Yprime', 2)]],
        drop_labels=['A-B', 'B-C', 'X-Y', 'Y-Z'],
        gapx=32,
        floor=76,
        force_w={'A': 76, 'B': 76, 'C': 76, 'X': 76, 'Y': 76, 'Z': 76, 'Yprime': 100},
    ),
    # Ch14 全书总图：诊断 → 三层 → 进阶 → 合拢 → 三产出
    'ch14-knowledge-map': dict(
        rows=[[('diagnose', 0)],
              [('five_maps', 0), ('six_scenes', 1)],
              [('one_defense', 0), ('eight_lanes', 1)],
              [('chapter_14', 0), ('total_map', 1)],
              [('followup_3', 0), ('plan_30d', 1)]],
        sub_override={'eight_lanes': 'stash、cherry-pick、bisect…'},
        # 三条边都汇入 eight_lanes，标签文本完全相同（'再走小路'）→ 只保留一条，
        # 否则两条标签会在同一走廊里互相压住（label-route-clearance）。
        drop_labels=['six-eight', 'one-eight'],
    ),
}


def round5(v):
    return int(round(v / 5.0) * 5)


def build(slug, spec):
    src = PRISTINE / f'{slug}.json'
    if not src.exists():
        src = FIGDIR / f'{slug}.json'
    d = json.load(open(src, encoding='utf-8'))
    # drop_components：把某些节点移出画布（其语义改由卡片承载）。
    # 图 2-1 的 5 个命令节点属于这种：它们与附录 A 命令速查表重复，且 5 条线扇入
    # 3 个区，在窄画布里必然穿过中间节点。
    drops = set(spec.get('drop_components', []))
    dropped = []
    if drops:
        dropped = [c for c in d['components'] if c['id'] in drops]
        d['components'] = [c for c in d['components'] if c['id'] not in drops]
        d['connections'] = [c for c in d['connections']
                            if c['from'] not in drops and c['to'] not in drops]
        # 边界框也要摘掉被撤的节点；成员不足 2 个的边界框整体去掉。
        for b in d.get('boundaries', []):
            b['wraps'] = [w for w in b.get('wraps', []) if w not in drops]
        d['boundaries'] = [b for b in d.get('boundaries', [])
                           if len(b.get('wraps', [])) >= 2]
    if dropped and spec.get('card_title'):
        # 被移出画布的节点不能丢信息：把它们的标签+副标签原样转成卡片条目。
        # 先按标题清掉上一次生成的同名卡片，保证反复运行幂等。
        d['cards'] = [c for c in d.get('cards', [])
                      if c.get('title') != spec['card_title']]
        order = {cid: i for i, cid in enumerate(spec['drop_components'])}
        items = [f'{c["label"]} — {c["sublabel"]}' for c in
                 sorted(dropped, key=lambda c: order[c['id']])]
        d['cards'].append({'dot': spec.get('card_dot', 'cyan'),
                           'title': spec['card_title'], 'items': items})
    if spec.get('add_cards'):
        d.setdefault('cards', [])
        d['cards'].extend(spec['add_cards'])
    by_id = {c['id']: c for c in d['components']}
    for cid, sub in spec.get('sub_override', {}).items():
        if cid in by_id:
            by_id[cid]['sublabel'] = sub
    for cid, lab in spec.get('label_override', {}).items():
        if cid in by_id:
            by_id[cid]['label'] = lab
    if spec.get('boundary_label'):
        for i, lab in enumerate(spec['boundary_label']):
            if i < len(d.get('boundaries', [])):
                d['boundaries'][i]['label'] = lab

    rows = spec['rows']
    force_w = spec.get('force_w', {})
    base_gapx = spec.get('gapx', GAPX)
    gapy = spec.get('gapy', GAPY)
    floor = spec.get('floor', 70)

    ncols = 1 + max(c for row in rows for _, c in row)
    colw = [0] * ncols
    rc = {}
    banner = spec.get('banner')
    for ri, row in enumerate(rows):
        for cid, col in row:
            c = by_id[cid]
            rc[cid] = (ri, col)
            if cid == banner:
                continue          # 横幅的宽度不参与列宽（它横跨整排）
            w = force_w.get(cid) or max(
                floor, round5(need_width(c.get('label', ''), c.get('sublabel', ''))))
            colw[col] = max(colw[col], w)

    missing = set(by_id) - set(rc)
    if missing:
        raise SystemExit(f'{slug}: 组件未排入布局 {sorted(missing)}')

    for cn in d['connections']:
        for k in ('fromSide', 'toSide', 'labelAt', 'labelDx', 'labelDy',
                  'labelSegment', 'via', '_violation', '_span'):
            cn.pop(k, None)
        if cn['id'] in spec.get('drop_labels', []):
            cn.pop('label', None)

    # 列缝宽度由「落在该缝上的横向标签」反推：gap = 24 + 8×标签字数（实测二分）。
    # 纵向标签的间隙需求与长度无关（≈36），所以把带标签的连线尽量安排成纵向更省宽。
    gapx = [base_gapx] * max(0, ncols - 1)
    for cn in d['connections']:
        rf, cf = rc[cn['from']]
        rt, ct = rc[cn['to']]
        lab = cn.get('label')
        if rf == rt and lab:
            i = min(cf, ct)
            if i >= len(gapx):
                raise SystemExit(f'{slug}: 连线 {cn["id"]} 两端同格')
            gapx[i] = max(gapx[i], label_cost_x(lab))

    colx, x = [], MARGIN
    for i, w in enumerate(colw):
        colx.append(x)
        x += w + (gapx[i] if i < len(gapx) else 0)

    for ri, row in enumerate(rows):
        y = MARGIN + ri * (NODE_H + gapy)
        for cid, col in row:
            c = by_id[cid]
            c['pos'] = [colx[col], y]
            c['size'] = [force_w.get(cid) or colw[col], NODE_H]

    # banner：该行只有一个节点时，让它横跨整排（如 ch08 的 .git/ 共享数据库）。
    # 这样它自己的宽度不再顶住所在列的列宽，列宽只由下面几排的节点决定。
    if spec.get('banner'):
        bid = spec['banner']
        bre = rc[bid][0]
        assert len(rows[bre]) == 1, f'{slug}: banner 所在行不止一个节点'
        row_w = colx[-1] + colw[-1] - MARGIN
        by_id[bid]['pos'] = [MARGIN, MARGIN + bre * (NODE_H + gapy)]
        by_id[bid]['size'] = [row_w, NODE_H]

    # 连线侧向与标签定位
    # ------------------------------------------------------------------
    # 三种情形：
    #  A 同排相邻列（横向）—— 侧向 right/left。标签走 archify 默认：贴在线上方 10px，
    #    只要求列缝 ≥ 标签宽 + 26（已由 gapx 保证）。
    #  B 同列相邻排（纵向）—— 侧向 bottom/top，但**必须显式给 labelAt**：
    #    archify 的 labelPoint 对两点直线用 `points[0][1] - 10`，这是按水平线设计的，
    #    对竖直线会把标签压进**起始节点内部**（这正是 strict 版报的
    #    「Label … overlaps component …」根因）。这里直接把它钉在列缝正中。
    #  C 其余（斜向 / 跨多排）—— 不写侧向，交给 archify 自己规划；
    #    跨多排的记 _span，它在视觉上必然穿过中间节点，需要改布局。
    yof = lambda r: MARGIN + r * (NODE_H + gapy)

    for cn in d['connections']:
        rf, cf = rc[cn['from']]
        rt, ct = rc[cn['to']]
        lab = cn.get('label')
        same_row, same_col = (rf == rt), (cf == ct)

        if same_row and abs(cf - ct) == 1:            # A 横向相邻
            cn['fromSide'] = 'right' if cf < ct else 'left'
            cn['toSide'] = 'left' if cf < ct else 'right'
        elif same_col and abs(rf - rt) == 1:          # B 纵向相邻
            lo, hi = min(rf, rt), max(rf, rt)
            if rf < rt:
                cn['fromSide'], cn['toSide'] = 'bottom', 'top'
            else:
                cn['fromSide'], cn['toSide'] = 'top', 'bottom'
            if lab and spec.get('pin_labels'):
                # 列缝正中：起点节点下沿 + gapy/2
                cn['labelAt'] = [colx[cf] + colw[cf] / 2.0, yof(lo) + NODE_H + gapy / 2.0]
        else:                                          # C 斜向 / 跨格
            if same_col or same_row:
                cn['_span'] = (f'连线 {cn["id"]}（{cn["from"]}→{cn["to"]}）跨 '
                               f'{abs(rf - rt) + abs(cf - ct)} 格，路线会穿过中间节点')

    span_x = max(c['pos'][0] + c['size'][0] for c in d['components']) - MARGIN
    ncards = len(d.get('cards', []))
    est_w = span_x + BOUNDARY_PAD
    est_h = len(rows) * NODE_H + (len(rows) - 1) * gapy + BOUNDARY_PAD + 70 * ncards
    return d, est_w, est_h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()

    print(f"{'图':32s}{'预计画布':>12s}{'别住':>5s}{'节点pt':>8s}{'副标签pt':>9s}{'tag pt':>8s}  判定")
    print('-' * 88)
    todo, bad = [], []
    for slug, spec in sorted(LAYOUTS.items()):
        if args.only and slug not in args.only:
            continue
        d, w, h = build(slug, spec)
        s = min(120.0 / w, 196.0 / h)
        node_pt, sub_pt, tag_pt = 11 * s * 2.8346, 9 * s * 2.8346, 7 * s * 2.8346
        bind = '宽' if 120.0 / w <= 196.0 / h else '高'
        ok = '✅' if node_pt >= 7 and w <= 534 else ('△' if node_pt >= 6.6 else '❌')
        print(f"{slug:32s}{f'{w:.0f}x{h:.0f}':>12s}{bind:>5s}{node_pt:>8.2f}{sub_pt:>9.2f}{tag_pt:>8.2f}  {ok}")
        notes = []
        for c in d['connections']:
            if '_span' in c:
                notes.append(c['_span'])
        if w > 534:
            notes.append(f'画布宽 {w:.0f} > 534')
        if node_pt < 7:
            notes.append(f'节点 {node_pt:.2f}pt < 7pt')
        for v in notes:
            print(f'      ⚠ {v}')
            bad.append(slug)
        todo.append((slug, d))

    if args.dry_run:
        return
    for slug, d in todo:
        for c in d['connections']:
            c.pop('_violation', None)
            c.pop('_span', None)
        json.dump(d, open(FIGDIR / f'{slug}.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
    print(f'\n已写回 {len(todo)} 个 spec')


if __name__ == '__main__':
    main()
