# 第 8 章　Worktree：一个人干三个人的活

> 《Git 的概念地图》第 8 章 · 场景章 · v1.0
> 场景决策部分的第三章：从"团队怎么并行"（第 7 章）落到"你一个人怎么并行"。
> 结构：症状 → 候选方案 → 判断规则。三段式。

---

## 8.1 场景引入：一个上午的四次打断

上午 9:47。你正在写一个复杂的表单校验逻辑，脑子里同时装着六个字段的依赖关系，手边打开着三份文档、两个 Chrome 标签页。你写到一半——半成品，跑不通，测试都还没写。

9:48。测试环境报警红了。产品跑过来："线上刚才那个下单接口 500 了，能不能先看一眼？"

你手指停在键盘上，心里盘算：

- 用 `git stash` 把当前改动压进去，然后切到 main 开个 hotfix 分支？——问题是你现在头脑里的上下文全在这个 feature 上，切走一趟回来还得重新加载十分钟。
- 直接 `git commit -m "WIP"` 把半成品钉在自己的 feature 分支上？——好一点，但切分支意味着**你的工作目录会被 Git 替换**，那些没保存的 IDE 状态、跑到一半的开发服务器、正在 debug 的浏览器 tab，都要重来。
- 干脆开一个新的终端窗口，`cd` 到另一个地方——但另一个地方从哪来？重新 clone 一份仓库要花几分钟，还占硬盘。

三个选项都痛。

9:53。你选了 stash。切到 main、拉最新、开分支 `hotfix/order-500`，修 bug，push，PR，合并。总耗时四十分钟。回来 `git stash pop`——冲突。因为 hotfix 里改了跟你半成品重叠的一个 util 函数。你花二十分钟解冲突，把脑子里的上下文重新拼起来。

10:57。刚坐下写第二个字段的校验，Slack 又亮了：设计师问能不能帮忙 review 一个前端同事的 PR，"就看看那个组件的交互逻辑就行"。这次的痛点变了——你不需要修改任何代码，只是想**在自己电脑上把那个 PR 跑起来看看**。

- stash + 切分支 + 装依赖 + 起服务器？——你现在的服务器还在跑，切分支它会中断。
- clone 一份？——占硬盘，装依赖又要两分钟。

11:36。你把 review 应付过去了，还没开始写下一段代码。这时候另一个消息：AI agent 在后台跑了一个大重构任务，快跑完了，需要你的工作区来 apply diff——**它要占用你的工作目录**。

你把电脑合上，去楼下买了杯咖啡，考虑要不要辞职。

---

上面这一个上午，四种打断的**共同结构**是这样的：

> **你需要在同一个仓库里，同时处于多个"分支状态"上。不是先后切换，是同时并存。**

Git 的传统答案是"切换"——`git switch feature` 把工作目录变成 feature 的样子，`git switch main` 把它变回 main 的样子。工作目录只有一个，同一时刻只能长成一副样子。所有的痛都从这个约束里长出来。

而这一章要摊开的这张地图，讲的是 Git 内置的一个被严重低估的功能——**worktree**——它把上面那个约束打破了。让你**在同一个仓库上，同时铺开多张工作台**。

---

## 8.2 祛魅时刻：一个 `.git/`，多个工作目录

回到项链-珠子-名牌的比喻体系（第 2、3 章）。

- 提交是**珠子**（不可变快照）。
- 历史是**项链**（珠子串起来）。
- 分支是**名牌**（挂在某颗珠子上的可移动书签）。
- 远程是**镜子里的另一条项链**（另一份缓存的副本，第 4 章）。

现在多一个新概念：

> **Worktree 是一张工作台。**
>
> 同一条项链（同一个 `.git/` 数据库）可以同时铺开在**多张工作台**上——每张台上摊开的珠子形态可以不同（各自 HEAD 指向不同的 commit），但珠子本体是**共享**的（对象库、引用表都只有一份）。

传统认知里，"仓库"和"工作目录"是一体的——你 clone 出来一个文件夹，`.git/` 藏在里面，工作文件摊在外面。这两者绑死了：一个文件夹 = 一个仓库 = 一个工作目录 = 同时只能站一个分支。

worktree 打破的就是**最后一层绑定**：

> **仓库（`.git/` 数据库）和工作目录是可以解耦的。**
> **一个 `.git/` 可以服务 N 个工作目录，每个工作目录站在不同的分支上。**

用 ASCII 图看清楚：

```
                    ┌─────────────────────────┐
                    │      .git/  (共享)       │
                    │                          │
                    │  ┌─ objects/            │ ← 珠子本体（对象库）
                    │  ├─ refs/               │ ← 所有引用（分支/tag）
                    │  ├─ HEAD → main         │ ← 主工作台的 HEAD
                    │  └─ worktrees/          │ ← 其他工作台的 HEAD
                    │       ├─ hotfix/HEAD    │
                    │       └─ review/HEAD    │
                    └─────────┬───────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ 主工作台     │  │ 工作台 A     │  │ 工作台 B     │
     │ ~/proj/     │  │ ~/proj-hot/ │  │ ~/proj-rev/ │
     │ 站在 main    │  │ 站在 hotfix │  │ 站在 pr/42  │
     │ ↑ 你写代码   │  │ ↑ 你修 bug  │  │ ↑ 你跑评审  │
     └─────────────┘  └─────────────┘  └─────────────┘
```

