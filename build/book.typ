// ============================================================
// 《Git 的概念地图》出版级排版模板 v3 —— 出版规范修订版
// typst 0.15 · 172×248mm · 宋体正文 + PuHuiTi 展示字 + Sarasa 代码
//
// v3 相对 v2 的修订（对应 REVIEW-v3-typeset-qa.md）：
//   P0-4  封面书名不再交给自动折行（关首行缩进/两端对齐，主标题包 box，字重 900→700）
//   P0-5  ASCII 箱线图按版心自动缩字号 + 禁跨页（原先既折行又跨页，边框全毁）
//   P1-7  红黄绿 emoji → 纯矢量圆点（AppleColorEmoji 是 Type3、无 FontFile，判"未嵌入"）
//   P1-8  行内代码前后被排入的多余空格（根因：show rule 替换体里的换行）
//   P1-9  DejaVuSansMono 为渲染那些多余空格而被动嵌入（随 P1-8 一并消失）
//   P1-10 PDF 元数据（title / author / keywords / date）
//   P1-12 章扉题字 GIT → Git
//   P1-13 行内代码按空格切成不可断小盒，`-vH` 这类开关不再被劈开
//   P2-16 章扉统一落奇数页（右页），插入的空白页不带书眉与页码
// ============================================================

// ---------- 元数据（单一版本源：P1-14） ----------
// 封面 / 扉页 / 版权页的版本号与日期都由 postprocess.py 从这里读取后写入，
// 不要再在别处手写第二份，否则就会出现"四处声明互相对不上"。
#let meta = (
  title: "Git 的概念地图",
  subtitle: "用自然语言驾驭版本控制 —— 一本不背命令的 Git 书",
  author: "binbinao",
  edition: "1.1（第二轮修订版）",
  date: "2026-10-04",
  keywords: (
    "Git", "版本控制", "概念地图", "AI 辅助开发",
    "自然语言编程", "reflog", "分支策略", "出版级排版",
  ),
)

// PDF 元数据（P1-10）：阅读器标题栏 / 书库 / 检索系统靠它取书目信息
#set document(
  title: "Git 的概念地图——用自然语言驾驭版本控制",
  author: meta.author,
  keywords: meta.keywords,
  date: datetime(year: 2026, month: 10, day: 4),
)

// ---------- 设计令牌（Design Tokens） ----------
#let teal     = rgb("#0F4C5C")   // 品牌深青：章号/表头/书眉线
#let teal-soft = rgb("#E7EFF1")  // 深青的浅背景
#let amber    = rgb("#E8A13D")   // 琥珀强调：标记/点缀
#let ink      = rgb("#1A1A1A")   // 墨黑正文
#let gray-6   = rgb("#595959")   // 次要文字
#let gray-b   = rgb("#BBBBBB")   // 细线
#let paper    = rgb("#F5F3EF")   // 暖灰纸感底
#let code-bg  = rgb("#F7F6F3")   // 代码底

// 安全标记三色（P1-7）
#let mark-green = rgb("#1F9D55")
#let mark-amber = rgb("#C99700")
#let mark-red   = rgb("#C0392B")

// ---------- 字体族 ----------
#let song = ("Songti SC", "Songti TC")                    // 正文
#let disp = ("Alibaba PuHuiTi 3.0", "PingFang SC")        // 展示黑体（章扉/封面）
#let hei  = ("PingFang SC", "Heiti SC", "Alibaba PuHuiTi 3.0")  // 节标题
#let mono = ("Sarasa Fixed SC", "Sarasa Mono SC")         // 代码 2:1 等宽
#let kai  = ("Kaiti SC", "Kaiti TC")                      // 引文

// ---------- 版心几何 ----------
#let page-w = 172mm
#let page-h = 248mm
#let margin-side = 26mm
#let margin-top = 27mm
#let margin-bottom = 25mm
#let text-w = 120mm                                       // 版心宽（供图块适配用）
#let text-h = 195mm                                       // 版心高

#set page(width: page-w, height: page-h,
  margin: (top: margin-top, bottom: margin-bottom, x: margin-side),
)

