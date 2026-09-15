# 附录 A · 命令速查表

> 全书唯一集中命令参考。按概念地图分组（非字母序），每条命令三列：命令 / 概念语义 / 想用 AI 说人话怎么说。

---

## 为什么本书最后才给你命令表

如果你从头一路读到这里，你就明白了：**命令是概念的投影，不是概念本身。**

`git branch feature-x` 是"往 `refs/heads/` 写一行文本"的投影；`git commit` 是"把暂存区打包成一颗珠子挂到当前标签上"的投影；`git push --force-with-lease` 是"我打算重写远端项链，但前提是远端在我上次听说之后没被别人动过"的投影。**投影可以有很多种写法**（老的 `checkout` 拆成了新的 `switch`/`restore`，`filter-branch` 被 `filter-repo` 取代，图形工具再把它们包一层按钮），但被投影的那件事——DAG 上的珠子和标签怎么动——五十年不变。

所以本书前十三章从不催你背命令：你先学地图，命令自然归位。等到你真的需要一条命令的时候，你脑子里想的应该是**"我要做什么"**（第三列），不是**"用哪个开关"**（第一列）——中间的翻译工作，第二列告诉你 Git 在物理上真正在做什么，AI 负责把第三列变成第一列。

这张表的正确用法：

1. **忘了某个动词的具体拼写** —— 顺着分组标题（"仓库"/"三区"/"分支"/"历史"/"远程"/"重塑"/"清理"）找到区，扫第一列。
2. **不确定某条命令的物理后果** —— 看第二列。第二列写的是".git/ 里到底发生了什么"，不是"人话说明"。
3. **不确定该用哪条命令** —— 只读第三列，然后直接把第三列念给 AI 听。AI 挑第一列，你审第二列，确认后放行。

**表里没有的命令，通常也不需要你知道**。真需要的时候，让 AI 查 `git help <verb>`，或者说人话让它翻译。

**颜色约定**（跟着全书 AI 指令箱统一）：

- 🟢 只读 / 造新对象但不动引用 —— 放心跑
- 🟡 移动引用 / 改工作区 —— AI 先出方案、你按快门
- 🔴 破坏性 / 影响远端 / 不可逆 —— 每次都必须重新签字

---

## A.1 仓库：一个自包含的历史数据库