**每张工作台是一个独立的文件夹**，文件夹里长得像一个完整的项目——源码、node_modules、构建产物、跑起来的服务器——但它没有独立的 `.git/`（有一个特殊的 `.git` **文本文件**指回主仓库）。所有对象、所有分支引用，都是从主仓库共享读写。

这带来了三个立刻可用的性质：

**性质一：便宜。** 新开一个 worktree 不复制 `.git/`（可能几百 MB 甚至几 GB），只 checkout 一次工作文件。用完删掉工作台，不影响主仓库。

**性质二：独立。** 每张工作台有自己的 HEAD、自己的工作文件、自己的 IDE 窗口、自己跑着的开发服务器。**互不打架。**

**性质三：一致。** 你在工作台 A 提交的 commit，工作台 B 立刻能看到（`git log` 里就有），因为对象库共享。你在 A 上创建的分支，B 上 `git branch` 也能看到。**数据是一份，视图是多张。**

### 一条 Git 的自我保护红线

worktree 有一条强制约束，值得单独拎出来记住：

> **同一个分支不能同时被两个 worktree 检出。**

你在主工作台上站在 `main` 上，就没法在另一个 worktree 上也检出 `main`——Git 会直接拒绝，报 `'main' is already checked out at ...`。

这条约束**不是为难你**。它是 Git 内建的自我保护——如果允许两张工作台同时改同一个分支，那分支引用（`refs/heads/main`）该指向哪次提交？两张台子各自的 index、各自的未提交改动，会互相冲刷。Git 直接从根上禁止了这种混乱。

绕开的方式是**给每张工作台一个自己的分支**——本来 worktree 的核心用法就是这个。要在两个地方看 main，你可以在其中一张台上创建 `main-review` 之类的临时分支从 main 拉过来，那就是两条独立的分支了。

（后面 8.6 节会展开这个约束在 AI agent 场景下的具体使用姿势。）

---

## 8.3 症状 → 候选方案 → 判断规则

分支策略章（第 7 章）的四问决策树是"团队决策"，本章的决策树是"你自己一个人当下这一刻的决策"。

先摆症状：

- **S1**：你在写代码，被叫去修一个 hotfix。
- **S2**：你在写代码，需要跑起另一个分支/PR 看效果（评审、demo、复现 bug）。
- **S3**：你在写代码，AI agent 想占用工作目录跑一个长任务。
- **S4**：你想试一个大重构或 rebase 实验，怕搞砸主工作区。
- **S5**：你在等一个长跑的测试/构建/CI，同时想推进别的工作。
- **S6**：你想同时开两个方向的功能（一个新特性 + 一个数据迁移脚本），彼此独立。

再摆候选方案：

- **A. Stash + 切分支**：`git stash`（或 `git stash push -m "wip"`），切到目标分支干活，回来 `git stash pop`。
- **B. Commit WIP + 切分支**：把半成品 `commit -m "WIP"` 钉在当前分支，切走，回来续写（用 `commit --amend` 收尾或 `reset --soft HEAD^` 还原到未提交状态）。
- **C. Worktree**：`git worktree add ../proj-hotfix hotfix/xxx`，在**新的目录**里干活，主工作区一动不动。
- **D. Clone 一份**：`git clone <本地路径> ../proj-copy`，或者直接 `cp -r` 整个仓库。

同一张判断表，把六个症状和四个方案对上：

| 症状 | 首选 | 说明 |
|---|---|---|
| S1 短 hotfix（< 15 分钟能修完） | A（Stash） | 简单直接。切回来 pop 就好。冲突概率低。 |
| S1 长 hotfix（可能超过半小时，或改动会跟你半成品重叠） | **C（Worktree）** | 主工作台的 IDE/服务器/上下文一动不动。修完直接删掉工作台。 |
| S2 review / 跑另一个 PR | **C（Worktree）** | 你完全不想动主工作区，还要另装依赖跑服务。这就是 worktree 的经典场景。 |
| S3 让 AI agent 干活 | **C（Worktree）** | 招牌场景。见 8.6。 |
| S4 试危险操作（大 rebase、reset、脚本重写历史） | **C（Worktree）** | 在独立工作台上做，搞砸了整支扔掉，主工作区毫发无损。 |
| S5 长跑测试 / 构建期间想推进别的事 | **C（Worktree）** | 主工作台被测试占着，你在另一张台上继续写。 |
| S6 两个方向的并行功能 | 看情况：C 或 B | 如果两个方向都需要频繁切换环境和跑服务，worktree；如果只是"心理上并行"其实一次只做一件，两个分支 + `switch` 也够。 |
| **反面**：你只是暂停 5 分钟去接杯水 | 什么都不用 | 保存文件走人。别过度设计。 |
| **反面**：你只是想"备份一下再改" | B（WIP commit）或 tag | 打个 tag 或者提交个 WIP，比开 worktree 轻。 |

### 一个三维对比表（stash / worktree / clone / 新分支）

