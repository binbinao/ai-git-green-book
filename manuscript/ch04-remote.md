# 第 4 章　远程：一面会呼吸的镜子

> 《Git 的概念地图》第 4 章 · 定调稿 v1.0
> 五张地图的第四张：你的项链，同事的项链，还有一堆镜子里的项链。

---

## 4.1 场景引入：一次 pull 之后的莫名其妙

周三下午三点，你想把同事最新的改动拉下来。手指毫无犹豫地敲：`git pull`。

十秒后，一堆信息刷屏：Auto-merging src/user.py、Merge made by the 'ort' strategy、6 files changed……最后你 `git log --graph --oneline -10`，屏幕上突然多出一颗你从没造过的 commit：

```
*   9f2a1b3  Merge branch 'main' of git.example.com:team/project
|\
| * a1b2c3d  同事的最新提交
* | 4e5f6a7  你自己的最新提交
|/
* d8e9f0a  昨晚的共同祖先
```

你盯着那颗**"Merge branch 'main' of ..."** 看了三秒。**这颗提交是谁造的？** 你没打过 `git merge`，你只打了 `git pull`。而且，为什么会有一个 Y 形分叉？你自己那边只有一个 commit，怎么就分岔了？

你隐约感觉发生了一件你并不完全理解的事，但代码看起来没问题，测试跑过。你耸耸肩，继续干活。

同样的 0.3 秒惊愕，也会出现在这些时刻：

- 你 `git push` 被拒，屏幕上飘红 `! [rejected]        main -> main (non-fast-forward)`——**Git 在保护什么？**
- 你 `git fetch` 完之后 `git status`，Git 说 "Your branch is up to date with 'origin/main'"——**它是怎么"知道" origin/main 在哪里的？现在？此刻？**
- 你在 GitHub 上看到别人 fork 你的项目、发 PR 过来——**你本地的仓库里，那个人的 fork 长什么样？**
- 你听说过 `origin` 和 `upstream` 两个名字，但从没想清楚它们到底是什么关系——**是不是有一个是"上游"、一个是"下游"？**

这一章要摊开的这张地图，会一次性回答上面所有问题。核心是三件事：**远程只是别名、远程分支只是本地缓存、只有几个命令会碰网络**。看懂了这三条，`pull` 的那颗神秘 merge commit 会失去神秘，`non-fast-forward` 会从警告变成朋友。

---

## 4.2 祛魅时刻：远程到底"是"什么

先给结论。

> **一个"远程"（remote）是你的仓库对另一个仓库的引用——本质上就是一个别名 + 一个 URL。`origin` 不是"服务器"，是"我给某个远端起的名字"；`origin/main` 不是"服务器上的 main 分支"，是"我上次听说远端 main 在哪儿的一份本地缓存"。**

关键词四个，每一个都戳穿一种主流的误解：

- **别名**：`origin` 是你随手起的名字，可以叫 `foo`、`bar`、`grandma`，Git 不关心。
- **另一个仓库**：Remote 指向的是另一份完整的 `.git/`——它可以在 GitHub 上，也可以在同事笔记本上，也可以在你自己电脑的另一个目录里。
- **本地缓存**：`origin/main` 这个东西**住在你本地**，不是住在服务器上。它是你自己给"上次听说的远端状态"贴的名牌。
- **一份**：注意是"一份"——服务器上的 main 分支现在是什么状态，你的本地缓存**不会自动更新**。它是被冻结的记忆，直到你显式执行 `git fetch` 让它刷新。

一句话：**远程仓库是另一条项链的拷贝（镜子里的项链）。`origin/main` 是你本地给"镜子里那条项链最新已知位置"贴的名牌。**

### 打开黑盒：`.git/config` 和 `refs/remotes/` 里到底有什么

不用相信我，自己看。找一个 clone 过远端的仓库，看两个地方：

**第一处：`.git/config` 里的两段配置。**

```ini
[remote "origin"]
    url = git@github.com:example/project.git
    fetch = +refs/heads/*:refs/remotes/origin/*

[branch "main"]
    remote = origin
    merge = refs/heads/main
```

翻译成人话：

- `[remote "origin"]`：**"origin"这个别名，对应的 URL 是这个。当我 fetch 的时候，把远端所有 `refs/heads/*`（远端的所有分支）搬到我本地的 `refs/remotes/origin/*`（我给它开的缓存区）里。"**
- `[branch "main"]`：**"我本地的 main 分支，它的上游（upstream）是 origin 这个远程的 main 分支。默认 push/pull 就走这条。"**

