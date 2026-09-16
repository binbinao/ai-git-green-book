# 第 13 章　进阶概念：小地图上没画的路

> 《Git 的概念地图》第 13 章 · 进阶稿 v1.0
> 前面十二章走完了主干：五张地图 + 六个场景 + 一道安全防线。这一章走的是**地图边缘那些细小的路**——不常用，但一旦遇到，你至少要知道它通往哪里。

---

## 13.1 场景引入：地图边缘那些没标注的岔路

翻回你手边的这张地图。仓库、提交、分支、远程、历史——五个大区都在，从主干到共享分支的黄金规则也都画上了。你甚至已经知道怎么在冲突面前不慌、怎么在 reflog 里救回昨天的 commit。

然后有一天，同事发过来一个 PR，说：「你看能不能只把里面那颗 `feat: 支持 SSO` 的提交摘出来先合进主干，其他几颗后面再说？」

你愣了一下。**摘出来**？摘哪儿？

或者是这样的时刻：CI 突然爆红。你 `git log` 一看，一周内 47 个 commit，红的是哪个引起的？一个个 checkout 回去试？

再或者：项目里冒出了一个 `.gitmodules` 文件、一个奇怪的 `libs/vendor-sdk/` 目录——`cd` 进去 `git log` 显示的是完全不同的一段历史，你被拽进了另一条项链。

这些都是**地图上没画、但迟早会撞上**的路。它们的共同特点是：单个概念很小、单独用不难，但因为你不知道\"这个概念在地图上的位置\"，遇到时容易紧张。这一章挨个走一遍，每一节都按熟悉的节奏来——**祛魅 → 场景 → AI 指令**——但节奏更紧凑，不再展开成一整章。

八条小路，覆盖你后半辈子 90% 会遇到的\"进阶时刻\"：

1. **stash**：抽屉里的暂存珠子
2. **cherry-pick**：从别人的项链上摘一颗过来
3. **bisect**：二分查找那颗\"坏珠子\"
4. **tag**：一张钉死的标签，和分支不是一个物种
5. **submodule vs subtree**：把别人的项链挂进你的项链
6. **sparse-checkout / partial clone**：只要项链的一段
7. **git gc / 对象库维护**：为什么仓库越来越慢
8. **detached HEAD 再访**：从\"正常工作状态\"视角

走完这八条，你手上的地图就真的完整了。

---

## 13.2 stash：抽屉里的暂存珠子

### 祛魅

**stash 是 Git 给你的一个抽屉**——把工作目录里未提交的改动打成一个小包，塞进抽屉里，工作目录立刻恢复干净。抽屉本身在 `.git/refs/stash` 里，是一条独立的引用链——**它是一个栈**（LIFO：后进先出）。

打开抽屉看看：

```
$ git stash list
stash@{0}: WIP on feature/user-profile: a1b2c3d 修改注册接口
stash@{1}: WIP on main: e4f5g6h 加日志
stash@{2}: On main: 临时改一下配置
```

**每一个 `stash@{N}` 其实是一颗（有时是两颗）匿名的 commit 珠子**——是的，本质上还是珠子，只不过它的 parent 是当时的 HEAD，名牌叫 `stash`。没有分支指向它，但 `refs/stash` 这条引用链保管着它。所以第 5 章讲的\"珠子不可变、reflog 保底\"那套原理，在 stash 上完全成立。

### 三个动作，语义完全不同

**`git stash push`（或裸 `git stash`）：塞进抽屉。**
把当前未提交的**追踪文件的改动**（tracked）打包成珠子、塞进抽屉、工作目录恢复到 HEAD 的干净状态。**注意**：默认**不包含 untracked 文件**——那些新建的、还没 `git add` 过的文件会留在工作目录里不动。想一起塞进去，用 `git stash push -u`（`-u` = include untracked）。想连 `.gitignore` 的都塞进去，用 `-a`（all）。

**`git stash apply`：从抽屉里拿出来，不动抽屉。**
把 `stash@{0}`（默认取栈顶）的改动应用到当前工作目录，**但抽屉里那份还在**——用完还能再用一次。这是三个动作里最保守、最推荐的默认。

**`git stash pop`：从抽屉里拿出来，同时把抽屉那份销毁。**
先 apply，再 drop（销毁 stash 珠子的引用）。**这是 stash 最出名的陷阱**：如果 apply 时遇到冲突，你可能会看到吓人的输出，误以为 stash 已经丢了；实际上——**冲突时 pop 不会 drop**（Git 保留了 stash 引用等你处理完再手动 drop），但很多人不知道这条规则，在恐慌里 `git stash drop` 或者 `git reset --hard` 一下就真的丢了。**记住：pop 遇冲突时，你的 stash 还在 `git stash list` 里，别急。**

**`git stash drop stash@{N}`：直接销毁某个抽屉格。**
不 apply，直接扔掉——这是唯一一个真会\"减少抽屉里内容\"的动作。

### 什么时候用 stash，什么时候不用

**用**：\"我正在写一个功能到一半，突然 pull 一下想同步主干\"——`git stash && git pull && git stash pop`。这是 stash 的经典甜蜜点：**几十秒内的暂停**。

**用**：\"我要临时切一下分支看眼东西，30 秒后就回来\"——stash 是这种\"眨眼间中断\"的最快容器。

**不用**：\"我要切去修一个可能要 2 小时的紧急 bug\"——第 3 章讲过：**这种场景应该 commit 到 WIP 分支上、或者开 worktree**（第 8 章）。stash 是抽屉不是仓库，堆到 10 个抽屉格你就再也分不清哪个是哪个了。

**不用**：\"这段代码我以后可能会用\"——那你应该起个分支叫 `spike/xxx` 提交进去，别丢进抽屉。抽屉是给\"接下来 10 分钟要接着做的事\"用的。

### 抽屉与 WIP 分支的对比（呼应第 6 章）

第 6 章讲过\"WIP commit 比 stash 更好\"的道理。这里正式对照一下：

| | stash | WIP commit（推荐） |
|---|---|---|
| 存活时长 | 短期（几分钟到几小时） | 任意长（几天几周都行） |
| 是否上远端 | 只在本地 | 可 push（有备份） |
| 是否可命名 | 只能加简短 message（`stash push -m`） | 有完整 commit message |
| 是否可 diff | `git stash show -p` | 正常 `git diff` |
| 冲突恢复 | pop 冲突时容易慌 | rebase / merge 正常流程 |
| 团队可见性 | 完全私密 | push 后队友可见 |