// ---------- 正文 ----------
// cjk-latin-spacing: none —— 源稿的中西文间隙是作者逐处手打的（实测 8488 处
// 中_西 + 8366 处 西_中，无一处漏打），引擎再自动插一次只会在「拉丁 → 全角
// 收尾标点」这类错位边界上塞进多余间隙（P1-8 的表象）。关掉即与手打结果一致。
#set text(font: song, size: 10.5pt, lang: "zh", region: "cn",
  fill: ink,
  cjk-latin-spacing: none,
  hyphenate: true,
)

#set par(justify: true, leading: 1.75em,       // 审计收紧：1.9→1.75 行距
  first-line-indent: (amount: 2em, all: true),
  spacing: 1.3em,
)

// ---------- 章扉：chapter-open(num, label, title, kind) ----------
// postprocess.py 预解析章号/标题；函数 emit 真 heading（供 outline/书眉 query）
#let chapter-open(num: "0", label: "第 0 章", title: "", kind: "ch") = {
  state("ch-num").update(num)
  state("ch-title").update(title)
  heading(level: 1)[#label　#title]
}

// 章扉视觉：独占页无书眉页码，巨型章号 + 章名 + 品牌色构图
// P2-16：章扉统一落奇数页（右页）。`set page(header/footer: none)` 必须写在
// pagebreak 之前 —— 这样 pagebreak(to: "odd") 为凑奇数页而插入的空白页会继承
// "无书眉无页码"的设置，不会出现"空白页还印着页码"的尴尬。
#show heading.where(level: 1): it => {
  set page(header: none, footer: none)
  pagebreak(to: "odd")
  page(header: none, footer: none)[
    #set align(left)
    #set par(first-line-indent: 0em)
    #v(3.5em)
    #box(width: 100%)[
      #box(width: 2.2em, height: 0.5em, fill: teal, outset: (y: 0.26em))
      #h(0.8em)
      // P1-12：Git 官方品牌写法恒为 `Git`；全书正文书眉用的也是 `Git`
      #text(font: disp, size: 11.5pt, weight: 600, fill: teal, tracking: 0.08em)[Git 的概念地图]
    ]
    #v(2.8em)
    #context text(font: disp, size: 88pt, weight: 900, fill: teal, tracking: -0.02em)[#state("ch-num").get()]
    #v(0.25em)
    #context text(font: disp, size: 25pt, weight: 700, fill: ink, hyphenate: false)[#state("ch-title").get()]
    #v(1.7em)
    #box(width: 34%, height: 2.5pt, fill: amber)
    #v(1fr)
    #text(font: song, size: 10pt, fill: gray-6)[概念先行 · 场景判断 · AI 执行]
    #v(2.2em)
  ]
  pagebreak()
}

// h2 = 节标题：深青色 + 左侧粗竖线
#show heading.where(level: 2): it => {
  v(1.1em)
  block[
    #set par(first-line-indent: 0em)
    #box(width: 3.5pt, fill: teal, outset: (y: 0.24em), radius: 1pt)[ ]
    #h(0.55em)
    #text(font: hei, size: 14.5pt, weight: 700, fill: teal)[#it.body]
  ]
  v(0.45em)
}

// h3 = 小节：墨黑 + 左侧细竖线
#show heading.where(level: 3): it => {
  v(0.7em)
  block[
    #set par(first-line-indent: 0em)
    #box(width: 2.5pt, fill: amber, outset: (y: 0.18em), radius: 1pt)[ ]
    #h(0.5em)
    #text(font: hei, size: 12pt, weight: 700, fill: ink)[#it.body]
  ]
  v(0.35em)
}

// h4 = 强调行：墨黑粗体
#show heading.where(level: 4): it => {
  v(0.45em)
  block[
    #set par(first-line-indent: 0em)
    #text(font: hei, size: 10.5pt, weight: 700, fill: ink)[#it.body]
  ]
  v(0.3em)
}

// ---------- 代码块 ----------
// 版心宽 120mm 减去左右 inset 各 10pt，即图块可用的最大宽度
#let block-avail-w = text-w - 20pt
// 版心高 195mm 减去上下 inset 各 8pt 与描边
#let block-avail-h = text-h - 18pt
// ASCII 箱线图的行高系数（实测 Sarasa Fixed SC：8.5pt 字号 → 12.0pt 行距）
#let art-line-factor = 1.42
// 自动缩字号的下限：比这更小就不缩了，改为允许在行边界断开
#let art-min-size = 7pt

