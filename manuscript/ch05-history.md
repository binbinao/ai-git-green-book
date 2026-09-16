# 第 5 章　历史是可塑的：重串项链的艺术

> 《Git 的概念地图》第 5 章 · 定调稿 v1.0
> 五张地图的最后一张——也是最让人又爱又怕的一张。前四章你造了珠子、串起项链、贴上名牌、照过镜子；这一章，你要学会**把项链拆下来重串**。

---

## 5.1 场景引入：一次差点变成灾难的 rebase

周四下午四点半，PR review 意见回来了。第一条评论就把你钉在椅子上：

> 「你这个 PR 里 8 个 commit，前 3 个是主要改动，后 5 个是'再改一下、再修一下、又改一下'的小修补。合并前请整理成 2-3 个原子提交，谢谢。」

你叹了一口气，认真人的要求，认真人的活。你听说过 `git rebase -i`——组里的老哥用过几次，你远远地看过一眼，屏幕上蹦出来一个满是 `pick` `squash` `fixup` `reword` 的文本编辑器，看起来像某种远古咒语。你决定这次自己上。

你敲下 `git rebase -i main`，编辑器弹出来，你把后 5 个 commit 的 `pick` 改成 `fixup`（大意是"这几个都是修补，合并进前面的"），保存、退出。屏幕唰唰唰地滚，最后停在一行绿字上：

```
Successfully rebased and updated refs/heads/feature/user-profile.
```

你 `git log --oneline`：果然，8 个 commit 变成了 3 个，每一颗都是干净的原子提交。你松了一口气，准备 push。

`git push`——**红色的报错刷屏**：

```
! [rejected]        feature/user-profile -> feature/user-profile (non-fast-forward)
error: failed to push some refs to 'git.example.com:team/project.git'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart.
```

你愣住了。**明明是同一条分支啊**——我没换分支，我甚至没换过项目。为什么远端会\"落后\"？我 rebase 之前那 8 个 commit 已经推过一次了……

你本能地想输 `--force`。手指已经落到了那 8 个字母上。**就在这时你想起了组里那句被反复叨叨的告诫**——「push --force 前，先问一下」。

**这一章要摊开的，就是那句告诫为什么必要，以及在它之外你其实还有一整套安全的操作方式**。核心是一个乍看矛盾、其实不矛盾的真相：

> **珠子是不可变的（第 2 章）。项链是可塑的（第 5 章）。**

你造出来的每一颗珠子的 SHA 永远是那个 SHA，永远不会被真的\"修改\"——但**你可以造一批新珠子重新串**，让某段项链呈现出你想要的样子。merge 是打一个结把两条项链合成一条，rebase 是把一段项链拆下来、逐颗复制、串到别的珠子后面。**看起来在\"改历史\"，其实一直在造新珠子。**

看懂了这件事，rebase、squash、reset、revert、reflog——本章讲的所有东西——都会从\"危险咒语\"变成\"简单可推理的操作\"。而且你会知道那一次 non-fast-forward 报错到底是怎么回事、`--force` 的边界在哪里、以及为什么 reflog 是你的隐形保险丝——**你以为丢了的珠子，几乎永远都能救回**。

---

## 5.2 祛魅时刻：珠子不可变 vs 项链可塑，是怎么共存的

先给结论。

> **一颗提交造出来之后，SHA 永远是那个 SHA，内容永远是那个内容，parent 永远是那个 parent——它不可变。但一段"历史"是由\"分支名牌指向哪颗珠子、每颗珠子的 parent 又指向谁\"共同决定的。你不能改一颗珠子，但你可以造一串近似的新珠子（内容相同或相似、parent 变了、SHA 就全变了），把名牌指过去，让 `git log` 呈现出的\"历史\"完全变个样子。**

这一条你在第 2 章末已经预告过。现在展开。

想象一下你手上有一条项链：

```
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D) ─▶ (E)
                                     ▲
                                    main
```

名牌 `main` 挂在珠子 E 上。log 里显示的\"历史\"是 A → B → C → D → E。

现在假设你想\"重写\"这段历史——比如把 B 和 C 合并成一颗、把 D 和 E 换个顺序。你**不能真的去动 B、C、D、E**（它们的 SHA 是内容 + parent 的哈希，一动就是别的珠子了）。你能做的是：

1. **造几颗新珠子** B'、C'D'（B 和 C 合并的产物）、E'（换过顺序后的 E）……
2. **把 main 名牌从 E 摘下来，挂到最末端的新珠子上**。
3. **旧的 B、C、D、E 还在** objects 里，只是 main 不再指着它们、它们暂时"离开了视线"——但 reflog 记得它们，30 天内你随时可以让 main 挪回去。

```
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D) ─▶ (E)        ← 旧项链，still there
             \
              ─▶ (BC') ─▶ (E') ─▶ (D')          ← 新项链
                                    ▲
                                   main（已挪过来）
```

看到了吗？**没有一颗珠子被修改**。发生的只是"造新珠子 + 挪名牌"——第 2 章告诉过你，Git 里所有看似\"改历史\"的操作本质都是这两个动作。**这一章要做的，是把这个原理落地到具体的招式上：merge、rebase、squash、reset、revert、reflog——每一个都是"造新珠子 + 挪名牌"的一种花式变奏。**

一句话总结这张图：**"历史重写"不是数据丢失，是名牌重定向**。

### 一条重要边界：这只对"你自己那份"成立

上面那张图里有一件事被小声掠过了：**旧的 B、C、D、E 还在——在你本地的 objects 里**。**别人已经从远端拉过这几颗珠子的话，他们本地也各有一份。**

那么当你把 main 从 E 挪到 D' 之后 push 上去，会发生什么？远端 main 也跟着挪——**但你的同事们本地还留着从旧项链上拉过的 D 和 E**。他们下一次 pull 时，Git 会尝试把他们的 D、E 和远端的新项链合并，得到一团乱麻。**你在\"你自己那边\"看起来是干净整理了，但从别人那边看起来是一次莫名其妙的历史分叉**——他们的 D、E 突然变成了游离在 main 之外的野珠子。

这就是**\"珠子不可变 vs 历史可塑\"这条哲学在共享分支上的裂缝**。它有一个名字，叫**黄金规则**：

> **不要 rebase / amend / reset 已经推送到共享分支的 commit。**

本章后半部分会把这条规则讲透。但你现在先要接受一件事：**\"重写历史\"这件事在你自己本地是廉价、安全、鼓励的；一旦跨过\"共享分支\"这条线，它就变成会伤及同事的高风险操作**。

好了，铺垫结束。下面依次讲 merge、rebase、squash 系列、reset、revert、reflog——每一招都建立在\"造新珠子 + 挪名牌\"这条原理上。

---

## 5.3 merge：打一个结，让两条项链变一条

先讲最温和的一招——merge。**merge 保留真实历史**：它承认\"两条项链存在过\"，然后打一个结把它们合起来。

merge 有三种情形，Git 会自动判断走哪一种。

### 5.3.1 情形 A：fast-forward——不打结，只挪名牌

如果你要 merge 的分支和当前分支之间**没有分叉**（当前分支的位置是被合入分支的祖先），那么 Git **不会造任何新珠子**——它只是把当前分支的名牌沿着项链前移到被合入分支的位置。