**结论**：**除了那种\"我 30 秒内就回来\"的最短暂停，都用 WIP commit 而不是 stash**。这不是审美偏好，是可靠性——stash 是 Git 里为数不多的\"没有安全网\"的操作（reflog 覆盖不到 stash 独立的引用链，虽然它自己也有 `stash reflog`）。

### AI 指令箱 · stash

**🟢 探索类**

- 「列一下当前仓库的 stash 全部：每一个 stash 的编号、message、创建时间、影响的文件数、以及基于哪个分支哪颗 commit。用中文表格给我。」
- 「展示 `stash@{0}` 里的具体改动 diff。之后告诉我：这些改动如果 apply 到当前分支，大概会不会冲突（对比一下当前 HEAD 里对应文件的状态）。」

**🟡 恢复类（有可能冲突）**

- 「把 `stash@{0}` 用 `apply` 应用到当前工作目录——**不要 pop**。执行前告诉我：如果冲突了你会停下来、不会自作主张 drop 掉这个 stash。」
- 「我刚才 `git stash pop` 了，遇到冲突。告诉我：（1）这个 stash 现在有没有从 list 里消失（应该没有）？用 `git stash list` 确认；（2）冲突具体是哪几个文件的哪几行；（3）解决完之后要不要手动 `git stash drop`，什么时候 drop 才安全。」

**🟡 清理类**

- 「列出所有 stash，标出每一个的创建时间。超过 30 天的算\"僵尸抽屉\"——挨个展示它们的 diff summary，让我逐个决定是 drop 还是恢复成一个分支保存。**不要批量 drop**。」

---

## 13.3 cherry-pick：从别人的项链上摘一颗过来

### 祛魅

**cherry-pick 就是把某一颗珠子的改动，复制一份、串到你当前项链的末端。** 一句话讲完。

物理动作和 rebase 里的\"重放一颗\"是**完全一样的**：

1. 取目标 commit 相对它 parent 的 diff。
2. 把这个 diff 应用到当前 HEAD 上。
3. 造一颗**新珠子**，parent 是当前 HEAD，改动内容和目标 commit 一样（可能会有微小差异，比如 message），**SHA 完全不同**。

```
cherry-pick 之前：
   main:      ...─▶ (A) ─▶ (B) ─▶ (C)          ← HEAD
   feature:   ...─▶ (X) ─▶ (Y) ─▶ (Z)
                            ▲
                          要摘的珠子

cherry-pick Y 之后：
   main:      ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (Y')  ← HEAD
                                          ▲
                                        新珠子：内容和 Y 一样，SHA 不同
   feature:   ...─▶ (X) ─▶ (Y) ─▶ (Z)          （Y 原样还在）
```

看清楚了吗？**cherry-pick 造的是新珠子。Y 和 Y' 是两颗不同的 commit——SHA 不同、parent 不同——虽然改动内容一样。**

### rebase 和 cherry-pick 的关系

现在把第 5 章讲的 rebase 拿过来对比：

**rebase 的本质，就是批量 cherry-pick。**

`git rebase main` 在 feature 分支上做的事，用 cherry-pick 语言讲，就是：

1. 记下 feature 从共同祖先到末端每一颗珠子的改动。
2. 把 feature 名牌暂时挪到 main 的末端。
3. **依次 cherry-pick 每一颗珠子**——一颗、一颗、一颗地重放。
4. feature 名牌停在最后一颗新珠子上。

这不是比喻，是**字面上的物理事实**。Git 内部实现里，`rebase` 就是循环调用 cherry-pick 逻辑。**所以 rebase 遇到冲突的行为——一颗一颗停、`--continue` 一颗一颗过——才和 cherry-pick 遇到冲突时长得一模一样**（`git cherry-pick --continue` / `--abort` / `--skip`，接口都对得上）。

**记住这条对应关系，你就不需要\"额外理解\" cherry-pick 了——它就是 rebase 拆成的最小单位**。

### 什么时候用 cherry-pick

**场景一：从别人的 PR 里摘一颗。**
同事的 feature 分支里有 5 个 commit，其中一个是\"顺便修的一个 bug\"，其他四个是他还没做完的功能。你想先把那个 bugfix 合进主干。`git cherry-pick <那颗 SHA>` 把它单独摘到 main 上。**摘完主干先享受修复效果，同事的其他四颗依然在 feature 分支上不受影响。**

**场景二：跨分支热修补（hotfix backport）。**
main 上刚合并了一个 bugfix，客户还在跑上一个 release 分支 `release/v2.3`。你需要把这个 bugfix 也带到 release 分支上。**做法：在 release 分支上 cherry-pick main 上的那颗 bugfix。**

**场景三：把提交搬到正确的分支（第 3 章预告过）。**
你不小心在 main 上直接提交了两颗本该在 feature 分支上的珠子。做法：切到 feature 分支、`git cherry-pick main~1 main`（把最后两颗摘过来），然后回 main、`git reset --hard HEAD~2`（把 main 复原）。**cherry-pick + reset 是错误分支提交的标准修复组合。**

### 使用注意

**注意一：cherry-pick 会造\"内容相同、SHA 不同\"的双胞胎珠子。**
如果之后 feature 分支要合并回 main，Git 通常能识别出\"这颗改动已经在 main 上了\"（通过内容 diff）并跳过——但不总是。特别是被 cherry-pick 那颗珠子如果后来又被修改过，合并时可能出现\"看起来是同一件事\"的冲突。**遇到这种冲突不要慌，通常两侧选一边即可。**

**注意二：合并 commit 的 cherry-pick 需要指定 parent。**
merge commit 有两个 parent，`git cherry-pick <merge-sha>` 会失败（因为 Git 不知道要按哪个 parent 算 diff）。你需要 `-m 1` 或 `-m 2` 明确指定：\"以第几个 parent 为准算差异\"。**日常用得少，遇到时知道去 `-m` 就行。**

**注意三：cherry-pick 一段范围。**
`git cherry-pick <A>..<B>` 会依次摘 A 之后到 B 的每一颗（不含 A、含 B）。**这就是一个小范围的 rebase**——上面讲过它俩本来就是同一件事。

### AI 指令箱 · cherry-pick

**🟢 探索类**

- 「同事的 feature/xxx 分支上有 5 个 commit，帮我列出来（SHA、message、影响文件）。我告诉你想摘哪几颗，你先展示这几颗合到当前分支上的 diff preview，让我确认。」

**🟡 摘取类**

