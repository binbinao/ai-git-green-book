# 附录 B　AI 提示词模板全集

本附录汇总全书正文各章「AI 指令箱」栏目里出现过的所有可复用提示词模板，去重后按**主题**重排（不按章节），方便你按场景直接查找、复制、改写。

## 使用说明

- **工具无关**：所有模板对 Claude Code / Cursor / GitHub Copilot / Aider / Windsurf 等带命令执行能力的 AI 助手通用。
- **颜色标注**（详见第 12 章安全边界；全书统一口径，按"要不要人确认"分级）：
  - 🟢 **绿色**——只读，或只造新对象不动既有引用；AI 可直接放行，无需人确认。
  - 🟡 **黄色**——会动引用 / 工作区 / 远端，但出了事还有安全网兜底；**AI 提出方案 → 你人工确认 → AI 执行**。
  - 🔴 **红色**——不可逆销毁、拆安全网、覆盖共享远端、涉及凭证 / 生产；须**流程级确认**（先备份、先吊销、先打招呼），AI 只能建议，由你亲自动手。
- **模板不是让你背的，是让你改的**。每条里的 `<...>` 是你要替换的字段；把仓库路径、分支名、SHA、时间戳换成你的现场值。
- **黄色和红色指令使用前**：建议先请 AI 建 `backup/*` 分支并展示 `reflog`——两把安全刷牙。

---

## B.1　仓库探索（Repository）

**B.1.1**　🟢 「打开我当前所在的仓库，告诉我这些事：它有多少个提交、多少个分支、多少个 tag、`.git/` 目录整体多大、`.git/objects/` 里有多少个对象。用一张表给我。」

**B.1.2**　🟢 「读 `.git/config` 文件，用中文解释一下里面每一段配置的意义。特别关注 `[remote]` 和 `[branch]` 那几段。」

**B.1.3**　🟢 「让我看一下 `.git/HEAD` 和 `.git/refs/heads/` 下的文件内容——不是 `git branch` 的输出，我要看那几个文本文件里到底写了什么。」

**B.1.4**　🟢 「用 `git rev-parse --is-bare-repository` 和 `git rev-parse --git-dir` 帮我确认：我现在在什么类型的仓库里、`.git` 目录在哪儿。用一句话总结。」

**B.1.5**　🟢 「我想 clone 这个仓库到本地：`<URL>`。clone 之前先告诉我这个仓库的大小估计有多大（用 GitHub API 查）、有哪些主要分支、上一次提交是什么时候。clone 完成后确认 `.git/` 的实际大小和对象总数。」

**B.1.6**　🟢 「在当前目录初始化一个新的 Git 仓库，默认分支设为 `main`。初始化后打印 `.git/` 里的目录结构（一层就行），让我看看什么都还没提交的时候仓库长什么样。」

**B.1.7**　🟢 「帮我做一个浅克隆（`--depth 1`）到 `/tmp/quick-look`，我只是想看看这个开源项目最新版长什么样，不需要历史。看完提醒我用 `rm -rf` 清理掉。」

**B.1.8**　🟡 「我想在 `~/existing-project` 目录初始化 Git，但那里已经有一堆代码了。在你执行 `git init` 之前，先扫描一下有没有明显的敏感文件（`.env`、`id_rsa`、`config.json` 之类），列出来，由我决定要不要先加 `.gitignore` 再 init。」

**B.1.9**　🟡 「clone 这个仓库到 `~/work/`，clone 完成后立刻检查有没有 `.env`、`credentials.json` 之类的敏感文件被 commit 进历史里。如果发现了，先别做任何清理，告诉我在哪几个 commit。」

---

## B.2　提交与信息（Commit / Message）

**B.2.1**　🟢 「我现在改了 5 个文件。看一下每个文件的变化，判断哪些属于'新功能'、哪些属于'顺手修 bug'、哪些属于'重构清理'。分成 2–3 个逻辑上独立的 commit 分别提交，每个给我起一个符合 Conventional Commits 格式的 message。执行前先把分组方案给我确认。」

**B.2.2**　🟢 「从当前暂存区的 diff 生成一条 commit message，遵循这个仓库的历史风格（先扫一下最近 20 条 commit）。生成 3 个候选让我挑，我挑完你再 commit。」

**B.2.3**　🟢 「我要提交一个 WIP 存档，message 里说清楚'这是半成品、还没跑测试'，然后带上当前 TODO 列表。这个 commit 只是我本地档案，不会推。」

**B.2.4**　🟢 「给我看看当前分支最近 10 个 commit——每个的 SHA 前 7 位、第一行 message、作者、时间。表格。」

**B.2.5**　🟢 「显示 SHA `<sha>` 这颗 commit 的完整信息：作者、时间、parent、改动的文件列表、每个文件的 diff。用中文帮我用一句话总结'这次提交做了什么、为什么'。」

**B.2.6**　🟢 「找出仓库历史里所有 message 写得含糊的 commit（比如只写 fix / update / wip）。列前 20 个，按时间排序。」

**B.2.7**　🟢 「看一下我当前 unstaged 的改动。按逻辑功能给我分成 3–5 组，每组一次 commit。给我每组包含的文件和 hunks，以及每组的 commit message 草稿。**先只列出方案，不要执行**。」

**B.2.8**　🟢 「把 `<v1.2.0>..HEAD` 之间的所有提交按类型分组，生成一份面向用户的 release note。`feat` 归 New Features，`fix` 归 Bug Fixes，其余归 Other Changes。`chore/style/refactor` 可以合并成一行。写完给我 markdown。」

**B.2.9**　🟡 「我刚 commit 的这条 message 打错字了。用 `--amend` 帮我改成'`<正确文本>`'。执行前告诉我：这个操作会造一颗新珠子，旧珠子进 reflog；如果这条 commit 已经推过，会有什么后果。」

**B.2.10**　🟡 「把当前分支最新 3 个 commit 撤回到暂存区、保留改动。用 `git reset --soft HEAD~3`。执行前明确：这只挪名牌、不丢改动，reflog 里旧位置还在。」

**B.2.11**　🟡 「我不小心 add 了一个不该 commit 的大文件到暂存区（还没 commit）。帮我把它从暂存区撤下来，工作目录里保留。」