**什么时候用**：新建仓库、克隆别人的仓库、体检 `.git/` 的家底。这一组命令的共性是"建立或勘察一个 Git 世界的边界"——它们要么造出一个新的 `.git/`，要么告诉你现有的 `.git/` 在哪、有多大。第一次接触一个新仓库，先跑一遍前三行你就知道自己身在何处。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git init` | 在当前目录新建 `.git/`，把这个目录变成仓库 | "在这个目录搭一个空的 Git 档案馆，还没有任何提交。" |
| 🟢 `git init --bare` | 造一个只有 `.git/` 内容、没有工作区的裸仓库 | "搭一个服务器用的裸仓库，只存历史，不要工作区。" |
| 🟢 `git clone <url>` | 把远端的整个档案馆复制过来，铺开工作区，登记远程别名 `origin` | "把这个 URL 的仓库整个克隆下来。" |
| 🟢 `git clone --depth 1 <url>` | 浅克隆：只要最新一层历史，不要全部珠子 | "克隆但只要最近一版，我不需要完整历史。CI 用。" |
| 🟢 `git clone <local> <dst>` | 本地对本地克隆，等价于复制 `.git` 目录 | "把这个本地仓库再克隆一份到 dst，作为演练沙盒。" |
| 🟢 `git clone --mirror <url>` | 镜像克隆：完整拷贝所有 refs，用作备份/迁移 | "在动 filter-repo 之前，先镜像备份一份。" |
| 🟢 `git ls-remote <url>` | 只问不下载：列出远端所有 refs 及其 SHA | "只查一下这个远程仓库有哪些分支和 tag，不要克隆。" |
| 🟢 `git rev-parse --git-dir` | 告诉我 `.git` 目录在哪里 | "我在哪个仓库里？.git/ 到底在哪？" |
| 🟢 `git rev-parse --show-toplevel` | 告诉我当前仓库的根目录 | "帮我打印仓库根目录的绝对路径。" |
| 🟢 `git count-objects -vH` | 统计 `.git/objects/` 的对象数量与体积（带人类可读单位） | "看看这个仓库有多少对象、占多大。" |
| 🟢 `git fsck --strict` | 走一遍所有对象，检查完整性 | "帮我做一次仓库完整性体检，看看有没有坏对象。" |

---

## A.2 提交三区：工作区 / 暂存区 / 仓库

**什么时候用**：你正在攒一次提交、想看这次要交上去的到底是什么、要撤下已经 add 上台的东西、要修补刚才那颗珠子的 message 或漏加的文件。三区模型的所有命令都在两条线上工作——把改动搬来搬去（`add` / `restore`），把三区之间的差异说清楚（`status` / `diff`）。这一组是你每天用得最多、也最容易被误用的。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git status` | 报告工作区 vs 暂存区 vs HEAD 三层之间的差异 | "现在工作区/暂存区/最近提交各是什么状态？" |
| 🟢 `git diff` | 工作区 vs 暂存区的差异（未 add 的部分） | "我改了什么还没 add 上台？" |
| 🟢 `git diff --staged` | 暂存区 vs 上次 commit 的差异（这次要 commit 的东西） | "这次要 commit 的内容让我先看一遍。" |
| 🟢 `git diff --cached --stat` | 这次要 commit 的规模概览（改了几个文件、多少行） | "这次 commit 大概多大？给我一份 stat。" |
| 🟢 `git diff --cached --name-only` | 只列这次要 commit 的文件名 | "列一下这次会进 commit 的文件名，我扫一眼有没有敏感文件。" |
| 🟡 `git add <file>` | 把这个文件的当前内容放上暂存区 | "把这个文件加到入库台。" |
| 🟡 `git add -p` | 逐个 hunk 交互式选择加入暂存 | "帮我把这堆改动按逻辑拆成两组分别 stage：一组是重构、一组是 bugfix。" |
| 🟡 `git add .` | 把工作区所有改动一股脑加入暂存 | "把所有改动一次性 add 上台。（会附带扫一次敏感文件）" |
| 🟡 `git restore --staged <file>` | 把这个文件从暂存区撤下，工作区改动保留 | "把这个文件从入库台撤下来，改动我先留着。" |
| 🟡 `git restore <file>` | 用暂存区（或指定 source）覆盖工作区里的这个文件 | "把这个文件恢复到最近一次 add 时的状态。" |
| 🟡 `git commit` | 把暂存区状态打包成一颗新珠子，挂到当前分支末端 | "把暂存区打包成一个 commit，打开编辑器让我写 message。" |
| 🟡 `git commit -m "..."` | 同上，附上一句 message | "把这次改动做成一个 commit，message 是 xxx。" |
| 🟡 `git commit -a` | 已跟踪文件的改动自动 add + commit（新增文件不管） | "帮我把所有已跟踪文件的改动一次性 commit 掉。" |
| 🟡 `git commit --amend` | 造一颗新珠子替换掉上一颗，旧的进 reflog | "帮我把刚才那颗 commit 的 message/内容补一下（还没 push）。" |
| 🟢 `git show <sha>` | 展示某颗珠子的完整内容和 diff | "把这个 commit 完整内容给我看，包括 diff。" |
| 🟡 `git rm <file>` | 从工作区和暂存区一并移除 | "把这个文件删掉并 stage 这个删除。" |
| 🟡 `git rm --cached <file>` | 只从暂存区/追踪列表移除，本地文件保留 | "取消追踪 `.env`（本地文件别删），配 .gitignore 一起用。" |
| 🟢 `git cat-file -t <sha>` | 查一个对象是什么类型（commit/tree/blob/tag） | "这个 SHA 到底是什么类型？commit / tree / blob / tag？" |
| 🟢 `git cat-file -p <sha>` | 以人类可读方式打印对象内容 | "把这个对象的原始内容打印出来给我看。" |

---

## A.3 分支与检出：给珠子起名字、挪 HEAD、挂标签