**远程就是两行字。就这么简单。** 你可以 `cat` 出来看，可以直接编辑（Git 提供了 `git remote add/rename/set-url` 这些命令帮你改，但底下就是在改这两段文本）。

**第二处：`.git/refs/remotes/` 目录。**

```
.git/refs/remotes/
└── origin/
    ├── main            ← 一个文件，40 个字符
    ├── develop         ← 一个文件，40 个字符
    ├── feature-x       ← 一个文件，40 个字符
    └── HEAD            ← 记 origin 那边的默认分支是哪个
```

每个文件里写的是一个 SHA——**你上次 fetch 时听说远端那个分支指向的珠子**。

回顾第 3 章：本地分支（`refs/heads/main`）也是这样——40 个字符指向某颗珠子。**远程分支和本地分支的物理结构完全一样，都只是一个指针文件。** 区别只有两点：

1. **住的目录不同**：本地分支在 `refs/heads/`，远程分支在 `refs/remotes/<remote_name>/`。
2. **谁能动它**：本地分支你随便动（switch、commit、reset、rebase）；远程分支**你不该手动动**——它是 Git 帮你维护的"上次听说的远端状态"缓存，只有 `fetch`、`pull`、`push` 会更新它。

用第 3 章的比喻扩展一下：

> **每条项链上都可以挂两种名牌——本地名牌（refs/heads/）是你自己贴的，远程名牌（refs/remotes/origin/）是"我上次从镜子里看到、抄下来贴在墙上的"。你本地是有那条镜子里的项链的完整拷贝的（objects 里全都有），但镜子里的项链现在是什么样，你只能靠 fetch 才能"再看一眼"。**

### 关键推论：**origin/main ≠ 服务器上的 main**

这是全章最重要的一句话，重要到值得单独强调。

**`origin/main` 是本地缓存**。它反映的是**你上次 fetch 那一刻**远端 main 的位置。从那以后：

- 同事往远端推了 5 个新 commit——你本地的 `origin/main` **纹丝不动**。
- 你自己的 main 往前推了 3 个 commit——你本地的 `origin/main` **纹丝不动**。
- 有人在远端删掉了 main（假设的极端情况）——你本地的 `origin/main` **纹丝不动**。

只有你自己主动 `git fetch`，Git 才会去问一次镜子，然后把本地 `origin/main` 更新到"此刻镜子里的位置"。

这个"缓存 + 显式刷新"的设计，是 Git **只有几个命令会碰网络**的直接后果——你的日常 log、status、diff 都在读本地缓存，永远瞬间返回，永远不需要网络。代价是：**你在本地看到的"origin/main"永远是一个略微过时的镜像**。这不是 bug，是设计。

---

## 4.3 三兄弟的真实语义：fetch、pull、push

日常碰网络的只有 **fetch 家族与 push**——`clone` / `fetch` / `pull` / `push` / `ls-remote` / `remote show` / `remote update` 都是它的变体，其余命令全部只读本地。日常里你天天用的就三个：fetch、pull、push。

它们各自到底干什么？

### fetch：只更新缓存，不动你的任何东西

`git fetch origin` 做的事：

1. 联系 `origin` 的 URL。
2. 拉取远端有、你本地没有的所有 objects（内容寻址，只传差集）。
3. 更新你本地的 `refs/remotes/origin/*`（远程分支缓存）。
4. **结束**。

**结束**的意思是：你本地的分支（`refs/heads/*`）、你的 HEAD、你的工作目录、你的暂存区——**全部不动**。你的代码保持你 fetch 之前的样子。log 里没有新 commit 出现（除非你显式看 `origin/main`）。

**fetch 是完全安全的操作**。它只更新"我上次听说远端在哪儿"这个缓存。它像是打开镜子照一眼、把镜子里的样子记下来——但你自己没有被改变一根汗毛。

你可以每天开工前无脑 fetch 一次，代价接近零，收益是**知道远端此刻的实际状态**。之后你才能做有信息的决策：\"我该不该 pull？\"\"我 push 之前需不需要先 rebase 一下？\"

### pull：fetch + merge（或 rebase）的封装

`git pull origin main` 做的事：

1. **`git fetch origin`**（更新缓存）
2. 然后 **`git merge origin/main`**（默认）或 **`git rebase origin/main`**（如果你设置了 `pull.rebase = true`），把刚 fetch 到的远端更新合并进你当前的本地分支。

**pull 不是一个原语，它是一个宏。** 它把两件性质完全不同的操作打包在一起——一个只读（fetch），一个改历史（merge 或 rebase）。

这个封装的**代价**在开篇场景里已经上演过了：