**B.2.12**　🟢（每周考古）「把最近 10 颗提交（`git log -10 --pretty=fuller --stat`）拿去审阅。对每一颗告诉我：（1）主题行是不是 ≤50 字符，type 有没有用对；（2）有没有 body？body 是不是在写'为什么'，不是复述 diff；（3）diff 的规模和 message 说的事情比例合理吗（有没有'塞私货'的痕迹）；（4）如果六个月后有人 blame 到这颗珠子，能不能一眼看懂？给出总分、每颗打分（1–5）和最需要改进的那颗。**不要修改历史**，只做审阅报告。」

---

## B.3　分支（Branch）

**B.3.1**　🟢 「看一下当前仓库的分支全景：本地分支、远程分支、每个分支最后一次提交的时间和 message，以及哪些分支已经完全合并进 main、哪些还有未合并的提交。」

**B.3.2**　🟢 「我和 main 的分叉点在哪？用文字画出从分叉点到现在，我这边每颗提交和 main 那边每颗提交的项链图。」

**B.3.3**　🟢 「解释一下我现在是不是处于 detached HEAD 状态，如果是，是哪个操作导致的，有没有我可能丢掉的提交。」

**B.3.4**　🟢 「我要开始一个新特性，叫 `<user-profile>`。按我们仓库的分支命名惯例给我建分支并切过去。建好之后告诉我当前 HEAD 的状态。」

**B.3.5**　🟢 「在当前位置建一个叫 `rescue/<YYYY-MM-DD>` 的分支，把我现在 detached HEAD 上这几颗提交挂到这张名牌上。」

**B.3.6**　🟡 「把 main 上最新 3 个提交中，属于我的那个（作者是我、message 是 `<xxx>`）搬到新分支 `feature/quick-fix` 上，并把 main 退回它提交之前。先列出你要执行的每一步和每一步的后果，我确认后再动 main。」

**B.3.7**　🟡 「列出所有已经合并进 main 的本地分支。我想清理它们。**先只列表，不要删**。」→ 看完再补一句「确认，删除列表里的这几个，保留 `<xxx>`」。

**B.3.8**　🟡 「我刚才在 main 上直接提交了两个不想进主干的 commit。帮我把它们搬到新分支上并把 main 复原。给出完整命令序列，标注哪一步之后数据就回不去了。」

---

## B.4　远程与同步（Remote / Fetch / Pull / Push）

**B.4.1**　🟢 「看一下当前仓库配置的所有 remote：每个的别名、URL、fetch/push URL 是否分开。用表格给我。」

**B.4.2**　🟢 「跟远端对齐一下认知：先 `git fetch --all`，然后告诉我我本地每一个分支和它对应的远程分支之间的关系——各自领先/落后多少个 commit，有没有分叉。」

**B.4.3**　🟢 「读 `.git/config`，用中文向我解释 `[remote "origin"]` 和 `[branch "main"]` 这两段配置。特别指明：如果我 `git pull` 什么都不加，Git 会去哪儿、拉什么、怎么合。」

**B.4.4**　🟢 「让我看看 `.git/refs/remotes/origin/` 下有哪些文件、每个文件里写的 SHA。**不是** `git branch -r` 的输出，我要看那几个物理文件。」

**B.4.5**　🟢 「fetch 所有远程的所有分支。fetch 完成后告诉我：这次 fetch 更新了哪些远程分支的位置（哪些前移了、前移了几格）、有没有新出现的远程分支、有没有本地缓存有但远端已经删除的分支。」

**B.4.6**　🟢 「我要跟上 origin 上 main 的最新进展。步骤：（1）fetch origin；（2）展示远端 main 和我本地 main 的差异（各自领先多少、有没有冲突风险）；（3）停下来等我决定用 rebase 还是 merge。」

**B.4.7**　🟡 「把我本地的 main 追上 origin/main 的最新。用 rebase，不要用 merge——我不想要那颗 merge commit。执行前告诉我：如果 rebase 中间遇到冲突，你会停下来让我处理，对吗？」

**B.4.8**　🟡 「我要把当前分支第一次 push 到 origin，同时建立 upstream 追踪。用 `-u`。执行前告诉我远端 origin 上现在有没有同名分支——如果有，别 push，先问我。」

**B.4.9**　🟡 「我 push 被拒了（non-fast-forward）。先 fetch，告诉我远端上出现了哪些我不知道的 commit（作者、message）。看完我再决定：rebase 我的改动上去，还是这些远端 commit 我要丢弃。**不要在我确认之前 force**。」

**B.4.10**　🟡（Fork 同步）「这是一个 fork 项目，我 clone 的是我自己 fork 的那份（origin）。帮我加一个 remote 叫 `upstream`，指向原始项目 `<URL>`。加完 fetch 一下 upstream。」

**B.4.11**　🟡（Fork 同步）「同步 `upstream/main` 到我本地 main，并推到我的 fork（origin）。策略：直接让本地 main 完全等于 `upstream/main`（因为我从不在 main 上开发）。用 `reset --hard` + `push --force-with-lease`。执行前列出会做的每一步。」

---

## B.5　历史重写（Rebase / Reset / Amend / Revert）

**B.5.1**　🟢 「用 `git log --graph --oneline --all -30` 展示当前仓库的历史全景。给我指出：主干在哪、有几条正在活跃的分支、有没有合并 commit、有没有明显的分岔。用中文描述这张图。」

**B.5.2**　🟢 「读 `git reflog` 的最近 50 条记录，用中文告诉我：过去这段时间在这个仓库里我做过哪些'改历史'的操作（rebase / reset / amend / branch delete）——按时间倒序列出，标出每一条的类型、影响的分支、before/after SHA。」

**B.5.3**　🟢 「当前 HEAD 之前 5 个 commit 里，有没有 message 显示为 fixup / wip / typo、或者内容很小的补丁？如果有，列出来。这些通常是可以 squash 到前一个'正片' commit 里的候选。」

**B.5.4**　🟡 「我要整理当前分支从 main 分叉点到 HEAD 的所有 commit。先执行 `git branch backup/before-rebase-$(date +%Y%m%d-%H%M%S)`，然后展示所有待整理的 commit（SHA、message、改动文件数）。之后**停下来让我决定 pick/squash/fixup/drop 的方案**，不要自动 rebase。」