| 维度 | Stash | 新分支（同工作台） | **Worktree** | Clone / cp -r |
|---|---|---|---|---|
| 心智模型 | 压栈暂停 | 换个名牌，同一张台 | **另开一张工作台** | 整个仓库搬家 |
| 硬盘开销 | 零 | 零 | 只多一份工作文件（`.git/` 共享） | 多一份 `.git/` + 一份工作文件（可能几百 MB～几 GB） |
| 上下文丢失 | 高（IDE 状态、服务器全断） | 高（同上） | **零**（主工作台一动不动） | 低（新目录，但依赖要重装） |
| 分支共享 | 是（同一仓库） | 是 | **是**（共享 `.git/`） | 否（两个 `.git/`，需要 push/fetch 同步） |
| 冲突风险 | 有（pop 时） | 有（切回来时） | **无**（主工作台的未提交改动不受任何影响） | 无 |
| 适合的时长 | 秒到分钟级 | 分钟到小时级 | **分钟到天级** | 天到永久级（比如你要长期维护一份实验分叉） |
| 反面案例 | 堆积三个 stash 后忘了哪个是哪个 | 半成品被"WIP commit" 污染 log | 忘了删除，仓库多了一堆游离工作台 | 硬盘爆炸，两份 `.git/` 不同步 |

一句话决策规则：

> **只是"暂停一下"用 stash；要"同时干"就上 worktree；只有"这个仓库我要长期分叉出去"才用 clone。**

---

## 8.4 机制解剖：git worktree add 到底做了什么

命令一条：

```
git worktree add ../proj-hotfix hotfix/urgent-fix
```

拆开看，Git 干了四件事：

1. **在你指定的路径下创建一个新目录** `../proj-hotfix`。
2. **在这个目录里 checkout 分支 `hotfix/urgent-fix` 的工作文件**（如果这个分支不存在，可以加 `-b` 自动创建）。
3. **在新目录里放一个 `.git` 文本文件**（不是目录！是文件！），内容是一行 `gitdir: /path/to/main-repo/.git/worktrees/proj-hotfix`——指回主仓库。
4. **在主仓库的 `.git/worktrees/proj-hotfix/` 目录里**记录这个工作台的元数据：它的 HEAD、它的 index、它的 gitdir 反向指针。

看一眼真实的目录结构：

```
~/projects/myapp/                 ← 主工作台
├── .git/                          ← 真正的数据库在这里
│   ├── objects/                   ← 所有珠子
│   ├── refs/                      ← 所有引用
│   ├── HEAD                       ← 主工作台指向 main
│   └── worktrees/                 ← 其他工作台的登记簿
│       ├── proj-hotfix/
│       │   ├── HEAD               ← 那个工作台指向 hotfix/urgent-fix
│       │   ├── index
│       │   └── gitdir             ← 反向指针，指回 ../proj-hotfix/.git
│       └── proj-review/
│           ├── HEAD
│           ├── index
│           └── gitdir
├── src/
├── package.json
└── ...

~/projects/proj-hotfix/           ← 副工作台（worktree A）
├── .git                            ← 【文本文件】gitdir: .../worktrees/proj-hotfix
├── src/
├── package.json
└── ...

~/projects/proj-review/           ← 副工作台（worktree B）
├── .git                            ← 【文本文件】gitdir: .../worktrees/proj-review
├── src/
├── package.json
└── ...
```

看清了几件事：

- **对象库只有一份**（在主仓库的 `.git/objects/`）。你在副工作台上创建的 commit，本质上是往主仓库的 objects/ 里写新对象。三张工作台的 `git log` 看到的是同一份历史，因为它们本来就在读同一份对象库。
- **引用表只有一份**（在主仓库的 `.git/refs/`）。副工作台创建的分支，`git branch -a` 在主工作台上立刻能看到。你在副工作台上 `git fetch`，抓下来的远程分支也是全局可见。
- **HEAD 是每张工作台独立的**。主工作台 HEAD 指向 main，副工作台 HEAD 指向 hotfix。它们互不干扰——这就是"同时站在多个分支上"的技术实现。
- **副工作台的 `.git` 是一个文本文件**，不是目录。这就是为什么你不能简单 `cp -r ~/projects/myapp ~/projects/proj-copy` 来达到 worktree 的效果——那个 `.git/` 是完整目录，你复制过去会得到两个各自独立、互不认识的仓库。

### 为什么这个设计能自然满足"独立"和"共享"

**独立的部分**：HEAD、index（暂存区）、工作文件——这些是"当下这张工作台在做的事"，各自一份。你在副工作台上 `git add` 的文件，主工作台上 `git status` 看不到，因为 index 是分开的。

**共享的部分**：对象、引用、hooks、config——这些是"仓库层的事实"，只有一份。你在副工作台上 push 出去的 commit，主工作台立刻能 fetch 到（其实都不用 fetch，本来就是同一个 refs）。

这个"共享数据 + 独立视图"的模型，非常像现代编辑器里"一个文件在多个 tab 打开"的心智——底层文件是同一份，每个 tab 是自己的视图状态。

---

## 8.5 陷阱与红线

worktree 好用，但有五个坑，踩过一次记一辈子。

### 坑一：同一分支不能同时在两个 worktree 检出（前面提过，再强调一次）