- 「把 `<SHA>` 这颗 commit cherry-pick 到当前分支。执行前展示这颗 commit 的完整改动、以及应用到当前 HEAD 上会不会冲突。如果冲突，停下来让我处理，不要用 `-X ours` / `-X theirs` 自动选边。」
- 「把 main 上最近的这颗 bugfix `<SHA>` backport 到 `release/v2.3` 分支。步骤：（1）切到 release/v2.3；（2）先建 backup 分支；（3）cherry-pick 那颗；（4）检查有没有冲突；（5）冲突有就停下来。**不要一口气 push 到远端。**」
- 「我在 main 上误提交了最后 2 颗 commit，它们本该在 feature/abc 上。修复方案：切到 feature/abc、cherry-pick main 的最后 2 颗、然后把 main reset --hard 到那 2 颗之前。执行前告诉我每一步的 before/after，并在动 main 之前停下来让我确认。」

---

## 13.4 bisect：二分查找那颗坏珠子

### 祛魅

**bisect 就是二分查找**。目标：在一段项链里，找出\"哪颗珠子第一次引入了某个问题\"。

物理动作：

1. 你告诉 Git 一颗**已知坏的**珠子（比如 HEAD）、一颗**已知好的**珠子（比如三周前的某颗 tag）。
2. Git 计算这两颗之间的中点，checkout 到那颗（进入 **detached HEAD** 状态——本章后面还会再谈这个）。
3. 你手动或跑测试判断这一颗好还是坏，告诉 Git（`git bisect good` 或 `git bisect bad`）。
4. Git 根据你的答案缩小一半范围，checkout 到新的中点。
5. 循环。

对 N 颗珠子的范围，最多 log₂(N) 轮就能定位到那颗\"第一次坏掉的\" commit。**1000 颗珠子只要 10 轮**——比人肉一颗一颗试快得离谱。

### 一次 bisect 的样子

```
$ git bisect start
$ git bisect bad HEAD              ← 当前是坏的
$ git bisect good v2.3.0           ← 三周前的这个 tag 是好的
Bisecting: 47 revisions left to test after this (roughly 6 steps)
[a1b2c3d] 优化数据库连接池

# Git 已经 checkout 到中点。跑测试：
$ pytest tests/test_login.py
FAILED

$ git bisect bad
Bisecting: 23 revisions left to test after this (roughly 5 steps)
[e4f5g6h] 增加用户偏好设置

# 继续：
$ pytest tests/test_login.py
PASSED

$ git bisect good
Bisecting: 11 revisions left to test after this (roughly 4 steps)
...

# 大约 7 轮后：
[i7j8k9l] 修改 session 中间件
i7j8k9l is the first bad commit

$ git bisect reset                 ← 结束，HEAD 回到 bisect 开始前
```

**找到了**——`i7j8k9l` 是第一次让 test_login 失败的珠子。看它的 diff，通常一眼就能看出问题。

### AI 时代的 bisect：让 AI 帮你跑

bisect 的物理逻辑非常适合自动化——每一轮你要做的就是\"跑测试、判断好坏\"。Git 内置了 `git bisect run <script>` 支持这个：

```
git bisect start HEAD v2.3.0
git bisect run pytest tests/test_login.py
```

Git 会自动 checkout 每个中点、跑测试、根据 exit code 判断、缩小范围、继续，**你去喝杯咖啡回来看结果**。exit code 的语义要记准：**0 = good；1–127（除 125）= bad；125 = 这颗测不了、跳过；其余退出码（≥128 等）直接中止整个 bisect**。所以 bisect run 的测试脚本里，**用 `exit 125` 表示"这颗没法测"**（编译不过、环境起不来就返回它）；手动一轮一轮跑时，等价命令是 `git bisect skip`。

**这也是 AI Agent 特别擅长的场景**：告诉 AI\"这段项链里某颗引入了 bug，症状是 X\"，AI 会自动跑 bisect、自动写测试脚本判断好坏、自动 checkout 每一轮、最终给你一个\"就是这颗\"的答案。**bisect + AI 是绿色区里最漂亮的一对组合**：AI 干重复劳动，你判断最终诊断结果。

### 使用注意

**注意一：bisect 期间你处于 detached HEAD。**
每一轮 checkout 都是 detach。别在里面提交东西——bisect 结束时那些提交会成\"无主孤珠\"。有 reflog 兜底，但没必要。

**注意二：`good` / `bad` 是相对的。**
你也可以用它找\"哪颗第一次修好了 bug\"——把\"修好\"标记成 `bad`、\"还坏\"标记成 `good`。语义反过来但机器不管，只关心边界。

**注意三：bisect 需要一段\"有明确好坏边界\"的历史。**
如果历史里到处都是\"编译不过\"、\"测试跑不起来\"的中间态，bisect 会一直得到\"无法判断\"（skip），效率骤降。**这也是保持 main 常绿（每颗都能跑测试）的一个隐性好处：不常 bisect，需要 bisect 时无痛。**

### AI 指令箱 · bisect

**🟢 启动类**

- 「用 `git bisect` 找出第一次让 `tests/test_login.py::test_login_flow` 失败的 commit。已知 HEAD 是坏的、tag v2.3.0 是好的。用 `git bisect run pytest tests/test_login.py::test_login_flow` 自动化。跑完把结果那颗 commit 的 diff 和 message 展示给我，并给出你对根因的判断。」
- 「我知道现在的 main 有个 UI bug（按钮点击没反应），但我没有自动化测试可以判断。帮我准备一个 bisect 剧本：每一轮 checkout 后你告诉我 checkout 到了哪颗、这颗的 message，我手动测试并告诉你 good/bad，你继续下一轮。跑完给出第一颗坏的珠子。」

**🟡 收尾类**

- 「bisect 结束了。现在：（1）跑 `git bisect reset` 回到原位置；（2）展示那颗被定位的 commit 的完整 diff；（3）判断问题最可能出在哪几行；（4）建议下一步（revert / 修一下 / cherry-pick 到 hotfix 分支）。」

---

## 13.5 tag 深入：一张钉死的标签

### 祛魅

第 3 章讲过：**分支是可移动的指针**。tag 呢？**tag 是钉死的指针**——理论上一旦挂在某颗珠子上就不再动。

物理位置：`.git/refs/tags/<name>`。看起来和分支的 `.git/refs/heads/<name>` 完全对称——都是一个文件、里面一行 SHA。**在 Git 的引用系统里 tag 和分支是同一等公民，只是约定不同**：分支跟着提交前移，tag 保持钉死。

### 两种 tag：轻量 vs 附注