```
* 9f2a1b3  Merge branch 'main' of git.example.com:team/project   ← 谁造的？
|\
| * a1b2c3d  同事的最新提交
* | 4e5f6a7  你自己的最新提交
|/
* d8e9f0a  昨晚的共同祖先
```

那颗神秘 merge commit 是 `pull` 里第二步 `merge` 造的——因为**你的本地 main 和远端 main 已经分叉了**（你有 4e5f6a7，远端有 a1b2c3d，两者都在共同祖先之后各走各路），Git 需要一颗 merge commit 把两条路合在一起，才能"pull 完成"。

**这颗 merge commit 通常没人真的想要**——它把项链弄得歪歪扭扭，log 里全是"Merge branch 'main' of ..."的噪音。真正想要的通常是"把我的改动放在远端最新之上，形成一条直线"——那应该用 rebase 而不是 merge。所以 Git 2.27 起干脆不再替你默默选：pull 遇到分叉会停下来**逼你显式选择**（merge / rebase / ff-only 三选一），提示里把三个选项并列摆出来，但**默认仍是 merge**。个人分支想要直线历史，可以配置：

```
git config --global pull.rebase true    # 个人分支：拉下来就 rebase 成直线
```

共享分支则更稳妥的是 `pull.ff only`（只允许快进，分叉就停，绝不自动造 merge commit）：

或者更明确的做法——**别用 pull，分成两步**：

```
git fetch origin        # 先刷新缓存
# 看一下情况：git log --oneline main..origin/main  和  origin/main..main
git rebase origin/main  # 把我的改动移到远端最新之上（如果没冲突）
```

这两步分开做的好处：**中间那一步你可以停下来判断**——远端有没有新东西？我这边有没有本地改动？分叉了没？该 merge 还是该 rebase 还是干脆放弃我这边的改动直接接受远端？**pull 把这些决策全部替你默默做了，而且做得往往不是你真正想要的那种。**

**AI 时代的补充**：让 AI 帮你封装这个"决策 + 执行"的流程比背命令更实在——「先 fetch，然后告诉我我这边和 origin/main 分叉了没、各有多少 commit、有没有冲突风险，我看完再决定 rebase 还是 merge」。这段话你说给任何 AI 编码助手听都能执行，比你敲一个 pull 之后被动接受 Git 的默认选择要好得多。

### push：把你的本地珠子和名牌同步到镜子那边

`git push origin main` 做的事：

1. 联系 `origin` 的 URL。
2. 检查远端 main 现在指向哪颗珠子。
3. **判断：**远端那颗珠子，是不是你本地 main 的**祖先**？
   - **是**：可以 push。把你本地的新珠子传过去，让远端 main 前移到你本地 main 的位置。这叫 **fast-forward**（快进）。
   - **不是**：**拒绝 push**（`non-fast-forward` 报错）。
4. push 成功后，更新你本地的 `origin/main` 缓存（你现在知道远端最新在哪里了）。

**注意 push 的方向：从本地推到远端。** 和 fetch 相反（fetch 是从远端拉到本地缓存）。fetch 不动你本地分支；push 会动远端分支。

**为什么会有 non-fast-forward 拒绝？** 因为 Git 在保护你和你的团队：

假设远端 main 指向珠子 X，你本地 main 指向珠子 Y。Git 检查发现 X 不是 Y 的祖先——这意味着 X 上面有一些珠子在 Y 的历史里**根本不存在**。如果 Git 允许你 push，你本地的 main 会覆盖远端的 main，那些珠子会**从远端项链上被踢下去**——所有拉过它们的同事会一头雾水地发现"我以为提上去的那三个 commit 呢？"

Git 拒绝 push 的言下之意是：**"你本地的 main 和远端 main 分叉了，我不敢帮你决定哪一边是对的。你自己想清楚——是把远端的东西拉下来合进你本地（fetch + merge/rebase 再 push），还是你真的确信要拿本地覆盖远端（force push，第 12 章有专门的红线警告）。"**

**这是 Git 里最重要的一道安全阀**。看到 non-fast-forward 不要慌，也不要立刻上 `--force`——它是 Git 帮你在按停按钮。第 4.5 节会展开讲。

---

## 4.4 upstream：本地分支和远端分支的绑定关系

上面说的三兄弟都可以带一个明确的目标：`git pull origin main`、`git push origin main`。但你可能注意到，你日常写的经常是简化版：`git pull`、`git push`——省略了 `origin main`。

Git 是怎么知道你要 pull/push 的是哪个远端的哪个分支的？

答案在 `.git/config` 那第二段：

```ini
[branch "main"]
    remote = origin
    merge = refs/heads/main
```