#let art-glyphs = "─│├└┌┐┘┤┬┴┼━┃┏┓┗┛┣┫┳┻╋═║╔╗╚╝╠╣╦╩╬▼▲◀▶→←↑↓"
#let is-art(txt) = txt.clusters().any(g => art-glyphs.contains(g))

#let code-shell(body, size: 8.5pt, brk: true) = block(
  width: 100%,
  fill: code-bg,
  stroke: (paint: gray-b, thickness: 0.5pt),
  inset: (x: 10pt, y: 8pt),
  radius: 3pt,
  breakable: brk,
  text(font: mono, size: size, fill: ink)[#body],
)

// P0-5：ASCII 箱线图是固定宽度艺术字 —— 折一行，整张图的边框与列对齐就全毁。
// 因此对含制表符的代码块：
//   ① 按最长行自动缩字号，保证绝不横向折行（宁可缩小）；
//   ② 缩到 7pt 仍装不满一页时才允许跨页，否则 breakable: false 禁跨页。
// 普通代码块保持原样（长命令清单本来就需要能跨页）。
#show raw.where(block: true): it => {
  let txt = it.text
  let lines = txt.split("\n")
  let maxw = lines.fold(0pt, (a, l) => calc.max(
    a, measure(text(font: mono, size: 8.5pt, l)).width,
  ))
  let art = is-art(txt)
  // ---- 第一步：横向。保证最长行不被迫折行（宁可缩小字号）----
  // P1-13：原先只有箱线图会缩字号，普通代码块固定 8.5pt —— 于是 12 个含长行的
  // 代码块（最长 91 字符）在 120mm 版心里被迫折行，而折点常常正落在连字符上：
  //     git reset --mixed <target>   →  行尾 "--" / 次行 "mixed）"
  //     git branch -D experiment/new-parser  →  "new-" / "parser'."
  // 命令被打断后读者复制即错。改为所有代码块统一按栏宽自适应，下限 7pt。
  let size = 8.5pt * calc.min(1.0, block-avail-w / maxw)
  if size < art-min-size { size = art-min-size }
  // ---- 第二步：纵向。只有箱线图必须整体不跨页（折行/跨页会毁掉边框对齐）----
  let fits-h = lines.len() * art-line-factor * size <= block-avail-h
  if art and not fits-h {
    let size-for-height = block-avail-h / (lines.len() * art-line-factor)
    if size-for-height >= art-min-size {
      size = size-for-height
      fits-h = true
    }
  }
  // 普通代码块允许跨页（长命令清单本来就需要）；箱线图只在装不下时才允许
  code-shell(txt, size: size, brk: not (art and fits-h))
}

// 行内代码
// P1-8 / P1-9 根因：替换体过去写成
//     highlight(...)[
//       #text(font: mono, size: 9pt, fill: teal)[#it]
//     ]
// 方括号里的换行 + 缩进在 Typst 里等价于一个空格，于是每一处行内代码前后都被
// 塞进一个空格；该空格又落回 raw 的默认字体 DejaVuSansMono（0.8em = 8.4pt），
// 于是同时产出两个现象：正文里 514 处"误入的中西文间隙"（P1-8），以及 PDF 中
// 无谓嵌入一款 DejaVuSansMono（2990 个空格 span、零可见字形，P1-9）。
// 现在写成单行、不留任何多余空白。
// 实证（最小复现）：方括号里带换行的多行写法输出 `' --amend '`（宽 40.5pt），
// 单行写法输出 `'--amend'`（宽 31.5pt），差 9pt = 左右各多一个空格。
// P1-13：再把代码按空格切成不可断的小盒，`git count-objects -vH` 这类命令
// 不会在 `-` 与 `-vH` 之间被劈开（仅对超长 token 保留断行能力，避免溢出）。
//
// size 参数的取值依据 —— raw 元素自带 0.8em 的基准字号，会和这里相乘：
//     正文 10.5pt × 0.8 × 1.07 = 9.0pt   ← 与旧模板写死的 9pt 一致
//     表内  9pt   × 0.8 × 0.86 = 6.2pt   ← 表内必须更小
// 为什么表内不能跟着正文一起放大：5 列表的最窄列可用宽只有 60pt，而装箱阈值
// 是 20 字符 —— 20 字符在 7.2pt 下宽 72pt，直接撑破单元格（P1-13 会复发）。
// 旧注释写"0.86em 落到约 7.7pt"是漏算了 raw 的 0.8em，实际是 6.2pt。
#let code-inline(txt, size: 1.07em) = text(font: mono, size: size, fill: teal)[#txt.split(" ").map(t => if t.len() <= 20 { box(t) } else { t }).join([ ])]