**什么时候用**：开新功能分支、切走去别的分支、给某颗珠子打 tag 做发布记号、临时进 detached HEAD 看看历史版本、清理已合并的旧分支。这一组的共性是**只挪指针，不改历史**——分支和 tag 都是"往 `refs/` 里写一行文本"，代价 O(1)，所以**试错应该大胆，删除不需要恐惧**。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git branch` | 列出所有本地分支，标出当前所在 | "列一下我这儿都有哪些本地分支。" |
| 🟢 `git branch -a` | 列出全部分支（本地 + 远程缓存） | "把本地和远程的分支都列一遍。" |
| 🟢 `git branch -av` | 上一条 + 每个分支指向的 sha 和 message | "列所有分支和它们的当前位置。" |
| 🟢 `git branch -vv` | 列本地分支 + upstream + 领先/落后多少 commit | "看看我的每个本地分支跟远端相比状态如何。" |
| 🟡 `git branch <name>` | 在当前 HEAD 位置挂一张新标签（不切换） | "在这里挂个分支叫 xxx，别切过去。" |
| 🟡 `git branch <name> <sha>` | 在指定 sha 位置挂一张新标签 | "在这颗 commit 上挂个分支叫 rescue/xxx，把孤儿救回来。" |
| 🟡 `git branch -d <name>` | 摘掉标签（拒绝摘未合并的分支） | "删掉这个分支（如果它已经合并了）。" |
| 🔴 `git branch -D <name>` | 强制摘标签（含未合并警告） | "强制删这个分支，我知道它还没合并。" |
| 🟢 `git branch --merged main` | 列出所有已合并进 main 的本地分支 | "列出所有已经合并进 main 的本地分支，我准备清。" |
| 🟢 `git branch -r --merged main` | 已合并进 main 的远程分支 | "远端有哪些分支已经并进 main 可以清了？" |
| 🟢 `git for-each-ref --sort=-committerdate refs/heads/` | 按最近提交时间排序列出本地分支（找僵尸分支） | "按最后提交时间从新到旧列所有本地分支，我找僵尸。" |
| 🟡 `git switch <name>` | 把 HEAD 挪到某分支上，铺开工作区（现代版 checkout） | "切到分支 xxx。" |
| 🟡 `git switch -c <name>` | 挂新标签 + 切过去，一步完成 | "从当前位置开一个新分支叫 xxx 并切过去。" |
| 🟡 `git switch -c <name> <起点>` | 从指定起点开新分支并切过去 | "从 origin/main 开一个新分支叫 feature/x 并切过去。" |
| 🟡 `git switch -` | 回到上一个待过的分支（`-` 是快捷键） | "切回上一个分支。" |
| 🟡 `git checkout <sha>` | HEAD 直接指向某颗珠子（detached HEAD） | "进入 detached HEAD 看看这颗 commit 的代码。" |
| 🟡 `git checkout --ours <file>` | merge/rebase 冲突时，整个文件采纳"我这侧" | "这个文件整个保留我这侧（我知道我要什么）。" |
| 🟡 `git checkout --theirs <file>` | 冲突时整个文件采纳"对面"（rebase 语义颠倒！） | "这个文件整个采纳对面版本。（注意 rebase 时含义相反）" |

---

## A.4 历史与检查：读地图、追作案、做二分

**什么时候用**：看看昨天/这周/这个 release 都发生了什么；追一行代码/一个 bug 是谁在什么时候引入的；某个功能什么时候还是好的、什么时候坏的；写 release note；review 别人的 PR。这一组命令**全都是只读的**——它们不动 `.git/objects/`，也不动 `refs/`，你怎么跑都不会坏东西。放心用，尤其放心让 AI 用。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git log` | 从 HEAD 往回走，按顺序列出所有能到达的珠子 | "从这里往前列 commit。" |
| 🟢 `git log --oneline` | 一行一颗珠子的紧凑视图 | "一行一颗给我列 commit。" |
| 🟢 `git log --oneline -10` | 只看最近 10 颗 | "最近 10 颗 commit 是什么？" |
| 🟢 `git log --oneline --graph --all` | 带图形的、包含所有分支的项链视图 | "画一下所有分支的项链图。" |
| 🟢 `git log --pretty=fuller` | 完整元信息（作者、committer、时间） | "把这些 commit 的完整元信息给我，包括 author 和 committer。" |
| 🟢 `git log -p <file>` | 追某个文件的完整改动史 | "这个文件从诞生到现在都被谁改过什么？" |
| 🟢 `git log --follow <file>` | 追某文件的历史（跨越改名） | "追这个文件的历史，改名前的也要。" |
| 🟢 `git log -L <start>,<end>:<file>` | 追某文件某段行的完整变更史 | "文件 x 的第 47–80 行的变更历史。" |
| 🟢 `git log -S 'string'` | pickaxe：搜索 diff 里增删过某字符串的 commit | "哪几个 commit 里出现过或删掉过 'foo_bar'？" |
| 🟢 `git log -G 'regex'` | 搜索 diff 里增删过匹配某正则的内容 | "找出 diff 里出现过匹配这个正则的 commit。" |
| 🟢 `git log --author='Alice'` | 按作者过滤 | "只列 Alice 的 commit。" |
| 🟢 `git log --after='2025-01-01' --before='2025-06-30'` | 按时间范围过滤 | "只看今年上半年的 commit。" |
| 🟢 `git log --since="3 months ago"` | 近 N 时间的 commit | "看看过去 3 个月的变化。" |
| 🟢 `git log v1.0..HEAD` | 某段范围内的 commit（做 release note 用） | "从 v1.0 到现在都改了什么，给我写份 release note 底稿。" |
| 🟢 `git log main..origin/main` | 远端有、本地没有的 commit | "origin/main 上有什么我这儿还没有的？" |
| 🟢 `git log origin/main..main` | 本地有、远端没有的 commit | "我本地有什么还没推上去的？" |
| 🟢 `git log <branch> --not main` | 相对 main 领先的独立 commit | "这个分支相对 main 领先了哪些 commit？" |
| 🟢 `git log --merge --oneline` | 当前冲突涉及的两侧独有 commit | "列出这次冲突两边各自独有的 commit。" |
| 🟢 `git log --show-signature` | 显示每颗 commit 的签名状态 | "检查一下这些 commit 的签名，我要看谁没签、谁签失败了。" |
| 🟢 `git log --all --full-history -- <file>` | 全历史里搜某文件是否出现过（含已删除） | "历史里有没有出现过 `.env` 这个文件？" |
| 🟢 `git rev-list --count main..<branch>` | 数一条分支相对 main 领先了几颗 | "这个分支比 main 多几颗 commit？" |
| 🟢 `git show <sha>` | 展示某颗珠子的完整内容 | "把这颗 commit 完整给我看。" |
| 🟢 `git show <blob-sha>` | 展示某个 blob 对象的内容 | "把这个 blob 内容打印出来。" |
| 🟢 `git show <blob-sha> > <path>` | 把 blob 内容还原成文件（救回未 commit 的改动） | "把这个 dangling blob 还原成文件 x。" |
| 🟢 `git blame <file>` | 每行标注最后修改者和 commit | "这个文件每一行最后是谁改的？" |
| 🟢 `git blame -L 47,80 <file>` | 只 blame 指定行范围 | "文件 x 的第 47–80 行，每行最后是谁改的？" |
| 🟢 `git shortlog -sn` | 按人聚合提交计数 | "谁贡献了多少 commit？" |
| 🟢 `git shortlog -sn --no-merges` | 排除 merge commit 的贡献榜 | "贡献榜，把 merge commit 排除掉。" |
| 🟢 `git shortlog -sn --after='6 months ago'` | 近半年贡献榜 | "近半年谁最活跃？" |
| 🟢 `git reflog` | HEAD 的移动史（最近的在最上面） | "让我看看最近 HEAD 是怎么挪的。" |
| 🟢 `git reflog --date=iso -50` | 带 ISO 时间的最近 50 条 reflog | "最近 50 次 HEAD 移动，带时间戳。" |
| 🟢 `git reflog show <branch>` | 某个分支的移动史 | "分支 main 最近挪过哪些位置？" |
| 🟢 `git bisect start` | 开始二分查错 | "开始二分查这个 bug。" |
| 🟢 `git bisect bad [<sha>]` | 标记坏点（默认 HEAD） | "这个版本是坏的。" |
| 🟢 `git bisect good <sha>` | 标记好点 | "这个版本是好的。" |
| 🟢 `git bisect run <script>` | 自动跑测试脚本二分 | "用这个脚本自动二分。" |
| 🟢 `git bisect reset` | 结束二分，HEAD 回到原位置 | "二分完了，收工。" |
| 🟢 `git describe` | 描述 HEAD 相对最近 tag 的位置 | "HEAD 相对最近的 tag 差多少颗 commit？" |
| 🟢 `git fsck --lost-found` | 列出所有 unreachable 的对象（孤儿珠子/blob/tree） | "扫一下所有 unreachable 对象，我在找丢的东西。" |
| 🟢 `git ls-files -u` | 列出 index 里所有 stage != 0 的条目（底层查冲突） | "底层看看 index 里的冲突条目。" |
| 🟢 `git diff --check` | 查找漏删的 `<<<<<<<` 冲突标记 | "扫一遍看有没有漏删的冲突标记。" |
| 🟢 `git diff --ours <file>` | 我的最终版本 vs ours 侧 | "我改完的版本相对 ours 侧改了什么？" |
| 🟢 `git diff --theirs <file>` | 我的最终版本 vs theirs 侧 | "我改完的版本相对 theirs 侧改了什么？" |