**B.5.5**　🟡 「按我给你的这份剧本执行 `rebase -i`（剧本：把第 4、5、6 个 commit fixup 进第 3 个；把第 8 个 drop 掉）。执行完展示 log 前后对比，并明确告诉我：如果中途冲突，你会停下来让我处理，不会自作主张选一边。」

**B.5.6**　🟡 「我要撤销最近 3 个 commit，但改动都要保留下来（因为我要重新组织提交）。用 `git reset --soft HEAD~3`。执行前告诉我：这个操作会挪 main 名牌、旧 3 个 commit 进 reflog；不会碰工作目录和暂存区里那 3 个 commit 的内容。」

**B.5.7**　🟡 「我要完全丢弃当前分支最近 2 个 commit（改动也不要了）。用 `git reset --hard HEAD~2`。执行前必须先：（1）检查我工作目录是不是干净的，如果不干净停下来提醒我先 stash；（2）建 backup 分支；（3）展示旧 HEAD 的 SHA 以备我需要恢复。」

**B.5.8**　🟡 「main 分支上第 3 个 commit（SHA `<a1b2c3d>`）是错的、已经推到远端了。**不能 reset，因为是共享分支**。用 `git revert <a1b2c3d>` 造一颗抵消珠子；执行前展示 revert 会产生的 diff，让我确认反向改动符合预期。」

**B.5.9**　🟡 「我 rebase 完 push 被拒了（non-fast-forward）。执行前先确认：（1）这条分支是不是纯粹我个人的？让 AI 检查最近 30 天有没有别的作者往上面 push 过；（2）如果确认是个人分支，用 `git push --force-with-lease`；如果不确定，停下来问我。**任何情况下都不要用裸的 `git push --force`**。」

**B.5.10**　🟡（团队协作前置）「我要在 `feature/checkout-v2` 上 rebase 一下 main 来整理历史。**执行前必须先做的三件事**：（1）`git fetch --all` 确认最新；（2）用 `git log feature/checkout-v2 --format='%an' | sort -u` 列出这条分支上所有贡献者，如果有其他人，**停下来让我发群通知**；（3）`git branch backup/before-rebase-$(date +%Y%m%d-%H%M%S)` 建备份分支。三件事都做完再动 rebase，rebase 完用 `--force-with-lease` 推。」

---

## B.6　冲突处理（Conflicts）

**B.6.1**　🟢 「我现在在冲突状态。用 `git status` 列出所有还未解决的冲突文件，按'两边都改' / '一边加一边删' / '二进制' / 'lockfile' 分类。**这一步不要改任何文件**。」

**B.6.2**　🟢 「读文件 `<path>` 里的每一段 `<<<<<<<  =======  >>>>>>>`。对每一段告诉我：（1）HEAD 那一侧的改动想干什么，一句话；（2）theirs 那一侧的改动想干什么，一句话；（3）这两侧的意图是相同的、正交的、还是互斥的。**不要改任何文件**——只输出分析。」

**B.6.3**　🟢 「读这次 merge 涉及的两侧最近 10 个 commit 的 message，告诉我：HEAD 分支这段时间在做什么主题的工作，theirs 分支在做什么主题的工作。冲突集中在哪些主题的交界处。」

**B.6.4**　🟢 「用 `git log --merge --oneline` 列出这次冲突涉及的两侧独有 commit，帮我判断：（1）这次合并跨了多久（两侧分叉多久了）；（2）冲突主要来自哪一侧的哪几个 commit。」

**B.6.5**　🟡 「针对 `<path>` 里那段 `<fn>` 的冲突：我判断这是伪冲突（HEAD 加参数、theirs 改类型，两个都要）。**先给我一份合成后的代码文本、不要动文件**——我读过之后你再帮我写进去。」

**B.6.6**　🟡（lockfile 处理）「针对整个文件级别的冲突，帮我操作：（1）`git checkout --theirs package-lock.json`；（2）`rm -rf node_modules`；（3）`npm install`；（4）`git add package-lock.json`。执行前先把这四步列给我确认。」

**B.6.7**　🟡 「这个二进制文件 `<path>` 有冲突。给我三个选项：（a）保留我这一侧（`git checkout --ours`）；（b）保留对面（`--theirs`）；（c）打开图片对比工具让我手工看。我选完你再动手，不要默认选任何一个。」

**B.6.8**　🟡（冲突解决后自检）「我刚解决完所有冲突，还没 commit。执行前的自查：（1）用 `git diff --check` 检查有没有漏删的 `<<<<<<<` 或 `>>>>>>>` 标记；（2）用 `git status` 列出所有 add 完的和未 add 的；（3）用 `git diff --ours` 展示我最终版本相对我这一侧的改动、`--theirs` 展示相对对面的改动——**让我看看有没有一整段冲突我实际上只是接受了一侧（这可能是我漏做了合成）**。」

**B.6.9**　🟡（冲突后测试）「冲突解决完了。跑一遍完整测试（不只是我改过的文件）：（1）编译/类型检查；（2）单元测试；（3）集成测试；（4）如果有 lint，也跑一下。**有任何失败停下来告诉我，不要'自动修复'**。」

**B.6.10**　🟡（语义冲突扫描）「合完之后扫一遍这个 diff，找语义冲突的迹象：（1）有没有函数签名变了、但调用点没跟着改；（2）有没有引用了不存在的字段/函数/import；（3）有没有类型看起来不匹配的地方。**只列可疑处，不改代码**。」

**B.6.11**　🔴（明确禁止）「任何情况下**不要'自动接受一侧'**（不要因为一侧看起来是主流、更新、或和别处一致就默默选它）——**永远先让我读两侧的意图**。rebase / merge 冲突处理过程中**不要修改冲突以外的 commit**。冲突解决后 push 被拒时**不要**执行 `git push --force`。」

---

## B.7　事故恢复（Recovery）

**B.7.1**　🟢（事故现场诊断）「跑 `git status`、`git log --oneline --all -20`、`git reflog --date=iso -30`、`git branch -av`。用中文向我总结：（1）我现在站在哪；（2）过去 30 分钟做过哪些改历史操作；（3）我当前工作区有没有未提交改动。**不要执行任何有副作用的命令**。」

