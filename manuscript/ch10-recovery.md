# 第 10 章　事故恢复：Git 几乎不扔东西

> 《Git 的概念地图》第 10 章 · 场景章 · v1.0
> 场景决策部分的第五章：把前九章讲过的所有机制，全都换成"事故当下"的视角。
> 结构：事故剧本手册。八个剧本，每个都是**现场 → 评估 → 恢复 → 预防**四段式。

---

## 10.1 场景引入：三点四十七分的一声"卧槽"

周三下午三点四十七分。你的耳机里正放着一首慢歌，屏幕上是一个刚刚合并完的 feature 分支。你在做最后的清理——把那些已经合并进 main 的旧分支删掉。

```
$ git branch --merged main
  feature/user-profile
  feature/email-verify
  hotfix/typo-in-readme
  experiment/new-parser
```

四条。你 `git branch -d` 依次删。删到最后一条时，Git 拦了你一下：

```
error: The branch 'experiment/new-parser' is not fully merged.
If you are sure you want to delete it, run 'git branch -D experiment/new-parser'.
```

你愣了 0.5 秒——"哦对，这个实验分支后来废弃了，没合进 main，但我记得代码也没什么用了"。手指几乎是条件反射地敲下：

```
$ git branch -D experiment/new-parser
Deleted branch experiment/new-parser (was a1b2c3d).
```

回车按下去的那一瞬间，你脑子里闪过一个念头——**"等等，那个分支上是不是还有上周三我写了半天的 tokenizer 重构？"**

你切回 main，`git log --all --oneline | grep tokenizer`——**没有**。

**"卧槽。"**

耳机里的慢歌还在放。你的心跳已经飙到 120。你打开浏览器准备搜"git 恢复已删除分支"——手抖到搜索框里打错了三个字母。

---

**先停下。** 把手从键盘上拿开。深呼吸一下。

这一章要交给你的第一件事，是一句话——**慌乱是事故的第二次伤害**。第一次伤害是那颗珠子暂时找不到了；第二次伤害是你在慌乱中乱敲命令，把原本能救回的局面搞成救不回。绝大多数"Git 事故"的最终损害，都是第二次伤害造成的。

第二件要交给你的事，是一句你应该在事故发生的**前 60 秒**就相信的话——

> **Git 几乎什么都不扔。**

你在本地做过的任何一个动作，哪怕是删分支、reset --hard、rebase 搞砸——被"清扫掉"的珠子几乎永远还在 `.git/objects/` 里躺着，`.git/logs/` 里记着它上一秒还挂在哪张标签上。第 5 章讲过 reflog 的机制，那时候讲的是"重写历史的原理"；这一章讲的是**同一个机制换成应急视角——每一次紧急抢救时，你要相信什么、找什么、按什么顺序按下什么命令**。

第三件要交给你的事——**"事故第一小时"清单**。任何 Git 事故发生后，**未来 60 分钟内，你要遵守的四条纪律**：

1. **别关终端。** 你此刻的 shell 历史、`.git/HEAD` 的当前值、reflog 的时间戳——都是最新鲜的证据。关掉终端不会丢数据，但让你少了一份现场笔录。
2. **别再敲命令。** 尤其是任何"我试试这个能不能救回来"的探索性命令。**在你不知道要救什么、要救到什么状态之前，任何多敲一条命令都可能覆盖 reflog 里的关键行。**
3. **先 fetch，不 pull。** 如果事故涉及远端（force push、误推），第一步是 `git fetch --all`——**读**远端的当前状态。**不要 pull**——pull 会尝试合并，把混乱带进本地。fetch 只是把远端的状态**拍照**到本地缓存，纯读，零副作用。
4. **叫 AI 读 reflog。** 让 AI 帮你读 `git reflog --date=iso --all`，找到事故发生前的最后一个已知良好状态的 SHA。**AI 读 reflog 比你自己读快十倍**——它不慌，它眼睛好。这是本章 AI 指令箱的核心用法。

这四条清单，请在你屏幕边贴一张便利贴。**\"事故当下的价值 = 平时打过多少遍 reflog\"**——本章要做的，就是把这四条纪律和随后的八个剧本，刻进你的直觉里。

---

## 10.2 祛魅时刻：Git 的事故恢复哲学

先给结论。

> **Git 是一个"追加式"数据库——它极少真正删除任何东西。你在本地做的任何一个操作，物理上的默认结果都是"造新对象 + 挪引用"，旧对象在 `.git/objects/` 里静静地躺着，`.git/logs/` 里记着刚才发生过什么。所以：只要事故是在本地发生的，事故当下丢失的东西，绝大多数都能在几分钟内找回。真正"丢"了的东西，只有一类：从来没被 Git 记录过的东西。**

这句话里三个字最要紧：**\"本地\"、\"记录过\"、\"绝大多数\"**。展开三条推论：

**推论一：只要一个对象被 Git 造过一次（`git add` 或 `git commit`），它就获得了 30-90 天的托管期。**

第 5 章讲过 reflog 保留期：`gc.reflogExpire = 90 天`、`gc.reflogExpireUnreachable = 30 天`。默认配置下，**一颗"没人再指着的孤儿珠子"，Git 还会替你保管 30 天才真的去 gc 它**。这段时间里它躺在 `.git/objects/`，你能用 `git fsck --lost-found` 把它找出来，能用 `git show <sha>` 看它的内容，能用 `git branch rescue <sha>` 把它接回项链。

**推论二：\"从来没被 Git 记录过的东西\"是唯一真正的坏消息。**

工作目录里那个你写了两小时、还没 `git add` 过的文件？Git 从来没见过它，不会替你保管。`git reset --hard` 抹掉它，就是真的抹掉了。**这类损失是本章唯一无法承诺救回的东西**——所以下面的剧本里，涉及 `reset --hard` 的部分会反复强调"未提交的改动"这个例外。

**推论三：一旦事故涉及"已推送到远端 + 覆盖了远端"，救援策略就要跨过一条边界。**

本地 gg 有 reflog 兜底，远端 gg 只能求"分布式副本"兜底——同事的 clone、CI 的 clone、你上一次 fetch 的镜像。这就要用到第 4 章"分布式副本"那张地图——**每一份 clone 都是一份完整的副本**，只要还有一个人手里的 clone 没被污染，那份历史就还活着。

### 事故恢复决策树的第一问

在你冲到 AI 面前敲救援命令之前，先在心里问自己一个问题——这个问题会决定接下来一切策略：

```
                      ┌────────────────────────────────┐
                      │  第一问：                       │
                      │  这颗珠子被 push 到远端过吗？   │
                      └────────────┬───────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                   否 ← 事故在本地             是 ← 事故跨到了远端
                    │                             │
                    ▼                             ▼
        ┌──────────────────────┐    ┌────────────────────────────┐
        │ reflog 是你的主武器  │    │ 先问第二问：                │
        │ 90% 概率一条命令搞定 │    │ 你或别人手上还有旧 clone 吗?│
        │ 慢慢来，别急         │    └──────────────┬─────────────┘
        └──────────────────────┘                   │
                                    ┌──────────────┴──────────────┐
                                    │                             │
                                   有 → 从旧 clone                没 → 事情变严重
                                    │   救出历史                   │   （敏感文件已扩散
                                    │                             │    → 立即吊销凭证）
                                    ▼                             ▼
                          ┌──────────────────┐          ┌────────────────────┐
                          │ 恢复策略是"合流"│          │ 恢复策略是"往前造 │
                          │ 用 revert 或再  │          │ 珠子"（第 5 章 revert│
                          │ push 一次       │          │ 而不是回退历史）    │
                          └──────────────────┘          └────────────────────┘
```

*图 10-1：事故恢复决策树的第一问和第二问。90% 的事故都停在最左边那个绿色的框里。*

**看清楚**：本章 8 个事故剧本，前 7 个都停在"事故在本地"这一支——它们都是"reflog 救援"的不同变奏。**只有第 5 号剧本（误提交敏感文件）和第 8 号剧本（误改 main 已推送）跨过了"事故到远端"这条线**——它们才是真正需要"叫团队"、"吊销凭证"、"revert 而不是 reset"的黄色事故。

好了，铺垫结束。八个剧本，逐个来。

---

## 10.3 剧本 1：误删分支（`branch -D` 之后想起里面还有东西）

### 事故现场

回到开篇那一幕。三点四十七分，你 `git branch -D experiment/new-parser`，Git 说了一句 `Deleted branch experiment/new-parser (was a1b2c3d).`——然后你想起来，那个分支上有你上周花了半天写的 tokenizer 重构。

**关键细节**：Git 在删分支时留下的那条消息里，写着 `was a1b2c3d`——**那七个字符就是这颗孤儿珠子的 SHA 头**。这是 Git 悄悄留给你的救援锚点。**如果你手快关了终端，这个锚点会一起消失**——但即使消失了也不是绝路，reflog 里还有。

### 损害评估

先冷静评估三件事：