---

## A.5 远程同步：本地项链和远端项链互相对齐

**什么时候用**：早上开工先同步一下、推自己的 feature 分支上去、别人的分支下来 review、清理已经删掉的远程分支缓存、协作时用 `--force-with-lease` 安全地重写共享分支。这一组是**全书唯一会碰网络**的命令族——记住只有 5 个：`clone / fetch / pull / push / remote update`，其他一切都在本地。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git remote -v` | 列出所有远程别名 + URL | "我这儿有哪些远程？" |
| 🟡 `git remote add <name> <url>` | 在 `.git/config` 里加一条远程别名 | "加一个叫 upstream 的远程指向这个 URL。" |
| 🟡 `git remote remove <name>` | 摘掉一个远程 | "把这个远程别名删了。" |
| 🟡 `git remote set-url <name> <url>` | 改远程的 URL | "把 origin 的 URL 改成 xxx。" |
| 🟢 `git fetch` | 更新默认远程的缓存，不动本地分支/工作区 | "拉一下最新的远端信息，先别合过来。" |
| 🟢 `git fetch origin` | 更新指定远程的缓存 | "从 origin 拉一下最新。" |
| 🟢 `git fetch --all` | 所有远程一起更新 | "把所有远程都 fetch 一遍。" |
| 🟢 `git fetch --prune` | fetch + 顺便把远端已删的分支从本地缓存清掉 | "fetch 一下，顺便清理本地那些远端已经删掉的分支缓存。" |
| 🟡 `git pull` | fetch + merge（或 rebase，看配置） | "把远端的合到我本地这条分支上。" |
| 🟡 `git pull --rebase` | 强制用 rebase 而不是 merge | "把我的本地改动 rebase 到最新的远端之上，不要造 merge commit。" |
| 🟡 `git push` | 推到 upstream 对应的远端分支 | "把我这条分支推上去。" |
| 🟡 `git push -u origin <branch>` | 首次推 + 建立 upstream 追踪 | "首次推这条分支，顺便把 upstream 挂上。" |
| 🟡 `git push origin <tag>` | 推指定 tag | "把这个 tag 推到 origin。" |
| 🟡 `git push --tags` | 推所有本地 tag | "把所有本地 tag 都推上去。" |
| 🔴 `git push --force-with-lease` | 温柔版 force：只在远端"没在你上次 fetch 之后变过"才允许 | "我要重写这条分支的历史推上去，用温柔版 force。（先确认没人在我之后 push）" |
| 🔴 `git push --force` | 核武器 force，无条件覆盖 | "无条件强推。（绝大多数场景该用 --force-with-lease）" |
| 🔴 `git push origin --delete <tag>` | 删远端 tag | "把远端这个 tag 删掉。" |
| 🔴 `git push --force --all` | 强推所有分支（历史清理后使用） | "清完历史了，把所有分支强推上去。" |
| 🟢 `git config --global pull.rebase true` | 把默认 `pull` 行为设为 rebase | "把默认 pull 改成 rebase，别再造 merge commit。" |

---

## A.6 历史重塑：造新珠子 + 挪标签 + 旧珠子进 reflog

**什么时候用**：合两条分支、把一条分支重播到另一条之上让历史线性化、撤销一颗已经 push 出去的珠子、把工作区/暂存区/HEAD 一键回到某个位置、把某颗珠子摘到当前分支上、临时把改动塞进抽屉。这一组是**全书最危险的一组**——所有"重写历史"都不是真的改珠子（珠子不可变），而是**造一批新珠子 + 挪标签 + 旧珠子进 reflog**，30 天内都能救。共享分支上永远优先 `revert`，不用 `reset`。

### merge 系（合流）

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git merge <branch>` | 把 branch 合到当前分支（可能 ff、也可能造 merge commit） | "把 branch 合过来。" |
| 🟡 `git merge --no-ff <branch>` | 强制造 merge commit（哪怕能 ff） | "把 branch 合过来，强制留下 merge 记号，别 ff。" |
| 🟡 `git merge --squash <branch>` | 把 branch 的改动作为一坨未提交状态摆到暂存区（不造 merge commit） | "把 branch 的改动 squash 到我的暂存区，我自己写一颗 commit。" |
| 🟢 `git merge --abort` | 冲突时放弃 merge，回到操作前 | "放弃这次 merge，恢复原状。" |
| 🟢 `git mergetool` | 调起配置的三方合并 UI | "打开 mergetool 让我图形化解冲突。" |