翻译：**"本地 main 分支的 upstream 是 origin 这个远程的 main 分支。"**

有了这条绑定，`git pull` 会自动读它、去 pull upstream 对应的远程分支；`git push` 也一样。这条绑定叫做 **upstream tracking**（上游追踪）。

**建立 upstream 的时机**通常有两个：

- **clone 的时候**：Git 会自动为默认分支建 upstream（本地 main → origin/main）。
- **首次 push 新分支时**：你敲 `git push -u origin feature-x`，那个 `-u` 就是 `--set-upstream`，一次性建好绑定。之后你就可以直接 `git push` 了。

第二个场景里如果你忘了 `-u`：`git push origin feature-x` 也能 push 成功一次，但没有绑定；下次你敲 `git push`，Git 会**直接报错**（`fatal: The current branch has no upstream branch`），并在提示里告诉你可以在 push 时加 `--set-upstream` 补上绑定——它从不交互式地问你"推到哪里"，而是把选择连同报错一起交回你手上。

`git status` 里那句 `Your branch is up to date with 'origin/main'` 就是在读这条 upstream 绑定：**你的本地 main 追踪的是 origin/main，两者当前指向同一颗珠子，所以 "up to date"。** 注意这句话说的是"和本地缓存 origin/main 一致"，**不是"和远端服务器一致"**——如果你没最近 fetch，远端服务器可能已经跑到前面去了，你的 status 只是不知道而已。

**关于命名："upstream" 有两个含义容易混淆。**

- **含义 A（Git 内建概念）**：任意一个本地分支绑定的那个远程分支——通用术语。
- **含义 B（Fork 工作流约定）**：在 fork 场景下，人们习惯把\"原始项目\"叫 `upstream`（区别于自己 fork 那份叫 `origin`）。

含义 B 里那个 upstream 只是别名的一种起法（就像 origin 一样是可以随便起的名字），它借用了含义 A 的语义感觉，但**技术上就是一个普通 remote**。下一节讲 Fork 工作流会用到。

---

## 4.5 non-fast-forward：Git 在按停按钮

`! [rejected]        main -> main (non-fast-forward)` 是 Git 里最常见的"红字警告"之一，也是最容易被误解的一条。

**它不是错误。它是 Git 帮你按停按钮。**

把上文的场景画出来：

```
    远端 origin/main（服务器上）
        │
        ▼
    A ── B ── C ── D ── E    ← 别人已经推了 D 和 E 上去
                    ▲
                    │
    你本地 main（自己电脑上）
        │
        ▼
    A ── B ── C ── X ── Y    ← 你在 C 之上造了 X 和 Y
                    ▲
                    │
                   你 push 就是想让远端从 E 挪到 Y
```

远端 main 指向 E，你本地 main 指向 Y。**E 不是 Y 的祖先**（Y 的祖先只有 X-C-B-A，没有 D 和 E）。你如果强推，D 和 E 就从远端 main 的项链上消失了——所有靠 D、E 干活的同事都要哭。

Git 拒绝这次 push，意思是：**"我发现远端有你不知道的 commit（D 和 E）。我不敢帮你选择——你要不要先把这些拉下来看看？"**

**正确应对流程**：

1. **`git fetch origin`**：把远端最新状态拉到本地缓存。
2. **看清楚**：远端多了什么？我本地多了什么？两边冲突吗？可以用 `git log --oneline --graph main origin/main` 或者让 AI 一句话总结。
3. **决策**：
   - **绝大多数情况**：`git rebase origin/main`——把你的 X、Y 移到 E 之上（成为 X'、Y'），历史变成直线 A-B-C-D-E-X'-Y'。之后 `git push` 就是 fast-forward，一次通过。
   - **有时候**：`git merge origin/main`——造一颗 merge commit 把两条路合并（你会得到那颗你未必想要的\"Merge branch 'main'\"）。
   - **极少数情况**：确认远端那些 commit 就是要丢弃（比如整个 D、E 是错的、要重来），`git push --force-with-lease`（**第 12 章讲**，比 `--force` 安全一档）。

**你会注意到，`--force` 没有出现在正确应对流程的默认选项里。** 这是有意的——`--force` 是**告诉 Git\"我不听你劝，覆盖远端\"**，它会让远端的 D 和 E 从 main 项链上被踢掉。在你完全清楚自己在干什么、并且已经和团队沟通过之前，永远不要用它。**已经推到共享分支上的 commit，不要单方面重写。**这是第 5 章会正式加冕的\"黄金规则\"，这一章先给你埋一个警告。

---

## 4.6 Fork 工作流：三层项链