```
合并前：
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D) ─▶ (E)
                ▲                    ▲
               main                feature

合并后（fast-forward）：
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D) ─▶ (E)
                                     ▲
                                   main、feature
```

名牌 main 从 B 顺着项链\"快进\"到了 E。没有 merge commit，没有分叉，log 里看起来就像 feature 分支从来没存在过一样——那些 commit 直接就是 main 历史的一部分。

**什么时候会发生 fast-forward？** 当你的 feature 分支是从 main 上直接长出来的、开发期间 main 没有前进过——这时候合并回来就是 fast-forward。

**如果你不想 fast-forward、想留下\"这里合并过一个 feature\"的痕迹**：`git merge --no-ff feature`。Git 会强制造一颗 merge commit，即使技术上完全可以 fast-forward。团队约定\"每次合并都留 merge commit\"（很多 PR 平台的默认）就靠这个开关。

### 5.3.2 情形 B：三方合并——造一颗有两个 parent 的珠子

如果两条项链**已经分叉**（各自都有独立的 commit），Git 就没法\"快进\"了。它会做一次**三方合并**（three-way merge）：

- 找到两条项链的**共同祖先**（merge base）。
- 把祖先→当前分支末端的改动、祖先→被合入分支末端的改动，都算出来。
- 尝试机械地把两侧改动合并到一起，生成一份新的项目快照。
- **造一颗新珠子（merge commit），它有两个 parent**——分别指向合并前两条项链的末端。

```
合并前：
  ...─▶ (A) ─▶ (B)         ← 共同祖先
              ├─▶ (C) ─▶ (D)      ← main
              └─▶ (X) ─▶ (Y)      ← feature

合并 feature 进 main 之后：
  ...─▶ (A) ─▶ (B)
              ├─▶ (C) ─▶ (D) ─────▶ (M)     ← merge commit（两个 parent）
              └─▶ (X) ─▶ (Y) ──────┘         ← 指向 D 和 Y
                                    ▲
                                   main
```

那颗 M 就是 merge commit，它的 message 默认是 `Merge branch 'feature' into main`。它有两个 parent 指针：一个指向 D（合并前 main 的末端），一个指向 Y（feature 的末端）。**这是全书至此你遇到的第一颗\"两个 parent\"的珠子**——第 2 章里预告过的合并型 commit。

**如果两侧的改动碰到了同一行代码怎么办？** 冲突（conflict）。Git 造不出这颗 M——它会停下来，把冲突文件里两侧的内容用 `<<<<<<< ======= >>>>>>>` 标注出来，让你手动决定。你解决完、`git add` 完、`git commit` 一下——这时候 M 才真正被造出来。第 9 章会详讲冲突的处理，本章你只要知道：**冲突的出现是三方合并没法机械完成的信号，M 这颗珠子被暂停在造出之前，等你的裁决。**

### 5.3.3 情形 C：章鱼合并——同时合并多个分支（少见）

`git merge branch1 branch2 branch3` 可以一次性把多个分支合并到当前分支上，造一颗**多 parent 的 merge commit**（可能有 3 个、4 个甚至更多 parent）。这叫**章鱼合并**（octopus merge）。

在日常开发里几乎用不到——它有严格的限制（不能有冲突），主要用于 Linux 内核这类需要一次性合并大量 topic 分支的场景。**你只要知道这种珠子存在就行**，本书不展开。

### 5.3.4 merge 的核心特征

- **保留真实历史**：两条项链的原样都保留着，中间用 M 打了个结。你可以 `git log --graph` 看出\"这里合并过、那里合并过\"。
- **只造新珠子（M），不改旧珠子**：C、D、X、Y 一颗都没被动过，SHA 全部保持不变。
- **不违反黄金规则**：因为 merge 不重写任何已存在的 commit，它连\"共享分支\"这条线都不会踩到。**merge 是绝对安全的合并方式**。

代价是：如果你的团队爱用 feature 分支，`git log --graph` 会很快变成一团铁丝，看不出主干在哪儿。这就是下一节 rebase 存在的理由。

---

## 5.4 rebase：拆下来重串一遍

如果 merge 是\"打个结\"，rebase 就是\"拆下来重串\"。它的目标不同：**rebase 追求一条线性的、干净的历史**，代价是**改写**（其实是**替换**）自己那一段的珠子。

### 5.4.1 rebase 的物理动作

`git rebase main`（当前在 feature 分支上）做的事，可以一步一步拆开：

1. **找到共同祖先 B**（feature 和 main 分叉的地方）。
2. **把 feature 分支从 B 到当前的每一颗珠子（X、Y）依次\"记下改动\"**（不是 SHA，而是"这颗珠子相对上一颗改了什么"）。
3. **把 feature 的名牌暂时移到 main 的末端**（也就是 D）。
4. **逐颗\"重放\"改动**：把 X 的改动应用在 D 之上，造出一颗**新珠子 X'**（内容和 X 一致，但 parent 是 D，所以 SHA 完全不同）；再把 Y 的改动应用在 X' 之上，造出 Y'；……
5. **feature 名牌停在最后一颗新珠子上**（Y'）。

```
rebase 之前：
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D)          ← main
              └─▶ (X) ─▶ (Y)               ← feature

rebase 之后：
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D) ─▶ (X') ─▶ (Y')     ← main、feature
              └─▶ (X) ─▶ (Y)                             ← 旧珠子还在 objects 里
                                                          （reflog 记得它们）
```

看清楚：

- **X 和 X' 内容一样，但 SHA 不同**（因为 parent 从 B 变成了 D）。它们是**两颗不同的珠子**，只是长得像。
- **旧的 X 和 Y 没有消失**——它们还在 `.git/objects/` 里，reflog 里也记得它们曾被 feature 名牌指过。只是从 log 视角看，feature 上再也看不到它们了。
- **feature 的历史现在是一条直线**：A → B → C → D → X' → Y'，没有分叉、没有 merge commit，读起来像 feature 从 D 上直接长出来的一样。

**这就是 rebase 的全部\"魔法\"**——一次批量的"造新珠子 + 挪名牌"。**没有一颗已存在的珠子被修改**（这条底层法则铁的不能再铁）。

### 5.4.2 rebase 冲突：一次一颗地停

rebase 中如果某一颗珠子的改动应用不上去（比如 main 上的 D 改了 X 想要改的同一行），Git 会**停在那一颗**，让你解决冲突：

```
error: could not apply a1b2c3d... 修改用户注册逻辑
Resolve all conflicts manually, mark them as resolved with
"git add <conflicted_files>", then run "git rebase --continue".
```

你解决完那一颗的冲突、`git add`、然后 `git rebase --continue`——Git 会造出那颗 X'，然后继续尝试下一颗（Y）。**如果 Y 又冲突，再停一次。**

**这就是 rebase 和 merge 处理冲突的关键差异**：merge 是**一次性**把两侧所有改动叠加，冲突全部一次爆发；rebase 是**逐颗**重放，冲突可能出现在中间某几颗上，每次只处理一颗的冲突。前者\"痛得集中\"，后者\"痛得分散\"——各有各的痛法。第 9 章会展开对比。