```
$ git worktree add ../proj-main main
fatal: 'main' is already checked out at '/home/you/projects/myapp'
```

Git 直接拒绝，你不用担心自己会不小心搞混。想在另一张工作台上"看看 main 的样子"，创建一个从 main 拉出来的临时分支就好：

```
git worktree add ../proj-main-view -b main-view main
```

或者直接检出到一个 detached HEAD（如果你只是想跑一下、不改）：

```
git worktree add --detach ../proj-main-view main
```

### 坑二：`rm -rf` 删了目录不等于注销 worktree

这是最高频的坑。

你用完了 `~/projects/proj-hotfix`，习惯性地：

```
rm -rf ~/projects/proj-hotfix
```

从表面看，工作台没了。但主仓库的 `.git/worktrees/proj-hotfix/` **元数据还在**——Git 仍然认为这张工作台存在。下次你想再开一个同名工作台会失败，`git worktree list` 里那个已经死了的工作台还会出现（标记为 `prunable`）。

正确的做法有两种：

**做法 A（先删元数据再删目录）**：

```
git worktree remove ~/projects/proj-hotfix
```

一条命令把目录和元数据一起清掉。**推荐这个**。

**做法 B（如果目录已经手删了，回来清理元数据）**：

```
git worktree prune
```

扫描 `.git/worktrees/` 下所有元数据，把对应目录已消失的清理掉。

**养成的习惯**：删除 worktree 一律用 `git worktree remove`；如果哪天手滑用了 `rm -rf`，事后跑一次 `git worktree prune`。

### 坑三：worktree 里改 `.git/hooks`、config 等**主仓库层**的东西会影响所有工作台

因为对象库和 refs 是共享的，很多东西都是"仓库全局"的。你在副工作台里 `git config user.email xxx`，改的其实是主仓库的 config——默认（含 `--local`）写的就是这份**共享**的 `.git/config`。要 per-worktree 的配置：先 `git config extensions.worktreeConfig true`（Git ≥ 2.20 引入），再用 `git config --worktree user.email xxx` 写进这张工作台自己的配置。

小心的地方：hooks、config、alias、submodule 状态——这些是全局的，一处改，全局生效。

（Git 提供了 `git config --worktree` 让你为单个工作台设置独立配置，需要主仓库先启用 `extensions.worktreeConfig`。真需要时查一下手册。）

### 坑四：submodule 在 worktree 下的坑

如果你的项目用了 submodule，在副工作台上 `git submodule update --init` 时可能出现意外——submodule 的 `.git` 目录位置在不同 Git 版本下行为不同。**如果你的项目重度依赖 submodule，第一次开 worktree 前先在小实验里跑通再上生产**。

（本书第 13 章会专门讲 submodule。）

### 坑五：locked 和 frozen 状态

有时你会看到 `git worktree list` 里某张工作台标记为 `locked`。这一般是你之前手动锁定过（`git worktree lock`），或者 Git 检测到这张工作台在远程存储/移动介质上不能随意清理。

- `git worktree lock <path>` / `git worktree unlock <path>`：手动加/解锁。
- 锁住的 worktree 不能被 `prune` 或 `remove` 清理，除非先解锁。

**什么时候用 lock**：你把某张工作台放在外接硬盘上、或它长期承担某个 AI agent 的长任务，不希望被自动清理机制误删——这时候 lock 一下。

---

## 8.6 招牌场景：让 AI 代理住进独立 worktree

这一节是这一章的核心，也是全书回应"AI 时代 Git 该长什么样"的一个关键节点。**如果你只从本章带走一件事，请带走这一节**。

### 问题：AI 代理和你抢工作区

现代 AI 编程代理（Claude Code、Cursor Agent、Aider、Devin、Copilot Cloud Agent…）执行任务时，通常需要**独占你的工作目录**——它要读文件、改文件、跑测试、跑构建、看输出。这带来了一系列冲突：

- **你在写代码，AI 也在改代码**：文件系统层面互相踩踏。你手边刚保存的一个文件，AI 一个 apply diff 覆盖了。
- **你在跑开发服务器，AI 在跑测试**：端口、缓存、临时目录互相干扰。
- **AI 跑到一半你要切分支看点东西**：一切分支，AI 那边的 checkout 状态全乱。
- **AI 犯错了你想回滚**：hard reset 一下，你自己写到一半的东西也一起没了。
- **想让多个 AI 并行干活**：`Cursor 2.0 Composer` 多 agent 并行时曾出过"Undo 删档"事故——官方论坛可查的至少两起：2.0.34 的 undo checkpoint 不区分 agent（在 A agent 里 undo 会撤掉所有 agent 的改动）、2.0.77 的 undo apply 会删掉未提交的工作文件——一部分根因就是多 agent 在同一工作目录上互相踩踏。

传统解法（stash / 切分支 / clone）都不解决根问题——**因为根问题是"工作目录只有一个"这个约束本身**。

### worktree 就是这个约束的解药

**新的干活姿势**：

```
主工作台 ~/projects/myapp/         ← 你自己写代码。IDE、服务器、上下文纹丝不动。
   ↓
worktree ~/projects/myapp-agent1/  ← Claude Code Agent 1 在这里跑长重构
worktree ~/projects/myapp-agent2/  ← Cursor Agent 2 在这里跑测试自动化
worktree ~/projects/myapp-agent3/  ← 你让 AI 跑的一个 bisect 任务
```