**B.7.2**　🟢 「读 `git reflog --date=iso -50`，按时间倒序告诉我：过去这段时间在这个仓库里 HEAD 发生过哪些位置变化。特别标出 commit / checkout / reset / rebase / merge / branch delete 这几类的每一条，每条给出 before/after SHA、时间、动作类型。」

**B.7.3**　🟢（悬空对象扫描）「用 `git fsck --lost-found` 列出所有 unreachable 的对象（dangling commits / blobs / trees）。**只读、不改任何东西**。每个 dangling commit 用 `git show <sha> --stat` 简要展示 message + 改动文件。让我认领。」

**B.7.4**　🟡（误删分支）「我刚才 `git branch -D <name>` 误删了分支。（1）先从终端历史或 `git reflog --all` 找到该分支被删前指向的 SHA；（2）`git show <sha>` 展示那颗 commit 让我核对；（3）核对通过后 `git branch <name> <sha>` 把分支挂回去。**每一步都停下来等我确认**。」

**B.7.5**　🟡（reset --hard 之后）「我刚 `git reset --hard` 之后发现丢东西了。（1）用 `git reflog -20` 找到 reset 之前的 HEAD 位置；（2）展示那颗 commit 的 message + 改动文件让我确认；（3）确认后 `git reset --hard <SHA>` 恢复。如果我丢的是**从没 add 过的工作区改动**，诚实告诉我：**这类改动 Git 恢复不了**，建议我去看编辑器的 Local History 或系统级快照。」

**B.7.6**　🟡（找回 add 过但没 commit 的文件）「我刚 `git reset --hard` 之后想找回一个我 add 过但没 commit 的文件 `<path>`。用 `git fsck --lost-found` 列出所有 dangling blobs；每个 blob 用 `git show <blob-sha> | head -20` 展示前 20 行让我认领。找到之后用 `git show <blob-sha> > <path>` 还原成文件。」

**B.7.7**　🟡（rebase 搞砸）「我 rebase 完发现丢了 commit / 走岔了。**如果 rebase 还在进行中**（`.git/rebase-*` 目录存在），直接 `git rebase --abort` 一键回滚。**如果已经 `Successfully rebased` 结束**，用 `git reset --hard ORIG_HEAD` 把当前分支整个挪回 rebase 之前——**这一步等我确认 ORIG_HEAD 就是 rebase 之前的位置再执行**。」

**B.7.8**　🟡（rebase 丢了一颗）「我 rebase 完丢了某一颗 commit（内容大致是 `<描述>`），但其他都要保留。用 reflog 找到那颗被丢的 SHA，`git show` 展示让我确认，然后 `git cherry-pick <sha>` 补到当前 HEAD。**cherry-pick 冲突时停下来让我处理，不要自作主张**。」

**B.7.9**　🟡（force push 灾难）「我 rebase 后 `git push --force-with-lease` 到了共享分支 `<branch>`，然后发现该分支上有同事的 commit 被我挤掉了。（1）**先让我在群里通知所有协作者停止 pull**；（2）从任何一位协作者的本地找出他们 clone 里 `<branch>` 指向的 SHA（那是事故前的黄金 SHA）；（3）让那位协作者用 `git push --force-with-lease` 把远端恢复。**由'clone 最干净的人'执行恢复推送，不是我**。」

**B.7.10**　🟡（已推送错误 merge 的 revert）「main 上误合了 PR `#<num>`（merge commit SHA `<sha>`），需要撤销。**因为是共享分支，用 revert 不用 reset**。（1）展示 `git show <sha>` 让我核对；（2）执行 `git revert -m 1 <sha>`（`-m 1` 指定主线 parent）；（3）展示 revert 产生的 diff 让我确认；（4）`git push`（**普通 push，不是 force push**）。」

**B.7.11**　🟡（在 main 误提交多颗的补救）「我不小心在 main 上直接 commit + push 了 4 颗（应该开分支的）。恢复流程：（1）从 main 当前 HEAD 建分支 `feature/misplaced-commits` 保住代码；（2）在 main 上用 `git revert --no-commit <old>..<new>` 一次性 revert；（3）commit + 普通 push；（4）feature 分支上再 rebase 到干净 main 之后走正常 PR。**每一步展示要跑的命令让我确认**。」

**B.7.12**　🟢（detached HEAD 救援）「我在 detached HEAD 上 commit 过一颗（message 大致是 `<描述>`）然后切走了。用 `git reflog -20` 找到那颗 commit 的 SHA（reflog 里类型是 `commit:` 的行），`git show` 展示让我确认，然后 `git branch rescue/<描述> <sha>` 把它挂上名牌。」

**B.7.13**　🔴（凭证泄漏第一优先级）「我误 commit + push 了 `.env`（含 API key / 私钥 / 密码）。**执行任何 git 操作之前，先做完这三件事**：（1）**立刻登录服务商后台吊销这个凭证**；（2）**生成新凭证并更新到正确的位置**（不再进 git）；（3）**审计服务商日志看有没有在我吊销前被人使用**。做完这三步后再回来告诉我，我再帮你做 git 层的历史清理。**清理只是辅助——泄漏一旦发生，唯一有效的止损是让 key 失效**。」

**B.7.14**　🔴（凭证吊销后的历史清理）「（已吊销 API key 后）帮我用 `git filter-repo --path <文件路径> --invert-paths --force` 从整个历史里删除这个文件。**执行前再次确认**：（1）已吊销凭证；（2）已通知所有协作者接下来他们需要重新 clone；（3）已备份当前远端（`git clone --mirror` 到本地一份）。执行完之后 `git push --force`（**这是极少数必须裸 force 的场景**）。」

---

## B.8　分支策略与团队规范（Branching Strategy）

**B.8.1**　🟢 「读一下我们仓库的最近 3 个月历史（`git log`）：本地和远程分支各有多少条、平均寿命多长、有没有长期没动的'僵尸分支'、合并方式是 merge/squash/rebase 里的哪种为主。给我一份现状报告。」

**B.8.2**　🟢 「基于这份仓库的历史（分支数量、平均寿命、合并频率、发布 tag 节奏），推断我们目前实际在跑的分支策略最像哪一种？找出跟三种主流策略不吻合的地方。」