#show raw.where(block: false): it => highlight(
  fill: teal-soft, top-edge: "ascender", bottom-edge: "descender", extent: 2pt,
)[#code-inline(it.text)]

// ---------- 安全标记：红黄绿（P1-7） ----------
// 🟢🟡🔴 在 PDF 里由 AppleColorEmoji 渲染，而它的字形是 Type3 字形程序、没有
// FontFile —— 印刷 preflight 会判"字体未嵌入"，不同 RIP 还可能丢色或变黑块。
// 改为纯矢量圆点：circle() 不依赖任何字体，颜色语义 100% 保留，同时解决
// "emoji 风格与全书排版语言不搭"的观感问题。
#let mark-dot(c) = box(baseline: 0.18em, circle(radius: 0.30em, fill: c))
#show "🟢": mark-dot(mark-green)
#show "🟡": mark-dot(mark-amber)
#show "🔴": mark-dot(mark-red)

// 其余装饰性 emoji 一并收敛为可嵌入字体里的等价符号（颜色语义保留）。
// 注意：show rule 只作用于正文与表格，代码块（raw）内部是逐字直排，
// 那里出现的 emoji 已在源稿里换成等宽的汉字标记。
#show "⭐": text(fill: mark-amber)[★]
#show "✅": text(fill: mark-green)[✓]
#show "❌": text(fill: mark-red)[✗]
#show "⚠": text(fill: mark-amber)[△]
#show "✨": text(fill: mark-amber)[◆]
#show "🚫": text(fill: mark-red)[×]
#show "💡": text(fill: mark-amber)[※]
#show "📋": text(fill: teal)[≡]
#show "🚨": text(fill: mark-red)[！]
// 🤖 曾经映射为文字「AI」，但栏目名本身就叫「AI 指令箱」→ 印出来是
// 「AI AI 指令箱」（全书 15 处）。其余章末栏目（命令侧栏 / 本章小地图 /
// 三大典型误解拆解 / 下一章预告）一律无标记符号，故直接删掉 🤖 字符、
// 不再为它保留 show rule —— 若日后又有 emoji 混入，P1-7 检查会当场拦下。

// ---------- 块引：左侧深青粗线 + 楷体 ----------
#show quote: it => block(
  width: 100%,
  fill: none,
  stroke: (left: 3pt + teal),
  inset: (x: 14pt, y: 8pt),
  text(font: kai, size: 10.5pt, fill: ink)[#it.body]
)

// ---------- 列表 ----------
#set list(indent: 1.2em, spacing: 0.65em, marker: ([•], [◦], [▪]))
#set enum(indent: 1.2em, tight: true)

#show list.item: it => {
  set par(first-line-indent: 0em)
  it.body
}

#show enum.item: it => {
  set par(first-line-indent: 0em)
  it.body
}

// ---------- 表格：深青表头 + 斑马纹 ----------
// P1-11：表头行由 postprocess.py 保留的 table.header(...) 提供，
// 这里用 it.y == 0 给首行上深青底白字 —— 两者必须同时存在，缺一则表头不再是表头。
#set table(inset: (x: 6pt, y: 5pt), stroke: none)