开源协作和内网多团队协作里最常见的模式是 **Fork + PR**。它涉及三份不同的仓库，而且这三份还有明确的层级关系。

一张图讲清楚：

```
    ┌─────────────────────────────────────────┐
    │  上游项目 (upstream)                     │
    │  github.com/original/project             │  ← 原始项目、\"官方\"、你没有 push 权
    │  远端项链: ...─▶ (D) ─▶ (E) ─▶ (F)      │
    └───────┬──────────────────────▲──────────┘
            │ Fork（平台操作）        │
            ▼                       │ Pull Request
    ┌─────────────────────────────────────────┐
    │  你的 fork (origin)                      │
    │  github.com/你的用户名/project           │  ← 你在 GitHub 上的一份拷贝、你有 push 权
    │  远端项链: 从 upstream 分岔出来的一支     │
    └───────┬──────────────────────▲──────────┘
            │ git clone            │  git push
            ▼                      │
    ┌─────────────────────────────────────────┐
    │  本地仓库 (你笔记本上)                    │
    │  .git/refs/remotes/origin/*             │  ← 你实际写代码的地方
    │  .git/refs/remotes/upstream/*  (可选)   │  ← 你手动加一个远程指向官方
    └─────────────────────────────────────────┘
```

*图 4-1：Fork 工作流的三层结构。origin 是你自己那份、upstream 是官方那份、local 是你笔记本上的。*

**关键观察点**：

1. **Fork 不是 Git 原生概念**——它是 GitHub / GitLab 这些平台加的功能，作用是"在服务器上给你复制一份远端仓库"。Git 本身不知道也不关心。
2. **你的本地仓库有两个远程**：`origin`（默认指向你的 fork）和 `upstream`（你手动加的，指向原始项目）。**这里 upstream 是别名的名字，不是 Git 内建的 upstream tracking 概念**——虽然共用一个词，语义完全不同。
3. **你日常 push 到 origin**（你的 fork，你有权），**从 upstream fetch**（官方项目最新进展，你没权 push 上去），**通过 PR 请求合并到 upstream**（PR 是平台层功能）。

**添加 upstream 的命令**（clone 完你的 fork 之后）：

```
git remote add upstream https://github.com/original/project.git
git fetch upstream
```

从此你本地就有两份"镜子里的项链缓存"了：`origin/main` 是你自己 fork 的 main，`upstream/main` 是官方项目的 main。**同步官方最新进展**变成：

```
git fetch upstream                    # 更新 upstream 缓存
git switch main                       # 切到本地 main
git rebase upstream/main              # 把本地 main 移到官方最新之上
git push origin main                  # （可选）把本地 main 同步到你的 fork
```

或者更简单的：

```
git fetch upstream
git switch main
git reset --hard upstream/main        # 让本地 main 完全等于官方最新
git push origin main --force-with-lease   # 让你的 fork main 也完全等于官方
```

（第二种更粗暴但更常用——因为在 fork 工作流里，本地 main 通常只用来同步、不用来开发，所有开发都在特性分支上。这时候本地 main 直接"覆盖式跟随"官方是最省心的。）

**PR 的本质**：你 push 你的特性分支到 `origin`（你的 fork），然后在 GitHub 页面上发起 Pull Request——"请把我 fork 里 feature-x 分支上的这些 commit 合并到 upstream/main"。**PR 是平台层的评审、讨论、批准载体**，Git 里没有 PR 命令。批准之后，平台会替你（或让你自己）执行一次 merge（在服务器上），远端项链上就多了你的贡献。

**这就是绝大多数开源项目的协作方式**。第 11 章会展开讲 PR 生命周期和 AI 在其中的位置，这里先建立三层结构的地图。

---

## 4.7 场景判断：远程操作的几条判断规则

**规则一：每天开工前 fetch 一次。**
`git fetch --all` 或至少 `git fetch origin`——纯读、纯安全、代价接近零，好处是**你本地那份"镜子里项链缓存"是最新的**。之后你所有的判断（要不要 pull、能不能 push、有没有分叉）都建立在准确信息上。**不 fetch 就贸然操作，等于闭着眼睛开车。**

**规则二：能用 fetch + rebase，就别用 pull。**
`pull` 是一个宏，替你做了两个决策（拉下来 + 合并方式）。分成两步做，你保留了中间决策的机会。**如果一定要用 pull**，配好 `pull.rebase = true` 至少能避免那颗恼人的 merge commit。

**规则三：看到 non-fast-forward，先 fetch，别 force。**
99% 的 non-fast-forward 是因为"我没跟上远端最新"，而不是"我要覆盖远端"。fetch 一下、rebase 一下、再 push——大多数情况一次通过。只有当你**确认远端那些 commit 就是要丢弃**（比如是你自己刚才误推的、要撤回来），才考虑 `--force-with-lease`（不是 `--force`）。