**B.8.3**　🟢 「我们团队每天产出多少次 push、平均一个 PR 从开出到合并花多久、CI 平均跑多久？基于这几个数字，判断我们的'工程成熟度'接近 L1/L2/L3 哪一档。」

**B.8.4**　🟢 「我给你我们团队的情况：`<人数>`、`<发布节奏>`、`<产品形态>`、`<有没有 feature flag>`、`<有没有 CI/CD>`、`<有没有多版本客户>`。基于第 7 章的四问决策树，推荐一个分支策略并解释为什么。」

**B.8.5**　🟢 「假设我们现在用的是 GitFlow，想迁移到 GitHub Flow。给我一个渐进式迁移方案：先做什么、后做什么、每一步的风险和回滚点。」

**B.8.6**　🟢 「我们团队想上 Trunk-Based，但没有 feature flag 平台。给我一份'前置能力清单'——哪些能力必须先建好、哪些可以之后补、大概需要多久投入。」

**B.8.7**　🟢 「基于我给你的分支策略选择（`<GitHub Flow>`），生成一份团队约定文档：分支命名规则、生命周期上限、main 保护规则、PR 模板、例外流程。用 Markdown 输出，可以直接放到 `CONTRIBUTING.md`。」

**B.8.8**　🟢 「给我一份 GitHub 仓库的 branch protection 配置 checklist，我照着在 Settings 里勾选。逐条解释每一条能防止什么。」

**B.8.9**　🟢 「生成一份 PR 描述模板，包含'改了什么/为什么改/怎么测试/风险与回滚/是否 AI 生成'五段。放到 `.github/pull_request_template.md`。」

**B.8.10**　🟡（下线 develop 分支）「我们要把 develop 分支下线（迁到 GitHub Flow）。给我一个完整迁移剧本：怎么把 develop 上未合并的 PR 转到 main、怎么调整 CI 配置、怎么通知团队、每一步的回滚方式。**执行前给我看完整计划，我批准后再动**。」

---

## B.9　Worktree（多工作台）

**B.9.1**　🟢 「用一段 300 字的自然语言解释：`git worktree add` 和 `git switch` 的本质区别是什么？分别在什么场景下选哪个？用第 8 章'工作台 vs 换名牌'的比喻。」

**B.9.2**　🟢 「列出我这个仓库里当前所有的 worktree（`git worktree list`），并对每一张说明：它站在哪个分支、有没有未提交改动、上次动过是什么时候、是不是可以清理。」

**B.9.3**　🟢 「读一下 `.git/worktrees/` 目录里的所有元数据。告诉我每张工作台的 gitdir 反向指针指向哪里，有没有孤儿元数据（对应目录已消失）。」

**B.9.4**　🟢 「我要为一个 hotfix 开一张 worktree，路径放在 `~/projects/proj-hotfix`，基于最新的 `origin/main` 切一个新分支 `hotfix/<YYYY-MM-DD>-<简短描述>`。给我完整命令序列，先解释再执行。」

**B.9.5**　🟢 「我要跑一下 PR `#<num>` 看看效果，帮我：（1）抓下这个 PR 对应的分支；（2）在 `~/projects/proj-review-<num>` 开一张 worktree 检出到它；（3）提示我看完后怎么完整清理。」

**B.9.6**　🟢（多 agent worktree）「帮我起 3 张 agent 专用 worktree，路径分别是 `~/projects/myapp-agent-{1,2,3}`，每张各自基于 main 开一个新分支 `agent/task-<日期>-<序号>`。用一个 shell 脚本一次搞定，并在最后 `git worktree list` 展示结果。」

**B.9.7**　🟡（清理）「列出我这台机器上所有仓库里的 worktree（可能有孤儿）。给我一份 checklist：哪些是可以清理的、哪些还在活跃使用中。**只列表，不执行任何清理**。」→ 看完再补一句「把标为可清理的那些用 `git worktree remove` 逐个清理，遇到 locked 的先给我看再决定」。

**B.9.8**　🟡（沙盘 rebase）「我想在 worktree A 上做一次大 rebase 实验，risk 比较高。开一张新的 worktree（不是在 A 上直接做），把它当作沙盘。给我完整方案：新 worktree 怎么开、rebase 怎么跑、成功了怎么合回、失败了怎么整支扔掉。」

**B.9.9**　🟡（放弃 agent 产出）「AI agent B 已经在 `~/projects/myapp-agent-b` 上跑了一个大重构，现在想放弃它的所有产出。给我一个**安全清理**的步骤：先确认它是不是在跑（有没有活的进程占用文件）、确认它有没有 push 出去、然后干净清理这张工作台和它创建的分支。」

---

## B.10　PR 起草与代码考古（Collaboration）

**B.10.1**　🟢（PR 六节结构初稿）「基于当前分支相对于 `origin/main` 的差异（`git log origin/main..HEAD`、`git diff origin/main..HEAD --stat`），起草一份 PR 描述。六节结构：（1）**背景/动机**——关联 Issue、要解决的问题（**标 [TODO：作者补充]，你不要编**）；（2）**改了什么**——按模块列表；（3）**为什么这样改**——技术方案取舍，看不出来就标 [TODO]；（4）**测试**——列出改动的测试文件，没加测试就明说'未加测试'，别粉饰；（5）**风险与回滚**——影响哪些下游、如何回滚；（6）**审查重点**——希望评审员重点看的文件和行。**任何你不确定的地方标 [TODO：作者补充]，不要编造 why**。」

**B.10.2**　🟢（PR 描述审读）「读这份 PR 描述初稿。指出：（a）有没有和 diff 不匹配的'编造出来的意图'；（b）有没有 diff 里改了但描述里没提的'顺手'改动；（c）有没有明显应该说明但没说的（比如没提 breaking change、没提 migration 步骤）。**只指出问题，不要替我改**。」

**B.10.3**　🟢（意图-证据比对）「这份 PR 的作者声称做了 X。基于 diff 判断：作者做的实际上是不是 X？如果不是，实际做的是什么？（做'意图-证据比对'这一件事就够，其它别写。）」