#show table.cell: it => {
  if it.y == 0 {
    set text(font: hei, size: 9pt, weight: 700, fill: white)
    // 表头里的行内代码要去掉 teal-soft 高亮底 —— 否则深青表头中间会嵌一块
    // 极浅的小方块（浅底 + 深青字），与"表头一色"的设计冲突。这正是 P1-11
    // 说的"同一张表内两种底色"的最后残留形态（实测第 3 列表头 `.git/`）。
    show raw.where(block: false): it2 => text(font: mono, size: 0.86em)[#it2.text]
    // width: 100% 必须写：block 默认按内容宽度收窄，三个表头的底色实测只有
    // 56 / 76 / 92pt，而列宽是 98 / 98 / 145pt —— 底色参差不齐，不成"表头带"。
    block(width: 100%, fill: teal, inset: (x: 4pt, y: 4pt), breakable: true)[#it]
  } else if calc.even(it.y) {
    set text(size: 9pt)
    block(width: 100%, fill: paper, inset: (x: 4pt, y: 4pt), breakable: true)[#it]
  } else {
    set text(size: 9pt)
    block(width: 100%, inset: (x: 4pt, y: 4pt))[#it]
  }
}

// 目录：章级条目加重 + 节级灰字；点线细灰
#show outline.entry.where(level: 1): it => {
  v(0.9em)
  block(width: 100%)[
    #set text(font: hei, size: 10.5pt, weight: 700, fill: ink)
    #set par(first-line-indent: 0em)
    #it
  ]
}
#show outline.entry.where(level: 2): it => {
  block(width: 100%)[
    #set text(font: song, size: 9.5pt, fill: gray-6)
    #set par(first-line-indent: 0em)
    #it
  ]
}

// 表格整体：占满版心宽；表格语境下长 token 断行（防 auto 列溢出版心）。
// 表内行内代码单独缩小一档（0.86em → 实际 6.2pt，正文是 9pt）：
// 装箱阈值 20 字符在正文里宽 90pt 毫无压力，但在 5 列表最窄的 60pt 列里
// 就会撑破单元格。这是 P1-13 与表格排版之间的硬约束，不能跟着正文一起放大。
#show table: it => block(breakable: true, width: 100%)[
  #show text: set text(hyphenate: true)
  #show raw.where(block: false): it2 => highlight(
    fill: teal-soft, top-edge: "ascender", bottom-edge: "descender", extent: 2pt,
  )[#code-inline(it2.text, size: 0.86em)]
  #it
  #v(0.4em)
]

// ---------- 图注 ----------
// P0-6：Typst 会给 figure 自动编号（lang: zh 时就是「图 1」「图 2」…），而源稿的
// caption 里**已经**手写了章号体系的「图 0-1：」。两者叠加，每张图题都印成
//     图 1　 图 0-1：Cargo-Cult Git 负循环……
// 这正是 REVIEW 说的"图号体系混乱 / 两套体系并存"在渲染层的表现。
// 用 it.body 只取 caption 正文，丢掉自动编号与前缀分隔符 —— 全书只保留章号体系。
// （全书 0 处 #ref()，不存在依赖自动编号的交叉引用。）
#show figure.caption: it => text(font: hei, size: 9pt, fill: gray-6)[#it.body]

// ---------- 书眉与页码 ----------
#let chapter-title() = context {
  let page-num = here().page()
  let heads = query(heading.where(level: 1))
  let current = heads.rev().find(h => h.location().page() <= page-num)
  if current != none { current.body } else { meta.title }
}

#let in-body = state("in-body", false)

#set page(header: context {
  if in-body.get() [
    #set text(font: song, size: 9pt, fill: gray-6)
    #align(center)[
      #if calc.even(here().page()) { meta.title } else { chapter-title() }
    ]
    #v(-0.9em)
    #box(width: 100%, height: 0.6pt, fill: teal)
  ]
}, footer: context {
  if in-body.get() [
    #set text(font: song, size: 9.5pt, fill: gray-6)
    #if calc.even(here().page()) {
      align(left)[#counter(page).display("1")]
    } else {
      align(right)[#counter(page).display("1")]
    }
  ]
})

// ---------- 场景切换隔断（源稿 --- 分隔线） ----------
#let divider() = {
  v(1.2em)
  align(center)[#box(width: 14%, height: 0.7pt, fill: amber, radius: 1pt)]
  v(1.2em)
}

// ---------- 目录 ----------
#let make-toc() = {
  pagebreak()
  // 目录页题：深青大字 + 琥珀短线
  page(header: none, footer: none)[
    #v(3em)
    #text(font: disp, size: 30pt, weight: 900, fill: teal)[目 录]
    #v(0.8em)
    #box(width: 2.2em, height: 2.5pt, fill: amber)
    #v(1.8em)
    #outline(title: none, depth: 2)
  ]
}