Git 里有两种 tag，长得像但实际不是一回事。

**轻量标签（lightweight tag）**：
```
git tag v1.0
```
就是往 `refs/tags/v1.0` 里写一行 SHA，指向当前 HEAD。**没有额外信息**——没有 tagger、没有时间、没有 message。它就是一个别名，`git log v1.0` 等同于 `git log <那颗 SHA>`。

**附注标签（annotated tag）**：
```
git tag -a v1.0 -m "Release 1.0"
```
`refs/tags/v1.0` 里存的不是直接指向 commit 的 SHA，而是指向一个**独立的 tag 对象**——那个对象存着：tagger、日期、message、被打标的 commit SHA、可选的 GPG 签名。它是 objects/ 里一颗完整的 Git 对象，和 commit、tree、blob 平级。

**看得出来吗？** `git cat-file -t v1.0`：轻量 tag 返回 `commit`，附注 tag 返回 `tag`。

### 什么时候用哪一种

**规则很直接：发布用附注 tag，个人书签用轻量 tag。**

**用附注 tag**：
- 语义化版本发布（v1.0.0、v2.3.1）——需要 tagger、时间、release notes、GPG 签名的正式发布点。
- CI/CD 触发条件（push a tag → build & deploy）——需要可追溯性。
- 团队里\"这就是我们发出去的那个版本\"的历史锚点——**至少 10 年后还能查\"谁在什么时候标了这个版本、release notes 说了什么\"**。

**用轻量 tag**：
- 你自己的临时书签——「这是我 refactor 前的位置」、「这是我 demo 用的版本」。
- 快速定位一颗 commit 的别名——比长 SHA 好记。

**结论**：**任何要 push 到远端、任何和团队/用户可见的\"版本\"，都用 `-a` 打附注 tag**——多敲两个字符，多 10 年的可追溯性。

### tag vs branch：不同的时机

第 3 章讲了什么时候开分支。这里补一条相邻的判断：**什么时候用 tag，什么时候用 branch？**

**核心区别**：
- **branch 会动**——commit 一次就前移一次，跟着开发。
- **tag 不动**——挂上去之后就是那颗珠子，永远。

**判断规则**：
- **正在开发中的东西 → 分支**：feature、bugfix、experiment，一切还会往前长的都用 branch。
- **发布快照 → tag**：v1.0、v2.3、rc1、beta——这些是历史时刻的锚点，永不移动。
- **需要\"从这个点长出新东西\"→ 分支（可以从 tag 长）**：hotfix 常见流程是「从 tag v2.3 长出 hotfix/2.3.1 分支」——tag 是发布锚，从它长分支去打补丁。补丁完成再打新 tag v2.3.1，hotfix 分支使命结束。

**一句话**：**发布用 tag、开发用 branch。tag 是钉子，branch 是绳子。**

### tag 的一个隐藏陷阱

**tag 默认不随 `git push` 一起推送。** 你打完 tag `git push`——tag 不上远端。想推 tag 要么 `git push origin v1.0`（推特定 tag），要么 `git push --tags`（推所有本地 tag）。

**很多团队 CI 依赖 tag 触发发布**——本地打完 tag 忘了 push，CI 一直等，几分钟后才反应过来。**这是新手最容易踩的 tag 陷阱**，提前知道就不会踩。

### AI 指令箱 · tag

**🟢 探索类**

- 「列出仓库里所有的 tag：区分轻量和附注、按时间排序、每一个显示 tagger（如果有）、message（如果有）、指向的 commit message。」
- 「当前 HEAD 距离最近的 tag 有多少颗 commit？(`git describe` 的语义)。如果我现在打 tag，按语义化版本推断，下一个版本号应该是什么？」

**🟢 打标类（正式发布）**

- 「用附注 tag 给当前 HEAD 打上 v1.2.0。tagger 用我 config 里的信息，message 用最近 15 个 commit 生成的简明 changelog（按 feat / fix / chore 分组）。打完展示 `git show v1.2.0`。之后**停下来问我要不要 `git push origin v1.2.0`**——别自动 push。」

**🟡 清理类**

- 「本地有一些废弃的实验 tag（比如 `wip-*`、`temp-*`）。列出来让我确认要不要删。批量删除本地 tag：`git tag -d`。**不动远端 tag**——远端 tag 是团队约定，不由我单方面清理。」

---

## 13.6 submodule vs subtree：把别人的项链挂进来

### 场景

你的项目要用一个内部 SDK，SDK 有自己独立的 git 仓库。选择有三种：（1）拷贝粘贴 SDK 的代码进你的项目；（2）用包管理器（npm / pip / maven）把它当依赖；（3）**把 SDK 那条项链挂进你自己的项链**——这就是 submodule 和 subtree 干的事。

**通常你的第一选择应该是包管理器**——它是为\"依赖别人的代码\"专门设计的，工具生态成熟。submodule 和 subtree 是\"当包管理器不适用时\"的备胎。

### submodule：挂一个链接

**submodule 的本质**：主仓库里存一个**指针**，指向子仓库某颗特定 commit 的 SHA。

物理上：
- 项目根目录多一个 `.gitmodules` 文件，记录\"这个路径挂着哪个远程仓库\"。
- `libs/vendor-sdk/` 这个目录**在主仓库的 tree 里被登记为一个特殊的 \"gitlink\" 对象**——不是普通的 tree，是一个 SHA 指针。
- `libs/vendor-sdk/` 目录本身其实是一个**独立的完整 git 仓库**（有自己的 `.git`），checkout 在那个指针指向的 commit 上。

```
主项目：       ...─▶ (A) ─▶ (B) ─▶ (C)      ← main
                              │
                              └─ 里面登记着：libs/vendor-sdk 挂在子项目的 X 上

子项目：       ...─▶ (X) ─▶ (Y) ─▶ (Z)      ← 子项目自己的 main
                    ▲
                  被登记的位置
```

**主仓库 commit 记录的是\"当时子仓库应该在哪颗 commit 上\"**。别人 clone 主仓库时，需要额外 `git submodule update --init --recursive`，Git 才会把子仓库拉下来 checkout 到指定 commit。

### 为什么 submodule 会痛苦

四个真实痛点：