1. **那个分支上的提交对象**——`.git/objects/` 里，**还在**。删除分支只是删了 `.git/refs/heads/experiment/new-parser` 那个文件（41 字节的文本文件，第 3 章讲过），提交对象本身没被动过。
2. **reflog 里的记录**——**还在**。`.git/logs/refs/heads/experiment/new-parser` 这个文件也**还在**（Git 删分支时不会立刻删除对应的 log 文件——它甚至会保留到下次 gc）。所以你能翻它。
3. **未合并的珠子在 30 天的托管期内**——**是**。默认 `gc.reflogExpireUnreachable = 30 天`，30 天内 `git gc` 不会去清扫它。

**结论**：这颗珠子完全没事。你只是暂时找不到通往它的路，路标（分支标签）刚被你摘了。

### 恢复步骤

**第一步**（AI 指令）：先把删除消息里那个 SHA 拿到手。

> 「我刚才执行了 `git branch -D experiment/new-parser`，终端里应该显示了 `Deleted branch experiment/new-parser (was <sha>)`。帮我把那个 SHA 抓出来。如果我不小心把终端翻走了，用 `git reflog --all | grep experiment/new-parser` 找。」

**第二步**（人工确认点）：你要确认那个 SHA 就是你想找的珠子。让 AI 读它的内容：

> 「用 `git show <sha>` 展示那颗提交的 message、作者、日期，以及改动文件列表。让我核对这就是我要救回的 tokenizer 重构。」

AI 会输出类似：

```
commit a1b2c3d4e5f6...
Author: 你 <you@example.com>
Date:   Wed Sep 8 14:22:31 2026 +0800

    重构 tokenizer：把递归下降拆成状态机

 src/parser/tokenizer.py     | 187 +++++++++++++++++++++--------
 tests/test_tokenizer.py     |  43 +++++++++
 2 files changed, 195 insertions(+), 35 deletions(-)
```

**你人工核对**：日期对得上、message 对得上、文件对得上——**这是本剧本关键的人工确认点**，AI 不能替你做（因为只有你知道你要救的是啥）。

**第三步**（AI 指令）：把分支挂回去。

> 「用 `git branch experiment/new-parser <sha>` 把这颗珠子重新挂上一个分支标签。执行完之后 `git branch -a | grep experiment` 确认标签回来了。」

Git 会创建一个新的 `.git/refs/heads/experiment/new-parser` 文件，写入那个 SHA。**41 字节的文件、耗时不到一毫秒**——你复原了刚才那 0.5 秒犹豫造成的所有\"损失\"。

**如果连删除消息里的 SHA 都没拿到怎么办？**

用 reflog 兜底：

```
git reflog --all --date=iso | grep -i "new-parser\|experiment"
```

或者更宽的：

```
git fsck --lost-found
```

`fsck --lost-found` 会把所有\"unreachable\"（没有任何引用指着的）提交列出来——里面就有你那颗孤儿珠子。逐个 `git show` 核对，找到目标 SHA。

### 预防

- **删分支前先 `git log --oneline <branch>`**——花 3 秒钟看一眼\"我这是要删掉哪几颗珠子\"。
- **保留 Git 那句"was xxx"的消息**：删分支的操作**不要在压屏幕的滚动日志中间做**，做完停一下、抬眼看一下\"was\"那一行的 SHA。
- **让 AI 帮你做删除**：`「列出所有已经合并进 main 的本地分支，逐个 branch -d（注意小写 d，不是 -D）；对于没合并的分支列出来但先不删，让我看一眼」`——`-d` 会拦住未合并的删除，是这类事故的天然刹车。**永远不要让 AI 默认用 `-D`**。

---

## 10.4 剧本 2：`reset --hard` 抹掉了工作区

### 事故现场

你在 feature 分支上写代码，写到一半发现思路不对，想\"重新开始\"。你已经改了七八个文件，两个已经 `git add` 过了（暂存区里），另外五六个没 `add`（只在工作目录里）。

你打算\"回到干净状态\"，敲下：

```
$ git reset --hard HEAD
HEAD is now at c4d5e6f 初步搭结算页骨架
```

工作目录一片干净。你满意地准备重新开始。

**三秒后你想起来**——`app/settings.py` 里有一段你花了两小时调出来的配置，那是最难的部分，你**还没 `git add`**。

你 `ls app/settings.py`——文件还在，但内容是**上一个 commit 的版本**。你的两小时**没了**。

### 损害评估

这一节要**诚实**——本章第一个也是**唯一**一个\"没那么好救\"的剧本。

先分类看：

- **已经 `git add` 过的改动**——**能救**（几乎肯定）。`git add` 会把文件的 blob 对象写进 `.git/objects/`。blob 一旦被造出来，就受 30 天托管期保护。用 `git fsck --lost-found` 能找到它。
- **只在工作目录、从来没 `add` 过的改动**——**大概率救不回**。Git 从来没见过这个内容，`.git/objects/` 里没有对应 blob，reflog 里也没记录。**这是本章唯一\"真的没了\"的情形**——第 10.2 节的推论二在这里兑现。

**为什么必须诚实说这条？** 因为很多"Git 万能救援"的说法会让人误以为 reflog 是万灵药，结果 `reset --hard` 完之后花两小时找 AI 折腾，最后一无所获——**心里的怨气比丢掉的两小时还大**。**真相是清楚的**：\"只在工作区从没进入过 Git 视野\"的内容，Git 没法救。这就是 `reset --hard` 被列为 Git 里最危险的一档命令（第 5 章 §5.6）、也是 Claude Code 官方建议 `deny` 掉 `Bash(git reset --hard*)` 的根本原因。

### 恢复步骤

**先分开处理两类内容**。

**类别 A：已 `git add` 过的改动（能救）**

**第一步**：找出所有\"孤儿 blob\"。

> 「用 `git fsck --lost-found` 列出所有 unreachable 的对象。特别关注 `dangling blob <sha>` 这一类——那是我 `add` 过但没 commit 的文件内容。逐个 `git show <sha> | head -20` 展示前 20 行，让我核对。」

AI 会输出类似：

```
dangling blob 3f5a8b9c...    ← 可能是 app/settings.py 的某个版本
dangling blob 7e4d2c1a...
dangling commit ...
```

**第二步**（人工核对）：`git show <blob-sha>` 看内容，认出你要找的那个 blob。

**第三步**：把 blob 内容还原成文件。

> 「找到之后用 `git show <blob-sha> > app/settings.py` 把内容还原成文件。让我确认恢复的是我要的版本。」

**类别 B：从没 `add` 过的改动（大概率没了）**

**残存的希望有三个来源**，逐一尝试：

1. **编辑器的本地历史**——VS Code / IntelliJ / Cursor 都有\"Local History\"或\"Timeline\"功能，独立于 Git 记录你每次保存。IntelliJ 的 Local History 保留 5 天、能按时间轴查看每次保存的 diff。VS Code 的 Timeline 视图能看到文件的历次编辑。**这是 `reset --hard` 前未 add 内容的最后救命稻草**。
2. **操作系统级备份**——macOS 的 Time Machine、Windows 的 File History、Linux 上的 snapper/timeshift。如果开了自动快照，可能有 15 分钟前的一个版本。
3. **AI 助手的对话记录**——如果这段代码是 AI 帮你写的、或者你在 Claude Code / Cursor 里让 AI 看过、改过——**对话记录里可能还有那段代码的原文**。翻聊天历史。

**如果三条都没有——诚实接受**。学到一课：**在 `reset --hard` 前先 `git add -A` + `git stash --include-untracked` 或至少 commit 一个 \"WIP\"**。

### 预防

这条剧本的预防比恢复更重要。**四条硬规则**：

1. **`reset --hard` 前必先 `git status` 看一眼工作区**——有任何 \"Changes not staged\" 或 \"Untracked files\"，**先停下来处理**再动 `--hard`。
2. **有未提交改动就先 stash 或 commit**：`git stash --include-untracked -m "backup before hard reset"`——这一句能把工作目录 + 未跟踪文件都保护起来，`stash` 在 reflog 里有引用、永不 gc。
3. **配置层强制约束**：Claude Code 的 `.claude/settings.json` 里加 `"deny": ["Bash(git reset --hard*)"]`，或至少改成 `"ask"`——**让 AI 每次都问你一句\"确定？\"**。
4. **心理规则**：一旦手指在往 `--hard` 上打，先深呼吸，把\"我此刻工作区里有没有未提交的东西\"这个问题回答清楚再回车。

---

## 10.5 剧本 3：rebase 中途弄丢提交（或压根找不到自己走到哪一步了）

### 事故现场

你在 feature 分支上 rebase 到最新的 main。这个分支有 12 个 commit。rebase 走到第 5 个的时候冲突了，你解了冲突、`git add`、`git rebase --continue`——然后又冲突。再解、再 continue。走到第 8 个时你已经眼花，看到冲突标记里两边内容都不太确定，你随便选了一边，`add`、`continue`。

又是几次冲突，你烦躁地 `continue`、`continue`、`continue`——**忽然屏幕安静了**。

```
Successfully rebased and updated refs/heads/feature/checkout-v2.
```

结束了。你 `git log --oneline main..HEAD` 数一下——**只有 9 个 commit**。之前明明是 12 个。**三个提交去哪了？**

翻代码，你意识到——第 5 个 commit 的改动完全不见了。你 rebase 中途某一次冲突里，AI（或你自己）\"选边\"选错了，把那颗珠子的改动整个吃掉了。

### 损害评估

