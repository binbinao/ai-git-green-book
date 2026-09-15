# 第 6 章　提交的艺术：让 AI 帮你写出人类能看懂的历史

> 《Git 的概念地图》第 6 章 · 场景决策 · 定调稿 v1.0
> 场景章的第一章：从"造珠子"这件最日常的事切入 AI 分工的第一道边界——**语法交给 AI，判断留给你**。

---

## 6.1 场景引入：一条被 blame 出来的提交

周四下午，你在追一个线上事故。日志指向 `payment/refund.py` 第 87 行，一个空指针。你 `git blame` 上去，找到那一行最后一次改动的 commit——

```
c3f9a12  fix: 修复退款问题
Author: 你自己 <you@example.com>
Date:   6 months ago
```

**六个月前的你，留给六个月后的你的全部线索，就是这七个字。**

你打开这次提交的 diff，倒吸一口凉气。里面有 217 行改动，横跨 8 个文件：改了退款金额的取整逻辑、顺手重构了三个 utility 函数、把 `Money` 类的字段从 `decimal` 换成了 `Decimal`（大小写不同的两个类）、还有一行——**就是那一行**——把 `if user.refund_account:` 改成了 `if user.refund_account is not None:`。而这条 message，只提到了"修复退款问题"。

**你恨透了这个六个月前的自己。**

同样的场景，AI 时代还有升级版：

- 你让 Cursor 帮你改一个 bug，它顺手就 commit 了，message 写着 `chore: update code`——**你想 revert 却发现它把三件事塞进了一颗珠子**。
- Copilot 在 PR 里塞了 12 颗小 commit，每颗的 message 都在描述"改了什么代码"，没有一颗告诉你"为什么改"——**评审人翻页翻到手酸**。
- 你在 Aider 里做了一个 30 分钟的功能，`/undo` 撤销了三次，git log 上留下一串 `wip`、`wip 2`、`wip fix`、`wip fix again`——**你自己都不敢 push 上去给同事看**。

本章要摊开的不是"如何写好 commit message"的又一份清单——那种清单网上有一万份，Conventional Commits 官网也就一页纸。本章要做的是**在 AI 时代把这件事重新分工**：哪些环节 AI 已经能替你做到 90 分（就用它），哪些环节 AI 永远替不了你（自己扛）。

---

## 6.2 概念回看：commit 是团队通信协议

先把地图翻到第 2 章那一页：**一次提交是一个不可变的三元组——快照、parent 指针、元信息（作者、时间、message）**。

前两项是给 Git 看的：快照让代码能被完整还原，parent 让历史能被串起来。**message 是给人看的**——给六个月后的自己、给同事、给 blame 上来的救火队员、给 release note 的读者、给两年后接手项目的新人。

这个身份决定了 commit 的本质：**它是团队里最持久的通信协议**。你在群里发的消息 24 小时后就沉底了，你在 Jira 上写的 ticket 三个月后就没人翻了，只有 commit message 会伴随代码走完它的整个生命周期，被 `git log`、`git blame`、`git bisect` 反复调用。

从这个身份出发，"好提交"的标准就自然浮现出来，就两条：

**标准一：原子性——一颗珠子只做一件事。**
一件事的定义是"能被一句话概括、能被作为一个整体 revert、能作为一个独立的评审单元"。改 bug 是一件事，重构是另一件事，改配置是第三件事。三件混在一颗珠子里，六个月后 revert 的时候你会哭。