**B.10.4**　🟢（下游影响分析）「这份 PR 改了 `<apiClient>` 的返回类型。全仓库搜索 `<apiClient>` 的所有调用点，列出：（a）改动后仍然工作的；（b）改动后会 break 的；（c）不确定的。给我一个表格。」

**B.10.5**　🟢（一行代码考古）「这个文件的第 `<N>` 行看起来很奇怪：`<code snippet>`。用 blame + log 挖一下：（a）这行最早是哪次 commit 加进来的？（b）当时的 commit message 和 PR 描述说了什么？（c）里面某个字段在仓库其它地方是怎么用的？（d）用一段话总结'这行代码为什么长成这样'。」

**B.10.6**　🟢（文件变更史）「查一下 `<path>` 近 6 个月的完整变更历史：每次 commit 的作者、日期、message 第一行，以及那次动了多少行。用时间轴表格给我。」

**B.10.7**　🟢（贡献分布 / 巴士因子）「查一下本仓库最近 3 个月的贡献分布：（a）每个作者的提交数（`shortlog -sn`）；（b）每个作者主要贡献的模块；（c）**巴士因子分析**：有没有哪个目录只有一个人贡献过？如果那个人明天不在，谁最有可能接手？」

**B.10.8**　🟢（沉睡代码）「找出本仓库里 6 个月没被任何人改过、但依然在被引用的'沉睡代码'——列出 top 20 个这样的函数/模块。用 `log --before='6 months ago' --name-only` 加过滤逻辑。」

**B.10.9**　🟡（评审意见落地）「基于 review 意见，把当前分支上散落的 15 个 commit 整理成 4 个原子 commit。方法：交互式 rebase（`rebase -i main`），你先给我一份**完整的 rebase todo 脚本**（每颗 commit 选 pick/squash/fixup/reword），我确认后你再执行。中途遇到冲突，停下来展示两侧内容让我判断，不要自作主张。」

---

## B.11　高级操作（Stash / Cherry-pick / Bisect / Tag / Submodule / Sparse / GC / Detached HEAD）

**B.11.1**　🟢（stash 列表）「列一下当前仓库的 stash 全部：每一个 stash 的编号、message、创建时间、影响的文件数、以及基于哪个分支哪颗 commit。用中文表格给我。」

**B.11.2**　🟢（stash 预览）「展示 `stash@{0}` 里的具体改动 diff。之后告诉我：这些改动如果 apply 到当前分支，大概会不会冲突（对比一下当前 HEAD 里对应文件的状态）。」

**B.11.3**　🟡（stash apply）「把 `stash@{0}` 用 `apply` 应用到当前工作目录——**不要 pop**。执行前告诉我：如果冲突了你会停下来、不会自作主张 drop 掉这个 stash。」

**B.11.4**　🟡（stash pop 冲突诊断）「我刚才 `git stash pop` 了，遇到冲突。告诉我：（1）这个 stash 现在有没有从 list 里消失（应该没有）？用 `git stash list` 确认；（2）冲突具体是哪几个文件的哪几行；（3）解决完之后要不要手动 `git stash drop`，什么时候 drop 才安全。」

**B.11.5**　🟡（清理僵尸 stash）「列出所有 stash，标出创建时间。超过 30 天的算'僵尸抽屉'——挨个展示它们的 diff summary，让我逐个决定是 drop 还是恢复成一个分支保存。**不要批量 drop**。」

**B.11.6**　🟢（cherry-pick 预览）「同事的 `feature/<xxx>` 分支上有 5 个 commit，帮我列出来（SHA、message、影响文件）。我告诉你想摘哪几颗，你先展示这几颗合到当前分支上的 diff preview，让我确认。」

**B.11.7**　🟡（cherry-pick 执行）「把 `<SHA>` 这颗 commit cherry-pick 到当前分支。执行前展示这颗 commit 的完整改动、以及应用到当前 HEAD 上会不会冲突。如果冲突，停下来让我处理，**不要用 `-X ours` / `-X theirs` 自动选边**。」

**B.11.8**　🟡（backport）「把 main 上最近的这颗 bugfix `<SHA>` backport 到 `release/v2.3` 分支。步骤：（1）切到 `release/v2.3`；（2）先建 backup 分支；（3）cherry-pick 那颗；（4）检查冲突；（5）冲突有就停下来。**不要一口气 push 到远端**。」

**B.11.9**　🟢（bisect 自动化）「用 `git bisect` 找出第一次让 `<tests/test_login.py::test_login_flow>` 失败的 commit。已知 HEAD 是坏的、tag `<v2.3.0>` 是好的。用 `git bisect run pytest <...>` 自动化。跑完把结果那颗 commit 的 diff 和 message 展示给我，并给出你对根因的判断。」

**B.11.10**　🟢（bisect 手动）「我知道现在的 main 有个 UI bug（按钮点击没反应），但我没有自动化测试可以判断。帮我准备一个 bisect 剧本：每一轮 checkout 后你告诉我 checkout 到了哪颗、这颗的 message，我手动测试并告诉你 good/bad，你继续下一轮。跑完给出第一颗坏的珠子。」

**B.11.11**　🟡（bisect 收尾）「bisect 结束了。现在：（1）跑 `git bisect reset` 回到原位置；（2）展示那颗被定位的 commit 的完整 diff；（3）判断问题最可能出在哪几行；（4）建议下一步（revert / 修一下 / cherry-pick 到 hotfix 分支）。」

**B.11.12**　🟢（tag 概览）「列出仓库里所有的 tag：区分轻量和附注、按时间排序、每一个显示 tagger（如果有）、message（如果有）、指向的 commit message。」

**B.11.13**　🟢（下一版本推断）「当前 HEAD 距离最近的 tag 有多少颗 commit？（`git describe` 的语义）。如果我现在打 tag，按语义化版本推断，下一个版本号应该是什么？」

**B.11.14**　🟢（打附注 tag）「用附注 tag 给当前 HEAD 打上 `<v1.2.0>`。tagger 用我 config 里的信息，message 用最近 15 个 commit 生成的简明 changelog（按 feat / fix / chore 分组）。打完展示 `git show <v1.2.0>`。**停下来问我要不要 `git push origin <v1.2.0>`**——别自动 push。」

