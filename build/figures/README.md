# 插图素材（build/figures/）

本目录存**位图插图**及其 archify spec：14 张 PNG + 同名 JSON。PDF 里共 16 个图号，
另外 2 张（`图 11-1`、`图 12-1`）是稿件内直接排的 ASCII 图，不在此目录。

图题**跟着稿件走**：源稿用标准 Markdown `![图 <章>-<序>：<中文说明>](figures/<slug>.png)`，
pandoc 转成 `#figure(image(...), caption: [...])`。本目录只提供图片，**不生成图题**。

## 已集成（14 张）

`output/git-concept-map-full.pdf`：552 页 / 9.2 MB / 467 书签。

| 章节 | 图题 | 文件 |
|---|---|---|
| Ch00 | 图 0-1 Cargo-Cult Git 负循环 | ch00-cargo-cult.png |
| Ch00 | 图 0-2 本章小地图 | ch00-mini-map.png |
| Ch01 | 图 1-1 远端 → 本地 clone | ch01-clone.png |
| Ch02 | 图 2-1 三区流 + 命令 | ch02-three-areas.png |
| Ch03 | 图 3-1 5 commit 链 + 2 分支 | ch03-branch-chain.png |
| Ch04 | 图 4-1 upstream/origin/local | ch04-remote-fork.png |
| Ch05 | 图 5-1 合并前两条分支分叉 | ch05-merge-before-new.png |
| Ch07 | 图 7-1 分支策略决策树 | ch07-branching-strategy.png |
| Ch08 | 图 8-1 .git/ + 3 工作台 | ch08-worktree.png |
| Ch09 | 图 9-1 三方合并冲突 | ch09-three-way-merge.png |
| Ch10 | 图 10-1 决策树 3 终策略 | ch10-decision-tree.architecture.png |
| Ch12 | 图 12-2 pre-commit/push/scanning 三道闸 | ch12-three-gates.png |
| Ch13 | 图 13-1 cherry-pick 双链 | ch13-cherry-pick.png |
| Ch14 | 图 14-1 9 节点全书结构 | ch14-knowledge-map.png |

## 未位图化的部分

- **ch05 的 4 张变体**（spec 留 `blk3/6/11/12/17`）：archify 的节点宽度 / step / 名牌位置
  硬约束反复触发，几何约束失败 → **保留 ASCII 渲染**（Sarasa 2:1 等宽，与书 design system
  对齐）。注意 `图 5-1`（merge-before-new）已位图化并集成，不在这批里。
- **`图 11-1`、`图 12-1`**：稿件内直接排的 ASCII 图，无位图。

## 端到端管线

```bash
# 1) archify spec → 出版级 PNG（JSON spec → render HTML → Chrome 4x 浅色截图 → 去点阵底纹）
build/.venv/bin/python build/render_figure2.py SPEC.json build/figures/OUT.png

# 2) 在稿件里引用（图题就是正文的一部分）
#    ![](figures/OUT.png)  ->  ![图 <章>-<序>：<中文说明>](figures/OUT.png)

# 3) 重建 PDF（自动跑复验闸门）
bash build/build.sh
```

> 早期靠 `inject_mini_map*.py` / `batch_inject.py` 把图**注入** `book-final.typ` 并自动生成
> 图题，正是 REVIEW-v3 的 P0-3（图题印成内部素材名 + 「（archify 优化版）」备注）与
> P0-6（两套图号并存）的成因。这些脚本已废弃删除，改为「稿件原生 Markdown 引用」。

`.pre-rerender/` 是重渲染前的旧图备份，不参与构建。

## 关键决断与坑

- **archify brand-marks 不支持自定义品牌色** → 用 light theme 默认 pastel 配色
- **SVG 嵌入 PDF 文字消失**（CSS vars 不被 PDF 解析）→ 改用 Chrome 4x DPR 截图
- **点阵底纹**（archify 自带）→ PIL 像素扫描识别近白灰色涂白
- **typst image 路径 sandbox 解析** → 用相对路径放 build 目录内
- **archify 几何约束严** → node width ≥ sublabel 宽度、step > 节点 width、名牌不与节点重叠——每次 spec 需手工调位置
- **渲染尺寸截断** → v1 固定 `--window-size=1100,620` 会切掉 16:9 之外的图，v2 改为按内容高度出图

## 剩余 40 张策略（不推荐继续）

| 类别 | 张数 | 推荐 |
|---|---|---|
| 概念隐喻（珠子/项链/档案馆比喻） | 28 | typst shape 自画（与书 design system 一致） |
| 重复 DAG（ch05 4 张变体） | 4 | archify 几何易失败 + 视觉雷同 → 保留 ASCII |
| 大地图（ch05 blk20 / ch14 blk0） | 2 | mermaid → PNG |
| 清单/特殊（ch06 / ch10 blk17） | 2 | typst grid 表格 |

剩余 40 张如要继续，建议**先建 typst shape 模板库**（绕过 archify 几何约束）。