1. **clone 忘记 `--recursive`**：clone 完发现子模块目录是空的、构建挂了。**每个新人第一次都会踩**。
2. **`cd libs/vendor-sdk`（进入子仓库）修一下代码提交——子仓库前移了，主仓库还指着旧的 SHA**。你要**在主仓库里也提交一次\"更新 submodule 指针\"**。忘掉这一步，队友那里子模块就是旧的。
3. **子模块目录里天然是 detached HEAD**（因为主仓库指定的是某颗 SHA、不是某个分支）。想在里面正常开发要手动 checkout 一个分支。第一次遇到会被吓到。
4. **子模块的分支切换**——主仓库切分支时子模块可能被留在错误位置，需要 `git submodule update`。**没有一个团队成员不曾在这里搞出过混乱**。

### 什么时候还是得用 submodule

尽管痛，有几种场景 submodule 是最佳选择：

- **同一家公司多个内部仓库需要严格版本 pinning**——包管理器成本高、submodule 一步到位。
- **子仓库有独立生命周期、独立 CI、独立发布**——不适合内联进主仓库。
- **需要\"精确锁定到某颗 commit\"的可追溯性**——submodule 天然做到（主仓库的历史里记录了每次子模块指针的变化）。

**一句话**：**submodule 是\"两个独立仓库通过指针弱耦合\"的方案**。它的痛点几乎全部源于\"两个仓库\"这个事实——痛的是协调成本，不是 Git 有 bug。

### subtree：把内容合并进来

**subtree 走的是另一条路**：**把子仓库的内容合并进主仓库的 tree 里**。合并之后主仓库看起来就像自己天生就有那些代码，没有指针、没有 `.gitmodules`。

物理动作（`git subtree add`）：
1. 从子仓库 fetch 到目标 commit。
2. 把子仓库那颗 commit 的整棵 tree \"合并\"到主仓库的指定子目录下。
3. 造一颗主仓库的 merge commit 记录这次合并。

之后 clone 主仓库的人**什么额外操作都不用做**——那些代码就在 tree 里。想升级子仓库？`git subtree pull`——把上游的新 commit 合并进来。

### subtree 的代价

- **主仓库变大**——因为子仓库的所有历史都真实地存在于主仓库的 objects 里了。
- **推送修改到上游子仓库很绕**——`git subtree push` 需要 Git 把主仓库里那部分子目录的历史\"拆出来\"作为独立 commit 序列推到子仓库，命令繁琐。**大部分团队实际用 subtree 时都是单向的：从上游拉、几乎不反向推**。
- **子仓库的独立性丢失了**——你不再能\"精确知道当前是子仓库的哪颗 commit\"（虽然 subtree 的 commit message 里会记录）。

### 对比与选择

| 维度 | submodule | subtree |
|---|---|---|
| **物理结构** | 主仓库里存 SHA 指针 | 主仓库里直接包含子仓库内容 |
| **clone 体验** | 需要 `--recursive` | 什么都不用做 |
| **主仓库大小** | 只多一个指针（小） | 增加子仓库全部历史（大） |
| **修改子仓库** | 进子目录、单独提交、主仓库更新指针 | 直接改、正常主仓库提交 |
| **升级子仓库** | `git submodule update --remote` | `git subtree pull` |
| **反向推给上游** | 直接 push 子仓库（正常操作） | `git subtree push`（繁琐） |
| **detached HEAD 问题** | 天然会遇到 | 无 |

**建议**：
- **首选包管理器**（npm / pip / maven / cargo / go mod）——生态成熟。
- **公司内部多仓库、包管理器不方便** → **submodule**（接受痛点）。
- **偶尔要 vendor 一份第三方代码进主仓库、不打算频繁反推上游** → **subtree**。
- **不想学这两个** → 直接拷贝粘贴（叫 \"vendoring\"）——加个 README 说明来源和版本，也是合理选择。

### AI 指令箱 · submodule / subtree

**🟢 探索类**

- 「这个仓库有没有用 submodule 或 subtree？如果有，列出：每一个的路径、指向的远程仓库、当前 pin 在哪颗 commit、是不是最新。」

**🟡 操作类（涉及子仓库状态，先看后做）**

- 「更新 `libs/vendor-sdk` 这个 submodule 到远端最新 main。步骤：（1）fetch 子仓库；（2）在子仓库里 checkout main；（3）回到主仓库；（4）`git add libs/vendor-sdk` 把新指针提交进主仓库；（5）展示主仓库 diff 让我确认再 commit。」
- 「我 clone 完发现 `libs/vendor-sdk` 是空的。用 `git submodule update --init --recursive` 初始化。完成后展示 `libs/vendor-sdk` 里的 `git log -1` 确认版本正确。」

---

## 13.7 sparse-checkout 与 partial clone：只要项链的一段

### 场景

有一天你要在一个 10GB 的 monorepo 里工作。你其实只关心其中一个前端子目录，200 MB 大小。**你需要把整个 10GB 都拉下来吗？**

不需要——Git 给了两种\"减负\"武器：**sparse-checkout**（只 checkout 一部分文件）和 **partial clone**（只下载一部分对象）。它们经常一起用。

### sparse-checkout

**动作**：**主仓库完整拉下来，但只在工作目录里展开一部分文件**。`.git/` 里所有对象都在，但你磁盘上的\"可见文件\"只有你指定的路径。

```
git clone <repo>
cd <repo>
git sparse-checkout init --cone
git sparse-checkout set frontend/ shared/
```

**结果**：`frontend/` 和 `shared/` 两个目录里的文件正常出现，其他所有目录里的文件都不出现在工作目录里。但 `git log`、`git diff`、`git blame` 全部功能正常——因为 objects 都在。

**用途**：
- 大 monorepo 里只做前端 → 只 checkout 前端目录，构建/搜索/编辑器全部飞快。
- 只关心某个子系统 → 减少认知负荷（\"我看不到的目录，就不会分心去想\"）。

**限制**：磁盘上 `.git/` 依然是全量的——sparse-checkout **只是让工作目录变小，不让仓库变小**。

### partial clone

**动作**：**clone 时就只下载一部分对象**——通常是\"跳过 blob\"（`--filter=blob:none`），等真正需要某个文件的内容时再按需拉取。

```
git clone --filter=blob:none <repo>
```

**结果**：`.git/objects/` 里只有 commit 和 tree 对象（骨架），没有 blob（文件内容）。你能看到项目结构、能读 log、能看 diff 的\"文件列表\"——但 `cat` 某个文件时 Git 会自动从远端按需拉取那个 blob。

**用途**：
- 超大仓库的初次 clone 从几小时变几分钟。
- CI 环境只需要 checkout 特定文件时，不必拉整个历史的所有 blob。

**限制**：
- 需要仓库托管方支持（GitHub、GitLab、Gitea 现代版本都支持）。
- 完全离线不能工作——很多操作需要按需回连远端。