### rebase 系（重播）

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git rebase <base>` | 把当前分支的独有 commit 重播到 `<base>` 之上（线性化） | "把我这条分支 rebase 到 main 最新上。" |
| 🟡 `git rebase -i <base>` | 交互式：pick/reword/squash/fixup/drop/reorder | "交互式重整我最近的 N 颗 commit：合并这两颗、reword 这一颗、丢掉那颗。" |
| 🟡 `git rebase --continue` | 冲突解决完，继续重播下一颗 | "冲突解完了，rebase 继续。" |
| 🔴 `git rebase --skip` | 跳过当前正在重播的珠子（罕见，慎用） | "跳过这颗（我知道我在干什么）。" |
| 🟢 `git rebase --abort` | 完全放弃这次 rebase，回到开始前 | "rebase 越搞越乱，放弃，回到原状。" |

### reset 系（挪标签，可能顺带改暂存/工作区）

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git reset --soft <target>` | 只挪当前分支标签，暂存区和工作目录都不动 | "把分支指针挪到那儿，改动全留在暂存区。" |
| 🟡 `git reset --mixed <target>` | 挪标签 + 重置暂存区（默认） | "挪分支指针，暂存区一并重置，工作区改动保留。" |
| 🔴 `git reset --hard <target>` | 挪标签 + 重置暂存区 + 重置工作目录（危险） | "所有东西一键回到那颗 commit（我确认丢掉当前所有未 commit 改动）。" |
| 🟢 `git reset ORIG_HEAD` | 撤销刚才的 merge/rebase/reset，一键回到操作前 | "刚才那次 merge/rebase 白搞了，一键回到操作前。" |
| 🔴 `git reset --hard HEAD@{N}` | 精确回到 reflog 里第 N 条记录的位置 | "回到 reflog 里那个位置。" |

### revert 系（造抵消珠子）

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git revert <sha>` | 造一颗抵消 `<sha>` 效果的新珠子挂到末端 | "把这颗已经推上去的 commit 撤销掉（造抵消珠子，不改历史）。" |
| 🟡 `git revert -m 1 <sha>` | 撤销一颗 merge commit（`-m 1` 指定要保留的主线 parent） | "把这颗 merge commit 撤了，主线是第一个 parent。" |
| 🟡 `git revert <sha1>..<sha2>` | 撤销一段范围（不含起点） | "把这一段 commit 全部 revert 掉，一颗一颗抵消。" |
| 🟡 `git revert --no-commit <a>..<b>` | 撤销一段但不自动 commit，最后合一颗 | "撤这段但先不 commit，我要合成一颗 revert commit。" |

### cherry-pick 系（摘珠子）

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git cherry-pick <sha>` | 复制某颗珠子到当前分支末端 | "把那颗 commit 摘到当前分支上。" |
| 🟡 `git cherry-pick <A>..<B>` | 摘一段（不含 A、含 B） | "把 A 到 B 这一段（不含 A）依次摘过来。" |
| 🟡 `git cherry-pick -m 1 <merge-sha>` | 摘一颗 merge commit（`-m` 指定 parent 侧） | "把这颗 merge commit 摘过来，主线取第一个 parent。" |
| 🟡 `git cherry-pick --continue` / `--skip` / `--abort` | cherry-pick 中途的三个开关 | "cherry-pick 冲突解完了，继续 / 跳过 / 放弃。" |