rebase 是本章救援机制最优雅的一个场景——因为 rebase 的每一步都被 reflog 详细记录着。

- **rebase 前 12 颗旧珠子**——**都在**。它们的 SHA 全部保留在 `.git/objects/`，reflog 里明确记着 `rebase (start): checkout main` 这一行之前 feature 指向哪个 SHA。
- **`ORIG_HEAD`**——Git 会在每次 rebase / merge / reset 之前把 HEAD 的当前值保存到 `.git/ORIG_HEAD` 这个特殊指针里。这是 Git 给你留的\"上一秒我在哪\"的书签。
- **rebase 生成的 9 颗新珠子**——**也在**，你现在正站在它们上面。

所以救援的物理动作很简单：**要么把 feature 标签整个挪回 rebase 之前的位置（放弃这次 rebase 重新来）、要么只把丢失的第 5 颗 cherry-pick 过来（保留 rebase 结果，补上丢的）**。选哪种取决于你对新 rebase 结果的信任度。

### 恢复步骤

**方案 A：整个放弃这次 rebase，回到 12 颗旧珠子的状态**

**第一步**：找 `ORIG_HEAD`。

> 「先运行 `git rev-parse ORIG_HEAD`——它是 Git 在 rebase 开始前自动保存的\"上一个 HEAD\"。展示这个 SHA 对应的 commit（`git show ORIG_HEAD --stat`），让我确认这就是 rebase 前 12 颗珠子的末端。」

**第二步**（人工确认点）：核对那颗珠子是不是 rebase 之前你 feature 的末端。

**第三步**：一键回退。

> 「用 `git reset --hard ORIG_HEAD` 把 feature 标签整个挪回 rebase 之前。展示 `git log --oneline main..HEAD` 确认现在有 12 颗珠子。」

**这一步之后你回到了 rebase 之前的状态**。慢慢再来一次 rebase，这次每颗冲突小心处理。

**方案 B：保留 rebase 后的 9 颗，把丢失的第 5 颗 cherry-pick 补上**

**第一步**：找到丢失那颗的 SHA。

> 「用 `git reflog --all --date=iso` 展示最近 50 条记录，我要找到 rebase 之前那 12 颗珠子里第 5 颗的 SHA。（rebase 之前 feature 的每一次 commit 都在 reflog 里，按倒序找 `commit:` 开头的行、跳过 rebase 相关的行。）」

**第二步**（人工确认点）：`git show <sha>` 看那颗的内容，确认是你要补回来的那颗。

**第三步**：把它 cherry-pick 到当前 HEAD。

> 「用 `git cherry-pick <sha>` 把这颗珠子复制到当前 feature 末端。如果 cherry-pick 又遇到冲突，停下来让我处理，不要自作主张选边。」

**跟 rebase 中途一样的忠告**：**这次遇到冲突，AI 停下来让人看**——不然可能再一次\"选边选错\"重演事故。

### rebase 进行中就发现走岔了怎么办？

上面讲的是 rebase 已经 `Successfully rebased and updated` 结束之后的救援。如果你**在 rebase 中途**就意识到不对——

**一键刹车**：`git rebase --abort`。

**`--abort` 是 rebase 的天然撤销键**：只要你还在 rebase 进行中（`.git/rebase-merge/` 或 `.git/rebase-apply/` 目录存在），无论走到第几颗、无论解过几次冲突、无论 continue 过几次——**`--abort` 会把 feature 标签恢复到 rebase 开始前的位置，就像什么都没发生过**。第 5 章讲过这一条，这里再强调一遍：**rebase 中途觉得不对 → `--abort` → 什么都没发生**。

**认清楚 abort 的边界**：一旦你看到 `Successfully rebased`，rebase 就结束了，`--abort` 就不能用了——这时候只能走 ORIG_HEAD / reflog 的路子。

### 预防

- **rebase 前必挂 backup 分支**：`git branch backup/before-rebase-$(date +%Y%m%d-%H%M%S)`——第 5 章讲过的黄色操作两步安全网。**这是本章预防措施里成本最低、收益最高的一条**。
- **rebase 中冲突时不要\"图快\"**：AI 指令里明确要求\"冲突时停下来展示两侧内容和 diff，我核对后再继续\"。**AI 最容易犯的错就是 rebase 冲突时\"觉得选一边合理\"然后自动 continue**。
- **心理阈值**：如果 rebase 的 commit 超过 6-8 个，或者中途冲突超过 3 次——**优先考虑 `--abort` 然后换用 merge**，或者拆成两次小 rebase 来做。

---

## 10.6 剧本 4：force push 覆盖了远端（还好有分布式副本）

### 事故现场

周五下午五点，你正在整理一个 PR。这个 PR 已经开了两周，有你、后端小李、前端小王三个人在合作——你们仨都往 `feature/checkout-v2` 上推过 commit。

review 意见回来了：\"提交太散了，整理成几个原子提交\"。你没多想，`git rebase -i main`，把 20 多个 commit 压成 6 个，`git push --force-with-lease`——

一切正常。你去泡了杯咖啡。

回来的时候看到小李在群里刷屏：

> \"卧槽我 pull 报错了\"
> \"你们谁 rebase 了？\"
> \"我今天早上推的两个 commit 呢？？\"
> \"我这边看不到了！！\"

**你脸绿了**。这**不是你个人的分支**——这是三人协作分支。你 rebase 把小李和小王在过去两天推的 commit 都从远端 log 里挤掉了。

### 损害评估

先冷静看一下损失面：

- **远端 `feature/checkout-v2` 的当前状态**——已经是你 rebase 后的 6 颗新珠子。原来的 20+ 颗珠子在远端 `.git/objects/` 里\"孤儿化\"了（还在，但没有引用指向）。
- **你本地**——是你 rebase 后的 6 颗，加上你本地 reflog 里 rebase 前 20+ 颗的 SHA。
- **小李本地**——**还是他昨晚 pull 完的旧状态**（20+ 颗，包括他自己推的两颗）。这就是关键——**他本地的 clone 是一份完整的、干净的、事故发生前的历史副本**。
- **小王本地**——同理，也是他上次 pull 时的旧状态。
- **CI runner**——如果你们的 CI 有过一次成功的 checkout，那台机器上也有一份旧状态的 clone（如果它还没被清理）。

**结论**：**只要还有一个人手里的 clone 没被你污染，那份历史就还在活着**——这就是第 4 章讲的\"分布式副本\"这张地图在事故场景下的兑现。Git 的分布式本质，本身就是一份灾备。

### 恢复步骤

**第一步**（叫团队 + 现场冻结）：立刻在群里喊住小李和小王——**不要 pull，不要 fetch，尤其不要 pull --rebase**。他们本地的旧状态就是你的救命稻草，一次 pull 可能就把它污染了。

> 「@小李 @小王 停一下！！我刚 rebase 完把远端搞乱了，你们**先什么都别动**。等我 5 分钟。」

**第二步**（AI 指令）：让小李（谁的本地状态最完整就找谁）确认他手上的状态。

> 「小李，帮我在你本地跑 `git log --oneline origin/feature/checkout-v2..feature/checkout-v2`（如果你之前是切在这个分支上）或者 `git log --oneline feature/checkout-v2 -30`——我要看你本地这个分支现在指向哪颗 SHA、包含哪些提交。这份状态就是我要恢复到远端的状态。」

小李输出一段 log，最末端 SHA 是 `a1b2c3d`——这就是**事故发生前的黄金 SHA**。

**第三步**（人工确认点）：核对这份状态包含所有该有的 commit（你的、小李的、小王的、这两周所有该有的）。

**第四步**（恢复远端）：让小李把他本地的完整旧状态强推回去。

> 「小李，你现在**先不要 fetch**——直接在你当前分支上 `git push --force-with-lease origin feature/checkout-v2`。这一步会用你本地的完整历史覆盖我刚才推坏的远端状态。执行完之后我们所有人再 fetch。」

**这里为什么让小李而不是你自己推？** 因为**你本地已经被你自己 rebase 污染了**，而小李本地是干净的原始状态。**\"谁手上的副本最干净，谁就是恢复者\"**——这是分布式恢复的核心原则。

**第五步**（收尾）：所有人 fetch，确认远端回到干净状态。**你**再重新 rebase，但这次先跟团队沟通\"我要 rebase 这条共享分支，暂停 30 分钟别推东西\"。

### 一个更狠的场景：所有人本地都被污染了

**如果不巧小李和小王中间都做过 pull**——他们本地也被拖成了新状态，怎么办？

**继续找副本**：

- **CI 的 workspace**：如果 GitHub Actions / GitLab CI / Jenkins 最近一次跑过 checkout，那台机器上还有旧的 workspace。**登录进去把 `.git/` 打包下来**，就是一份灾备。
- **服务器上的 checkout**：staging / dev 环境如果部署的是 `git pull` 拉的代码，那台机器上也可能有旧状态。
- **Git 服务端的 reflog**：**GitLab / Gitea 有服务端 reflog 且默认保留几周**（GitHub 也有类似机制但不对外暴露 API，需要联系 support）。**这是最后的兜底**——服务端 reflog 里记着 `feature/checkout-v2` 从 SHA X 变到 SHA Y 的每一步，联系管理员或用 API 能翻出\"事故发生前那一秒远端指向哪个 SHA\"。有了那个 SHA，恢复就变成一次 `push --force` 到那个 SHA。