每个 agent 在自己的**独立目录 + 独立分支**上干活。它写坏了、跑歪了、把整个 node_modules 删了，你的主工作区**毫无感知**。你要审查它的成果——直接 `cd` 过去看，或者让它把分支推到远程，你在主工作台 fetch 下来 diff。你要放弃它的成果——`git worktree remove` 一条命令灭掉整张工作台。

**这不是花哨的技巧，这是 AI 时代 Git 使用姿势的一次基础设施升级。** 就像 Docker 让"环境隔离"从"每个人一台服务器"变成"每个进程一个容器"一样，worktree 让"任务隔离"从"每个任务一次切分支"变成"每个任务一张工作台"。

### 典型工作流：三种姿势

**姿势 A：让 AI 在独立 worktree 上跑一个长任务**

```
# 你在主工作台上，正在写 feature/checkout-v2
# 你想让 Claude Code 帮忙做一个大型的目录结构重构，预计要跑半小时

git worktree add ../myapp-refactor -b agent/refactor-dirs main
cd ../myapp-refactor
# 起一个 Claude Code / Cursor 会话，指令："把 src/ 下所有的目录按照
# domain-driven design 重构，每次改动小步 commit，跑完给我一个 PR 描述"
# 然后你 cd 回主工作台，继续你的 feature 开发
```

半小时后回来看：`cd ../myapp-refactor && git log --oneline`——一堆 agent 的 commit。你在主工作台上 `git fetch`（因为 refs 是共享的，其实立刻可见）看 `agent/refactor-dirs` 这条分支，直接跑 diff 或开 PR review。

**姿势 B：给每个 AI agent 一个专用 worktree（长期化）**

一些工程师现在的做法是**永久保留几张 agent worktree**：

```
~/projects/myapp/          ← 主工作台（你）
~/projects/myapp-agent-a/  ← 长期给 Agent A 用（比如 Claude Code 专用）
~/projects/myapp-agent-b/  ← 长期给 Agent B 用（比如 Aider 专用）
~/projects/myapp-review/   ← 专用于 review 别人 PR
```

每次让 agent 干活前，先 `cd` 进它的工作台，切到一个新分支：

```
cd ~/projects/myapp-agent-a
git switch -c agent/task-<date>-<desc> main
# ...让 agent 干活...
```

**这种模式的好处**：agent 的 IDE 会话、依赖、缓存都长期驻留在那张工作台里，不用每次都重装。而且工作台的物理位置固定，你写脚本、写 alias、配 shell 都容易。

**这种模式的注意**：agent worktree 里也会积累未清理的分支和 `node_modules`，定期清一下。

**姿势 C：多 agent 并行（谨慎版）**

如果你的任务能被拆成互不相关的子任务，可以让多个 agent 并行：

```
git worktree add ../myapp-parallel-1 -b agent/task-1 main
git worktree add ../myapp-parallel-2 -b agent/task-2 main
git worktree add ../myapp-parallel-3 -b agent/task-3 main
```

三个终端窗口，三个 agent 会话，各自在自己的目录里跑。

**这里有一个安全边界必须提**：**Cursor 2.0 Composer 多 agent 并行时曾出过 Undo 操作误删用户工作文件的事故**（官方论坛 2.0.34、2.0.77 两起事故帖，见上文）。多 agent 并行 ≠ 无脑放心。worktree 给了你**文件系统层的隔离**，但如果多个 agent 各自跑一半、你手动去某个 worktree 里 undo，一定确认自己 undo 的是哪张工作台的东西。

### 为什么 worktree 特别适合 AI，而不是"你自己也可以用"就够了

对**人**来说，worktree 是一件"锦上添花"的工具——没有它，你也能用 stash 凑合。

对 **AI agent** 来说，worktree 是"雪中送炭"的基础设施：

- **AI 不擅长处理"中断"**：让 AI 在你的主工作区跑一半，被叫去干别的事，回来能不能恢复现场？很难。而独立 worktree 天然把每个任务锁在一个空间里，agent 不需要"记住上下文之外的世界"。
- **AI 会犯错，需要低成本回滚**：`git worktree remove` 是一条最干净的"整体扔掉"操作——比 `git reset --hard` 安全（不会误伤别的东西），比 `rm -rf` 干净（会一并清理元数据）。
- **AI 应该被限制在可界定的边界内**：主工作台不给 agent 访问权限（Claude Code 支持 deny 规则、Aider 支持 read-only 文件列表），agent 只能在自己的 worktree 里活动。这是**基础设施层的隔离**，比任何"请你不要动那个文件"的 prompt 都靠谱。

**AI 时代的心智模型转变**：过去你把 Git 当成"版本控制工具"；现在你把它当成"agent 沙箱管理系统"。worktree 是这个新用法里最基础的一层。

---

## 8.7 AI 指令箱 · Worktree

以下指令模板与工具无关（Claude Code / Cursor / Copilot / Aider 皆适用）。

**🟢 认知类（帮你把 worktree 摸熟）**