### stash 系（抽屉）

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git stash` | 把当前工作区+暂存区的改动塞进抽屉，工作区变干净 | "把手头改动先塞抽屉，我要切个分支。" |
| 🟡 `git stash push -u -m "..."` | 塞抽屉，`-u` 含 untracked，附一句说明 | "塞抽屉，untracked 文件也带上，写一句备注。" |
| 🟢 `git stash list` | 看所有抽屉格 | "抽屉里都有什么？" |
| 🟢 `git stash show -p [stash@{N}]` | 看某格的 diff | "第 N 个抽屉里到底是什么改动，diff 给我看。" |
| 🟡 `git stash apply [stash@{N}]` | 从抽屉取出，不销毁抽屉 | "从抽屉取出来，抽屉别销毁。" |
| 🟡 `git stash pop [stash@{N}]` | 取出 + 销毁（冲突时不销毁） | "把抽屉里那格取出来用掉。" |
| 🔴 `git stash drop [stash@{N}]` | 只销毁抽屉（不取出） | "把那格抽屉直接扔掉。" |

---

## A.7 清理与维护：垃圾回收、僵尸清理、历史手术

**什么时候用**：仓库变大了想瘦身、`rm -rf` 过某个 worktree 目录留了元数据孤儿、要从历史里彻底清除某个泄漏的密钥/大文件、开启后台定期维护。这一组的共性是**动 `.git/objects/` 或 `refs/` 本体**——`gc` 之前的东西都还救得回来，`gc --prune=now` 之后基本救不了；`filter-repo` 更是重写所有历史 SHA、动摇整个团队根基的"核武器"。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git clean -n` | dry-run：列出会被清理的 untracked 文件（不真删） | "先只列出这个仓库里所有 untracked 会被清掉的东西，不要真删。" |
| 🔴 `git clean -fd` | 真删 untracked 文件和目录 | "确认清掉刚才那些 untracked，包括目录。" |
| 🟢 `git gc` | 打包散落对象、压缩 `.git/objects/` 存储 | "帮我做一次常规 gc，压缩一下 objects。" |
| 🟢 `git gc --aggressive` | 深度重打包（慢，仓库很大时用） | "深度重打包，我等得起。" |
| 🔴 `git gc --prune=now` | 立即清理所有 unreachable 对象（危险，撤销托管期） | "立即清理 unreachable 对象。（我确认不需要 30 天托管期）" |
| 🟢 `git maintenance start` | 启用后台定期维护（Git 2.29+） | "帮我开启后台定期维护。" |
| 🔴 `git reflog expire --expire-unreachable=now --all` | 让 reflog 立即过期（配合 `--prune=now` 才真删） | "让 reflog 立即失效，我要真的清干净。（配合 gc --prune=now）" |
| 🟢 `git worktree list` | 列出所有 worktree | "我这台机器上所有 worktree 都在哪？" |
| 🟢 `git worktree list --porcelain` | 脚本友好的输出（含 HEAD/bare/detached 标记） | "把 worktree 列表用脚本友好格式输出。" |
| 🟡 `git worktree add <路径> <已有分支>` | 在指定路径铺开一张工作台，检出已有分支 | "在 ../proj-hotfix 铺一张工作台，检出 hotfix/x 分支。" |
| 🟡 `git worktree add <路径> -b <新分支> <起点>` | 从起点创建新分支并铺开工作台 | "开一张新工作台，基于 origin/main 造个 review/pr-142 分支。" |
| 🟡 `git worktree add --detach <路径> <sha>` | detached HEAD 模式铺开工作台（只读跑一下） | "在那儿铺一张 detached 工作台，我要跑一下这颗历史版本。" |
| 🟡 `git worktree add --lock <路径> <分支>` | 创建时立刻锁定 | "开工作台并立刻锁上，防误清理。" |
| 🟡 `git worktree lock <路径>` | 锁住工作台，防止被 prune/remove 误清 | "锁住 ../longrun 那张工作台。" |
| 🟡 `git worktree lock <路径> --reason "..."` | 加锁并记原因 | "锁住这张工作台，原因写在里面。" |
| 🟡 `git worktree unlock <路径>` | 解锁 | "解锁那张工作台。" |
| 🟡 `git worktree move <旧> <新>` | 移动工作台到新位置（同步更新元数据） | "把这张工作台目录挪到新位置。" |
| 🟡 `git worktree repair` | 元数据和实际路径对不上时修反向指针 | "worktree 元数据和实际路径对不上了，帮我修一下。" |
| 🟡 `git worktree remove <路径>` | 干净地删除工作台（含元数据） | "删掉这张工作台。" |
| 🔴 `git worktree remove --force <路径>` | 有未提交改动时强制删 | "强制删这张工作台，未提交改动我不要了。" |
| 🟢 `git worktree prune --dry-run` | 只看会清理什么，不真动 | "先列出所有孤儿 worktree 元数据，不要清。" |
| 🟡 `git worktree prune` | 清理孤儿元数据（手 rm 过目录后用） | "清掉那些 rm -rf 后留下的僵尸 worktree 元数据。" |
| 🔴 `git filter-repo --path <file> --invert-paths --force` | 从全历史里彻底删除某文件（重写所有 SHA） | "把这个泄漏的文件从全历史里彻底清掉。（先备份，先吊销凭证）" |
| 🔴 `git filter-repo --replace-text <file>` | 从全历史里替换某字符串为 REDACTED | "把历史里所有出现过的这个密钥字符串替换成 REDACTED。" |