**这就是为什么 force push 到共享分支被列为黄色操作、Claude Code 建议 `deny` 掉 `Bash(git push --force*)`——不是因为它\"不可救\"，是因为\"救援成本\"随着传播时间指数上升**。事故发生后 5 分钟内叫住团队 → 一次 force-with-lease 搞定；30 分钟后所有人都 pull 过 → 要联系 Git 服务端管理员翻服务端 reflog。**代价差 10 倍**。

### 预防

- **黄金规则再念一次**（第 5 章）：**不要 rebase 已推送到共享分支的 commit**。这条 force push 灾难 90% 是这条规则被违反造成的。
- **push 之前问一句\"这条分支有别人推过 commit 吗\"**：`git log <branch> --format='%an' | sort -u`——如果作者列表里有别人，你 rebase 前必须先在群里问一句。
- **`--force-with-lease` 不是免死金牌**：`--force-with-lease` 只保证\"远端没在你上次 fetch 之后被别人改过\"——如果你 fetch 完到 push 之间那 30 秒里同事没推东西，lease 是通过的，但**如果同事上周就推过而你没 fetch**，lease 完全无能为力。
- **分支保护规则**：GitHub / GitLab / Gitea 都支持在共享分支上禁用 force push、要求 PR review 才能合并——这是**工具层**的兜底，比任何\"规矩\"都可靠。**任何 shared 分支（main、develop、release/*、shared feature branches）都应该开分支保护**。

---

## 10.7 剧本 5：误提交敏感文件（.env / API key / 私钥）

### 事故现场

周二早上十点。你在 dev 环境调试第三方 API，把 API key 直接贴在了 `.env` 文件里（打算调完删掉）。调完之后你写代码写得投入，直接：

```
$ git add -A
$ git commit -m "feat: 接入结算 API"
$ git push
```

三条命令一气呵成。

十五分钟后，GitHub 给你发了一封邮件——**Secret scanning alert**：

> We detected a Stripe live API key in your commit `a1b2c3d` in repository `yourorg/checkout-service`, in file `.env`.

你脸\"唰\"地就白了。这个 key 是**生产环境的 Stripe secret key**——不是 test key。

### 损害评估

这是本章**最严重的一个剧本**——严重到\"物理救援\"是次要的，**\"凭证吊销\"才是第一优先级**。

先说清楚为什么这么严重：

1. **这颗 commit 已经推到 GitHub 了**——push 上去的那一秒起，**假设它已经泄漏了**。全世界的 secret 扫描机器人（好人和坏人都有）每分钟都在扫 GitHub 新 push 的 commit，一颗新 commit 里的 Stripe key 从 push 到被拿走的时间中位数是**几分钟到几十秒**。
2. **就算你立刻 force push 覆盖**——**旧 SHA 依然在 GitHub 的 objects 里存在几周甚至几个月**。GitHub 直到 gc 才会真正回收。而且你没法确定在那之前没被人拉走过。
3. **就算你联系 GitHub support 强制清除**——**已经被拉走的 clone 你追不回来**。

**结论**：**任何一个 secret 一旦被 push 到公网仓库，你都必须假设它已经泄漏，唯一能救的动作是\"让它失效\"——吊销这个 key，重新生成新的**。git 层的历史清理是**次要的辅助动作**——它只是让新的 clone 者看不到这个 key，不能救已经泄漏的部分。

### 恢复步骤（两阶段：先吊销，再清理）

**阶段 A：立即吊销凭证（分钟级，第一优先级）**

**第一步**（**不用 AI，你自己做**）：**立刻登录服务商后台**——Stripe / AWS / OpenAI / 数据库 / 任何被泄漏的凭证的发行方——**revoke 这个 key**。

- Stripe：Dashboard → Developers → API keys → \"..\" → Roll key（或 Reveal 后 Delete）
- AWS：IAM → Access keys → Deactivate + Delete
- OpenAI：Platform → API keys → Revoke
- 数据库：改密码 + 检查连接日志
- 服务器 SSH key（如果泄漏的是 id_rsa）：立即从所有服务器的 authorized_keys 里删掉

**吊销之后立刻生成新的 key**，更新到你的\"该在的地方\"（`.env.local` 加 `.gitignore`、CI secrets、K8s secret、vault ——**这次不要再进 git 了**）。

**第二步**（**审计泄漏影响**）：

- 检查服务商的 API 调用日志——**在你吊销 key 之前，这个 key 有没有被用过（非你自己的调用）**？
- Stripe 有 Events 日志、AWS 有 CloudTrail、OpenAI 有 Usage 日志——**看有没有异常来源的调用**。
- 如果有可疑调用——立刻按你们公司的安全事件流程报告，可能涉及资金损失、数据泄漏。

**这一步不是可选的**。**AI 事故里最贵的一类损失，是 secret 泄漏之后被人用来烧钱**（AWS 挖矿、OpenAI 刷 token）——**账单可能几小时几万美元**。

**阶段 B：git 历史清理（小时级，第二优先级）**

**这一阶段的目的不是\"救\"（key 已经失效了），是\"止损未来泄漏 + 团队合规\"**。

**第一步**（AI 指令）：把 `.env` 从当前工作目录里挪走 + 加入 .gitignore。

> 「先把 `.env` 移到 `.env.local`（或者复制内容到别处后删除）。然后在 `.gitignore` 里加 `.env`、`.env.*`、`*.pem`、`*.key`、`id_rsa*` 这些常见敏感文件模式。commit 这个 .gitignore 更新。」

**第二步**（AI 指令）：清理最新一颗 commit 里的 `.env`（如果只有最新一颗涉及）。

> 「用 `git rm --cached .env`（不删本地文件，只从暂存区移除）、`git commit --amend --no-edit`。这一步会 amend 掉最新一颗 commit，把 `.env` 从这颗珠子的树里拿掉。然后 `git push --force-with-lease`。」

**第三步**（**只在 secret 出现在多颗历史 commit 里时**）：用 `git filter-repo` 从整个历史里清除 `.env`。

> 「用 `git filter-repo --path .env --invert-paths --force` 从整个 git 历史里彻底删除 `.env` 这个文件。这是**红色操作**——它会**重写所有 commit 的 SHA**，团队所有人都必须重新 clone。执行前请**再次确认**：（1）我已经吊销了 key；（2）我已经在群里通知了所有协作者；（3）我已经备份了 clean 状态下的 remote（`git clone --mirror` 一份到别的位置）。」

⚠️ `git filter-repo`（或旧的 `git filter-branch`、或 `BFG Repo-Cleaner`）**是本章唯一一个真正\"重写全部历史\"的操作**——它会**改变每一颗 commit 的 SHA**（因为 tree 变了，parent 变了，级联下去）。这不是黄色操作，是**红色操作**——第 12 章会详讲。**没有 100% 的必要不要做**。

**第四步**（团队通知）：force push 上去之后，**每一个协作者都必须**：

- 删掉他们本地 clone（`rm -rf your-repo`）
- 重新 `git clone`
- 把他们本地未推的分支 rebase 或 cherry-pick 到新历史上

**这个协调成本是巨大的**——所以\"历史清理\"不是万能药，能不做就不做。

### 一个更常见的分支：secret 在最新一颗 commit 里、还没 push

**如果你及时发现——commit 完但**还没 push**——恢复成本是本剧本 1/100**：

```
git rm --cached .env
echo ".env" >> .gitignore
git add .gitignore
git commit --amend --no-edit
```

一条 commit 被 amend 掉，`.env` 从来没到过远端。**这就是为什么 `git status` 应该是 commit 前的肌肉记忆——如果每次 commit 前都扫一眼 status，你会在 push 前发现 `.env` 混进了 stage**。

### 预防

**四层防御**，每一层都能挡住绝大多数事故：

1. **文件命名 + .gitignore 保护**：`.env` / `.env.*` / `*.pem` / `*.key` / `id_rsa*` / `credentials*` / `secrets.*` ——**这些应该是每一个新仓库 `git init` 之后立刻加的 .gitignore 条目**。**很多脚手架已经默认加了**，但 AI 生成的项目有时会忘。
2. **pre-commit hook 扫描**：`gitleaks`、`trufflehog`、`detect-secrets`——commit 前扫 diff 里有没有像 secret 的字符串。**这是本地的最后一道刹车**。用 `pre-commit` 框架配起来 10 分钟的事。
3. **AI 指令层 deny 规则**：Claude Code 的 `.claude/settings.json`：`"deny": ["Read(./.env*)", "Read(./secrets/**)"]`——**从源头切断 AI 读 .env 的能力**。⚠️ 但记住 shoofly.dev 的关键论断：**`.gitignore` 不能阻止 AI Agent 读 .env**——AI Agent 直接读文件系统，绕过 git。所以 AI 层的 deny 规则**必须独立配**。
4. **服务端 secret scanning**：GitHub / GitLab / Gitea 都支持服务端 secret scanning——push 上来立刻扫、发现 Stripe key / AWS key / OpenAI key 立刻告警、可选阻止 push。**开这个功能**。GitHub 免费仓库也支持。

**记住四层的顺序**：**吊销永远是第一步**。git 层的清理是可选的辅助。**没有先吊销就冲去 filter-repo 的，是在做\"表演\"，不是在做\"止损\"**。