**如果 rebase 中途你想放弃**：`git rebase --abort`。Git 会把 feature 分支恢复到 rebase 开始前的位置，就像什么都没发生过。**这是 rebase 天然的\"撤销键\"**——只要你还在 rebase 过程中，永远可以 abort 出来。

### 5.4.3 交互式 rebase：整理提交的瑞士军刀

上面讲的是\"不交互\"的 rebase（`git rebase main`）——它逐颗重放、不修改任何 commit 的 message 或结构，只是把 parent 换掉。这已经很有用。

但 rebase 真正强大的地方是**交互式模式**（`git rebase -i <base>`）：

```
git rebase -i main
```

Git 会弹出一个编辑器，列出从共同祖先到当前分支末端的每一颗 commit，每一行一颗，前面标着 `pick`：

```
pick a1b2c3d 初步实现用户注册接口
pick e4f5g6h 修正邮箱大小写
pick i7j8k9l 再修一个 typo
pick m0n1o2p 补个单测
pick q3r4s5t 又改一下

# Rebase abc..q3r4s5t onto abc (5 commands)
#
# Commands:
# p, pick <commit>   = 保留原样重放
# r, reword <commit> = 重放，但让我改 message
# e, edit <commit>   = 重放到这颗停下来，让我改内容
# s, squash <commit> = 合并进上一颗，让我改 combined message
# f, fixup <commit>  = 合并进上一颗，丢弃这颗的 message
# d, drop <commit>   = 直接丢弃这颗
# 你还可以调整这些行的顺序——顺序就是重放顺序
```

你在这里改动作、改顺序、保存退出——Git 就按你写的剧本重放。**这是"整理项链"最强大的工具**。

日常最常用的三招：

- **squash / fixup**——把\"再改一下\"、\"再修一个 typo\"这些琐碎珠子合并进它们真正属于的那颗上。squash 会让你重新写 combined message，fixup 直接丢弃小珠子的 message。开篇场景里那个 PR review 意见就是让你用这个。
- **reword**——批量修改 commit message。比如你意识到前 5 个 commit 的 message 都不符合团队 Conventional Commits 规范，一口气全改。
- **reorder / drop**——调整 commit 顺序、删掉一颗没用的 commit（比如误提交了一个日志打印）。

**开篇场景的正确操作**：

```
git rebase -i main

# 编辑器里：
pick a1b2c3d 初步实现用户注册接口
pick e4f5g6h 补充邮箱验证
pick i7j8k9l 加接口文档
fixup m0n1o2p 修改用户注册逻辑     ← 修补，合并进 a1b2c3d
fixup q3r4s5t 修改用户注册逻辑     ← 修补，合并进 a1b2c3d
fixup u6v7w8x 修 typo              ← 修补，合并进 e4f5g6h
...
```

保存退出，Git 逐颗重放，最后 8 颗珠子变成 3 颗干净的原子提交。**这就是\"整理提交\"最典型的姿势**。

### 5.4.4 rebase 遇上共享分支：黄金规则登场

现在回到开篇场景没解决的那个问题：**你 rebase 完 push 被拒了**。

看清楚发生了什么：

```
rebase 之前（你已经 push 过一次）：
  远端 feature/user-profile:  ...─▶ (X1) ─▶ (X2) ─▶ ...─▶ (X8)
  你本地 feature/user-profile: ...─▶ (X1) ─▶ (X2) ─▶ ...─▶ (X8)
  一致。

你 rebase -i、squash/fixup 之后：
  远端 feature/user-profile:  ...─▶ (X1) ─▶ (X2) ─▶ ...─▶ (X8)   ← 没变
  你本地 feature/user-profile: ...─▶ (X1') ─▶ (X2') ─▶ (X3')     ← 3 颗全新珠子
  
  X1-X8 都在你本地 objects 里，但 feature 名牌指着新的 X1'-X3'。
```

你 `git push`——Git 检查发现：远端 feature 指着 X8，你本地 feature 指着 X3'，而**X8 不是 X3' 的祖先**（X3' 的祖先里根本没有 X8）。Git 拒绝 push：\"我没法从 X8 快进到 X3'，你告诉我怎么办？\"

**这不是 Git 犯傻**——它是在保护你：**\"这次推上去，远端 feature 上的 X1-X8 会从 log 里\"消失\"（其实还在 objects 里，但没有名牌指着，早晚会被 gc 掉），已经拉过这条分支的同事会陷入混乱。你确定吗？\"**

现在关键问题：**这条 feature 分支上有没有别人在协作？**

- **场景 1：只有你一个人**（很多个人 feature 分支）——用 `--force-with-lease` 覆盖远端，安全。
- **场景 2：这是团队共享分支**（有同事从上面拉过、可能开了子分支）——**不要 --force**。你已经在给别人惹麻烦了，止损方式是**先把 rebase 撤回（用 reflog，见 5.7），恢复 8 颗旧珠子；然后用 merge 或 revert 的方式整理**。

**这就是黄金规则**：

> **不要 rebase 已经推送到共享分支的 commit。**

再翻译一遍就是：**\"重写历史\"这件事，只在\"你自己那份\"上安全。一旦跨过\"共享\"这条线（\"分享\"给别人拉过），你就在改造别人已经拥有的实体，就一定会破坏一些人的世界。**

### 5.4.5 --force-with-lease：温柔一档的 force

`git push --force` 是**告诉 Git\"我不听劝，覆盖远端，别管远端现在什么样\"**。这是核武器。

`git push --force-with-lease` 是**告诉 Git\"我要覆盖远端，但前提是远端还是我上次 fetch 时看到的那个样子——如果同事在这之间往上面推过东西，请拒绝我\"**。这是一个安全阀。

第 4 章讲过：`origin/feature` 是你本地缓存，反映的是你上次 fetch 那一刻远端的位置。`--force-with-lease` 就是拿这份缓存去和远端此刻的位置对比——一致就允许强推，不一致就拒绝（意味着有别人往上推过东西，你的\"覆盖\"会踢掉他们的贡献）。

**准则**：

- 任何时候你觉得必须 force，先想\"用 `--force-with-lease` 够不够？\"——**99% 够**。
- **不要为了 push 去 fetch。**`--force-with-lease` 的价值恰恰来自你的缓存是\"旧\"的——旧缓存会让 Git 在远端变过时拦住你。想同时具备\"保护\"和\"对齐预期\"，用带期望值的形式：`git push --force-with-lease=<branch>:<你期望远端仍是的那颗 SHA>`（官方文档中唯一非实验性的写法）；或用 `--force-if-includes` 兜住\"后台自动 fetch 把缓存刷掉\"的情形（IDE / 编辑器插件自动 fetch 很常见）。
- **裸的 `--force`** 保留给你完全清楚自己在干什么、并且和团队沟通过的极少数场景（比如 CI 里的自动化流程、临时清理你自己的沙盒分支）。第 12 章会展开安全边界，也会给出 Claude Code / Cursor 层面 deny 掉 `git push --force*` 的推荐配置。

**回到开篇场景的正确应对流程**：