**通常两个一起用**：`git clone --filter=blob:none --sparse <repo>` 是 monorepo 时代的标准姿势——**只下必要对象、只展开必要文件**。

### 什么时候用

- **仓库超过 1 GB、你只关心其中一部分** → 值得配。
- **仓库几十 MB** → 不折腾，全量 clone 更省心。
- **CI 环境** → sparse + partial 是标配（节约 CI 存储、加速 clone）。

### AI 指令箱 · sparse / partial

**🟢 配置类**

- 「这个仓库有 8 GB，我只关心 `services/user-api/` 和 `shared/`。帮我从头重新 clone 一份，用 partial clone（blob:none）+ sparse-checkout 只展开这两个目录。给出完整命令序列并解释每一步在做什么。」
- 「当前 clone 是全量的。转换成 sparse-checkout 模式，只保留 `services/user-api/` 和 `shared/` 可见。执行前告诉我：这个操作会不会丢数据（应该不会——只影响工作目录展开范围）。」

---

## 13.8 git gc 与对象库维护：为什么仓库越来越慢

### 祛魅

**gc = garbage collection。** 但 Git 的 gc 不只是\"清垃圾\"，它包含三件事：

1. **打包对象**：把 `.git/objects/` 里散落的\"松散对象\"（每个对象一个文件）打包进 packfile（一个二进制大文件，配一个索引），大幅提升访问速度。
2. **压缩 packfile**：packfile 内部用 delta 压缩——相邻版本的对象只存差异，大幅减小体积。
3. **清理 unreachable 对象**：把\"没有任何引用可以到达\"且\"reflog 过期\"的对象真删掉。

**没跑过 gc 的仓库的三个症状**：
- `git status` 越来越慢。
- `.git/` 目录越来越大（松散对象越堆越多）。
- 有时候 `.git/` 里能看到几万个小文件——文件系统本身开始吃力。

### Git 什么时候自动 gc

**Git 默认会自动 gc**。触发条件（`gc.auto` 默认 6700 个松散对象、`gc.autopacklimit` 默认 50 个 pack）：
- 每次 `git commit`、`git merge`、`git rebase` 等操作之后 Git 会检查，达标就自动跑一次 `gc --auto`。
- **对绝大多数个人仓库你根本不需要手动 gc**——它已经在悄悄跑了。

**你需要手动 gc 的时刻**：

- **仓库明显变慢、变大**：跑 `git gc --aggressive` 做一次深度重打包（`--aggressive` 会用更激进的 delta 算法，慢但压缩率更高）。
- **大量历史被重写之后**（比如批量 rebase、filter-branch、BFG）——旧的对象成了 unreachable，磁盘占用不减。跑 `git gc --prune=now` 立即清理（**注意：它只删得掉已经没有任何引用（含 reflog）指向的对象**。想连 reflog 一起清，要用"reflog expire + gc"两步组合，见下文）。
- **服务端仓库（bare repo）** 通常需要定期跑 gc——bare repo 上没有工作目录操作触发 auto gc，需要 cron。

### 一个常被忽视的操作：`git maintenance`

现代 Git（2.29+）内置了 `git maintenance` 命令，可以配置\"后台定期维护\"：
```
git maintenance start
```
Git 会通过 cron / systemd timer 定期跑：gc、pack-refs、commit-graph 优化、fetch 保温——**装完就可以忘掉**，仓库保持一直很快。

### gc 会不会删掉我需要的东西？

**关键理解**：gc 只清理\"unreachable + reflog 过期\"的对象。第 5 章讲的 reflog 保留期（默认 30 天 unreachable、90 天 reachable）就是这一层保险。

**推论**：
- 只要你还在 30 天内，reflog 里那些看似丢掉的 commit 都在。
- 想立刻清干净（比如误提交了敏感文件想彻底删除）——需要 `git reflog expire --all --expire-unreachable=now` **加** `git gc --prune=now` 两步组合。**这是危险操作**，第 12 章的红黄绿里属于黄色偏红。

### AI 指令箱 · gc 与维护

**🟢 诊断类**

- 「这个仓库的 `.git/` 目录多大？松散对象有多少？packfile 几个？跑一下 `git count-objects -vH`，告诉我需不需要手动 gc。给出判断依据。」

**🟢 维护类**

- 「跑一次常规 `git gc`（不加 `--aggressive`、不加 `--prune=now`），把松散对象打包。跑完展示前后对比：`.git/` 大小、objects 目录里文件数变化。」
- 「配置 `git maintenance` 定期后台维护。告诉我它会做什么、跑的频率、如何关闭。」

**🟡 深度清理（涉及\"真删\"）**

- 「仓库里我不小心提交过一次 20 MB 的日志文件，后来 rebase 掉了，但 objects 还在。目标：让那个 blob 从磁盘上真删除。步骤：（1）确认 reflog 里没有还引用它的位置；（2）用 `git reflog expire --expire-unreachable=now --all`；（3）跑 `git gc --prune=now`；（4）展示前后 `.git/` 大小。**执行前先备份整个仓库目录到 /tmp**。」

---

## 13.9 detached HEAD 再访：正常工作状态下的\"临时\"

### 呼应第 3 章、第 10 章

第 3 章从**祛魅**角度讲了 detached HEAD：不是错误状态，是 HEAD 直接按住一颗珠子的姿势。
第 10 章从**恢复**角度讲了它：\"在 detached 状态里 commit 了没挂名牌，用 reflog 找回。\"

这里从**正常工作状态**的第三个视角讲一下——**什么时候你会（也应该）正常处在 detached HEAD 里？**

### 三种\"正常\"的 detached 场景

**场景一：checkout 一颗历史珠子来\"看看\"。**
```
git checkout v2.3.0
# 或
git checkout <某个 SHA>
```
你只是想\"跑一下三个月前的代码\"、\"看看当时那个 bug 什么样\"、\"给客户复现一下老版本的行为\"——**你不打算在这个位置提交任何东西**。这是 detached HEAD 的**最纯粹用法**。看完 `git switch main` 回来，工作目录恢复到 main 最新，一切干净。

**场景二：bisect 期间。**
上面 13.4 讲的 bisect 每一轮 checkout 都是 detach。你只是**判断 good/bad**，不提交东西。bisect reset 之后 HEAD 回来。

**场景三：rebase 内部状态。**
`git rebase` 执行过程中，Git 会把 HEAD 挪到重放的每一颗新珠子上——那些珠子还没被任何分支指向，本质上就是 detached。**你通常看不到这个中间态**（除非 rebase 停在冲突上让你处理），但它一直在发生。