---

## 10.8 剧本 6：merge 错了、还推了、想撤销

### 事故现场

你合了一个 PR 到 main。合完 5 分钟后线上开始报错——那个 PR 里有一段代码把 Redis 缓存 key 的前缀改了，但没同步改读取端，导致所有缓存查询失效，DB 被打穿。

你想：赶紧把这个 merge 撤销。

你的第一反应是 `git reset --hard HEAD~1` + `git push --force`——**如果你真这么做了，就是从一场应用事故升级成一场协作事故**。

好在你想起了黄金规则（第 5 章 §5.4.4）：**共享分支不 reset，共享分支不 force push**。

### 损害评估

- **main 上多了一颗错误的 merge commit**——需要撤销其效果，但**不需要\"物理擦除\"**它。
- **线上服务正在报警**——**这是首要的时间压力**，撤销必须快。
- **已经有其他同事 pull 过这颗 merge**——如果你 reset + force，他们下一次 pull 会陷入混乱。

### 恢复步骤

**merge commit 的 revert 有一个特殊语法，比普通 commit 的 revert 复杂一点点**。

**第一步**（AI 指令）：找出 merge commit 的 SHA 和它的\"主线 parent\"。

> 「用 `git log --merges --oneline -5` 展示最近 5 个 merge commit。我要撤销的是刚才那个 SHA `a1b2c3d` 的 merge。展示 `git show a1b2c3d --stat` 让我核对。同时告诉我这颗 merge commit 的两个 parent 分别是哪个 SHA、哪个是主线（main 的原状态）、哪个是被合入的分支末端。」

AI 输出：

```
commit a1b2c3d (HEAD -> main)
Merge: c4d5e6f  b7a8c9d
    Merge pull request #142 from feature/cache-refactor

Parents:
  1: c4d5e6f   ← main 合并前的状态（主线）
  2: b7a8c9d   ← feature/cache-refactor 的末端
```

**第二步**（人工确认点）：确认 parent 1 就是你希望回到的 main 状态。

**第三步**（AI 指令）：revert 这颗 merge commit，指定主线 parent。

> 「用 `git revert -m 1 a1b2c3d` 撤销这颗 merge commit。**`-m 1` 告诉 Git\"以 parent 1 为主线\"——意思是撤销掉从 parent 2 那一支合过来的所有改动**。执行前展示 revert 会产生的 diff，让我核对反向改动符合预期（应该是把 cache key 前缀改回去、以及 feature/cache-refactor 分支上所有改动的反向）。」

**第四步**：commit + push。

> 「Revert 完成后展示 `git log --oneline -5`——main 上应该多了一颗 `Revert "Merge pull request #142..."` 的 revert commit。用普通 push（**不是 force push**）推上去。」

**这就是共享分支撤销的正确姿势——造一颗\"抵消珠子\"，不动任何旧珠子**（第 5 章 §5.8）。log 里错误的 merge 和撤销它的 revert 都在，历史完整可追溯。

### 一个副作用：revert 一次 merge 之后，那个分支的功能就永远\"合不进来\"了吗？

**是的，直接再 merge 一次是没用的**——因为 revert 之后 main 上还挂着\"feature/cache-refactor 已合并\"的记录（那颗被 revert 的 merge commit），Git 不会重复合并。

**如果你以后想重新合入这个功能**（修好 bug 之后）——有两种方式：

1. **revert the revert**：`git revert <revert-commit-sha>`——撤销那次撤销，功能又回来了。适合 revert 之后很快就能修好、且没什么额外改动的情形。
2. **rebase 那个 feature 分支到 main 最新之上，然后重新 merge**：把 feature/cache-refactor 的所有 commit rebase 到当前 main 上（会造出新的 SHA），修好 bug，然后 merge 过来。适合 revert 之后已经过了一段时间、feature 分支需要大修的情形。

**这个副作用是 revert 相比 reset 的\"代价\"**——但换来的是共享分支的安全性。**在\"简单方便\"和\"不给团队制造混乱\"之间，共享分支永远选后者**。

### 预防

- **PR 合入前必过 CI + 灰度**——大部分\"合完立刻挂\"的事故是本可以在 pre-merge CI 或灰度里发现的。
- **feature flag 覆盖破坏性变更**——像\"改缓存 key 前缀\"这种改动，应该用 feature flag 而不是直接切换。这样出事故时不用 revert，直接后台关 flag 即可。
- **main 分支保护 + require CI green**——push 到 main 只能通过 PR、PR 必须过 CI——**服务端强制**这一条，比\"团队规矩\"可靠 100 倍。
- **准备好 revert 的心理默认**：**共享分支上出问题永远想 revert，不是 reset**。这句话应该刻进每个团队 lead 的 muscle memory。

---

## 10.9 剧本 7：detached HEAD 上提交后切走了（新提交\"消失\"了）

### 事故现场

你想看看 3 个月前的项目长什么样，好方便对着老版本调试一个 bug。你 `git checkout a1b2c3d`——直接 checkout 到 3 个月前那颗 commit 上。

```
Note: switching to 'a1b2c3d'.

You are in 'detached HEAD' state. ...
```

你熟悉这个红色警告（第 3 章 §3.3 讲过）。你在这个旧状态里读代码、跑测试、试了一段修复方案——修出来了！你随手 `git add -A && git commit -m "fix: 修好那个古老 bug"` 提交了一下。

然后你切回 main：`git switch main`。

Git 弹了一个警告：

```
Warning: you are leaving 1 commit behind, not connected to
any of your branches:

  e4f5g6h fix: 修好那个古老 bug

If you want to keep it by creating a new branch, this may be a good
time to do so with:

 git branch <new-branch-name> e4f5g6h
```

**你没看那行提示**——回车过快，直接切走了。切到 main 之后你 `git log --oneline | grep "古老 bug"`——**没有**。你想找的那颗 fix commit 不在 main 的项链上。

\"我刚才提交的那颗 commit 呢？？\"

### 损害评估

**好消息**：那颗 commit **完全没事**。它的 SHA `e4f5g6h` 在 Git 的临别赠言里明明白白写着；就算你没记住，reflog 里也一定有它。

**你只是切走的时候没给它挂一张标签**——它现在是一颗\"无主孤珠\"（第 3 章讲过）。**孤儿珠子的 30 天托管期从现在开始计时**。30 天内你随时可以救回来。

### 恢复步骤

**第一步**（AI 指令）：找回那颗 SHA。

> 「用 `git reflog --date=iso -20` 展示最近 20 条 HEAD 移动记录。我在 detached HEAD 上 commit 过一颗 message 包含\"古老 bug\"的 commit，帮我找到它的 SHA。」

AI 输出：

```
e4f5g6h HEAD@{2}: commit: fix: 修好那个古老 bug
a1b2c3d HEAD@{3}: checkout: moving from main to a1b2c3d
d7c8b9a HEAD@{4}: ...
```

`e4f5g6h` 就是它。**注意 HEAD@{2} 那一行**——\"commit\" 类型的记录就是你在 detached 状态下的提交。

**第二步**（人工确认点）：确认那颗 commit 是你要救的那颗。

> 「用 `git show e4f5g6h --stat` 展示这颗 commit 的改动列表，让我确认这是我的修复。」

**第三步**（AI 指令）：给它挂一张分支标签，让它\"接回项链\"。

> 「用 `git branch rescue/ancient-bug-fix e4f5g6h` 把这颗孤儿珠子挂上一个分支标签。这颗珠子从此有名有姓，不会被 gc 掉了。」

**第四步**（决策点）：这颗修复要不要合到 main？

**如果 3 个月前那个版本还在客户环境里跑（多版本共存）**——那颗 fix 属于旧版本，把它挂在旧版本的维护分支上。

**如果只是当时用旧版本调试、修复要合到 main**——用 cherry-pick：

> 「切回 main，用 `git cherry-pick e4f5g6h` 把这颗修复复制到 main 项链末端（会造一颗新 SHA、内容相同的珠子）。如果 cherry-pick 遇到冲突（3 个月的差距很可能有），停下来让我处理。」

### 一个变种：切走的时候连警告都没看到

有些 Git 版本 / 配置下，切走时的\"leaving X commit behind\"警告可能不显眼、或者你压根没看。

**这不影响救援**——**reflog 会记录一切**。你只要知道\"我曾在某个 detached 状态下 commit 过\"这一件事，reflog 就能找到那颗珠子。**reflog 不需要标签、不需要引用、不需要任何东西——它就是 Git 本地的行车记录仪**。

### 预防

- **detached HEAD 上做任何提交前先挂标签**：`git switch -c experiment-<描述>` ——**这一步在\"我要试一下\"的开始就做**，一劳永逸。
- **看到\"leaving N commits behind\"警告时**——**别忙着按回车**。看清楚 N 是几、message 是什么。**Git 的这句警告是它已经能说的最人性化的挽留了**——它甚至把恢复命令都印给你了（`git branch <new-branch-name> <sha>`）。
- **心理模型**：**detached HEAD 不是错误状态**（第 3 章讲过）——它是\"看一看试一试\"的正确姿势。**危险的从来不是 detached 状态本身，而是\"在 detached 里 commit + 切走时不挂标签\"这个组合**——本剧本就是这个组合的兑现。