1. 确认这是你**个人**的 feature 分支（PR review 场景通常是）。
2. 看一眼缓存里的参照物：`git log --oneline origin/feature`——它指向的应该正是你 rebase 之前那 8 个 commit。**不要为了这次 push 再去 fetch**：缓存一刷新，下一步的 lease 保护就归零了（原因见上面那条准则）。
3. `git push --force-with-lease` 把整理后的 3 颗珠子推上去——Git 拿你的参照物和远端此刻对比，一致（没人在你上次 fetch 之后动过它）才允许覆盖，否则拒绝。
4. 在 PR 评论里说一句"整理成 3 个原子提交，已 force-push，请 reviewer 重新看下"——**这一步不是仪式，是给 reviewer 一个明确信号，因为 GitHub / GitLab 上你 force-push 之后 review 意见的锚点可能会漂移**。

---

## 5.5 何时 merge、何时 rebase：三条判断规则

merge 和 rebase 都能\"把两条项链合到一起\"，但选谁不是审美问题，是有清晰判断规则的。

**规则一：往共享分支合入时——用 merge。**
一个 feature 分支开发完了，要合入 main——**用 merge**（很多平台的 PR 默认就是 merge）。理由：主干需要留下\"这里合并过一个 feature\"的痕迹，方便 code archaeology、revert、release note 生成。**不要在合入前做\"把 main rebase 到 feature 上\"这种操作**——那是在给共享分支 main 重写历史。

**规则二：把主干最新变化拉进自己的 feature 分支——用 rebase。**
你开发到一半，main 上又进了别人的几个 commit，你想\"跟上主干最新\"。这时候的选择：
- **`git rebase main`（推荐）**：把你的 feature 珠子移到 main 最新之上，历史保持直线，PR 里 reviewer 只看到你的改动、不看到"顺便合了一下 main\"的噪音。
- `git merge main`：造一颗 merge commit 把 main 最新拉进来。**能用但不推荐**——你的 feature 分支上会有一颗\"Merge branch 'main' into feature\"的噪音 commit，PR review 时会看到不属于你的改动。

**规则三：整理自己个人分支的提交——用 interactive rebase。**
squash / fixup / reword / reorder / drop——这些整理动作只在 rebase -i 里有。**只对你自己一个人操作的分支用**。整理完 `--force-with-lease` push 上去。

**反规则一：不要用 `--force` 去修\"我 rebase 完 push 不上去\"的问题——先看这条分支有没有别人。**
问自己一句：\"这条分支有没有别人在协作？\"——不确定就在 Slack/企微问一句，代价 30 秒，避免的可能是一场 debug 灾难。

**反规则二：不要为了\"看起来干净\"就 rebase 已经在 PR 里被 review 过的分支——除非 reviewer 明确要求。**
每次 rebase 都会让 PR 里的 review 锚点（针对某一行的评论）漂移或消失，reviewer 要重新对比。合作 PR 的默认约定是 **push 上去的 commit 尽量别动，等 review 通过再一次性整理**。

---

## 5.6 reset 三态：--soft / --mixed / --hard

到这里你已经知道 merge 和 rebase 的机理。现在讲一个更基础但也更容易踩坑的操作——**reset**。

`git reset` 的核心动作只有一个：**把当前分支名牌往回（或往任意位置）挪**。三个参数决定的是\"挪名牌之外，工作目录和暂存区跟不跟着挪\"。

用一张图讲清楚。假设你现在 HEAD 指向 E，你想 `reset` 到 C：

```
初始状态：
  ...─▶ (A) ─▶ (B) ─▶ (C) ─▶ (D) ─▶ (E)
                              ▲     ▲
                              目标  HEAD/main
                              位置

  工作目录：E 的快照 + 你未提交的改动（如果有）
  暂存区：  E 的状态（假设一切干净）
```

**`git reset --soft C`：只挪名牌。**
- main 名牌从 E 挪到 C。
- **工作目录不动**、**暂存区不动**。
- 结果：从 log 视角看，D 和 E 消失了；但工作目录里的文件还是 E 版本的内容——D 和 E 的所有改动都留在了暂存区里，等你重新 commit。
- **用途**：\"我想撤销最近几次 commit，但不想丢掉改动——我要重新组织成新的 commit。\"

**`git reset --mixed C`（默认，不写 `--mixed` 也是这个）：挪名牌 + 重置暂存区。**
- main 从 E 挪到 C。
- 暂存区重置到 C 的状态。
- **工作目录不动**——D 和 E 的改动还在你的文件里，但暂存区里没有它们了。
- 结果：`git status` 会显示你有一堆\"未暂存的改动\"（就是 D 和 E 的所有改动）。
- **用途**：\"我想撤销最近几次 commit，改动保留但要重新 add——我要重新挑选哪些进暂存、哪些不进。\"

**`git reset --hard C`：挪名牌 + 重置暂存区 + 重置工作目录。**
- main 从 E 挪到 C。
- 暂存区重置到 C。
- **工作目录也重置到 C**——D 和 E 的所有改动**从你的文件里被抹掉了**。
- 结果：一切像 D 和 E 从没存在过一样（除了 reflog 里的记录）。
- **用途**：\"我要完全丢弃最近几次 commit 和它们的改动——一键回到干净的 C 状态。\"
- **这是唯一一个会\"抹掉你工作目录里未提交改动\"的 reset**——是 reset 家族里唯一真正危险的一档。社区通行的 AI 工具最小权限配置里，把 `Bash(git reset --hard*)` 设成 ask 或 deny 是标准一项（第 12 章展开）。

一张对照表：

| 命令 | 挪 HEAD/branch | 重置暂存区 | 重置工作目录 | 未提交改动 |
|---|---|---|---|---|
| `git reset --soft C` | ✅ | ❌ | ❌ | 全部保留在暂存区 |
| `git reset --mixed C` (默认) | ✅ | ✅ | ❌ | 保留在工作目录（未 add） |
| `git reset --hard C` | ✅ | ✅ | ✅ | **全部丢失** |

**关键澄清**：**这三个 reset 都不会真的销毁那些被跳过的 commit（D 和 E）**——它们的 SHA 永远存在于 objects/ 里，reflog 里也有记录，你随时能让 main 挪回去。**reset --hard 危险的地方不在 D 和 E**（那两颗是有 reflog 保底的），而在**\"reset --hard 那一刻你工作目录里未提交的改动\"**——那些改动从来没被 commit 过、reflog 里也没有它们的记录，被 --hard 冲掉就是真的没了。

**结论：**

- **reset --soft、--mixed 是完全可撤销的**（找到旧 SHA `reset` 回去就好，reflog 里有）。
- **reset --hard 唯一不可撤销的部分是\"当时你工作目录里未提交的改动\"**——所以**执行 reset --hard 之前，如果你手上有未提交的改动，先 stash 或 commit 一下**。

---

## 5.7 reflog：你的隐形保险丝

好了，本章你已经见过太多\"造新珠子、挪名牌、旧珠子还在\"的场景。现在正式介绍那个让\"旧珠子还在\"这件事变得可用的机制——**reflog**。

### 5.7.1 reflog 是什么

**reflog 是本地操作的黑匣子**。每次 HEAD 或某个分支名牌的位置发生变化，Git 都会在 `.git/logs/` 下的一个文本文件里记一行：\"什么时刻、什么操作、从哪个 SHA 挪到了哪个 SHA\"。