### 什么时候 detached HEAD 变成\"该挂名牌了\"

**唯一的判断规则**：**如果你在 detached HEAD 上做了任何 commit，先挂名牌再切走**。

Git 会在你切走的那一刻给出警告：
```
Warning: you are leaving 1 commit behind, not connected to any of your branches:
    a1b2c3d 试着修一下那个 bug
If you want to keep it by creating a new branch, this is a good time to do so with:
    git branch <new-branch-name> a1b2c3d
```

**Git 已经把话说到这个份上了**——它在提醒你 SHA 是 `a1b2c3d`、告诉你怎么救。看到这段警告要么救（`git branch <name> a1b2c3d`），要么明确决定不要（那颗珠子进 reflog，30 天内还能救）。

**很多人对 detached HEAD 的恐惧就来自没读这段警告——它其实非常礼貌地告诉你怎么办。**

### AI 指令箱 · detached HEAD

**🟢 探索类**

- 「我现在是不是 detached HEAD 状态？如果是，是通过什么操作进入的（`.git/HEAD` 内容、reflog 最后几条）？我从进入到现在有没有做过 commit（如果有，列出这些 commit 的 SHA 和 message）？」

**🟡 收尾类**

- 「我在 detached HEAD 上做了一些改动想保留。用 `git switch -c rescue/2026-11-XX` 在当前位置挂一张分支名牌保存下来。执行前展示当前 HEAD 的 SHA 和最近几颗 commit，让我确认这就是想保留的状态。」
- 「我在 detached HEAD 上看完了历史版本，什么都没提交。用 `git switch main` 回到 main 分支。执行前确认工作目录是干净的——如果不是，停下来提醒我。」

---

## 13.10 命令侧栏

```
stash 系
git stash push [-u] [-m "message"]   # 塞抽屉（-u 含 untracked）
git stash list                        # 看所有抽屉格
git stash show -p [stash@{N}]         # 看某格的 diff
git stash apply [stash@{N}]           # 拿出来，不动抽屉
git stash pop  [stash@{N}]            # 拿出来 + 销毁抽屉（冲突时不销毁）
git stash drop [stash@{N}]            # 只销毁抽屉

cherry-pick 系
git cherry-pick <sha>                 # 摘一颗
git cherry-pick <A>..<B>              # 摘一段（不含 A、含 B）
git cherry-pick -m 1 <merge-sha>      # 摘一颗 merge commit（-m 指定 parent）
git cherry-pick --continue / --abort / --skip

bisect 系
git bisect start
git bisect bad [<sha>]                # 标记坏点（默认 HEAD）
git bisect good <sha>                 # 标记好点
git bisect run <script>               # 自动跑测试脚本
git bisect reset                      # 结束，回到原位置

tag 系
git tag <name>                        # 轻量 tag
git tag -a <name> -m "..."            # 附注 tag
git tag -a <name> <sha>               # 给指定 commit 打 tag
git push origin <tag>                 # 推特定 tag
git push --tags                       # 推所有本地 tag
git tag -d <name>                     # 删本地 tag
git push origin --delete <tag>        # 删远端 tag
git describe                          # 描述 HEAD 相对最近 tag 的位置

submodule / subtree
git submodule add <url> <path>
git submodule update --init --recursive
git submodule update --remote          # 更新到子仓库远端最新
git subtree add   --prefix=<path> <url> <branch> --squash
git subtree pull  --prefix=<path> <url> <branch> --squash

sparse / partial
git clone --filter=blob:none --sparse <url>
git sparse-checkout init --cone
git sparse-checkout set <path1> <path2> ...
git sparse-checkout list
git sparse-checkout disable            # 恢复全量

维护
git count-objects -vH                 # 看仓库统计
git gc                                 # 常规 gc
git gc --aggressive                    # 深度重打包（慢）
git gc --prune=now                     # 立即清理 unreachable（危险）
git maintenance start                  # 启用后台定期维护
git reflog expire --expire-unreachable=now --all   # 让 reflog 立即过期（配合 --prune=now 才真删）

detached HEAD
git checkout <sha>                     # 进入 detached
git switch -c <branch> [<sha>]         # 在当前（或指定）位置挂分支
git switch -                           # 回到上一个分支（'-' 是快捷键）
```

---

## 13.11 本章小地图

```
八条边缘小路 · 一张地图

stash          ─ 抽屉：短期暂停（<10 分钟），长期用 WIP commit 或 worktree
cherry-pick    ─ 摘一颗珠子：本质是 rebase 的最小单位（一次一颗的重放）
bisect         ─ 二分坏珠子：log₂(N) 轮定位；AI 时代配 `bisect run` 自动化
tag            ─ 钉死的指针：发布用附注 tag、开发用 branch；tag 不随 push 走
submodule      ─ 指针指向另一条项链：能用包管理器优先用；痛点几乎全在\"两个仓库\"
subtree        ─ 把内容并进主项链：clone 无痛，反推上游麻烦
sparse-checkout─ 只展开工作目录一部分
partial clone  ─ 只下载对象一部分：两者常一起用，monorepo 标配
gc / maintenance ─ 让 Git 自己维护自己；手动 gc 在\"重写大量历史后\"或\"仓库明显变慢\"
detached HEAD  ─ 不是错误，是姿势：看历史、bisect、rebase 内部都在用；
                 在里面 commit 了就挂名牌，别切走。

一句话总括：
  这些概念都建立在前五张地图上，没有一个引入新原理——
  它们只是\"造珠子 + 挪名牌 + 挪指针\"的新组合。
```

---

## 13.12 三大典型误解拆解

**误解一：\"stash 是个更轻量的 commit，可以用来长期保存修改。\"**
**stash 不是版本控制手段，是短期抽屉**。它没有清晰的 message 结构、栈越堆越乱、pop 冲突时的心智负担大、reflog 覆盖不到 stash 独立引用链——它是**为\"几分钟到几十分钟的暂停\"设计的**。想长期保存修改的正确容器是分支（哪怕 message 写 \"WIP\"）：分支可以命名、可以 push 备份、可以正常 diff 和 rebase。**\"stash 越堆越多\"是 Git 世界最典型的\"用错工具\"信号——那些抽屉里大概率有你早就忘了的、后来重复实现过的、或者永远不会再需要的代码。**每隔一段时间清理 stash list 是好习惯；把\"想长期保留的\"变成分支是更好的习惯。