---

## 10.10 剧本 8：误改了 main 并 push 了

### 事故现场

你在改一个功能，改着改着以为自己在 feature 分支上。写了 4 个 commit，`git push` 一气呵成。

推完之后你 `git status`——

```
On branch main
Your branch is ahead of 'origin/main' by 0 commits.
```

**你一直在 main 上**。

你 `git log --oneline -10` 一看——最近 4 颗 commit 是你随手写的\"wip\"、\"再改一下\"、\"typo\"——**全部推到了 origin/main**。这不是私人分支的\"整理提交\"问题——这是**把 4 颗未评审的、message 都不体面的 commit 直接怼进了主干**。

CI 应该已经跑起来了。同事的 IDE 里应该已经有 pull 提醒了。

### 损害评估

- **main 上多了 4 颗不该在的 commit**——需要撤销它们的效果、并且把 main 的 log 恢复到不那么难看。
- **但撤销必须遵守共享分支黄金规则**——不能 reset、不能 force push。
- **有一件好事**：**你这 4 颗 commit 本身的代码可能是有用的**——你要救的不是\"删掉代码\"，是\"把它们从 main 挪到 feature 分支\"。

### 恢复步骤

**这个剧本的关键姿势是\"两手活\"**：**一手在 main 上 revert 让主干干净，另一手在 feature 分支上 cherry-pick 让代码不丢**。

**第一步**（AI 指令）：找出误推的 4 颗 commit 的 SHA 范围。

> 「用 `git log --oneline origin/main~4..origin/main` 展示最近 4 颗 commit（假设是从 SHA `w1x2y3z` 往回 4 颗）。让我核对哪几颗是我误提交的。」

**第二步**（AI 指令）：从当前 main 的位置开一个 feature 分支，把代码搬走。

> 「先从 main 当前位置（origin/main HEAD）开一个新分支 `feature/misplaced-commits`：`git branch feature/misplaced-commits`。这样这 4 颗 commit 在 feature 分支上就都留住了——虽然它们**也**还在 main 上，但至少代码不会丢。」

**第三步**（AI 指令）：在 main 上 revert 掉这 4 颗。

> 「切回 main（现在在 main 上），用 `git revert --no-commit <老 sha>..<新 sha>` 一次性 revert 这 4 颗（`--no-commit` 让 revert 都堆在暂存区，最后一起 commit）。然后 `git commit -m "revert: 撤销误推入 main 的 4 颗 commit（详见 feature/misplaced-commits）"`。」

⚠️ revert 一段 SHA 范围的语法要小心：`git revert A..B` 是 revert **B, B~1, ..., A~0 之后的每一颗**——**不包括 A 本身**。所以给的老 SHA 应该是\"要保留的那颗\"，B 是\"最新那颗\"。**让 AI 明确复述范围**再执行。

**第四步**：正常 push（不需要 force）。

> 「push 上去（不加 --force）。因为 revert 是往前造珠子，属于 fast-forward，push 一定成功。」

**第五步**：feature 分支切过去、rebase 到干净的 main 之后（现在 main 又干净了）、开正式 PR。

> 「切到 `feature/misplaced-commits`。用 `git rebase --onto main <旧 main HEAD> feature/misplaced-commits`——把这 4 颗 commit 重新 rebase 到干净的 main 之上（避开那颗 revert commit）。然后开 PR 走正常流程。」

**第五步的另一种走法**：如果这 4 颗 commit 本身太糟糕（message 全是 wip），**用 `git rebase -i` 整理一下再开 PR**——保留代码，抛弃提交结构。

### 预防

**这个事故 99% 是分支保护缺失造成的**——如果 main 有分支保护，第一次 `git push origin main` 就会被服务端拒绝。

**分支保护的最少配置**（每个 shared 分支都要开）：

- **禁止直接 push**——所有改动必须通过 PR。
- **PR 必须有 CI green**——不过 CI 不给合。
- **PR 必须至少一人 review**——不过 review 不给合。
- **禁止 force push**——force push 也直接拒。
- **禁止删除**——删除 main 直接拒。

**这套配置在 GitHub 是 Settings → Branches → Branch protection rules，5 分钟能配好。GitLab / Gitea 也都支持**。**任何一个团队仓库，main 没开分支保护就是在等一场事故**。

其他辅助预防：

- **本地 shell prompt 显示当前分支**（zsh 的 `PS1`、bash 的 `PROMPT_COMMAND`）——让\"我在哪个分支\"始终肉眼可见。
- **commit 前扫一眼 `git status` 第一行**——\"On branch main\"这句话如果不是你期望的分支名，**立刻停**。
- **AI 指令层的默认**：让 AI 在 commit 前默认展示 `git status` 前 5 行，主动提示\"你当前在 main 分支，是否确认？\"。

---

## 10.11 事故第一小时清单（贴屏幕的便利贴版本）

八个剧本讲完，把\"该做什么、不该做什么\"压成一张便利贴：

```
┌─────────────────────────────────────────────────────────────┐
│  Git 事故第一小时清单                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏸  别关终端（现场就是证据）                                 │
│  ⏸  别再敲命令（尤其是探索性的）                             │
│  ⏸  先深呼吸，慌乱是第二次伤害                               │
│                                                             │
│  📋  先做完这五件事再决定救援策略：                          │
│      1. 事故是发生在本地？还是已经到远端？                   │
│      2. `git reflog --date=iso -30` 打印出来                │
│      3. `git status` 看一眼工作区状态                        │
│      4. `git log --oneline --all -20` 看一眼当前项链         │
│      5. 涉及远端？先 `git fetch --all`（**不 pull**）        │
│                                                             │
│  🚨  涉及 secret 泄漏？——先吊销凭证，再谈 git                │
│                                                             │
│  🤖  叫 AI 帮忙读 reflog：                                   │
│     「我刚才执行了 X，之后发现 Y，请从 reflog                │
│      找到执行 X 之前的 HEAD 位置和分支状态。                 │
│      给我恢复方案，但**在我确认前不要执行**。」               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**这张便利贴的价值**：**它把\"事故发生时该有的第一反应\"从\"慌乱\"改成\"流程\"**。有流程的人不会犯二次伤害的错。

---

## 10.12 AI 指令箱 · 事故恢复

以下指令模板与工具无关（Claude Code / Cursor / Copilot / Aider / Windsurf 皆适用）。**颜色标注**：本章救援指令**几乎全是黄色**——因为救援本身就是危险操作的对面（rebase / reset / branch -D / force push）。**核心纪律：AI 提出方案 → 人工确认 → AI 执行**。

**🟢 探索与诊断类（只读，事故当下先跑这几条）**

- 「事故现场诊断：跑 `git status`、`git log --oneline --all -20`、`git reflog --date=iso -30`、`git branch -av`。用中文向我总结：（1）我现在站在哪；（2）过去 30 分钟做过哪些改历史操作（reset / rebase / merge / branch delete / force push）；（3）我当前工作区有没有未提交改动。**不要执行任何有副作用的命令**。」
- 「读 `git reflog --date=iso -50`，按时间倒序告诉我：过去这段时间在这个仓库里 HEAD 发生过哪些位置变化。特别标出：commit / checkout / reset / rebase / merge / branch delete 这几类的每一条——每条给出 before/after SHA、时间、动作类型。」
- 「用 `git fsck --lost-found` 列出所有 unreachable 的对象（dangling commits / dangling blobs / dangling trees）。**只读、不改任何东西**。每个 dangling commit 用 `git show <sha> --stat` 简要展示 message + 改动文件。让我认领。」

**🟡 误删分支救援**

- 「我刚才 `git branch -D <name>` 误删了分支 `<name>`。（1）先从终端历史或 `git reflog --all` 找到该分支被删前指向的 SHA；（2）`git show <sha>` 展示那颗 commit 让我核对；（3）核对通过后 `git branch <name> <sha>` 把分支挂回去。**每一步都停下来等我确认**。」

**🟡 reset --hard 之后救援**

- 「我刚 `git reset --hard` 之后发现丢东西了。（1）用 `git reflog -20` 找到 reset 之前的 HEAD 位置；（2）展示那颗 commit 的 message + 改动文件让我确认；（3）确认后 `git reset --hard <那个 SHA>` 恢复。如果我丢的是**从没 `add` 过的工作区改动**，诚实告诉我：**这类改动 Git 恢复不了**，建议我去看编辑器的 Local History 或系统级快照。」
- 「我刚 `git reset --hard` 之后想找回一个我 `add` 过但没 commit 的文件 `<path>`。用 `git fsck --lost-found` 列出所有 dangling blobs；每个 blob 用 `git show <blob-sha> | head -20` 展示前 20 行让我认领。找到之后用 `git show <blob-sha> > <path>` 还原成文件。」

**🟡 rebase 搞砸救援**

- 「我 rebase 完发现丢了 commit / 走岔了。**如果 rebase 还在进行中**（.git/rebase-* 目录存在），直接 `git rebase --abort` 一键回滚。**如果已经 `Successfully rebased` 结束**，用 `git reset --hard ORIG_HEAD` 把当前分支整个挪回 rebase 之前——**这一步等我确认 ORIG_HEAD 就是 rebase 之前的位置再执行**。」
- 「我 rebase 完丢了某一颗 commit（内容大致是 `<描述>`），但其他 commit 都想保留。用 reflog 找到那颗被丢的 SHA，`git show` 展示让我确认，然后 `git cherry-pick <sha>` 把它补到当前 HEAD。**cherry-pick 冲突时停下来让我处理，不要自作主张**。」

**🟡 force push 灾难救援**

- 「我 rebase 后 `git push --force-with-lease` 到了共享分支 `<branch>`，然后发现该分支上有同事的 commit 被我挤掉了。（1）**先让我在群里通知所有协作者停止 pull**；（2）从任何一位协作者的本地找出他们的 clone 里 `<branch>` 指向的 SHA（那是事故前的黄金 SHA）；（3）让那位协作者用 `git push --force-with-lease origin <branch>` 把远端恢复。**由\"clone 最干净的人\"执行恢复推送，不是我**。」

**🔴 敏感文件泄漏（这是红色，第一优先级不是 git）**

- 「我误 commit + push 了 `.env`（或其他敏感文件），文件里有 API key / 私钥 / 密码。**执行任何 git 操作之前，先做完这三件事**：（1）**立刻登录服务商后台吊销这个凭证**；（2）**生成新凭证并更新到正确的位置**（不再进 git）；（3）**审计服务商日志看有没有在我吊销前被人使用**。做完这三步后再回来告诉我，我再帮你做 git 层的历史清理。**清理只是辅助——泄漏一旦发生，唯一有效的止损是让 key 失效**。」
- 「（吊销完 API key 后）帮我用 `git filter-repo --path <文件路径> --invert-paths --force` 从整个历史里删除这个文件。**执行前再次确认**：（1）已吊销凭证；（2）已通知所有协作者接下来他们需要重新 clone；（3）已备份当前远端（`git clone --mirror` 到本地一份）。执行完之后 `git push --force`（这是极少数必须裸 force 的场景）。」

**🟡 已推送的错误 merge / commit 撤销**

- 「main 上误合了 PR `#<num>`（merge commit SHA `<sha>`），需要撤销。**因为是共享分支，用 revert 不用 reset**。（1）展示 `git show <sha>` 让我核对；（2）执行 `git revert -m 1 <sha>`（`-m 1` 指定主线 parent）；（3）展示 revert 产生的 diff 让我确认反向改动符合预期；（4）`git push`（普通 push，**不是 force push**）。」
- 「我不小心在 main 上直接 commit + push 了 4 颗 commit（应该开分支的）。恢复流程：（1）从 main 当前 HEAD 建分支 `feature/misplaced-commits` 保住代码；（2）在 main 上用 `git revert --no-commit <old>..<new>` 一次性 revert 这几颗；（3）commit + 普通 push；（4）feature 分支上再 rebase 到干净 main 之后走正常 PR 流程。**每一步执行前展示要跑的命令让我确认**。」