看一下：

```
$ git reflog
a1b2c3d (HEAD -> main) HEAD@{0}: rebase (finish): returning to refs/heads/main
e4f5g6h HEAD@{1}: rebase (pick): 修补用户注册单测
i7j8k9l HEAD@{2}: rebase (pick): 初步实现用户注册接口
m0n1o2p HEAD@{3}: rebase (start): checkout main
q3r4s5t HEAD@{4}: commit: 又改一下
u6v7w8x HEAD@{5}: commit: 修 typo
y9z0a1b HEAD@{6}: commit: 补个单测
c2d3e4f HEAD@{7}: commit: 再修一个 typo
g5h6i7j HEAD@{8}: commit: 修正邮箱大小写
k8l9m0n HEAD@{9}: commit: 初步实现用户注册接口
```

**这是你本地最近所有 HEAD 移动的完整日志**。它记了 rebase 之前那 8 个 commit 的 SHA、rebase 之后新的 3 个 commit 的 SHA、每一次 commit / checkout / reset / merge 的具体动作。

**关键 mental model**：**reflog 是"本地历史"的历史**——你操作 Git 的每一步 Git 都替你记着，就像行车记录仪一样。它是**本地的**，不会 push 也不会被 clone 同步过来——每个人都有自己的一份。

### 5.7.2 reflog 的救援用法

想象你刚刚 `git reset --hard HEAD~3` 意外抹掉了 3 个 commit，你想找回它们。步骤：

```
git reflog
# 输出里找到 reset --hard 之前那一行的 SHA，假设是 a1b2c3d
git reset --hard a1b2c3d
# main 名牌挪回 a1b2c3d，3 颗 commit 回归
```

或者你 rebase 搞砸了，想回到 rebase 之前的状态：

```
git reflog
# 找到 rebase (start) 那一行之前的 SHA
git reset --hard <那个 SHA>
# 或者更明确：git reset --hard HEAD@{N}，其中 N 是 reflog 里那一行的编号
```

**几乎所有\"哎呀 Git 搞砸了\"的场景，reflog 都能救回**。这是本书最重要的心理防线之一——**你以为丢了的珠子，几乎永远都能救回**。

### 5.7.3 reflog 保留期：默认 30 到 90 天

reflog 不是永久保留的。默认配置：

- `gc.reflogExpire = 90` 天（reflog 里\"有引用\"的条目——即当前还能通过某种方式到达的珠子——保留 90 天）
- `gc.reflogExpireUnreachable = 30` 天（reflog 里\"unreachable\"的条目——即没有任何名牌能到达的珠子——保留 30 天）

**通俗说法**：**默认 30 天**——一颗被\"抛弃\"的珠子（没有任何分支/tag 指着它），reflog 会替你保管 30 天。30 天后 `git gc` 才会真正把它清扫掉。

**要真的\"丢掉\"一颗珠子，需要三件事同时满足**：

1. 没有任何 branch / tag / HEAD 指着它（unreachable）。
2. reflog 里也没有它了（超过 30 天）。
3. `git gc` 运行了。

三件事同时发生的概率对普通用户接近于零——所以你在 Git 里\"丢失数据\"是罕见事件，绝大多数\"完了完了\"的惊呼都可以被一次 `git reflog` + `git reset --hard <sha>` 化解。

### 5.7.4 危险操作前的安全网

**每一次做黄色操作之前（rebase / reset --hard / branch -D），推荐这两步**：

```
git branch backup/<描述性名称>-$(date +%Y%m%d-%H%M)   ← 建一条备份分支
git reflog                                              ← 看一下当前 HEAD 位置
```

第一步是**在当前珠子上挂一张\"我随时能回来\"的名牌**——即使 reflog 过期了、gc 跑了，这张名牌也还挂在原位置，那颗珠子就有引用不会被清扫。第二步是让你**心里对当前状态有底**，出问题时更容易找到目标 SHA。

**这两步各花 3 秒**。它们把黄色操作从\"心跳过速\"降级为\"轻松尝试\"。**任何 AI 时代的 Prompt 模板里\"backup branch + reflog anchor\"都应该是不用讨论的默认**——这是本章送给你的最实在的安全习惯。

---

## 5.8 revert：造一颗抵消珠子

上面所有的操作——rebase、reset、amend——都在\"重写历史\"。它们都要面对同一条黄金规则的限制：**别在共享分支上用**。

那如果你已经把一个错误 commit 推到了共享分支（比如 main）上、需要撤销它，怎么办？

答案是 **revert**——它不重写历史，它**造一颗\"抵消\"珠子**。

### 5.8.1 revert 的物理动作

假设远端 main 上有一颗 X，做了错误的改动。`git revert X` 做的事：

1. 算出 X 的改动的**反向 diff**（X 加了什么，就要删什么；X 删了什么，就要加回来）。
2. 把这个反向 diff 应用到当前 HEAD 上。
3. **造一颗新珠子 X⁻¹**，parent 指向当前 HEAD，内容是\"X 的效果被抵消了\"。

```
revert 之前：
  ...─▶ (A) ─▶ (B) ─▶ (X) ─▶ (D)
                              ▲
                             main

revert X 之后：
  ...─▶ (A) ─▶ (B) ─▶ (X) ─▶ (D) ─▶ (X⁻¹)
                                     ▲
                                   main
```

**X 还在项链上，log 里能看到它**——但 X⁻¹ 把 X 的改动"平掉"了，最终项目状态相当于 X 没发生过。**这是"造新珠子 + 挪名牌"原理最优雅的应用**：不改任何旧珠子、追加一颗新珠子来抵消错误。

### 5.8.2 revert 和 reset 在共享分支上的本质差异

对比同一个场景——\"我在 main 上推了一颗错误 commit X，要撤销它\"：

| | reset --hard B | revert X |
|---|---|---|
| **物理动作** | main 名牌从 D 挪回 B | 造一颗新珠子 X⁻¹ 追加到 D 之后 |
| **需要 force push** | ✅（远端 main 是 D，本地要成 B，non-fast-forward） | ❌（远端 main 是 D，本地是 D+X⁻¹，正常 fast-forward） |
| **X 从远端 log 里消失吗** | ✅（对 pull 过 D 的同事造成混乱） | ❌（X 还在 log 里，X⁻¹ 记录了撤销这件事） |
| **是否重写历史** | 是（旧的 X、D 珠子在 main 上失去引用） | 否（所有旧珠子在 main 上都还在） |
| **共享分支安全吗** | ❌ 违反黄金规则 | ✅ 完全安全 |
| **保留\"曾经撤销过\"的证据** | ❌ 无痕 | ✅ log 里 X 和 X⁻¹ 都在 |

**结论**：**共享分支上撤销 commit 的正确方式，永远是 revert，不是 reset**。

**revert 的另一个优点**：`revert` 造的珠子可以被再次 revert——比如你 revert 完发现\"其实那个改动是对的，我想加回来\"，`git revert X⁻¹` 就是\"revert 那次 revert\"，效果等于把 X 的改动再加回来。**没有信息丢失，一切都是往前造珠子。**