**B.11.15**　🟡（清理本地 tag）「本地有一些废弃的实验 tag（`wip-*`、`temp-*`）。列出来让我确认要不要删。批量删除本地 tag：`git tag -d`。**不动远端 tag**——远端 tag 是团队约定，不由我单方面清理。」

**B.11.16**　🟢（子仓库探测）「这个仓库有没有用 submodule 或 subtree？如果有，列出：每一个的路径、指向的远程仓库、当前 pin 在哪颗 commit、是不是最新。」

**B.11.17**　🟡（submodule 更新）「更新 `<libs/vendor-sdk>` 这个 submodule 到远端最新 main。步骤：（1）fetch 子仓库；（2）在子仓库里 checkout main；（3）回到主仓库；（4）`git add <path>` 把新指针提交进主仓库；（5）展示主仓库 diff 让我确认再 commit。」

**B.11.18**　🟢（submodule init）「我 clone 完发现 `<libs/vendor-sdk>` 是空的。用 `git submodule update --init --recursive` 初始化。完成后展示 `<path>` 里的 `git log -1` 确认版本正确。」

**B.11.19**　🟢（sparse-checkout 首次）「这个仓库有 `<8 GB>`，我只关心 `<services/user-api/>` 和 `<shared/>`。帮我从头重新 clone 一份，用 partial clone（`blob:none`）+ sparse-checkout 只展开这两个目录。给出完整命令序列并解释每一步在做什么。」

**B.11.20**　🟢（切换为 sparse）「当前 clone 是全量的。转换成 sparse-checkout 模式，只保留 `<...>` 可见。执行前告诉我：这个操作会不会丢数据（应该不会——只影响工作目录展开范围）。」

**B.11.21**　🟢（gc 诊断）「这个仓库的 `.git/` 目录多大？松散对象有多少？packfile 几个？跑一下 `git count-objects -vH`，告诉我需不需要手动 gc。给出判断依据。」

**B.11.22**　🟢（常规 gc）「跑一次常规 `git gc`（不加 `--aggressive`、不加 `--prune=now`），把松散对象打包。跑完展示前后对比：`.git/` 大小、objects 目录里文件数变化。」

**B.11.23**　🟢（后台维护）「配置 `git maintenance` 定期后台维护。告诉我它会做什么、跑的频率、如何关闭。」

**B.11.24**　🔴（深度清理）「仓库里我不小心提交过一次 20 MB 的日志文件，后来 rebase 掉了，但 objects 还在。目标：让那个 blob 从磁盘上真删除。步骤：（1）确认 reflog 里没有还引用它的位置；（2）`git reflog expire --expire-unreachable=now --all`；（3）`git gc --prune=now`；（4）展示前后 `.git/` 大小。**执行前先备份整个仓库目录到 `/tmp`**。」

**B.11.25**　🟢（detached HEAD 探测）「我现在是不是 detached HEAD 状态？如果是，是通过什么操作进入的（`.git/HEAD` 内容、reflog 最后几条）？我从进入到现在有没有做过 commit（如果有，列出 SHA 和 message）？」

**B.11.26**　🟡（detached 上挂名牌保留）「我在 detached HEAD 上做了一些改动想保留。用 `git switch -c rescue/<YYYY-MM-DD>` 在当前位置挂一张分支名牌保存下来。执行前展示当前 HEAD 的 SHA 和最近几颗 commit，让我确认这就是想保留的状态。」

**B.11.27**　🟡（detached 切回 main）「我在 detached HEAD 上看完了历史版本，什么都没提交。用 `git switch main` 回到 main 分支。执行前确认工作目录是干净的——如果不是，停下来提醒我。」

---

## B.12　陪练模式（Training / Quiz / Simulation）

面向"练"的模板：让 AI 出题、扮演、批改，把知识变成反射。

**B.12.1**　「假装我是一个只用过 GitHub 网页界面、从没在命令行用过 Git 的人。给我出 8 个判断题：'仓库到底在哪里'、'远程和本地的关系'、'clone 到底做了什么'、'删除 GitHub 上的仓库我的代码还在不在'等等。每题四选项，我答完你批改并讲评错的那道。」

**B.12.2**　「用'档案馆'的比喻，向一个刚从 SVN 迁移过来的开发者解释：为什么 Git 可以脱网干活。用 200 字以内，别提命令，只讲仓库结构。」

**B.12.3**　「假装我是一个只用过'改文件→保存→交给团队'的开发者，从没接触过暂存区概念。给我出 6 道题：'为什么改了文件 commit 上去还是老版本'、'add 和 commit 的区别'、'为什么 `git commit -a` 有时候不管用'等等。一次问一个，根据我的回答决定下一题。」

**B.12.4**　「用'档案馆入库单'的比喻，向一个纠结'为什么 Git 要多一个暂存区'的新手解释：三区模型的价值是什么。300 字以内。」

**B.12.5**　「给我 5 个真实的 diff 片段（你随便造，涵盖新功能、bugfix、重构、文档、依赖升级）。让我练习给每个写 commit message，我写完你按 Conventional Commits 标准打分并给建议。」

**B.12.6**　「给我 10 道'这是不是该开分支'的判断题，场景覆盖修 bug、重构实验、改文档、半成品切换、紧急 hotfix。我答完你批改并讲评。」

**B.12.7**　「假装我从没搞清楚 `origin/main` 和 `main` 的区别。问我 5 个诊断题：'当我在本地 commit 之后 `origin/main` 有没有变'、'fetch 之后我的 main 分支会不会前移'、'`status` 说 up to date 是相对什么在说'、'`pull` 里那个我没造过的 merge commit 是谁造的'、'push 被拒是 Git 在保护什么'——一次一个，看我答得对不对，讲评。」

**B.12.8**　「给我 8 道'我该 fetch 还是 pull 还是 push 还是 force push'的场景判断题。场景包括：'我刚 commit 完想同步'、'我刚被 push 拒了'、'我要发 PR 前跟上主干'、'我误推了要撤回'等等。」

**B.12.9**　「给我 8 道场景判断题：给一个具体情境（'我 amend 完一个已推送的 commit'、'我在 feature 分支上 rebase 完 push 被拒'、'我要撤销 main 上一颗已 push 的错误 commit'、'我 reset --hard 之后想找回改动'……），我要说出正确的操作、以及一个常见但错误的操作。你批改并讲评。」