**🟢 detached HEAD 恢复**

- 「我在 detached HEAD 上 commit 过一颗 commit（message 大致是 `<描述>`），然后切走了。用 `git reflog -20` 找到那颗 commit 的 SHA（reflog 里类型是 `commit:` 的行），`git show` 展示让我确认，然后 `git branch rescue/<描述> <sha>` 把它挂上标签。」

**训练用指令（陪练模式）**

- 「给我 10 道场景判断题：给一个具体事故描述（\"我 branch -D 之后想起分支上还有东西\"、\"我 reset --hard 之后丢了工作区改动\"、\"我误 push 了 .env\"、\"我 rebase 完 push 被拒\"、\"我在 detached HEAD 上 commit 后切走\"……）。我要说出：（1）优先级——先做什么；（2）恢复策略——用哪个命令；（3）预防措施——下次怎么避免。你批改并讲评。」
- 「模拟一次 secret 泄漏事件——你扮演 Slack 里的团队 lead，我作为工程师报告刚刚 push 了 .env 到 GitHub。你要按事故响应流程和我对话：先问我什么？什么时候让我做 git 层清理？什么时候让我暂缓？训练我把\"吊销凭证\"作为第一反应而不是\"filter-repo\"。」

---

## 10.13 执行后的世界

| 你说的话 | AI 大概率执行 | `.git/` 里的真实变化 |
|---|---|---|
| \"救回我刚 `-D` 掉的分支 X\" | `git branch X <sha-from-reflog>` | 新建文件 `.git/refs/heads/X`，41 字节。**没有任何提交对象被造出来**——它们本来就在 `.git/objects/` 里躺着。 |
| \"从 fsck --lost-found 里救回那个未 commit 的文件\" | `git show <blob-sha> > <path>` | 读 `.git/objects/<sha 前 2 字符>/<剩余 38 字符>` 这个 blob 对象、把内容写回工作目录。**Git 内部状态零变化**，只有工作目录多了一个文件。 |
| \"rebase 搞砸了，回到之前\" | `git reset --hard ORIG_HEAD` | 读 `.git/ORIG_HEAD`（一个 41 字节的文本文件，保存着 rebase 开始前的 HEAD SHA）；`.git/refs/heads/<current>` 挪回那个 SHA；工作目录和暂存区都重置到那个 SHA 对应的快照。rebase 产生的新 commit 对象**仍然留在 objects 里**（30 天托管期）。reflog 加一条 `reset: moving to ORIG_HEAD`。 |
| \"force push 覆盖了共享分支，让小李恢复\" | 小李本地 `git push --force-with-lease origin <branch>` | 远端 `refs/heads/<branch>` 从你 rebase 后的新 SHA 挪回小李本地的旧 SHA。远端 objects 里你 rebase 造的新 commit **仍在**（远端 gc 前）。远端服务器的 reflog 记录：`<branch>: force-update from <你的 SHA> to <小李的 SHA>`。 |
| \"revert 那颗 merge commit\" | `git revert -m 1 <sha>` | `.git/objects/` 里**新增一颗抵消 commit**——它的 tree 是\"main 合并前的状态\"、parent 是 merge commit（即当前 HEAD）、message 是 `Revert "Merge pull request #..."`。`.git/refs/heads/main` 前移 1 格。原来那颗 merge commit **原样保留在 log 里**——它和它的 revert 一起构成\"合过又撤了\"的完整证据。 |
| \"救回 detached HEAD 上 commit 后切走的那颗珠子\" | `git branch rescue <sha-from-reflog>` | 新建文件 `.git/refs/heads/rescue`，41 字节。那颗孤儿珠子从\"unreachable\"变成\"reachable\"，脱离 30 天倒计时。 |
| \"用 filter-repo 清除历史里的 .env\" | `git filter-repo --path .env --invert-paths --force` | **`.git/objects/` 里全部 commit 对象被重新造一遍**（tree 里删掉了 .env、parent 相应变化、SHA 全变）；所有分支 ref 挪到新 SHA；旧的 commit 对象**理论上都会留在 objects 里**但 filter-repo 默认会重新打包 + 清理引用。**这是本章唯一会\"真的改动几乎所有 SHA\"的操作，红色**。 |

看懂这张表你会最终确认本章的核心：**除了 filter-repo 那一行（红色）之外，所有的\"事故救援\"物理上都归结为\"挪一挪 refs 指针 + 读一读 reflog\"——本身零副作用、零风险**。**在你救援时手抖的那一秒，你实际上做的物理动作，是 41 字节文本文件里 40 个字符的替换**。这就是 Git 事故恢复哲学的物理底：**它极少扔东西，所以你极少能真的把事情搞砸**。

---

## 10.14 命令侧栏

```
诊断类（只读，事故当下先跑）
git status                          # 看工作区状态
git log --oneline --all -30         # 看当前所有分支上的项链
git reflog --date=iso -50           # 看最近 50 次 HEAD 移动
git branch -av                      # 看所有本地和远程分支的当前位置
git fsck --lost-found               # 列出所有 unreachable 对象（孤儿珠子）

分支救援
git branch <name> <sha>             # 把孤儿珠子挂回一张标签
git branch rescue/<描述> <sha>      # 给孤儿珠子起个描述性名字

reset 之后救援
git reset --hard ORIG_HEAD          # 一键回到上次 merge/rebase/reset 之前
git reset --hard <sha-from-reflog>  # 精确回到某个历史位置

rebase 救援
git rebase --abort                  # rebase 进行中时的天然撤销键
git cherry-pick <sha>               # 把某颗珠子复制到当前项链

blob 救援（找回未 commit 的文件）
git show <blob-sha>                 # 展示某个 blob 的内容
git show <blob-sha> > <path>        # 把 blob 内容还原成文件

共享分支撤销（永远用 revert，不用 reset）
git revert <sha>                    # 撤销一颗普通 commit
git revert -m 1 <sha>               # 撤销一颗 merge commit（-m 1 指定主线）
git revert <old>..<new>             # 撤销一段范围（不含 <old> 自己）
git revert --no-commit <a>..<b>     # 撤销一段但不自动 commit（一次性 commit）

force push 救援（分布式副本兜底）
# 从有干净 clone 的同事那台机器上：
git push --force-with-lease origin <branch>

远端历史清理（红色，谨慎）
git filter-repo --path <file> --invert-paths --force
git push --force --all              # 清理完之后必须 force 推所有分支
```