**规则四：新分支第一次 push 记得加 `-u`。**
`git push -u origin feature-x`。省你后面每次都要写全参数。

**规则五：远程分支缓存不新鲜是常态，不是异常。**
`git status` 说\"up to date with origin/main\"的时候，它说的是"和你本地缓存的 origin/main 一致"——远端服务器**此刻**是什么状态，除非你刚 fetch 过，Git 说不准。**这不是 Git 的缺陷**，是它\"只有几个命令碰网络\"的设计后果。习惯它。

---

## 4.8 AI 指令箱 · 远程

以下指令模板与工具无关。**颜色标注**：绝大多数远程操作都可以做到黄色以下（fetch 是最纯粹的绿色），涉及 push（尤其是 force）的转黄，force push 到共享分支已经踩到黄红交界（第 12 章会展开）。

**🟢 探索类（只读，放心用）**

- 「看一下当前仓库配置的所有 remote：每个的别名、URL、fetch/push URL 是否分开（有些团队会分）。用表格给我。」
- 「跟远端对齐一下认知：先 `git fetch --all`，然后告诉我我本地每一个分支和它对应的远程分支之间的关系——各自领先/落后多少个 commit，有没有分叉。」
- 「读 `.git/config`，用中文向我解释 `[remote "origin"]` 和 `[branch "main"]` 这两段配置。特别指明：如果我 `git pull` 什么都不加，Git 会去哪儿、拉什么、怎么合。」
- 「让我看看 `.git/refs/remotes/origin/` 下有哪些文件、每个文件里写的 SHA。**不是** `git branch -r` 的输出，我要看那几个物理文件。」

**🟢 同步类（fetch，纯安全）**

- 「fetch 所有远程的所有分支。fetch 完成后告诉我：这次 fetch 更新了哪些远程分支的位置（哪些前移了、前移了几格）、有没有新出现的远程分支、有没有本地缓存有但远端已经删除的分支。」
- 「我要跟上 origin 上 main 的最新进展。步骤：1) fetch origin；2) 展示远端 main 和我本地 main 的差异（各自领先多少、有没有冲突风险）；3) 停下来等我决定用 rebase 还是 merge。」

**🟡 需要盯着的（会改本地历史或推到远端）**

- 「把我本地的 main 追上 origin/main 的最新。用 rebase，不要用 merge——我不想要那颗 merge commit。执行前告诉我：如果 rebase 中间遇到冲突，你会停下来让我处理，对吗？」
- 「我要把当前分支第一次 push 到 origin，同时建立 upstream 追踪。用 `-u`。执行前告诉我远端 origin 上现在有没有同名分支——如果有，别 push，先问我。」
- 「我 push 被拒了（non-fast-forward）。先 fetch，告诉我远端上出现了哪些我不知道的 commit（作者、message）。看完我再决定：rebase 我的改动上去，还是这些远端 commit 我要丢弃。**不要**在我确认之前 force。」

**🟡 Fork 同步类**

- 「这是一个 fork 项目，我 clone 的是我自己 fork 的那份（origin）。帮我加一个 remote 叫 upstream，指向原始项目 <URL>。加完 fetch 一下 upstream。」
- 「同步 upstream/main 到我本地 main，并推到我的 fork（origin）。策略：直接让本地 main 完全等于 upstream/main（因为我从不在 main 上开发）。用 `reset --hard` + `push --force-with-lease`。执行前列出会做的每一步。」

**训练用指令（陪练模式）**

- 「假装我从没搞清楚 origin/main 和 main 的区别。问我 5 个诊断题：'当我在本地 commit 之后，origin/main 有没有变''fetch 之后我的 main 分支会不会前移''status 说 up to date 是相对什么在说''pull 里那个我没造过的 merge commit 是谁造的''push 被拒是 Git 在保护什么'——一次一个，看我答得对不对，讲评。」
- 「用'镜子里的项链'和'贴在墙上的名牌'比喻，向一个刚从 SVN 迁过来的人解释：为什么 Git 里的\"远程分支\"实际住在本地。200 字。」
- 「给我 8 道'我该 fetch 还是 pull 还是 push 还是 force push'的场景判断题。场景包括：'我刚 commit 完想同步'\"我刚被 push 拒了\"\"我要发 PR 前跟上主干\"\"我误推了要撤回\"等等。」

---

## 4.9 执行后的世界