> **关于 `git filter-branch`**：这是老式的历史重写工具，官方已在文档中标记为"不推荐使用"，被 `git filter-repo` 取代（更快、更安全、语义更清晰）。本书正文一律用 `filter-repo`，遇到旧文档里的 `filter-branch` 你知道它是这个的祖先即可，不再单独列在表里。

---

## A.8 附：配置与安全（穿插各章）

**什么时候用**：首次配 Git 身份、开启 rerere / 签名 / 分支保护 / safe.directory / hooks 目录等一次性设置。这些命令不直接对应"操作"——它们改的是 `~/.gitconfig` 或 `.git/config` 的文本，一次设定，长期生效。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git config --global user.name "..."` | 在 `~/.gitconfig` 写入署名 | "帮我配全局 git 用户名。" |
| 🟢 `git config --global user.email "..."` | 在 `~/.gitconfig` 写入邮箱 | "帮我配全局 git 邮箱。" |
| 🟢 `git config --global rerere.enabled true` | 开启"记住冲突解法"（重复冲突自动重放） | "开启 rerere，让 Git 记住我上次的解冲突结果。" |
| 🟡 `git config --global gpg.format ssh` | 用 SSH key 做签名（不用 GPG） | "配置用 SSH key 而不是 GPG 签名。" |
| 🟡 `git config --global user.signingkey ~/.ssh/id_ed25519.pub` | 指定签名用的 SSH 公钥 | "签名用这把 SSH key。" |
| 🟡 `git config --global commit.gpgsign true` | 默认每次 commit 都签名 | "让每次 commit 都自动签名。" |
| 🟡 `git commit -S -m "..."` | 显式带签名的 commit（`commit.gpgsign=true` 后可省 `-S`） | "这次 commit 带上签名。" |
| 🟢 `git log --show-signature -10` | 看最近 10 颗的签名状态 | "让我看最近 10 颗 commit 的签名验证结果。" |
| 🟡 `git config --global --add safe.directory <path>` | 把某仓库加入信任白名单 | "把这个仓库加入 safe.directory 白名单（我知情且信任）。" |
| 🟡 `git config --global protocol.file.allow user` | 限制 submodule 通过 file:// 拉本地仓库 | "限制 submodule 只能在用户交互下拉 file://。" |
| 🟡 `git config core.hooksPath .githooks` | 显式声明 hooks 目录（供审计） | "把 hooks 目录显式定到 .githooks，让 CI 可审计。" |
| 🟡 `git config --worktree ...` | 为单个 worktree 配置独立设置（需先启用 `extensions.worktreeConfig`） | "只给当前这张 worktree 配一个独立的 user.email。" |

---

## A.9 附：tag / submodule / subtree / sparse（第 13 章边缘小路）

**什么时候用**：打版本 tag、引用另一个仓库作为子目录、在超大 monorepo 里只 checkout 部分路径。这些不是每天用的，用时再回来查。

### tag

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git tag <name>` | 挂一个轻量 tag（就是一行文本引用） | "在这儿打个轻量 tag。" |
| 🟡 `git tag -a <name> -m "..."` | 附注 tag：有作者、日期、message | "打个正式的附注 tag，我要写 release note。" |
| 🟡 `git tag -a <name> <sha>` | 在指定 sha 上打附注 tag | "给那颗历史 commit 补一个 v1.0 tag。" |
| 🔴 `git tag -d <name>` | 删本地 tag | "本地删掉这个 tag。" |

### submodule / subtree

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟡 `git submodule add <url> <path>` | 引一个外部仓库到子路径（本仓库只记 sha 指针） | "把这个外部仓库作为 submodule 挂到 vendor/xxx。" |
| 🟡 `git submodule update --init --recursive` | 初始化并递归拉所有 submodule | "把所有 submodule 拉齐。" |
| 🟡 `git submodule update --remote` | 更新到子仓库远端最新 | "把 submodule 更新到子仓最新。" |
| 🟡 `git subtree add --prefix=<path> <url> <branch> --squash` | 把外部仓库合并进本仓子路径（历史压扁） | "用 subtree 把这个仓库合到 vendor/xxx，历史压成一颗。" |
| 🟡 `git subtree pull --prefix=<path> <url> <branch> --squash` | 更新 subtree | "拉一下 subtree 的最新。" |

### sparse / partial

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `git clone --filter=blob:none --sparse <url>` | 部分克隆 + 稀疏检出：不下载全部 blob | "在这个 20GB monorepo 上用 sparse+partial 克隆，别把所有 blob 拉下来。" |
| 🟡 `git sparse-checkout init --cone` | 启用 cone 模式的稀疏检出 | "开启 sparse-checkout。" |
| 🟡 `git sparse-checkout set <p1> <p2>` | 只 checkout 指定路径 | "只 checkout services/api 和 shared/。" |
| 🟢 `git sparse-checkout list` | 看当前稀疏检出的路径 | "现在稀疏检出的是哪些路径？" |
| 🟡 `git sparse-checkout disable` | 恢复全量检出 | "关掉 sparse-checkout，我要全量。" |