不需要背。事故当下回来看，或者让 AI 翻译人话。

---

## 10.15 本章小地图

```
Git 事故恢复哲学
  │
  ├─ Git 极少扔东西
  │   ├─ 造过的对象 → objects/ 里躺着
  │   ├─ 挪过的 HEAD → reflog 里记着
  │   └─ 默认 30 天托管期
  │
  ├─ 唯一真丢：从没被 git 记录过的东西
  │   └─ reset --hard 之前的未 add 改动
  │
  └─ 慌乱是第二次伤害
      └─ 事故第一小时清单：别关终端 / 别再敲命令 / 先 fetch / 叫 AI 读 reflog

事故恢复决策树（第一问）
  │
  └─ 这颗珠子被 push 到远端过吗？
      │
      ├─ 否 → 事故在本地
      │      → reflog 是主武器
      │      → 90% 一条命令搞定
      │
      └─ 是 → 事故到远端
             │
             ├─ 还有别人 clone 未污染 → 从他手上恢复
             ├─ secret 已扩散 → 立即吊销凭证（第一优先级）
             └─ 都没有 → revert 而不是回退

8 大事故剧本 · 一句话记忆
  1. 误删分支             → reflog + git branch <name> <sha>
  2. reset --hard 抹工作区 → fsck --lost-found（未 add 的诚实认输）
  3. rebase 弄丢提交       → ORIG_HEAD / reflog / cherry-pick
  4. force push 覆盖远端   → 从同事 clone 恢复（叫团队）
  5. 误提交敏感文件        → 先吊销凭证，再谈 git（红色事故）
  6. merge 错了已推        → revert -m 1（不是 reset）
  7. detached HEAD 切走    → reflog + git branch rescue <sha>
  8. 误改 main 已 push     → revert + 分支保护补丁

三大安全习惯（黄色操作前必做）
  1. git branch backup/<描述>-$(date +%Y%m%d-%H%M%S)
  2. git reflog（心里对当前状态有底）
  3. 未提交改动？先 stash --include-untracked
```

**三大典型误解拆解**

1. **\"git reflog 什么都能救回。\"** ——**几乎**什么都能，但不是\"什么都\"。**从没被 `git add` 过的工作区改动，reflog 救不回来**——它们在 Git 视野之外，没有 blob 被造过、没有 ref 被移动过、reflog 里没有痕迹。**这类损失只能靠编辑器的 Local History、系统级快照、或者\"吃一堑长一智\"**。**准确的说法应该是**：\"reflog 救得回 Git 见过的任何东西，从未见过的救不回\"——这条精细分界是本章要教给你的第一个直觉。
2. **\"删分支/reset/rebase 都是危险操作，不到万不得已别用。\"** ——**恰好相反**。**在本地、在你自己的分支上，这些都是廉价、安全、鼓励的操作**——因为它们**物理上都是\"造对象 + 挪引用\"，reflog 记账 + 30 天托管**。**它们变成\"危险\"，仅当它们跨过\"共享\"和\"远端\"这两条线**——rebase 一条只有你自己的 feature 分支，你可以每天做十次；rebase 一条三个人在协作的共享分支，那是马上要惹祸的操作。**别把\"命令危险\"和\"上下文危险\"混为一谈**。本章 8 个剧本里最严重的两个（#4 force push 灾难、#5 敏感文件泄漏）——都是命令本身没错，是**上下文**（共享 / 已 push / secret 敏感）让它们变严重。
3. **\"误 push 了 .env？——赶紧 filter-repo 清历史！\"** ——**顺序错了**。**第一件该做的事永远是\"吊销那个凭证\"**——因为你 push 上去的那一秒起，必须假设 key 已经被 secret 扫描机器人拿走。之后所有 git 层的清理（amend、filter-repo、BFG）**只是止损未来泄漏，不能救已经泄漏的部分**。**很多团队第一反应是 filter-repo 而不是 revoke，几小时后才发现有异常调用，账单几万美元**——这就是顺序错了的代价。**记住：secret 泄漏是安全事件，不是 git 事件。先按安全事件流程处理，再谈 git**。

---

## 10.16 下一章预告

到这里，你已经具备了应对**几乎所有 Git 事故**的心理防线和救援武器。你知道 Git 极少扔东西、reflog 是你的隐形保险丝、事故第一小时该做什么和不该做什么、八个高频剧本每一个都有稳定的救援路径。

**但本章讲的这些事故——尤其是剧本 4（force push 覆盖共享分支）、剧本 5（敏感文件泄漏）、剧本 8（误改 main）——都有一个共同的\"上游\"：它们在\"团队协作\"这一层就该被预防**。**分支保护、PR 流程、代码评审——这些不只是\"工程规范\"，它们本质上是\"事故的服务端防火墙\"**。

**第 11 章《团队协作：Fork、PR 与代码评审》**：把 Git 从\"你一个人的工具\"升级到\"团队通信协议\"这一层。为什么 Fork/PR 不是 git 命令而是**平台特性**？如何让 AI 帮你起草 PR 描述、按 review 意见迭代？为什么 commit-msg hook 和 Conventional Commits 是团队通信协议的语法基石？如何用分支保护 + required review + CI green 三件套构建\"就算某个团队成员失手也不至于炸\"的服务端防线？**读完第 11 章你会发现——本章的 8 个剧本，其中 5 个都可以在第 11 章讲的层面被结构性预防**——从\"救火\"升级到\"防火\"，才是本书\"AI 时代 Git\"这个主题的真正压轴。

---

> **🤖 AI 指令箱 · 本章实战演练**
>
> 找一个你自己的**沙盒**仓库（**不要**用生产仓库！这些练习会故意搞坏），按顺序执行下面这几组\"事故模拟\"。**每一组做完对着本章的救援步骤把它救回来**——救援时**必须**先跑 `git reflog` 打印现场，再执行任何有副作用的命令。
>
> - **模拟事故 1 · 误删分支**：「造一个仓库，main 上 5 颗 commit。开分支 experiment，上面再造 3 颗 commit（**不合并回 main**）。切回 main，`git branch -D experiment`。**现在把 experiment 分支救回来**——用 reflog、`fsck --lost-found`、`git branch <name> <sha>` 三步。展示救回后的 log 和救援前的 log 完全一致。」
> - **模拟事故 2 · reset --hard 混合场景**：「造一个仓库，先造几颗 commit，然后：（a）在工作区改文件 A（**不 add**）；（b）改文件 B 并 `git add`（**不 commit**）；（c）改文件 C 并 `git add && git commit`（一颗新 commit）。现在跑 `git reset --hard HEAD~1`。**分别救回 A、B、C**——你会发现：C 用 reflog 秒救；B 用 `fsck --lost-found` + `git show <blob> > B` 能救；**A 救不回**（因为 Git 从没见过它）。把这个\"实操区分\"的结果记住——它是本章最重要的直觉。」
> - **模拟事故 3 · rebase 走岔**：「造一个仓库，main 上 3 颗 commit。开 feature 分支，上面 6 颗 commit。故意让其中第 3 颗和 main 上一颗改同一行（制造冲突）。`git rebase main`。在第 3 颗冲突时**故意选错边**（保留 main 那侧、丢弃你自己那侧）、continue 到底。跑 `git log --oneline main..HEAD`——你会发现 log 变了但代码丢了一颗的改动。**现在两种方式各救一次**：（a）`git reset --hard ORIG_HEAD` 整个回退；（b）`git cherry-pick <lost-sha>` 只补回丢的那颗。对比两种方式最终 log 和代码状态的差异。」
> - **模拟事故 4 · 敏感文件泄漏演习**（**用测试仓库、用假 key**！）：「造一个仓库，写一个假的 `.env` 文件（内容随便写一个\"看起来像 API key 但绝对不是真的\"的字符串）。`git add .env && git commit -m "feat: 接入 API" && git push`（推到你自己的测试仓库）。**现在按本章剧本 5 的步骤演一遍完整应急**：（1）（假装）吊销那个 key + 生成新的 + 更新到 .env.local；（2）加 .gitignore；（3）`git rm --cached .env`；（4）`git commit --amend --no-edit`；（5）`git push --force-with-lease`（因为是测试仓库、只有你一个人，允许 force）。感受一下\"先吊销后清理\"这个顺序在肌肉记忆里的份量。」
> - **模拟事故 5 · detached HEAD 上的孤儿珠子**：「造一个仓库，main 上 4 颗 commit。`git checkout HEAD~2`——进入 detached 状态。改一个文件，`git commit -m "detached-fix"`——造一颗孤儿珠子。`git switch main`——**注意看 Git 那句\"you are leaving 1 commit behind\"的警告**。然后跑 `git log --oneline --all`——找不到那颗 detached-fix。**现在用 reflog 救回来**：找到 SHA、`git branch rescue/detached-fix <sha>`。切到 rescue 分支确认那颗珠子活着。」
>
> **五个练习总用时 30-40 分钟，做完你会发现——之前让你半夜惊坐起的\"Git 事故\"，绝大多数在本章的剧本里都是\"三行命令 + 一次人工确认\"就能解决的家常事**。**这就是本章的最终交付**：**从\"事故 = 灾难\"的心理模型，升级到\"事故 = 例行公事\"的心理模型**。