| 你说的话 | AI 大概率执行 | `.git/` 里的真实变化 |
|---|---|---|
| \"看看远程有什么\" | `git remote -v` | **零变化**（读 `.git/config`） |
| \"fetch 一下\" | `git fetch origin` | 可能新增 objects/（新对象）；更新 `refs/remotes/origin/*` 里的一堆文件；**你本地分支和 HEAD 完全不动** |
| \"pull 一下\" | `git pull` = fetch + merge/rebase | fetch 那步同上；merge/rebase 那步造一颗或多颗新 commit，把当前本地分支的名牌移过去 |
| \"push 到远端\" | `git push origin main` | 本地新对象打包传给远端；远端 `refs/heads/main` 前移；**你本地** `refs/remotes/origin/main` **也前移**（本地缓存自动更新到你刚推的位置） |
| \"加个远程叫 upstream\" | `git remote add upstream <url>` | `.git/config` 里新增一段 `[remote "upstream"]`；`refs/remotes/` 下**暂时不新增东西**（要 fetch 才会） |
| \"删掉 origin\" | `git remote remove origin` | `.git/config` 里那段配置消失；`refs/remotes/origin/` 目录被删除；**objects 里对应的 commit 对象一颗不少地留着** |
| \"改 origin 的 URL\" | `git remote set-url origin <new>` | 只改 `.git/config` 里的 URL 字段。缓存的 refs 不动。 |

看懂这张表你会理解：**几乎所有\"远程操作\"落到 `.git/` 里，最终都归结为两件事——读写 `.git/config` 里几段文本、读写 `.git/refs/remotes/` 里几个文件。** 加上 fetch/push 那一小段网络传输，就是全部了。

---

## 4.10 命令侧栏

```
git remote -v                  # 列出所有远程 + URL
git remote add <name> <url>    # 加一个远程（就是给 config 加两行字）
git remote remove <name>       # 摘掉一个远程
git remote set-url <n> <url>   # 改远程的 URL

git fetch                      # 更新默认远程的缓存
git fetch origin               # 更新指定远程的缓存
git fetch --all                # 所有远程一起更新
git fetch --prune              # 顺便把远端已删除的分支从本地缓存里清掉

git pull                       # = fetch + merge（或 rebase，看配置）
git pull --rebase              # 强制用 rebase
git pull --ff-only              # 只允许快进，分叉就停（共享分支建议）

git push                       # 推到 upstream 对应的远端分支
git push -u origin <branch>    # 首次 push 并建立 upstream 追踪
git push --force-with-lease    # \"温柔的\"force：只在远端没在你上次 fetch 之后变过才允许

git branch -vv                 # 列出本地分支 + 它们的 upstream + 各自领先/落后多少
git log main..origin/main      # 远端有、本地没有的 commit
git log origin/main..main      # 本地有、远端没有的 commit
```

不需要背。需要时回来看，或者直接说人话让 AI 翻译。

---

## 4.11 本章小地图

```
远程 = 你的仓库对另一个仓库的引用 = 别名 + URL（.git/config 里两行字）
  │
  ├─ 别名（origin/upstream/whatever）—— 你随便起
  ├─ URL —— 指向另一份 .git/
  └─ fetch refspec —— 从哪儿拉、放到哪儿

远程分支 = 本地缓存！ = .git/refs/remotes/<remote>/<branch>
  │
  ├─ 物理上：一个文件，40 个字符（和本地分支一模一样）
  ├─ 语义上：\"我上次听说远端那个分支指向哪颗珠子\"
  └─ 更新时机：只有 fetch / pull / push 会碰它

碰网络的只有 fetch 家族与 push：clone / fetch / pull / push / ls-remote / remote show / remote update
  │
  ├─ fetch  只更新缓存，本地分支/HEAD/工作区全不动（最安全）
  ├─ pull   = fetch + merge/rebase（一个宏，把决策塞进了默认）
  └─ push   把本地推到远端（受 fast-forward 保护）

upstream = 本地分支绑定的远程分支（默认 push/pull 走这条）
  │
  └─ 首次 push 时用 -u 建立；之后 push/pull 不用写目标

Fork 工作流三层：
  local ──▶ origin (你的 fork) ──▶ upstream (原始项目)
        push          PR

non-fast-forward = Git 在按停按钮
  │
  ├─ 意思：远端有我不知道的 commit，我不敢帮你决定
  ├─ 正确应对：fetch → 看清楚 → rebase → 再 push
  └─ 绝不要：一见拒就 --force（尤其在共享分支上）
```

---

## 4.12 三大典型误解拆解