**B.12.10**　「用'珠子不可变、项链可塑'这条原理，向一个刚学 Git 的新人解释：为什么 `git commit --amend` 不是真的'改' commit、为什么 rebase 完 SHA 都变了、为什么 reflog 里能找回我以为丢掉的 commit。300 字以内。」

**B.12.11**　「让我练一次交互式 rebase：你随便造一段 10 个 commit 的 fake 历史（其中 4 个是 wip / typo 的琐碎修补），把这段历史贴给我；我用文字回复我的整理方案（pick/squash/fixup/reorder/drop），你判断我方案的对错、给出理由。」

**B.12.12**　「给我 5 段虚构的 `<<<<<<<  =======  >>>>>>>` 冲突片段，覆盖：真冲突、伪冲突、过时冲突、设计信号、和一段实际上没有真冲突（应该合成）。我读完告诉你我判断是哪一类、要怎么处理，你批改。」

**B.12.13**　「造一个跨文件语义冲突的场景：一个分支改函数签名、另一个分支写新调用点。用两段 diff 告诉我'合并算法看到的是干净的自动合并'，然后让我说出这里为什么危险、我该做什么检查。」

**B.12.14**　「给我 10 道场景判断题：给一个具体事故描述（'我 `branch -D` 之后想起分支上还有东西'、'我 `reset --hard` 之后丢了工作区改动'、'我误 push 了 `.env`'、'我 rebase 完 push 被拒'、'我在 detached HEAD 上 commit 后切走'……）。我要说出：（1）优先级——先做什么；（2）恢复策略——用哪个命令；（3）预防措施——下次怎么避免。你批改并讲评。」

**B.12.15**　「模拟一次 secret 泄漏事件——你扮演 Slack 里的团队 lead / SRE on-call，我作为工程师在凌晨报告刚刚 push 了 AWS key / `.env` 到 public repo。**按事故响应流程和我对话**：先问我什么？什么时候让我做 git 层清理？什么时候让我暂缓？训练我把'吊销凭证'作为第一反应而不是'filter-repo'。扮演结束后给我一份'下次怎么让这个事故不发生'的三道闸检查清单。」

**B.12.16**　「模拟一个团队场景（自己编）：告诉我团队规模、产品形态、发布节奏、工程能力。我根据这些信息推荐一个分支策略。你评价我的推荐并指出遗漏考虑的因素。来 5 轮。」

**B.12.17**　「给我 10 道'这是不是伪需求'的判断题——场景覆盖'我们要用 develop 分离环境'、'AI 生成的不用 review'、'大厂都用 GitFlow'等。我判断真伪，你批改。」

**B.12.18**　「模拟一个场景：我在写 feature X，被叫去修 hotfix Y，然后又要 review PR Z。我告诉你每一步我怎么处理（stash / commit WIP / worktree / 切分支 / clone…），你评价我的选择、指出更省事的做法、以及潜在的坑。来 4 轮。」

**B.12.19**　「出 5 道'这个场景该用 stash / worktree / clone 哪一个'的判断题，包含反面案例（不需要 worktree 的场景也拿来考我）。我做完你逐题批改并解释判断理由。」

**B.12.20**　「让我复述一遍：为什么同一个分支不能同时在两个 worktree 检出？你听我讲，指出我的理解漏洞。」

**B.12.21**　「给我 8 道'PR 描述里的信息够不够'判断题。每道题给一份 diff + 一份描述，我判断这份描述能不能让评审员做出'是否 approve'的判断——不够的话缺什么。你批改讲评。」

**B.12.22**　「给我 5 段真实感的 commit message（既有好的也有坏的），我打分（1–5 分），你也打分并给出你的评分理由。看我和你打分的差异——差异大的地方一起讨论。」

**B.12.23**　「假装你是新来的实习生，问我 6 个关于'我们团队为什么这么用 Git'的问题，覆盖：为什么开分支保护、为什么用 PR 不能直接 push、为什么要写 PR 描述、fork 和 shared repo 的区别、force push 为什么危险、CODEOWNERS 是干什么的。我答完你打分。」

**B.12.24**　「给我 10 道场景判断题，每题一个具体情形，我要判断这个操作应该是绿色 / 黄色 / 红色档。场景覆盖：`git commit` 常规 / `git push` 到 feature / `git push --force` 到 main / `git filter-repo` / `git branch -D` 未合并分支 / AI 读 `.env` / AI 读 `~/.ssh/id_rsa` / AI 建议加 `safe.directory = '*'` / AI 建议 `git config credential.helper store` / AI 想 clone 一个不认识的 GitHub 仓库。我答完你批改并讲评。」

---

## B.13　对话精化：追问三式（Meta-Prompts）

当 AI 答非所问时，别原句重复——用这三条把"愿望"翻译成"意图"。

**B.13.1**（第一式：换概念词）「把我原来的说法翻译成第 5 章的词汇（'珠子/名牌/项链'或 rebase/reset/merge/amend），不允许出现'合并''整理''搞一下'这类模糊词。我的原话是：`<原始请求>`。请重写成一句不给你留猜测空间的指令。」

**B.13.2**（第二式：要求复述）「先不要跑命令。用你自己的话告诉我：你打算做什么、会改动哪些引用（`refs/...`）、会不会碰远端、旧引用去了哪里（是否在 reflog 里可救回）。**我确认后你再动**。」

**B.13.3**（第三式：列可能）「我说不清我想做什么。关于 `<现象描述，比如"历史看起来乱">`，你猜我可能想做的是哪几件事？列出 3–5 种，每种说清：（a）具体命令；（b）对项链的影响；（c）后悔了怎么救回。我从里面选。」

---

## 附：使用后回顾

跑完一条黄色或红色指令，建议顺手做三件事——这是本书反复讲的\"三把安全刷牙\"：

1. `git reflog -20`——看看这条指令到底挪了什么。
2. `git status`——确认工作目录、暂存区、HEAD 的现在状态。
3. `git log --oneline --all -10`——确认项链的整体形状符合预期。

这三条构成你和 AI 之间最短的信任回路：**你出意图，AI 出语法，你出判断，AI 出复盘线索**。用得多了，本附录里的模板你会越来越少直接复制——那正是概念地图内化的信号。