- 「用一段 300 字的自然语言解释：`git worktree add` 和 `git switch` 的本质区别是什么？分别在什么场景下选哪个？用第 8 章"工作台 vs 换名牌"的比喻。」
- 「列出我这个仓库里当前所有的 worktree（`git worktree list`），并对每一张说明：它站在哪个分支、有没有未提交改动、上次动过是什么时候、是不是可以清理。」
- 「读一下 `.git/worktrees/` 目录里的所有元数据。告诉我每张工作台的 gitdir 反向指针指向哪里，有没有孤儿元数据（对应目录已消失）。」

**🟢 场景类（帮你落地）**

- 「我要为一个 hotfix 开一张 worktree，路径放在 `~/projects/proj-hotfix`，基于最新的 origin/main 切一个新分支 `hotfix/<今天日期>-<简短描述>`。给我完整命令序列，先解释再执行。」
- 「我要跑一下 PR #142 看看效果，帮我：① 抓下这个 PR 对应的分支；② 在 `~/projects/proj-review-142` 开一张 worktree 检出到它；③ 提示我看完后怎么完整清理。」
- 「帮我起 3 张 agent 专用 worktree，路径分别是 `~/projects/myapp-agent-{1,2,3}`，每张各自基于 main 开一个新分支 `agent/task-<日期>-<序号>`。用一个 shell 脚本一次搞定，并在最后 `git worktree list` 展示结果。」

**🟡 需要盯着的（清理与危险操作）**

- 「列出我这台机器上所有仓库里的 worktree（可能有孤儿）。给我一份 checklist：哪些是可以清理的、哪些还在活跃使用中。**只列表，不执行任何清理。**」→ 看完确认再补一句「把列表里标为可清理的那些，用 `git worktree remove` 逐个清理，遇到 locked 的先给我看再决定」。
- 「我想在 worktree A 上做一次大 rebase 实验，risk 比较高。开一张新的 worktree（不是在 A 上直接做），把它当作沙盘。给我完整方案：新 worktree 怎么开、rebase 怎么跑、成功了怎么合回、失败了怎么整支扔掉。」
- 「AI agent B 已经在 `~/projects/myapp-agent-b` 上跑了一个大重构，现在想放弃它的所有产出。给我一个**安全清理**的步骤：先确认它是不是在跑（有没有活的进程占用文件）、确认它有没有 push 出去、然后干净清理这张工作台和它创建的分支。」

**⚠️ 陪练模式（让 AI 当学习伙伴，不动手）**

- 「模拟一个场景：我在写 feature X，被叫去修 hotfix Y，然后又要 review PR Z。我告诉你每一步我怎么处理（stash / commit WIP / worktree / 切分支 / clone…），你评价我的选择、指出更省事的做法、以及潜在的坑。来 4 轮。」
- 「出 5 道\"这个场景该用 stash / worktree / clone 哪一个\"的判断题，包含反面案例（不需要 worktree 的场景也拿来考我）。我做完你逐题批改并解释判断理由。」
- 「让我复述一遍：为什么同一个分支不能同时在两个 worktree 检出？你听我讲，指出我的理解漏洞。」

---

## 8.8 执行后的世界：从命令到文件系统

透视一下——你用 worktree 干了以下几件事之后，仓库和文件系统里到底发生了什么？

| 你说的话（或执行的命令） | 命令 | 文件系统/仓库里的真实变化 |
|---|---|---|
| "为 hotfix 开一张工作台" | `git worktree add ../proj-hotfix -b hotfix/x main` | ① 创建目录 `../proj-hotfix/`；② 该目录下 checkout hotfix/x 的工作文件；③ 该目录下放 `.git` 文本文件（一行 gitdir 指回主仓）；④ 主仓 `.git/worktrees/proj-hotfix/` 目录被创建，含 HEAD/index/gitdir 三个元数据文件；⑤ 主仓 `refs/heads/hotfix/x` 被创建，指向 main 当前 commit |
| "在副工作台上 commit 一个改动" | `cd ../proj-hotfix && git commit -m "fix"` | ① 对象库（主仓 `.git/objects/`）里新增 tree/blob/commit 对象；② `.git/worktrees/proj-hotfix/HEAD`（副工作台的 HEAD）更新指向新 commit；③ 主仓 `refs/heads/hotfix/x` 更新指向新 commit（引用是共享的） |
| "在主工作台看有没有那个新 commit" | 在主工作台 `git log hotfix/x` | 立刻能看到——因为 objects 和 refs 都共享，副工作台的提交对主工作台是即时可见的 |
| "用完了，删掉工作台" | `git worktree remove ../proj-hotfix` | ① 删除目录 `../proj-hotfix/`（连同里面所有文件）；② 删除主仓 `.git/worktrees/proj-hotfix/` 元数据目录；③ **分支 `hotfix/x` 不删**——如果需要连分支一起删，还得 `git branch -d hotfix/x` |
| "只删了目录，忘了 remove" | `rm -rf ../proj-hotfix` | ① 目录没了；② 但 `.git/worktrees/proj-hotfix/` 元数据留着；③ 下次 `git worktree list` 会看到它标为 `prunable` |
| "清理孤儿工作台" | `git worktree prune` | 扫描 `.git/worktrees/` 下所有元数据，把对应目录已消失（且未 locked）的元数据清理掉 |
| "锁住一张工作台防止误清理" | `git worktree lock ../proj-hotfix` | 在 `.git/worktrees/proj-hotfix/` 下创建一个 `locked` 标记文件；此后 prune/remove 都会拒绝，除非先 unlock |