**误解一：\"origin/main 就是服务器上的 main。\"**
不是。**`origin/main` 是你本地 `.git/refs/remotes/origin/` 下的一个文件里写着的一个 SHA——它反映的是\"你上次 fetch 那一刻，远端 main 的位置\"**。从那以后，服务器上 main 无论怎么变，你本地的 origin/main 都不会动，直到你下一次 fetch。这个"缓存"设计不是 Git 的缺陷，是它\"离线优先、显式同步\"哲学的核心。**理解了这一条，`git status` 里的\"up to date with origin/main\"这句话你就会读出真正的意思了——它说的是\"和缓存一致\"，不是\"和远端服务器一致\"。** 想知道服务器\"此刻\"的样子？先 fetch，再 status。

**误解二：\"pull 就是拉代码下来看看，完全安全。\"**
`pull = fetch + merge/rebase`——**第二步会改你本地的分支历史**。它不是只读操作，它是\"拉 + 合并\"两步的封装，第二步是彻头彻尾的写操作。你会得到一颗你没主动造的 merge commit（如果本地和远端分叉了、又用了默认的 merge 策略），或者你的 commit 会被 rebase 换 SHA（如果配了 rebase）。**\"pull 很安全\"这个直觉害了很多人**——它把两个性质完全不同的操作装进一个动词里，让人以为\"我只是想同步一下嘛\"。真正安全的只读同步操作是 `fetch`。养成 fetch-first 的习惯，pull 只在你**明确知道自己想要\"顺便合并\"** 的时候用。

**误解三：\"push 被拒（non-fast-forward）说明我要 --force。\"**
**方向反了。** non-fast-forward 是 Git 在说\"远端有你不知道的 commit，如果你强推会踢掉它们\"。99% 的正确应对是：**fetch → 看清楚远端多出来什么 → 把你的改动 rebase 到远端最新之上 → 再 push（这次会 fast-forward 通过）**。`--force` 的正确用法极其罕见，通常只在你**自己刚才误推了想撤回**、**且没有别人拉过那颗错误的 commit** 的情况下用；即便如此也应该用 `--force-with-lease` 而不是裸的 `--force`（第 12 章展开安全边界）。**在共享分支上 --force 是 Git 世界里少数几个会真正伤害同事的操作之一**——它让别人本来拉过的 commit 从项链上消失，别人再 pull 就会陷入一堆混乱的合并冲突。看到 non-fast-forward，先深呼吸，再 fetch。

---

**下一章预告：** 到这里五张地图你已经掌握了四张：仓库、提交、分支、远程。最后一张——**历史是可塑的**——揭开 Git 里最让人又爱又怕的一层：`merge` 和 `rebase` 到底在做什么、为什么 rebase 会\"改写\"历史（其实是造新珠子）、\"不要 rebase 已推送的 commit\"这条黄金规则为什么是黄金、以及**为什么 reflog 是你的隐形保险丝——你以为丢了的珠子，几乎永远都能救回来**。

（你会在第 5 章看到本章埋的伏笔正式兑现：`origin/main` 是本地缓存这条事实，会解释为什么 fork 工作流里"我 rebase 完往 origin 推为什么被拒"、"我 amend 完为什么远端 pull 下来会有冲突"——一切都可以在\"珠子不可变、项链可以重串、远端项链只是本地一份缓存\"这三条上推导出来。）

---

> **🤖 AI 指令箱 · 本章实战演练**
>
> 找一个真实的远程仓库（或临时 clone 一个开源项目，比如某个你不熟的开源工具），按顺序执行下面几条：
>
> - 「打开这个仓库。列出所有 remote、每个 remote 的 URL。然后列出所有本地分支和它们的 upstream 追踪关系（用 `git branch -vv`）。用表格给我。」
> - 「fetch 一下所有远程，fetch 前后对比：`.git/refs/remotes/origin/` 目录里哪些文件被更新了（内容 SHA 变了）、有没有新出现的文件、有没有本地已经不存在于远端的分支（用 `--prune` 清一下）。」
> - 「造一个假分叉场景来练手：a) 在本地 main 上造一颗新 commit（随便改点东西）b) 让 AI 假装远端上也造了一颗（其实是先切到 detached HEAD 手动造一颗然后 update-ref 到 origin/main，或者从另一个 clone 里 push 上去）c) 观察 `git status` 说什么 d) 观察 `git push` 会不会被拒 e) 用 `fetch + rebase + push` 的三步收拾干净。」
> - 「假设你 fork 了一个开源项目，clone 下来后加 upstream 指向原项目。同步 upstream 最新到本地 main 并推到你的 fork。让 AI 列出所有步骤和每一步之后 `.git/refs/` 目录里发生的变化。」