---

## 5.9 AI 指令箱 · 历史重写

以下指令模板与工具无关（Claude Code / Cursor / Copilot / Aider / Windsurf 皆适用）。**颜色标注**：本章几乎全是黄色——涉及 rebase、reset、amend、force push 的任何操作都需要盯着看。**每一条黄色操作前，都建议先要求 AI 挂 backup 分支 + 展示 reflog**。

**🟢 探索类（只读，先看清楚再决定）**

- 「用 `git log --graph --oneline --all -30` 展示当前仓库的历史全景。给我指出：主干在哪、有几条正在活跃的分支、有没有合并 commit、有没有明显的分岔。用中文描述这张图。」
- 「读 `git reflog` 的最近 50 条记录，用中文告诉我：过去这段时间在这个仓库里我做过哪些'改历史'的操作（rebase / reset / amend / branch delete）——按时间倒序列出，标出每一条的类型、影响的分支、before/after SHA。」
- 「当前 HEAD 之前 5 个 commit 里，有没有 message 显示为 'fixup'、'wip'、'typo'、或者内容很小的补丁？如果有，列出来。这些通常是可以 squash 到前一个'正片' commit 里的候选。」

**🟡 整理提交类（rebase -i、amend——只在个人分支上）**

- 「我要整理当前分支从 `main` 分叉点到 HEAD 的所有 commit。先执行 `git branch backup/before-rebase-$(date +%Y%m%d-%H%M%S)`，然后展示所有待整理的 commit（SHA、message、改动文件数）。之后**停下来让我决定 pick/squash/fixup/drop 的方案**，不要自动 rebase。」
- 「按我给你的这份剧本执行 rebase -i（剧本：把第 4、5、6 个 commit fixup 进第 3 个；把第 8 个 drop 掉）。执行完展示 log 前后对比，并明确告诉我：如果中途冲突，你会停下来让我处理，不会自作主张选一边。」
- 「我刚 commit 的这条 message 打错了。用 `git commit --amend` 帮我改成'<正确文本>'。执行前告诉我：这条 commit 之前有没有 push 过？如果 push 过，我 amend 之后再 push 会怎么样？」

**🟡 撤销类（reset / revert——先判断分支性质）**

- 「我要撤销最近 3 个 commit，但改动都要保留下来（因为我要重新组织提交）。用 `git reset --soft HEAD~3`。执行前告诉我：这个操作会挪 main 名牌、旧 3 个 commit 进 reflog；不会碰工作目录和暂存区里那 3 个 commit 的内容。」
- 「我要完全丢弃当前分支最近 2 个 commit（改动也不要了）。用 `git reset --hard HEAD~2`。执行前必须先：（1）检查我工作目录是不是干净的，如果不干净停下来提醒我先 stash；（2）建 backup 分支；（3）展示旧 HEAD 的 SHA 以备我需要恢复。」
- 「main 分支上第 3 个 commit（SHA a1b2c3d）是错的、已经推到远端了。**不能 reset，因为是共享分支**。用 `git revert a1b2c3d` 造一颗抵消珠子；执行前展示 revert 会产生的 diff，让我确认反向改动符合预期。」

**🟡 与远端交互（force push——极谨慎）**

- 「我 rebase 完 push 被拒了（non-fast-forward）。执行前先确认：（1）这条分支是不是纯粹我个人的？让 AI 检查最近 30 天有没有别的作者往上面 push 过；（2）如果确认是个人分支，用 `git push --force-with-lease`；如果不确定，停下来问我。**任何情况下都不要用裸的 `git push --force`。**」

**🟢 reflog 救援类**

- 「我刚才 `git reset --hard` 之后发现丢了改动。请用 `git reflog` 找到 reset 之前 HEAD 的位置，展示那颗 commit 的 message 和 diff summary，让我确认那就是我要找回的状态。确认后用 `git reset --hard <那个 SHA>` 恢复。」
- 「我刚才 `git branch -D feature-x` 误删了一个分支。用 `git reflog --all` 或直接翻 `.git/logs/refs/heads/feature-x` 找到它最后指向的 SHA。找到后 `git branch feature-x <那个 SHA>` 把分支救回来。」
- 「rebase 中途我搞砸了、想完全放弃。如果 rebase 还在进行中（`.git/rebase-*` 目录存在）用 `git rebase --abort`；如果已经 finish 了、我发现结果不对，用 reflog 找到 rebase 之前的 SHA、`git reset --hard` 回去。」

**训练用指令（陪练模式）**

- 「给我 8 道场景判断题：给一个具体情境（'我 amend 完一个已推送的 commit'、'我在 feature 分支上 rebase 完 push 被拒'、'我要撤销 main 上一颗已 push 的错误 commit'、'我 reset --hard 之后想找回改动'……），我要说出正确的操作、以及一个常见但错误的操作。你批改并讲评。」
- 「用'珠子不可变、项链可塑'这条原理，向一个刚学 Git 的新人解释：为什么 `git commit --amend` 不是真的'改' commit、为什么 rebase 完 SHA 都变了、为什么 reflog 里能找回我以为丢掉的 commit。300 字以内。」
- 「让我练一次交互式 rebase：你随便造一段 10 个 commit 的 fake 历史（其中 4 个是 wip / typo 的琐碎修补），把这段历史贴给我；我用文字回复我的整理方案（pick/squash/fixup/reorder/drop），你判断我方案的对错、给出理由。」

---

## 5.10 执行后的世界

| 你说的话 | AI 大概率执行 | `.git/` 里的真实变化 |
|---|---|---|
| \"把最近 5 个 commit 整理成 3 个\" | `git rebase -i HEAD~5`（配合你的剧本） | `objects/` 里新增 **3 颗新 commit 对象**（对应整理后的珠子）；`refs/heads/<current>` 从旧末端挪到新末端；**旧的 5 颗 commit 对象还在** objects 里；reflog 记录整个 rebase 过程的每一步 |
| \"改一下刚才那颗 commit 的 message\" | `git commit --amend -m \"...\"` | `objects/` 里**新增一颗 commit 对象**（新 SHA）；`refs/heads/<current>` 从旧 SHA 挪到新 SHA；旧珠子还在 objects 里；reflog 加一条 |
| \"撤销最近 3 个 commit 但保留改动到暂存区\" | `git reset --soft HEAD~3` | `refs/heads/<current>` 往回挪 3 格；被跳过的 3 颗 commit 对象**原封不动**留在 objects 里；index（暂存区）保持在 HEAD~0 时的状态；工作目录不动；reflog 记录这次跳跃 |
| \"完全丢弃最近 2 个 commit 及改动\" | `git reset --hard HEAD~2` | `refs/heads/<current>` 往回挪 2 格；index 和工作目录都重置到 HEAD~2 时的快照；被跳过的 2 颗 commit 对象**仍在** objects 里；**你未提交的改动被抹除**（这一部分真的没了）；reflog 记录 |
| \"撤销 main 上那颗错误 commit（已推送）\" | `git revert <sha>` | `objects/` 里**新增一颗抵消 commit**（把那颗 commit 的改动反向应用）；`refs/heads/main` 前移 1 格；**错误的那颗 commit 原样保留在 log 里**——旁边多了一颗撤销它的珠子 |
| \"rebase 完 push 到远端\" | `git push --force-with-lease` | 本地新对象打包传给远端；远端 `refs/heads/<branch>` 从旧 SHA 挪到新 SHA；**远端旧 SHA 对应的珠子**在远端 objects 里失去引用（多久后被 gc 由远端配置决定）；本地 `refs/remotes/origin/<branch>` 同步更新 |
| \"帮我从 reflog 里找回昨天的一个 commit\" | `git reflog` + `git reset --hard <sha>` | 读 `.git/logs/HEAD` 和相关文件（纯读）；找到目标 SHA 后 reset 一次——就是一次\"挪名牌\"，被找回的珠子重新回到分支上 |