看懂这张表，你就能理解**worktree 不是一个"高级功能"**——它只是把 `.git/` 目录和工作文件的关系从"绑死"改成了"一对多"，其他一切都还是老规矩：objects 存对象、refs 存分支、HEAD 指当前位置。**心智负担一旦跨过"多个 HEAD 并存"这道坎，剩下的全是熟悉的东西**。

---

## 8.9 命令侧栏

```
# 创建 worktree
git worktree add <路径> <已有分支>            # 检出到一个已有分支
git worktree add <路径> -b <新分支> <起点>    # 从某个 commit/分支创建新分支并检出
git worktree add --detach <路径> <某commit>   # detached HEAD 模式（只读跑一下）
git worktree add --lock <路径> <分支>         # 创建时立刻锁定

# 观察
git worktree list                              # 列出所有 worktree
git worktree list --porcelain                  # 脚本友好的输出（含 HEAD、bare、detached 等标记）
ls .git/worktrees/                             # 直接看元数据目录

# 清理
git worktree remove <路径>                     # 干净地删除（推荐）
git worktree remove --force <路径>             # 有未提交改动时强制删（谨慎）
git worktree prune                             # 清理孤儿元数据（当你手动 rm 过目录）
git worktree prune --dry-run                   # 只看会清理什么，不真动

# 锁定/解锁
git worktree lock <路径>                       # 锁住，防止被 prune 或 remove 误清理
git worktree lock <路径> --reason "长跑任务"    # 带原因（会记录在 locked 文件里）
git worktree unlock <路径>                     # 解锁
git worktree list                              # 已锁的会显示 locked 标记

# 移动
git worktree move <旧路径> <新路径>            # 移动一张 worktree 到新位置（会同步更新元数据）

# 修复（罕见但救急）
git worktree repair                            # 元数据和实际路径对不上时修复反向指针

# 组合姿势
git worktree add ../proj-review-$(date +%m%d) -b review/pr-142 origin/pr-142
# ↑ 一条命令：加日期后缀的工作台 + 创建新分支 + 基于远程 PR 分支

for i in 1 2 3; do
  git worktree add "../myapp-agent-$i" -b "agent/task-$i" main
done
# ↑ 一次开三张 agent 工作台
```

**记住**：worktree 相关的命令一共就这么些，全都在 `git worktree <子命令>` 下。**它是一个自成一族的命名空间**，跟主工作流的 `switch/commit/push` 是不同的层级——你切换分支还是在**一张工作台内部**做的事；worktree 命令是**在工作台之间**做的事。

---

## 8.10 本章小地图

```
Worktree = 同一个 .git/ 数据库同时铺开的多张工作台
  │
  ├─ 核心事实：仓库 与 工作目录 可以解耦
  │    → 一份 objects/refs（共享）
  │    → 多个 HEAD/index/工作文件（独立）
  │
  ├─ 三条使用姿势：
  │    A. 短命工作台     → hotfix / PR review / 长跑测试期间加班
  │    B. 长期专用工作台 → 给每个 AI agent 一张固定工作台
  │    C. 并行沙盘       → 危险实验（大 rebase / reset / 脚本重写）
  │
  ├─ 选择表（当下这一刻）：
  │    暂停一下         → stash
  │    只是想换个视角    → 切分支 or WIP commit
  │    要"同时干两件事" → worktree
  │    要长期分叉出去   → clone
  │
  ├─ AI 时代的招牌用法：
  │    让 agent 住进独立 worktree
  │    → 主工作区零干扰
  │    → 试错整支扔掉（worktree remove）
  │    → 多 agent 并行有文件系统层隔离
  │
  ├─ 三条铁律：
  │    ① 同一分支不能同时检出在两张工作台上
  │    ② 删目录不等于注销（要 remove 或 prune）
  │    ③ 对象/引用/hooks/config 是仓库全局的（一处改全局改）
  │
  └─ 清理动作：worktree remove（干净）> worktree prune（补救）> rm -rf（错误）
```

**三大典型误解拆解**

1. **"worktree 就是分支的另一种写法。"** ——完全不同。分支是"名牌"（一颗珠子上的一个字），worktree 是"工作台"（一张摊开珠子的桌子）。同一个分支可以有零张、一张、也只能一张 worktree（不能两张）；同一张 worktree 上同时只能站一个分支。**分支管的是"版本身份"，worktree 管的是"物理工作场所"。** 把两个混为一谈的表现是：你以为多开 worktree 是为了"多开分支"——不，多开分支用 `switch -c` 就够了，多开 worktree 是为了"多开工作场所让上下文互不干扰"。

2. **"worktree 会复制一份代码，所以占硬盘。"** ——半对半错。它复制的是**工作文件**（就是你在编辑器里看到的那些源码），不复制**对象库**（`.git/objects/`——通常占大头，几百 MB 到几 GB）。相比 `git clone` 一份完整仓库能省 80–95% 的硬盘。所以"因为怕占硬盘不敢用 worktree"是完全没必要的顾虑——真要顾虑，也是顾虑 clone，不是 worktree。**worktree 就是 clone 的轻量替代品**。