---

## A.10 附：安全扫描与协作辅助工具（非 git 本体，但书里出现过）

**什么时候用**：需要机密扫描、需要 GitHub 平台特性（PR 管理、分支保护）。**它们不是 git 命令**，但书里多次用到，一并放这里方便查。

| 命令 | 它在做什么（概念语言） | 想用 AI 说人话怎么说 |
|---|---|---|
| 🟢 `gitleaks detect --no-git` | 扫当前工作区的机密（不看历史） | "扫一下工作区有没有泄漏的密钥。" |
| 🟢 `gitleaks detect --source .` | 扫当前 commit 的机密 | "扫这次 commit 有没有敏感信息。" |
| 🟢 `trufflehog git file://.` | 扫全历史的机密（备选工具） | "跑一遍 trufflehog 扫整个历史。" |
| 🟡 `pre-commit install` | 装 pre-commit 框架，登记本地钩子 | "装 pre-commit 框架，我要每次 commit 前自动扫敏感信息。" |
| 🟢 `pre-commit run --all-files` | 全量试跑一遍所有 hook | "先全量跑一遍 pre-commit，看看有没有漏网。" |
| 🟢 `gh pr create --title "..." --body-file pr.md` | 从文件创建 PR（GitHub CLI） | "从 pr.md 创建一个 PR。" |
| 🟢 `gh pr view <num>` | 查看 PR 详情 | "看看 PR #123 的详情。" |
| 🟢 `gh pr diff <num>` | 看 PR 的 diff | "PR #123 的 diff。" |
| 🟡 `gh pr review <num> --approve` | 批准 PR | "批准 PR #123。" |
| 🟡 `gh pr review <num> --comment -b "..."` | 评论 PR | "给 PR #123 加一条评论。" |
| 🟡 `gh pr review <num> --request-changes -b "..."` | 打回 PR | "打回 PR #123，理由如下。" |
| 🟡 `gh pr merge <num> --squash` | squash 合并 PR | "把 PR #123 squash 合并。" |
| 🟡 `gh pr checkout <num>` | 把 PR 分支 checkout 到本地 | "把 PR #123 的分支 checkout 到本地跑一下。" |
| 🟡 `gh repo edit --enable-auto-merge` | 开启仓库自动合并 | "开启这个仓库的自动合并。" |
| 🟢 `gh api repos/:owner/:repo/branches/main/protection` | 查看分支保护配置 | "看一下 main 分支的保护规则怎么配的。" |
| 🟡 `git lfs lock <file>` | Git LFS 加锁：声明"这个大二进制文件我在改" | "把这个 psd 文件加锁，防止别人同时改。" |

---

## 覆盖度自查

本表覆盖第 0 章到第 13 章各章命令侧栏以及正文中出现的所有命令，按概念地图七大分组重排（**非字母序**）：

1. **仓库**（§A.1）—— `init` / `clone` / `ls-remote` / `rev-parse` / `count-objects` / `fsck --strict` —— 对应第 1 章
2. **提交三区**（§A.2）—— `status` / `diff` / `add` / `restore` / `commit` / `--amend` / `show` —— 对应第 2 章、第 6 章
3. **分支与检出**（§A.3）—— `branch` / `switch` / `checkout` / `for-each-ref` —— 对应第 3 章、第 7 章
4. **历史与检查**（§A.4）—— `log` / `show` / `blame` / `shortlog` / `reflog` / `bisect` / `describe` / `fsck --lost-found` / `ls-files -u` / `diff --check` —— 对应第 5 章、第 10 章、第 11 章
5. **远程同步**（§A.5）—— `remote` / `fetch` / `pull` / `push` / `--force-with-lease` / `--prune` —— 对应第 4 章
6. **历史重塑**（§A.6）—— `merge` / `rebase` / `reset` / `revert` / `cherry-pick` / `stash` / `mergetool` —— 对应第 5 章、第 9 章、第 10 章、第 13 章
7. **清理与维护**（§A.7）—— `clean` / `gc` / `maintenance` / `worktree` / `filter-repo` —— 对应第 8 章、第 10 章、第 12 章、第 13 章

附加三个辅助区（§A.8 配置与安全 / §A.9 tag+submodule+subtree+sparse / §A.10 平台工具 gitleaks/gh），把散落在第 9、11、12、13 章的配置类命令和平台工具集中起来。

**如果表里没有你想找的命令**：极大概率是这本书没讲到，也就意味着你日常不需要它。真需要时——`git help <verb>`，或者念第三列给 AI 听。

---

**接下来**：附录 B 是本书 AI 指令箱的全集重排（按场景检索）。命令表和指令箱互为镜像——第一列（命令）是给电脑的话，第三列（自然语言）是给 AI 的话，你在两者之间做的那件事，叫**判断**。