看懂这张表你会最终确认本章的核心：**没有任何一颗已存在的珠子被真正修改过——所有操作都归结为\"造新珠子 + 挪名牌 + reflog 记账\"这三个动作的排列组合。** merge 是"造一颗 M + 挪一个名牌"；rebase 是"批量造 N 颗新珠子 + 挪一个名牌"；reset 是"只挪一个名牌（也许附带清理暂存区/工作目录）"；revert 是"造一颗抵消珠子 + 挪一个名牌"；amend 是"造一颗替代珠子 + 挪一个名牌"。**五张变奏，一个主题。**

---

## 5.11 命令侧栏

```
merge 系
git merge <branch>              # 合并 branch 到当前分支（可能 ff、可能造 merge commit）
git merge --no-ff <branch>      # 强制造 merge commit（哪怕能 ff）
git merge --abort               # 冲突时放弃 merge，恢复原状
git merge --squash <branch>     # 把 branch 的改动作为一个未提交的状态摆到暂存区（不造 merge commit）

rebase 系
git rebase <base>               # 把当前分支重放到 <base> 之上（线性化）
git rebase -i <base>            # 交互式：pick/reword/squash/fixup/drop/reorder
git rebase --continue           # 冲突解决完继续下一颗
git rebase --skip               # 跳过当前这颗（罕见，慎用）
git rebase --abort              # 完全放弃这次 rebase，恢复到开始前

reset 系
git reset --soft <target>       # 只挪名牌，暂存区/工作目录都不动
git reset --mixed <target>      # 挪名牌 + 重置暂存区（默认，可省略 --mixed）
git reset --hard <target>       # 挪名牌 + 重置暂存区 + 重置工作目录（危险）
git reset ORIG_HEAD             # 撤销刚才的 merge/rebase/reset（一键回到操作前）

revert 系
git revert <sha>                # 造一颗抵消 <sha> 的 commit
git revert -n <sha>             # revert 但不自动 commit（想把多个 revert 合并时用）
git revert <sha1>..<sha2>       # revert 一段 commit（一次造多颗抵消珠子）

reflog 系
git reflog                      # 看 HEAD 的移动史（最近的在最上面）
git reflog show <branch>        # 看某个分支的移动史
git reset --hard HEAD@{N}       # 回到 reflog 里第 N 条时的位置
git reset --hard <sha>          # 同上，直接用 sha

推送
git push --force-with-lease     # 温柔版 force：只在远端没在你身后变过时才允许
git push --force                # 核武器 force（尽量别用）
```

不需要背。需要时回来看，或者直接说人话让 AI 翻译。

---

## 5.12 本章小地图 + 全书五张地图汇总

### 本章小地图

```
核心原理：珠子不可变，项链可塑
  │
  ├─ "重写历史" = 造一批新珠子 + 挪名牌 + 旧珠子进 reflog
  └─ 旧珠子还在 objects 里，reflog 记着，30 天 GC 期

合并两条项链的两种方式：
  ┌─ merge：打个结（造一颗有两个 parent 的 M 珠子）
  │    ├─ fast-forward：不打结、只挪名牌
  │    ├─ 三方合并：造 M 珠子（可能有冲突）
  │    └─ 章鱼合并：多个分支一次合（M 有多个 parent，罕见）
  └─ rebase：拆下来重串（造一串新珠子）
       ├─ 线性化历史，SHA 全变
       ├─ 冲突逐颗停，可 --continue 或 --abort
       └─ 交互式（-i）：pick / squash / fixup / reword / reorder / drop

黄金规则：不要 rebase / amend / reset 已推送的共享分支
  │
  ├─ 违反后果：同事本地的旧珠子成"野"珠子，pull 时天翻地覆
  ├─ 安全边界：个人 feature 分支可以 rebase，共享分支只能 merge / revert
  └─ push 被拒（non-fast-forward）：先 fetch，看清楚，再决定

reset 三态：
  ┌─ --soft  只挪名牌           （改动全保留在暂存区）
  ├─ --mixed 挪名牌 + 清暂存区   （改动留在工作目录）
  └─ --hard  挪名牌 + 清全部     （危险：会抹掉未提交改动）

revert：造抵消珠子，不改历史（共享分支唯一安全的"撤销"方式）

reflog：本地操作的黑匣子，默认 30 天 GC 期
  │
  └─ 几乎所有"哎呀丢了"的场景都能救回：git reflog + git reset --hard <sha>

黄色操作前的两步安全网：
  1) git branch backup/<描述>-<时间戳>
  2) git reflog  （心里对当前 HEAD 有底）
```

### 五张地图汇总（全书概念部分至此完成）

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                      五张地图 · 全书概念主干
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【地图 1 · 仓库】（第 1 章）
    .git/ = 内容寻址数据库 + 引用表
    仓库是自包含的、本地完整的、可脱网运行的历史数据库
    clone 不是"下载文件"，是复制整个数据库

【地图 2 · 提交】（第 2 章）  ─── 珠子
    commit = 全量快照 + parent 指针 + 元信息 + SHA
    不可变：改任何一样，SHA 就变，就是别的珠子
    三区模型：工作目录 → add → 暂存区 → commit → 仓库

【地图 3 · 分支】（第 3 章）  ─── 名牌
    branch = refs/heads/ 里的一行 SHA（可移动的指针）
    分支不是代码拷贝、删除分支不是删除代码、切换分支不是搬运
    HEAD = 指向指针的指针（正常态和 detached 态）

【地图 4 · 远程】（第 4 章）  ─── 镜子里的项链
    remote = 别名 + URL（config 里两行字）
    远程分支 = 本地缓存（refs/remotes/<remote>/<branch>）
    碰网络：fetch 家族与 push（clone/fetch/pull/push/ls-remote/remote update）
    non-fast-forward = Git 在按停按钮

【地图 5 · 历史】（第 5 章）  ─── 重串项链
    珠子不可变，项链可塑
    "重写历史" = 造新珠子 + 挪名牌 + 旧珠子进 reflog
    merge 打结、rebase 重串、reset 挪名牌、revert 造抵消珠子
    黄金规则：共享分支不重写
    reflog = 本地黑匣子，保管期 30/90 天（不可达 30、可达 90）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