**误解二：\"cherry-pick 是复杂的高级操作，只有资深人员才用。\"**
**cherry-pick 是 Git 里最简单的\"造珠子\"动作**——它只是\"取一颗珠子的 diff、应用到当前 HEAD、造一颗新珠子\"。这个动作在第 5 章讲 rebase 时你已经见过 20 次了（rebase 的每一颗重放）——只是那时候它是自动批量做的，cherry-pick 是手动一次一颗。**它的\"高级感\"来自于\"不常单独用\"，不是来自于概念难**。真正需要注意的只有两件事：（1）cherry-pick 造的是新珠子，SHA 和原珠子不同——所以之后合并回来时可能出现\"看起来一样的双胞胎\"的冲突；（2）cherry-pick merge commit 需要 `-m` 指定 parent。**其他都和普通 commit 一样**。把 cherry-pick 从心里的\"高级区\"降到\"常规区\"，你会发现\"跨分支 backport 一个 hotfix\"、\"从别人 PR 里摘一颗好东西\"这些日常场景都变得顺手。

**误解三：\"submodule 是搞团队协作的正确方式，只是学习曲线陡。\"**
**submodule 的痛不是学习曲线问题，是设计代价——它是\"两个独立仓库通过弱指针耦合\"的方案，任何耦合方案的成本都会在协作里放大**。忘 `--recursive`、忘更新指针、天然 detached HEAD、切分支时子模块跟不上——这些不是\"熟练了就没事\"的入门问题，是\"团队规模越大问题越明显\"的架构问题。**大部分选 submodule 的项目，一年之后都会怀疑当初为什么没用包管理器**。判断规则很简单：先问\"能不能用包管理器\"——npm/pip/maven/cargo/go mod/内部 artifact 仓库任何一个能用都优先用；只有当\"这是两个必须精确同步的独立 git 仓库、包管理器帮不上忙\"时，submodule 才是正确答案。**subtree 也不是万灵药**——它的\"clone 无痛\"是用\"反推上游繁琐\"换来的，如果你会频繁把改动推回上游，subtree 会比 submodule 还麻烦。**没有免费的午餐，只有\"哪种代价我能吃下\"的选择**。

---

## 13.13 下一章预告

到这里，全书的地图部分几乎全部走完——五张主图、六个场景、一道安全防线、八条边缘小路。**最后一章 · 第 14 章《终章：把 AI 变成你的 Git 副驾》** 要做的是\"合体\"：把这些散落在十三章里的地图、判断、指令、误区拆解，收拢成一套可以随身带的心智装备。

具体你会读到：
- **五张地图的合体图**——一张贯穿全书概念的总览，从仓库到历史，加上进阶节点、场景决策路径、红黄绿边界。
- **提示词方法论的三条铁律**——如何向任何 AI（不管产品叫什么、迭代到什么版本）描述 Git 意图，让它翻译成正确的动作。
- **从 AI 回复反推概念**——每一次 AI 用命令回你话，都是一次\"我这边的概念地图对不对\"的校对机会；这一节讲怎么用日常提问把 mental model 越用越准。
- **30 天练习计划**——一份可以贴在墙上的日程，按天走一遍全书每一章的核心动作。

从\"抄命令\"到\"读地图\"——你在第 0 章接受的那个诊断，将在第 14 章拿到一份可以合上书之后独自继续走的处方。**这本书的最后一页不是终点，是你第一次靠自己走这张图的起点。**

---

> **🤖 AI 指令箱 · 本章实战演练**
>
> 挑一个你自己的真实仓库（或临时 clone 一个中等大小的开源项目做沙盒），按顺序走一遍下面的\"八边小路\"。每一步先问 AI，让 AI 解释再执行——把这一章当成一次\"AI 陪你走一遍进阶地图\"的实景导览。
>
> - **stash**：「造一点未提交的改动（比如改一个 README 的两行）。stash 一下，展示 stash list。切一个分支再切回来，`stash pop`——观察改动是否恢复。第二次尝试：造一点冲突（在 pop 前先修同一行），pop 遇冲突时不 drop——用 `git stash list` 证明 stash 还在。」
> - **cherry-pick**：「找到 main 上最近 5 颗 commit，随便挑一颗。开一个新分支 `feature/experiment`（从 3 颗之前的位置开），cherry-pick 那颗过来——观察新 commit 的 SHA 和原 commit 的 SHA 不一样；观察改动内容一致。」
> - **bisect**：「造一段假的\"引入 bug\"历史：先造 10 颗好的 commit（都能通过 `python -c 'exit(0)'`），第 7 颗故意改成 `exit(1)`。跑 `git bisect run python -c 'exit(0)'`——观察 Git 自动定位到第 7 颗。」
> - **tag**：「给当前 HEAD 打一个附注 tag v0.1.0-experiment（message 用最近 5 颗 commit 的简明总结）。跑 `git show v0.1.0-experiment` 观察附注 tag 的完整信息。再打一个轻量 tag v0.1.0-lite；对比 `git cat-file -t` 两者的差异（应该分别是 `tag` 和 `commit`）。」
> - **submodule**：（如果时间紧可跳过）「在这个 sandbox 里 `git submodule add https://github.com/xxx/small-lib libs/small-lib`。观察 `.gitmodules` 的生成、`libs/small-lib` 里的 detached HEAD 状态。删掉本地 clone、重新 clone 不加 `--recursive`——观察 `libs/small-lib` 是空的；再 `git submodule update --init --recursive` 补齐。」
> - **sparse + partial**：「随便挑一个大点的开源仓库（几百 MB 起），用 `git clone --filter=blob:none --sparse` clone 到一个新目录。对比全量 clone 的耗时和磁盘占用。用 `git sparse-checkout set <某个子目录>` 只展开一部分，观察工作目录变化。」
> - **gc**：「跑 `git count-objects -vH`——记录松散对象数量和 packfile 情况。做几次 commit 后再跑一次——观察变化。跑 `git gc` 后再看——观察松散对象变成了 pack。」
> - **detached HEAD**：「`git checkout HEAD~5`——观察进入 detached；写一颗 commit（改一个字）——`git switch main` 观察警告；用警告里给的 SHA 把那颗珠子救成一个分支。整个过程你会看清\"detached HEAD、警告、reflog、救回\"这四件事的完整闭环。」
>
> 走完这八小步，你手上的 Git 地图就真的完整了——**它不只包括你天天走的主干，也包括那些一年偶尔遇到一次、但遇到时你至少知道方向的边缘小路**。