**标准二：可读性——message 是给人的电报，不是给 Git 的元数据。**
业界共识的格式是 [Conventional Commits](https://www.conventionalcommits.org/)——一种**极简的电报语法**：

```
<type>(<scope>): <subject>       ← 主题行，≤50 字符

<body>                           ← 正文，每行 ≤72 字符，说清"为什么"
                                 ← 空行分隔

<footer>                         ← 关联 issue、breaking change 声明
```

`type` 就那么几个：`feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `perf` / `style` / `build` / `ci` / `revert`。`scope` 是可选的作用域（`auth`、`payment`、`api`）。主题行 50 字符是给 `git log --oneline` 一行显示留的余地，body 72 字符折行是给 `git show` 在 80 列终端里读留的余地——**这些数字不是玄学，是电报时代的物理约束在版本控制里的遗存**。

于是"六个月后能救命"的那颗珠子，长这样：

```
fix(payment): 处理 refund_account 为 None 的情况

用户注销后 refund_account 会被置空，原判断 `if user.refund_account:`
在空字符串场景下也会误判为无效。改用 `is not None` 精确判断。

Fixes #4172
```

三条信息一次到位：**发生了什么**（type+subject）、**为什么这么改**（body）、**关联的上下文**（footer）。六个月后的你打开 blame，一眼看懂，事故 5 分钟内定位。

**AI 在这幅图里能扛哪一段？** 拆下去看。

---

## 6.3 AI 能替你做的三件事

Conventional Commits 是一套**结构化的、可自动化的、语法层面的**规范。任何一个能读懂 diff、能生成短文本的 LLM 都能把它做到 85 分以上。事实是各家 AI 工具都把这件事做成了一键功能——

### 6.3.1 从 diff 生成 message

原理简单粗暴：把 `git diff --cached` 的内容喂给 LLM，配上一个"输出 Conventional Commits 格式"的提示词，得到一段像样的 message。各家把这个流程包装成了不同的 UI：

| 工具 | 触发方式 | 默认格式 | 备注 |
|---|---|---|---|
| **Cursor** | Source Control 面板的 ✨ sparkle 按钮 | 参考仓库历史风格 | 会读你之前的 commit 学习你团队的语气 |
| **GitHub Copilot** | Source Control 输入框 ✨ 按钮 | 相对自由 | 长文摘要能力强 |
| **Aider** | `--auto-commits` 默认开 | Conventional Commits | 每次 AI edit 成功即 commit，可用 `--commit-prompt` 定制 |
| **Claude Code** | `/commit` 斜杠命令 | Conventional Commits | 会附加 `Co-Authored-By: Claude` trailer |
| **Windsurf / Cascade** | Source Control 一键 | 相对自由 | 付费功能 |

**它们哪里已经"够好"？** 对于**内容单一、意图明显**的 diff——比如你改了一个函数名、修了一个 typo、加了一个 utility——AI 生成的 message 90% 时候可以直接 commit，你只需要瞄一眼确认"type 对不对、scope 有没有漏、主题行没写错事实"。

**它们的"够好"里藏着什么陷阱？** 三条：

1. **它会把"做了什么"当成"为什么做"**——因为它只能看 diff，看不到你脑子里的意图。message 里说"把 decimal 改成 Decimal"，但读者想知道的是"为什么改"。**body 的"为什么"永远需要你亲手补一句**——就一句，AI 都写不出来。
2. **它会顺着 diff 的表面语义走**——如果你 diff 里既有 bugfix 又有重构，它可能选一个更"响亮"的写成 `feat`，把另一半藏进 body。**这不是 message 的问题，是 diff 本身该拆的问题**（见 6.4）。
3. **它对"废话"没有免疫力**——`chore: update code`、`fix: minor fix`、`refactor: improve code quality` 这种废话 AI 也会说。**你得对废话有过敏反应**。

### 6.3.2 按逻辑分组拆分提交

第二个能力更值钱：你手上一坨零散改动（改了 3 个文件、跨越两个功能、混着一点重构），让 AI 帮你**按逻辑分组、分批 stage、分批 commit**。

比如你可以这么说：

> "看一下我当前 unstaged 的改动。按逻辑功能给我分成 3–5 组，每组一次 commit。给我每组包含的文件和 hunks，以及每组的 commit message 草稿。**先只列出方案，不要执行。**"

现代 AI 工具能把这活干得像模像样——它会用 `git diff` 看改动、用启发式规则分组（同一模块的改动放一起、测试文件跟着源文件、纯注释改动单独一组），最后用 `git add -p` 或 `git add <path>` 分批 stage。**这是"AI 时代原子提交观"的第一次兑现**：你不必再在写代码的时候强迫自己"改一点就 commit 一次"，你可以自由地写、写乱、写多，最后请 AI 帮你**做提交前的整理师**。

Aider 把这件事推到了极端：**每一次 AI 编辑成功即自动 commit**。你的 git 历史会变成一串"AI 每完成一小步就存档一次"的原子记录，`--auto-commits` 是默认开的。想撤销上一步？`/undo` 一键 reset。这是全书目前见到的、**离"每颗珠子只做一件事"最近的一种工作流**。代价是历史会变得很密（一个功能可能 20 颗珠子），需要在 push 之前用 rebase 挤水（见 6.6）。

### 6.3.3 生成 release notes

第三个能力是"跨提交的摘要"：给它一段 commit 范围（`v1.2.0..HEAD`），让它总结成用户能读懂的 release note。

```
🟢 「把 v1.2.0..HEAD 之间的所有提交按类型分组，
     生成一份面向用户的 release note。
     feat 归 'New Features'、fix 归 'Bug Fixes'、
     其余归 'Other Changes'。用户不关心的（chore/style/refactor）
     可以合并成一行。写完给我 markdown。」
```

原理和写 commit message 一样，只不过输入从"一次 diff"扩大到了"一段 commit 列表"。Claude Code 的 `/commit-push-pr` 插件、Copilot 的 PR 描述自动填充、Cursor 的 commit 摘要都是这条路径上的实现。**这也顺手证明了 6.2 那条主张：Conventional Commits 的 type 前缀不是仪式，是给下游自动化留的抓手。** 你今天多写一个 `fix:`，明天 release note 就能少一次人工分类。

---

## 6.4 AI 替不了你的三件事

上面三条都是"语法工作"。语法工作 AI 做得动。但 commit 这件事里，还有三件**判断工作**——它们是本章存在的真正理由，也是"AI 时代提交观"里最需要人守的一段。

### 场景一：这坨改动，该拆成几颗珠子？

**症状**：你埋头写了两小时，`git status` 一看，18 个文件被改过，涵盖了：给购物车加了"优惠券"功能、顺手把 `utils/date.py` 里的一个函数改名了、给测试目录补了几个 fixture、还把 README 更新了。**要不要一次性 commit 掉？还是拆成几颗？**

**三个候选方案**：

- **方案 A：一次 `git add . && git commit -m "feat: 优惠券功能"`**。快、省事、AI 一键搞定。**代价**：`utils/date.py` 的重命名藏在这颗珠子里，六个月后有人 blame 到这行会一脸问号；如果优惠券功能要 revert，重命名也被一起撤销了。
- **方案 B：一颗珠子一件事，拆成 4 颗**。`feat(cart): 增加优惠券` / `refactor(utils): 重命名 date.parse 为 date.parse_iso` / `test(cart): 补齐优惠券测试 fixture` / `docs: 更新 README 的优惠券章节`。**代价**：要花 3–5 分钟做拆分。**收益**：每颗珠子都能被独立评审、独立 revert、独立 cherry-pick。
- **方案 C：让 AI 全权决定拆分**。`git status | AI` → "按逻辑帮我拆"。**代价**：AI 分得对不对得看运气——它可能把 fixture 拆进 `feat` 里（因为文件路径靠得近），也可能把 `date.py` 的重命名归为 `feat`（因为它跟 cart 是同一次 session 里改的）。

**判断规则**（内化后可以两秒决定）：

> **一颗珠子 = 一句能干净说完的话。**
> 如果你的 message 里出现了"以及"、"顺便"、"还"、"and also"，就是在提示你**应该再切一刀**。
> 唯一的例外：**同一意图下的连带改动**——比如加优惠券功能连带补了它的测试，测试跟功能是同一颗珠子的一部分；但**重构 date.py**不是"顺便"，它是一件独立的事，独立一颗。

用一句更狠的话说：**revert 是不是能干净地撤销一件事，是这颗珠子该不该被造出来的黄金试金石**。你造完之前先问自己一句"如果这颗珠子要被 revert，会连带撤销掉多少无关的事？"——超过零，就再切一刀。

**🟡 AI 指令**（黄色——AI 提议、你决定）：

> "我现在有一堆 unstaged 改动。**先只做诊断**，别 stage 别 commit：
> 1) 列出所有变动的文件和每个文件的 diff 摘要。
> 2) 按'一颗珠子一句话'的原则给我一个拆分方案（3–6 组），每组给出：包含哪些 hunks、建议的 Conventional Commits 主题行、你的理由。
> 3) 如果你觉得某两组'合并 vs 拆开'边界模糊，把两个选项都列出来让我决定。"

看完再说"OK，按方案二执行"或者"把第 2 组和第 4 组合并"。**AI 提方案，你按快门**——这是本章最关键的一次分工。

### 场景二：现在这个时点，该不该 commit？

**症状**：你刚写完一半功能，测试还没跑，代码里有几个 `TODO`，甚至有一处编译过不了。老板路过说"我马上要看昨天你说的那个 demo"。**现在要不要 commit 一下自保？**

**三个候选方案**：

- **方案 A：直接在当前分支 commit 一颗 `wip` 珠子**。快，代价是主分支的历史里多了一颗半成品；如果这颗珠子被 push 出去，同事拉下来会莫名其妙。
- **方案 B：`git stash`**。看似干净，代价是 stash 是**栈**——第 3 章讲过——你等下再手忙脚乱又 stash 一次，栈里堆了三个之后你就分不清哪个是哪个了。而且 stash 存活于本地 reflog，**它不会跟着分支走**。
- **方案 C：先开一个 wip 分支，把半成品 commit 到那个分支上，然后从主干开新分支应付老板**。慢一点，但**半成品在自己的分支上安睡**，你随时可以回来续写，命名清晰，还能 push 到远端（如果你和团队约好了 `wip/*` 分支的规矩）。

**判断规则**：

> **看你多久会回来。**
> - 5 分钟内回来（去个厕所、接个电话）：什么都不做，工作区放着就行。commit 是仪式，不是刚需。
> - 30 分钟到 2 小时内回来（临时救火）：**方案 C——wip 分支**。半成品有名字、有位置、有时间戳，切回来时你的脑子能接得上。
> - 超过一天或者要换电脑：**必须是方案 C**——因为半成品还得跟你走远，stash 会随着 reflog 30 天过期，wip 分支不会。
> - **永远不要选方案 A**（除非那就是你的独立开发分支，且你确信没人会拉这颗珠子）。

这条规则背后其实是第 3 章"规则三"的回响：**并行推进两条线时，开分支是唯一正解，不要用 stash 凑合**。第 3 章讲的是场景层面的判断，本章把它落实到"提交时点"这个具体维度上。

**🟢 AI 指令**：

> "我有一坨半成品的改动想临时存起来去做别的事。给我三个方案对比：
> 1) 直接 commit 在当前分支
> 2) git stash
> 3) 开一个 wip 分支 commit 过去
> 分别说清楚：命令序列、7 天后能不能找回、如果我换台电脑还能不能续、如果我 push 了会不会污染队友的历史。"

### 场景三：这个"半成品"，是不是根本就不该 commit？

**症状**：AI 生成的 commit message 是 `feat: 添加登录页面`，你打开 diff 一看——它把 `console.log('debug')` 也一起 commit 了、把你测试用的假 token 也 commit 了、还有几行 `.env` 里的敏感字段被它 echo 进了配置文件的注释里。

**三个候选方案**：

- **方案 A：信 AI，直接 push**。**灾难**。调研 2 里 shoofly.dev 的关键论断：**`.gitignore` 并不能阻止 AI Agent 读取 `.env`**——Agent 直接读文件系统，可能把内容顺手 echo 进代码或复述进 commit。CSA 研究显示三个不同的 coding agent 都会从 issue、PR 描述、仓库文件里"顺手"提取 CI/CD secrets 塞进提交。
- **方案 B：commit 前跑一遍 `git diff --cached` 亲眼过一遍**。慢，但**是唯一救得回来的时点**。一旦 push 到 GitHub，密钥就得当作已泄漏处理（第 12 章会讲一次完整的凭证轮换流程）。
- **方案 C：装一个 pre-commit hook，用 `gitleaks` / `trufflehog` 之类的工具自动扫描**。一劳永逸的方案，团队协作时强烈推荐；但初次接入需要 10 分钟配置。

**判断规则**：

> **AI 生成的 commit，push 之前你必须至少扫一眼 diff。**
> 三条最低限度检查：① 有没有 debug/console.log/print 遗留？② 有没有假数据、临时 token、绝对路径？③ 敏感字段（`.env*`、`*.pem`、`*.key`、`id_rsa*`、`*credentials*`）名字出现在 staged 列表里？只要命中其一，**回车键就得停 3 秒**。

**🔴 AI 指令**（红色——必须人肉复核）：

> "在你 commit 之前，**先跑三步只读检查**：
> 1) `git diff --cached --stat`，列出这次要提交的所有文件。
> 2) `git diff --cached --name-only | grep -iE '\.env|\.pem|\.key|credential|secret|token|id_rsa'`，命中的任何文件就停下告诉我。
> 3) `git diff --cached | grep -iE 'console\.log|print\(|debugger|TODO|FIXME|localhost:|127\.0\.0\.1'`，命中的地方列给我看。
> **上面任何一条报警就停，不要 commit。** 都干净再执行 commit。"

这条指令值得作为一条别名放在你的 CLAUDE.md / `.cursor/rules` / AGENTS.md 里，每个 AI 会话都自动加载。第 12 章会把它扩写成完整的 Sensitive-file Guard 模式。

---

## 6.5 WIP 存档战术：分支 vs stash 的最终对决

上面场景二已经点了这件事，本节把它彻底说透——因为**这是每个开发者每天都要做十次的微决定**。

先摆两个工具的物理事实：

**`git stash`**：把工作区和暂存区的改动打包成一个特殊的引用（`refs/stash`），存进一个栈（stack）。它是本地的、易失的、非分支绑定的。
- 栈：后进先出，多次 stash 会堆叠。
- 本地：不能 push，换台电脑就没了。
- 易失：只挂在 reflog 上，Git GC 一到（默认 30 天）就可能被清理。
- 非分支绑定：你在分支 A 上 stash 之后切到分支 B 再 `stash pop`，它会尝试把改动应用到 B 上——**这既是特性也是坑**。

**wip 分支**：一个正常的分支，只是名字上带一个 `wip/`、`spike/` 前缀，里面的 commit 允许粗糙。
- 正常引用：`refs/heads/wip/xxx`，40 字节，全套 branch 语义。
- 可 push：与团队约好命名前缀后，可以推到远端云同步。
- 长寿：只要标签在，珠子就在，30 年也不会消失。
- 分支绑定：半成品和主线不会混。

**对比表**：

| 维度 | `git stash` | wip 分支 |
|---|---|---|
| 存活时长 | 30 天（reflog 保护期） | 永久（只要标签在） |
| 能否 push 到远端 | ❌ 只有本地 | ✅ 全套分支语义 |
| 能否换电脑续 | ❌ | ✅ |
| 半成品数量爆炸时 | 栈越堆越乱 | 分支列表清晰 |
| 心智成本 | "我 stash 了什么来着？" | 分支名就是答案 |
| 适合场景 | 5 分钟以内的临时插入 | 超过 30 分钟的并行开发 |

**AI 时代的加强判断**：如果你在用 Aider 或 Claude Code 这种"AI 会主动 commit"的工具，**永远选 wip 分支**——因为你根本不确定 AI 什么时候会替你 commit 什么，主分支的干净度必须靠"隔离"来保证，而不是"记住"。让 AI 在 `wip/ai-<日期>-<任务>` 这样的独立分支上闹腾，主分支永远只接受你亲手 rebase 整理过的干净历史。

**🟢 AI 指令 · wip 分支模式**：

> "我要开始做一个探索性的任务：{任务描述}。给我建一个 wip 分支，命名格式 `wip/2026-09-15-{短描述}`，从当前 main 长出来，切过去。**接下来在这个分支上你可以自由 commit，message 允许粗糙**——我们打算最后 squash rebase 成 1–3 颗干净的珠子再合回 main。"

一整天写完，回来一次性 `git rebase -i main` 挤水（见第 5 章）——**AI 可以帮你把粗糙的 20 颗 wip 珠子重写成 3 颗漂亮的珠子**，rebase 期间的 conflict 让它一起解，你只做最后审阅。这就是 AI 时代的"每次 AI edit = 一次 atomic commit"和"push 出去的历史干净"两个诉求的和解方案。

---

## 6.6 协作约定：AI 生成的 message 到底要不要人工过目？

这是本章最容易吵架的一节。两派观点：

**"要过目"派**：AI 只看 diff，看不到意图。它写的 message 是**表面事实**，不是**根本原因**。message 是团队的通信协议，通信协议出错的代价是六个月后的救火队员多花一小时——你的一分钟盯审，是团队的六个月保险。

**"不必过目"派**：AI 已经很准了，团队每天上百个 commit，逐条审阅是 bottleneck；不如通过 CI（commitlint 之类）保证格式正确，语义交给平均质量，出问题再修。

本书站"要过目"派——但要给出**站得住的证据**，不是意识形态。举一个真实感十足的假想案例：

**案例：一颗 message 写着"修复登录 bug"、diff 里藏着重构的珠子**

你让 Cursor 帮你修一个登录页面的空指针。它扫了代码，改了 `login.py` 第 42 行的空判断——没问题。**然后它顺手做了三件你没让它做的事**：把 `login.py` 里的一个大函数抽成了三个小函数（因为"这样更 Pythonic"）、把老式的 `%s` 格式化换成了 f-string（因为"更现代"）、把两处 `logger.info` 改成了 `logger.debug`（因为"这不该是 info 级别"）。

它生成的 message 是：

```
fix(auth): 修复登录时的空指针问题
```

**技术上没错**——那一行空指针的确修了。但 diff 里 90% 的改动是**它自主决定的重构**，message 里只字未提。这颗珠子被 merge 进 main 之后：

- 半年后有人 blame 到某行 f-string，看到 `fix(auth): 修复登录时的空指针问题`，一脸问号。
- 有人想 revert 这颗珠子——因为发现那次重构导致了另一个隐蔽 bug——但 revert 会把空指针修复也一起撤销。
- release note 里只会说"修了个登录 bug"，用户完全不知道日志级别变了、函数结构变了。

**这不是 message 写得烂，是 diff 和 message 不匹配。而这类不匹配，AI 自己检测不出来——它只看 diff，写下"它自认为的摘要"，摘要必然偏向它认为最重要的一件事，把其他事悄悄埋进 body 或干脆不提。**

于是"要过目"派的立场其实是两条：

> **① message 由 AI 起草，你至少读一遍并修一句"为什么"。**
> **② 如果 diff 和 message 的比例不对（message 说 A，diff 里 A 只占 10%），把 diff 拆了再 commit，别硬写 message。**

第二条比第一条更重要——**当你想"重写 message 来盖住 diff 的复杂性"时，那是在提示你 diff 该拆了**。这个感觉就是场景一的判断规则的另一次兑现。

**给 AI 用的团队约定**（可以直接抄进 CLAUDE.md / `.cursor/rules` / AGENTS.md）：

```markdown
## Commit 生成约定

- 每次 commit 前先跑 `git diff --cached --stat` 报告变动比例。
- 如果某个文件的改动看起来跟 commit 主题无关，先停下问用户。
- Commit message 主题行 ≤ 50 字符，正文 ≤ 72 字符折行。
- 使用 Conventional Commits：feat / fix / refactor / docs / test / chore / perf。
- 正文必须包含"为什么这么改"，不只是"改了什么"。
- 敏感文件检查：.env* / *.pem / *.key / *credentials* 出现在 staged 列表即停止。
- 不主动 push；push 由用户显式指令触发。
```

---

## 6.7 末节：让 AI 当"提交审查员"——做一次代码考古

commit 的读者除了 blame 上来的救火队员，还有一位常被忽略的角色：**你自己，一周后、一个月后、半年后**。你今天写的 commit 是一个个漂流瓶，一段时间后的自己会成为收件人。

这个"未来读者"视角有个好用的操作化姿势——**让 AI 做定期代码考古**：把最近 10 颗珠子丢给它，让它像不认识你一样评点。

**🟢 AI 指令 · 每周考古**：

> "把最近 10 颗提交 (`git log -10 --pretty=fuller --stat`) 拿去审阅。对每一颗告诉我：
> 1) 主题行是不是 ≤50 字符，type 有没有用对？
> 2) 有没有 body？body 是不是在写'为什么'，不是在复述 diff？
> 3) diff 的规模和 message 说的事情比例合理吗？（有没有'塞私货'的痕迹）
> 4) 如果六个月后有人 blame 到这颗珠子，能不能一眼看懂？
> 
> 给出总分、每颗打分（1–5 分）和最需要改进的那颗。**不要修改历史**，只做审阅报告。"

这条指令的绝妙之处在于——**它不修历史（安全），只暴露问题（有用）**。你会发现：

- 有些 message 你写的时候觉得很清楚，一周后看完全看不懂——**你写少了 body**。
- 有些珠子塞了两三件事——**当时的你偷懒了，现在被 AI 抓到**。
- 有些 `chore: update` 混在里面——**这不是提交，是垃圾**。

久了你会自然内化本章讲的所有规则，因为你每周会被一个中立的第三方（AI）打一次分。**这是本章最经济的实操收尾——你不必背 Conventional Commits 的规则，让 AI 每周替你做一次审计就行。**

进阶版：**做一次月度审查**——让 AI 分析最近 100 颗提交的类型分布（`feat` 占多少、`fix` 占多少、`chore` 占多少）。如果 `chore` 占比过高，说明团队大量精力花在了非产品价值的事情上；如果 `fix` 占比过高，说明质量流程有问题；如果 `refactor` 常年为零，说明技术债在悄悄堆积。**commit 的类型分布是团队健康度的一份免费体检报告，只要你之前把 Conventional Commits 用起来了。**

---

## 6.8 命令侧栏

```
git commit -m "..."               # 造一颗珠子，附上电报
git commit                        # 打开编辑器写完整的 message
git commit --amend                # 重造上一颗珠子（第 2 章讲过）
git add -p                        # 交互式选 hunks 分批 stage
git diff --cached                 # 看这次要 commit 的东西（人肉复核必备）
git diff --cached --stat          # 看这次 commit 的规模
git diff --cached --name-only     # 只列文件名（配 grep 做敏感文件扫描）
git log --oneline -10             # 看最近 10 颗珠子的主题行
git log --pretty=fuller           # 看完整元信息（作者、committer、时间）
git log v1.0..HEAD                # 看某段范围内的所有提交（release note 用）
git rebase -i <base>              # 交互式重写历史，squash / reword / reorder
git stash                         # 压栈暂停（30 分钟内的临时插入）
git stash pop                     # 出栈恢复
```

不需要背。需要时回来看，或者直接说人话让 AI 翻译。

---

## 6.9 本章小地图

```
commit = 一颗不可变的珠子 + 一段给人看的电报（message）

好提交的两条标准：
  ① 原子性：一颗珠子一件事 ──▶ revert 试金石：能不能干净地撤销一件事？
  ② 可读性：Conventional Commits + body 写"为什么" ──▶ 六个月后的自己看得懂

AI 分工：
  ┌─ AI 做得动（语法工作）─────────────┬─ AI 做不了（判断工作）───────────┐
  │ · 从 diff 生成 message              │ · 判断拆分边界在哪              │
  │ · 按逻辑分组、分批 stage            │ · 判断此时该不该 commit         │
  │ · 跨提交摘要（release note）        │ · 判断半成品该不该以 wip 存档   │
  │ · 每周做代码考古（审阅报告）        │ · 判断 message 和 diff 是否匹配  │
  └─────────────────────────────────┴─────────────────────────────────┘

半成品存档决策：
  5 分钟内回来 ──▶ 什么都不做
  30 分钟到 2 小时 ──▶ wip 分支（不要 stash！）
  超过一天 / 换电脑 ──▶ 必须 wip 分支
  AI 参与开发 ──▶ 一律 wip 分支（隔离主分支的干净度）

红黄绿三色：
  🟢 让 AI 生成 message、拆分方案、release note、每周审阅
  🟡 让 AI 拆 commit / squash 历史 —— 先给方案，你按快门
  🔴 push 之前必须人眼扫 diff：debug 遗留、假数据、敏感文件
```

**三大典型误解拆解**

1. **"AI 会生成 message 了，我就不用管 commit 了。"** ——AI 只能看 diff，看不到意图。它写的是"发生了什么"，不是"为什么"。**你必须补一句"为什么"**，否则六个月后你自己都看不懂。更狠的一点：AI 有时会自作主张多改一些无关的东西，然后写一句只描述主任务的 message——**diff 和 message 不匹配的珠子是最毒的珠子**，因为它骗过了未来的所有 blame。

2. **"半成品用 stash 就够了。"** ——stash 是本地的、易失的、栈式的。它适合 5 分钟内的临时插入，超过就成了负债。**stash 里超过三个改动的开发者，正在积累一场必然发生的意外**。分支是免费的（第 3 章推论一），wip 分支只是一个约定俗成的前缀，命名清晰、可 push、不过期——**没有理由不用**。特别是 AI 时代：你自己都不知道 AI 什么时候替你 commit 了什么，主分支的干净度必须靠"隔离"守，不是靠"记住"守。

3. **"Conventional Commits 就是形式主义。"** ——两个反例：① 你今天多写一个 `fix:` 前缀，明天 release note 自动化才能少一次人工分类，`git log --grep '^fix' v1.0..HEAD` 才能一秒钟给你所有 bugfix 列表；② `type` 分布是团队健康度的免费体检报告——`chore` 过多说明团队被杂事拖累、`fix` 过多说明质量流程有问题、`refactor` 常年为零说明技术债在堆积。**形式主义之所以能坚持几十年，是因为它在结构化的输入上换来了无穷的下游自动化**——commit message 是最典型的例子。

---

**下一章预告：** 珠子造好了，串成了漂亮的项链。接下来的问题是：**你的项链、同事的项链、release 的项链、hotfix 的项链，它们怎么组织成一个团队能长期跑下去的策略？** 是所有人都在 main 上快跑（Trunk-Based）、还是各有 feature 分支等 review（GitHub Flow）、还是分 develop / release / hotfix 三层（GitFlow）？第 7 章一次讲清三大策略、给出选型决策树，以及每种策略下 AI 协作模式的差异。

---

> **🤖 AI 指令箱 · 本章实战演练**
>
> 找一个你自己的真实仓库，把这几条指令依次发给 AI，看看它对你的 commit 历史有多严厉：
>
> - 「把我最近 20 颗提交按 Conventional Commits 规则打分，1–5 分制。列出打分表和每颗的主要问题。**不要修改历史**。」
> - 「看一下我当前 unstaged 的所有改动。**先只做诊断**：按'一颗珠子一句话'拆分成 N 组，给出每组的文件、hunks、message 草稿、你的理由。我看完再决定执行。」
> - 「我准备 commit 了。**先做红色区检查**：① `git diff --cached --stat`；② 敏感文件扫描（.env / .pem / .key / credentials）；③ debug 遗留扫描（console.log / print / TODO）。任何一条报警就停。」
> - 「把 v1.0..HEAD 之间的所有 commit 按 type 分组，生成一份面向用户的 markdown release note。chore/style/refactor 合并成一行。」
> - 「以我们仓库最近 30 颗 commit 的 message 风格为参考，给我 staged 的这些改动生成一条 Conventional Commits 格式的 message。要有 body。**body 里必须写清楚'为什么'**——如果 diff 里看不出为什么，就在 body 里问我。」