3. **"我 rm -rf 掉了 worktree 目录，就等于删除了这张工作台。"** ——这是最高频的错误认知。**没有**。你只删了目录里的文件，主仓库的 `.git/worktrees/<name>/` 元数据还在，Git 仍然认为这张工作台存在。下次你想开同名的会被拒绝，`git worktree list` 里会看到一个 `prunable` 状态的僵尸。**永远用 `git worktree remove` 删工作台**；万一手滑用了 `rm -rf`，事后跑一次 `git worktree prune` 补救。**这个纪律和"用 git branch -d 而不是 rm .git/refs/heads/xxx"是同一等级的基本操作**——不遵守不会立刻炸，但会在半年后某天让你困惑半小时。

---

## 8.11 下一章预告

worktree 解决了"同时干几件事"的物理场所问题。当你终于可以从容并行——主工作台写 feature、副工作台修 hotfix、agent 工作台跑重构——**几件事完成之后总要合到一起**。合的时候，Git 会问你一个从第 5 章"历史可塑性"就在等着的问题：**这两条项链的珠子有分歧，你想让哪颗珠子活下来？**

这就是**冲突**。冲突不是错误，冲突是 Git 举手示意"我理解不了你的意图，请你亲自决定"。传统 Git 教材讲冲突讲的是命令层（`<<<<<<< HEAD`、`>>>>>>> feature` 这些标记符）；AI 时代讲冲突要讲**语义层**——AI 能不能读懂两侧的意图、能不能替你判断"该保留哪边"、什么时候该让 AI 自动决、什么时候必须人守最后一道防线。

**第 9 章 · 冲突：不是 Git 的错，是你的语义需要仲裁**。三段式：症状分类（merge 冲突 vs rebase 冲突 vs cherry-pick 冲突）→ 候选方案（三方合并工具 vs 语义级 AI 合并 vs "两边都要"的手工方案）→ AI 指令模板（让 AI 解释、提议、慎重执行）。

---

> **🤖 AI 指令箱 · 本章实战演练**
>
> 找一个你自己电脑上真实的仓库，把下面这几条指令依次跑一遍，一小时内你就把 worktree 内化了：
>
> - 「列出这个仓库当前所有的 worktree（`git worktree list`）。如果只有主工作台，帮我在旁边开一张练习用的 worktree，路径 `../<项目名>-playground`，基于当前 HEAD 建一个新分支 `playground/learn-worktree`。」
> - 「进入 playground 那张工作台，创建一个新文件 `PLAYGROUND.md`，写点内容 commit。回到主工作台，用 `git log playground/learn-worktree` 确认那次 commit 立刻可见（说明 objects/refs 是共享的）。用一句话总结这次实验证明了什么。」
> - 「在主工作台上尝试 `git worktree add ../another main`——观察 Git 报错。用中文复述报错的意思，并解释为什么这条约束存在。」
> - 「假想你现在是一位 AI agent，我要让你在 `../<项目名>-agent` 这张 worktree 上做一个小任务：给 README 加一段目录。完成后我在主工作台 review 你的分支，approve 后合并。给我完整的操作剧本——包括创建 worktree、切分支、你干活、我 review、我合并、我清理——每一步一行命令 + 一句话解释。」
> - 「扫描我这台机器上所有 Git 仓库的 worktree 状态（找一下 `~/projects` 下面所有仓库），列出所有孤儿 worktree（prunable 状态的）。**只列表，别清理。**」看完再补一句「确认清理列表里除了 xxx 之外的全部，用 `git worktree prune`」。

---

## 8.12 自查清单（章末速览）

写作/阅读双方对齐用：

- [x] 第二人称"你"贯穿全章，未出现"我们"式集体叙事。
- [x] 比喻体系一致：项链-珠子-名牌（继承）+ 工作台/沙盘（本章新设，与前系统兼容——工作台是"摊开珠子的物理场所"）。
- [x] 三段式：症状（8.1、8.3）→ 候选方案（8.3、8.4）→ 判断规则（8.3 判断表 + 8.5 陷阱）。
- [x] 固定栏目齐全：场景引入（8.1）→ 概念祛魅（8.2）→ 判断（8.3）→ 机制（8.4）→ 陷阱（8.5）→ AI 招牌场景（8.6）→ AI 指令箱（8.7）→ 执行后的世界（8.8）→ 命令侧栏（8.9）→ 小地图（8.10）→ 三大误解（8.10 末尾）→ 下一章预告（8.11）→ 实战演练（章末 AI 指令箱）。
- [x] AI 指令箱🟢🟡分级 + 陪练模式齐全。
- [x] 命令降级到侧栏（8.9），主线是概念 → 场景 → 判断 → 指令。
- [x] ASCII 图示（8.2 目录结构、8.4 组织结构、8.10 小地图）替代正式绘图，符合本书样张阶段做法。
- [x] 中文术语 + 关键英文（worktree / HEAD / index / prune / lock）并行。
- [x] 字数：约 8800 字（在 6000–10000 字目标区间内）。