这五张地图组合起来的 mental model：

    (仓库) = 装 (珠子) 的档案馆
        │
        └─ 珠子之间靠 parent 指针串成 (项链)
              │
              └─ (名牌) 挂在某颗珠子上，标出"我在这儿"
                    │
                    └─ 同样的项链在别人档案馆里也有一份，
                        我这边给它开了一面 (镜子) 观察
                          │
                          └─ 项链可以被拆下来重串（造新珠子），
                              但共享分享的珠子不要动
                              （黄金规则）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**如果你能对每一张地图都用一句话说清\"它在物理上是什么、在概念上是什么、常见误解是什么\"——你已经具备了在 AI 时代驾驭 Git 的完整心智模型**。剩下的场景手册（第 6-11 章）和安全防线（第 12 章），都建立在这五张地图之上。

---

## 5.13 三大典型误解拆解

**误解一：\"rebase 会丢代码。\"**
**恰好相反——rebase 是 Git 里最不容易\"丢\"代码的操作之一**。它做的全部事情是"逐颗重放你的改动、造出内容相同但 parent 换了的新珠子\"——你的每一处改动都被完整地搬运到了新的珠子里。真正会\"丢\"东西的操作是 `reset --hard` 时抹掉工作目录里未提交的改动。这两件事经常被混淆——因为 rebase 中途遇到冲突时 log 里那些旧 SHA 突然\"看不到了\"，让人以为它们消失了；实际上它们还在 objects/，reflog 里也全都记着，随时可以 `git reset --hard <旧 SHA>` 一键回来。**\"rebase 会丢代码\"是新手最容易得的病，也是让很多人一辈子不敢用 rebase 的心理阴影**——治愈它的药方就是这一章讲的两件事：（1）rebase 前挂 backup 分支；（2）出问题 `git reflog` 一看，救回来往往只需要一条命令。**你越用越会发现：rebase 不是烫手的山芋，它就是"造新珠子 + 挪名牌"的一种批量花式变奏。**

**误解二：\"amend 就是改一下 message，很小的操作。\"**
**"改" message 这件事在 Git 世界里根本不存在**——你在做的是**造一颗新珠子替换掉旧的**。第 2 章讲过这条，第 5 章要提醒你它的**实际后果**：如果你 amend 的那颗 commit **已经推送到远端了**，你本地的新珠子和远端的旧珠子是两颗不同的 commit——SHA 不同、historical identity 不同。下一次 push 就会 non-fast-forward 报错；如果你本能地 `--force` 上去，就是在给团队制造混乱（尤其如果是共享分支）。**amend 只在\"这颗 commit 我还没 push 过\"的情况下是完全安全的**；一旦已 push，它和 rebase、reset 一样受黄金规则的限制。**很多团队的 pre-push hook 会阻止对已推送 commit 的 amend，就是这个原因**——不是不让你改，是不让你在共享分享上单方面重写别人已经拥有的珠子。

**误解三：\"revert 就是 undo，能把项目状态回滚到之前。\"**
**revert 不是"回滚"，是"造一颗抵消珠子"**——两者在\"最终效果\"上可能相同，但\"如何达到\"的物理路径完全不同，也决定了对共享分支的安全性完全不同。回滚（reset --hard）是\"名牌往回挪，旧珠子成为野珠子\"——在共享分支上做就是灾难。revert 是\"往前造珠子\"——log 里错误珠子 X 依然存在，旁边多了 X⁻¹ 撤销它。**结果就是 revert 的历史更长（多了一颗珠子），但每一步都是可追溯的，都是"往前"造，没有任何珠子被"回收"**。这是**共享分支上唯一安全的撤销方式**。而且 revert 可以被再次 revert（"撤销这次撤销"），保持了完整的可追溯性——这对生产环境的事故回溯至关重要。**记住这条口诀：个人分支撤销用 reset（或 rebase），共享分支撤销用 revert。**

---

## 5.14 下一章预告

到这里，全书**第 1 部分 · 概念地图**正式结束——五张地图你已经全部走过一遍。你现在应该能做到：

- 用一句话说清仓库、提交、分支、远程、历史各是什么。
- 用\"造珠子 + 挪名牌\"这条原理推导出几乎所有 Git 命令的物理效果。
- 知道每一条操作是绿色（放心用）、黄色（先看后做）、还是黄红交界（force push 到共享分支）。
- 拥有 reflog 这道心理防线：几乎所有\"哎呀丢了\"都能救回。

**从下一章开始，你进入第 2 部分 · 场景决策手册（第 6-11 章）**。前五章教你\"地图上有什么\"，后六章教你\"面对具体场景该选哪条路\"——从\"懂了\"到\"会选\"。

**第 6 章《日常提交：让 AI 写出有灵魂的 commit》**：把第 2 章讲的\"commit 是团队通信协议\"落地成日常工作流。为什么 commit message 应该遵循 Conventional Commits、AI 时代\"一次 AI 编辑 = 一次原子提交\"的 Aider 范式、从 diff 生成有语义的 message、批量整理 wip commit 成干净原子提交——所有这些都会用到第 5 章讲的 interactive rebase、amend、backup 分支这套武器。**从这一章开始，前五章的地图会变成你在真实场景里选路的直觉。**

---

> **🤖 AI 指令箱 · 本章实战演练**
>
> 找一个你自己的真实仓库（或临时 clone 一个开源项目做沙盒），按顺序执行下面这几条。**每一条执行前都先建 backup 分支 + `git reflog`**——把这两步做成肌肉记忆。
>
> - **练 merge 三种情形**：「造一个空目录、git init，造 3 颗 commit 在 main 上。开一个 feature 分支、造 2 颗 commit。回 main。做一次 `git merge feature`——发生了什么（fast-forward 还是三方合并）？现在再造场景：从 main 分岔开 feature 之后，main 上也造一颗新 commit，让两条真的分叉。再 merge——这次呢？告诉我 log --graph 长什么样、`refs/heads/main` 指向哪颗珠子、有没有 merge commit。」
> - **练 interactive rebase**：「造一段脏历史：main 上 10 颗 commit，其中 3 颗是 'wip'、2 颗是 'typo'、1 颗是 'oops'——message 都是随便糊的。整理这段历史成 4 颗干净的原子 commit，用 rebase -i。先建 backup/before-cleanup 分支；然后停下来让我选剧本；执行完对比 log 前后。」
> - **练 reflog 救援**：「先做一次故意搞砸：`git reset --hard HEAD~5`（假装我不小心执行了）。之后请用 reflog 找回被抛弃的 5 颗 commit，把 main 恢复到 reset 之前的位置。展示 reflog 里那次 reset 的记录、以及恢复用的具体命令。」
> - **练 revert vs reset 的选择**：「main 上第 4 颗 commit（假设 SHA a1b2c3d）是错的。假设 (a) 这条分支只有我一个人：用什么撤销？为什么？(b) 这条分支已经推到远端、其他 5 个人从上面拉过：用什么撤销？为什么？两种方式各操作一遍，展示 log 前后对比。」
> - **练 --force-with-lease 的边界**：「在本地 feature 分支上 rebase 一次（造新 SHA）。尝试 `git push`——观察被拒的报错。用 `--force-with-lease` 推——成功。现在做一个恶意场景：让 AI 假装同事往远端推了一颗新 commit（其实是从另一个 clone 里 push 上去），你不 fetch 就 `--force-with-lease` 推——观察 lease 是否拦下了这次推送。」
