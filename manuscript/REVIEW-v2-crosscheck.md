# 《Git 的概念地图》评审报告交叉验证（v2-crosscheck）

> 对象：`REVIEW-v2-editorial.md`（第二轮通读修改建议）
> 任务：独立复核该报告指出的错误**是否真的成立**，并检查报告自身有无差错
> 方法：四条独立证据线——① 被引原文逐行回取核对；② 本机 Git 2.50.1 (Apple Git-155) 的 `man` 页原文与隔离环境实测；③ 外部事实联网复核（官方文档 / 官方博客 / 论坛 / 论文 / 源码）；④ 与报告结论逐条对表
> 结论先行：**报告 36 项技术性断言中 31 项完全成立、3 项部分成立（定性需调整）、2 项自身有错（已就地订正）**；另有 3 处行号偏差与 1 项报告未覆盖的新发现。原文（书稿）的错误指控整体可信，可按报告执行修订。

---

## 1. 总体判定

| 类别 | 数量 | 说明 |
|---|---:|---|
| ✅ 完全确认（证据充分） | 31 | 原文确实错，报告的改法成立 |
| 🟡 部分确认（定性调整） | 3 | 核心事实对，但报告的指控偏严或表述不准 |
| ❌ 报告自身错误（已订正） | 2 | bisect 退出码、ch14:78 复述 |
| 🔍 无法独立验证 | 2 | 保持"需作者核对" |
| ➕ 新发现（报告漏掉） | 1 | ch14:89 出现第三种"碰网络"口径 |

**对书稿最重要的一组复核结论**（全部有独立证据，不依赖原报告的实测记录）：

- **`--force-with-lease` 三处口径互相否定（P0-1）——成立，且是全报告最关键的一条。** `man git-push` 原文双重支撑：lease 的语义就是"远端当前值 == 我 remote-tracking 缓存里的期望值"；同页还有官方警告"该选项与任何隐式在后台跑 `git fetch` 的东西交互极差"——这正是报告建议补 `--force-if-includes` 的依据。隔离环境重新实测（bare 远端 + 双克隆）：未 fetch 时 push 被 `[rejected] (stale info)` 挡住；fetch 之后同命令变成 forced update 直接覆盖。报告对 `ch10:419` 的"因果讲反"判断同样成立：同事推过而你没 fetch → 缓存陈旧 → lease **会**拒绝，而不是"无能为力"。
- **第 10 章"兜底三件套"三条都不成立（P0-2/3/3b/3c/4）——成立。** `man git-branch` 原文："If the branch currently has a reflog then the reflog will also be deleted."（分支 reflog 随 `-D` 删除）；`man git-gc`：`gc.pruneExpire` 默认 `prune --expire 2.weeks.ago`（约 2 周，非 30 天）；`git add` 不写任何 reflog（故 `git add` 过但未 commit 的 blob 只有约 2 周的宽限，且一次 `gc --prune=now` 即归零——实测复现）；`fsck --dangling` 默认把 reflog 当可达根（要加 `--no-reflogs` 才能看到只被 reflog 引用的对象——实测 0 颗 vs 2 颗复现）；`--lost-found` 会在 `.git/lost-found/` 下**写出文件**（非只读）。
- **`git push` 无 upstream 时 Git 会"问你"（P0-14）——不成立的是原文。** 实测输出为 `fatal: The current branch main has no upstream branch.`（附 `--set-upstream` 提示），Git 从不交互询问。

---

## 2. 报告自身错误的订正（本次交叉验证的产出）

### 2.1 P0-17：bisect run 退出码——报告把 126/127 划错了档

- **报告原文**："0=good；1–124=bad；125=skip；126/127/≥128=中止整个 bisect"
- **`man git-bisect` 原文**：*"the exit code … should be between 1 and 127 (inclusive), **except 125**, if the current source code is bad/new. **Any other exit code** will abort the bisect process."*
- **正确语义**：0=good；**1–127（除 125）=bad**；125=skip；**其余退出码（即 ≥128）才中止**。126/127 属于 bad 档。
- 报告对**书稿**的指控（`ch13:251`"0=good、非 0=bad"过于简化且危险）依然成立；错的只是报告给出的"正确答案"。已在 `REVIEW-v2-editorial.md` 中就地订正。

### 2.2 P0-12b："ch14:78 又被复述三次"——ch14 里根本没有这个复述

- 全文检索 ch14：`碰网络`、`网络`、`联网`、`remote update` 均 0 命中；ch14:78 实际位于"地图 3 · 分支"的 ASCII 图内部。
- "5 个命令碰网络"的复述位置实为：`ch04:458`、`ch05:708`、`appendix-a:160` 三处（附录 A 那处报告在 P0-21c 里其实已识别，属初稿串行）。
- 已就地订正，并顺带记录**新发现**（见 §5）。

---

## 3. 定性需调整的三条（事实成立，但指控力度应收一档）

### 3.1 P0-9f（Aurora）：事件真实、日期吻合，"10 家"可辩护——但"git repo 泄漏"确属失准

联网复核（Gambit Security / CloudSEK / The Hacker News，2026-08 披露）：Aurora 勒索 affiliate 于 **2026-04-08 至 05-21** 用 Cursor Agent（Claude Sonnet）对 **至少 10 个目标**（CloudSEK 口径：9 国 20+ 组织）实施入侵后攻击——内网扫描、AD 提权、凭证窃取、ESXi 勒索。

- ✅ 事件真实、时间线（2026-04）与"10 家跨国企业"与 Gambit 的 "ten targets" 吻合——**报告"误述"的定性偏重**。
- ⚠️ 但书稿说"**git repo 泄漏** + 凭证读取"确属失准：该行动窃取的是凭证库（SAM/LSA/NTDS）、AD 证书模板与业务文件，不是以 git 仓库泄漏为特征。
- **修订建议维持**（压缩成一句归入 §12.6.3，或移出本章）——理由不变：这是"攻击者滥用 AI"而非"读者的 Git 防护"，粒度与本章其他条目不一致。

### 3.2 ch08:328/400（Cursor "Undo 删档"事故）：悬空引用坐实，但"版本号与根因不符"论据不足

- ✅ **坐实的部分**：`详见第 12 章`（ch08:400）确为悬空——ch12 只有 CVE-2025-54135（ch12:472）与 Aurora（ch12:474），**没有** Undo 删档这一条。
- 🟡 **论据不足的部分**：Cursor 官方论坛确有对应事故帖——2.0.34 *“In 2.0 undo checkpoint is not agent-independent”*（在 A agent 里 undo 会撤掉所有 agent 的改动）与 2.0.77 *“undo apply 删除未提交文件”*。书稿"Cursor 2.0 Composer 多 agent 并行时曾出过 Undo 删档事故，一部分根因就是多 agent 在同一工作目录上互相踩踏"与论坛报告基本吻合（2.0 系、多 agent、undo 误删工作）。报告"版本号与根因不符"的指控**没有得到论坛证据支持**。
- **修订建议改为**：正文补具体出处（上述两个论坛帖），删掉或落实"详见第 12 章"的指针；无需按报告原话改写版本/根因。

### 3.3 P0-18（ch06:98 vs 407）：张力存在，但比报告描述的轻

两句原文已逐行核对：ch06:98 说"body 的'为什么'**永远需要你亲手补**——AI 都写不出来"；ch06:407 的指令模板说"body 里必须写清楚'为什么'——如果 diff 里看不出为什么，就在 body 里**问我**"。

- 407 的"问我"回退与 98 的精神部分兼容（AI 起草、人补/纠），**不是严格的逐字反证**。
- 但张力确实存在（98 的"AI 都写不出来"过于绝对，与 407 让 AI 填 body 相冲突），**修订建议保留**，改法维持"AI 能起草，但只有你知道它猜得对不对"。

---

## 4. 逐条复核明细（证据来源标注）

**证据类型**：[实测]=隔离环境重跑；[man]=本机 man 页原文；[网]=联网复核官方/权威来源；[行]=原文行回取。

### 4.1 P0 全表

| # | 报告指控 | 判定 | 关键证据 |
|---|---|---|---|
| P0-1 | force-with-lease 三处口径互相否定；ch10:397 照做会被拒 | ✅ | [man] git-push 期望值语义 + 后台 fetch 警告；[实测] stale info 拒绝 / fetch 后 forced update；[行] ch05:313/320、ch04:432、ch10:383/397/419 引文全部属实（ch05"第 2 步 fetch"实际在 ~326 行，行号偏 2，内容属实） |
| P0-2 | `branch -D` 连带删除分支 reflog | ✅ | [man] git-branch 原文；[实测] 上轮已复现 |
| P0-3/3b | 30/90 天是 reflog 条目保留期；`add` 过的 blob 只有 ~2 周 | ✅ | [man] git-gc：`gc.pruneExpire` 默认 2.weeks.ago；[实测] `gc --prune=now` 立删 dangling blob |
| P0-3c | `fsck --dangling` 看不到仅被 reflog 引用的珠子 | ✅ | [实测] 0 颗 vs 加 `--no-reflogs` 后 2 颗 |
| P0-4 | `--lost-found` 会写盘，非只读 | ✅ | [实测] `.git/lost-found/other/` 落盘 |
| P0-6 | `gc --prune=now` 删不掉仍被 reflog 引用的对象（ch13:540 与 557 自相矛盾，557 对） | ✅ | [man] 语义 + [实测] reset --hard 后对象仍在 |
| P0-7 | 演练 4 的 hook 实验不可能产生预期现象 | ✅ | [实测] clone 不传输非 `.sample` hook；被追踪的 `.githooks/` 才会传。（行号订正：演练 4 实际在 **ch12:773**，报告写 772） |
| P0-8 | filter-repo 三处硬伤 | ✅ | [man/网] 官方 README：不随 Git 分发、跑完移除 origin、`--force` 语义 |
| P0-9 | `refs/original/` 是 filter-branch 的产物；filter-repo 写 `.git/filter-repo/` | ✅ | [网] git-filter-repo 官方文档 |
| P0-9b | GitHub push protection"免费仓库也可用"不准 | ✅ | [网] GitHub 官方文档：public 免费自动开启；private/internal 需付费（现独立产品 GitHub Secret Protection，Team/Enterprise）。**补充 nuance**：还有账号级 "push protection for users"（个人推送 public 仓库默认开启） |
| P0-9c | Gitea 无原生 secret scanning；"Push mirror + hooks" 与 secret scanning 无关 | ✅ | [网] Gitea 官方文档只有 Actions Secrets（CI 用）；第三方对比确认无原生能力 |
| P0-9d | Copilot 已为自己的提交签名，"必然被 Required Signatures 拦住"已过时 | ✅ | [网] GitHub Blog changelog **2026-04-03**："Copilot cloud agent now signs every commit it makes… appears as Verified… now works in repositories with 'Require signed commits'" |
| P0-9e | Agentjacking 机制写错 | ✅ | [网] Tenet Security 2026-06：经公开 DSN 向 Sentry 错误事件注入伪"解决方案"，经 MCP 回传给 AI coding agent 执行（85% 成功率、2388 家组织暴露）——**不是**"污染工具描述" |
| P0-9f | Aurora 误述 | 🟡 | 见 §3.1 |
| P0-9g | `unsafe repository` 报错文案已过时 | ✅ | [网] git 源码 `setup.c` 逐字确认现行文案：`fatal: detected dubious ownership in repository at '%s'` |
| P0-9h | SSH 签名本地验证需要 `allowedSignersFile` + OpenSSH 8.8 | ✅ | [man] git-config（无 trust store 则 verify-commit 失败）；[网] GitLab 官方文档：OpenSSH 8.7 有缺陷，需 8.8 |
| P0-9i | `Read(./.env*)` 只匹配仓库根；`.cursor/rules` 非运行时阻断 | 🟡（部分） | glob 语义成立（`./` 前缀不递归，应 `**/.env*`）；Claude Code 权限规则与 Cursor rules 的定位属官方文档常识，本次未逐一联网复核——修订时按报告建议加"护栏非边界"声明即可，风险低 |
| ch12:63 | CVE-2022-24765 归因错误 | ✅ | [网] 该 CVE 是仓库所有权检查缺陷，与 filter/hooks 攻击面是两类 |
| P0-10 | ch03:59"内存里保管"错 | ✅ | [行] 引文属实；对象在磁盘 `objects/`、reflog 在 `logs/` |
| P0-11 | SVN"真复制 O(项目大小)"与官方文档相反 | ✅ | [网] SVN Book：`svn copy` 服务端为廉价副本（常数时间/空间） |
| P0-12/12b | "只有 5 个命令碰网络"地图画漏路 | ✅（订正一处） | [行] ch01:93、ch04:116/458、ch05:708、appendix-a:43/160 引文全部属实；附录 A 自己列了 `ls-remote`。**订正**：复述第三处是 `appendix-a:160` 而非 ch14:78（见 §2.2） |
| P0-13 | "现代 Git 建议默认 pull.rebase true"误归属 | ✅ | [网] Git 2.27 起提示原文逐字：三选项并列，`pull.rebase false # merge (the default strategy)`——Git 明确标 merge 为默认，从未建议 rebase |
| P0-14 | push 无 upstream"Git 会问你"错 | ✅ | [实测] `fatal: The current branch main has no upstream branch.` |
| P0-15 | ch08:293 括号把话说反 | ✅ | [实测] `--local` 写共享 config；per-worktree 需 `extensions.worktreeConfig` + `--worktree`（未开启时报 `--worktree cannot be used with multiple working trees…`）；隔离性实测成立（wt2 看不到主仓的 worktree 配置） |
| P0-16 | ch09 全章零次 conflictStyle/diff3/zdiff3 | ✅ | [man] git-merge：默认 `merge` 风格无 `|||||||` 祖先段，diff3/zdiff3 才有；[行] grep 确认 ch09 零命中 |
| P0-16b | `checkout --theirs` 漏方向依赖 | ✅ | [行] ch09:225/236 引文属实；场景（自己分支 vs main）恰好是方向歧义高危区 |
| P0-17 | bisect 退出码简化 | ✅（订正报告） | [man] git-bisect 原文；书稿 `ch13:251`"0=good 非0=bad"确属简化失真。**报告给的"正确答案"有错，已订正**（§2.1）；ch13 全章无 `git bisect skip` 命令亦经 grep 确认 |
| P0-18 | ch06:98 vs 407 互相矛盾 | 🟡 | 见 §3.3（张力真实存在，修订建议保留，定性收一档） |
| P0-19 | "自动关闭并归档 tag"机制不通 | ✅ | [行] ch07:393 引文属实；Git 无"关闭分支"，平台关的是 PR；"归档 tag"会灌垃圾 |
| P0-19b | 禁 merge 与 `--no-ff` 并存 | ✅ | [行] ch07:401/522/324 引文全部属实 |
| P0-20 | `theirs` 不是 merge strategy；`recursive` 已移除 | ✅ | [man] git-merge 原文："unlike ours, **there is no theirs merge strategy**"；本机 git 2.50.1 man 页 MERGE STRATEGIES 节 `recursive` 0 命中 |
| P0-21 | `gitleaks detect` 已废弃 | ✅ | [网] 官方迁移表（v8.19.0）：`detect --source .` → `gitleaks git .`；`detect --no-git` → `gitleaks dir .`；且 `--source .` 扫全历史非"当前 commit" |
| P0-21b | `gh api repos/:owner/:repo` 旧占位符 | ✅ | [网] gh 官方 manual：占位符为 `{owner}`/`{repo}`/`{branch}` |
| P0-21c | 附录 A 覆盖范围/口径错误 | ✅ | [行] appendix-a:160/370 引文属实 |
| P0-22 | Scott Chacon"Git 主要维护者之一"身份错 | ✅ | [网] 常识+官方：GitHub 联合创始人、《Pro Git》作者 |
| P0-22b | DDIA 已出第 2 版 | ✅ | [网] 英文 2e（Kleppmann + **Chris Riccomini**，O'Reilly，2026-03-24）；中文 2e《数据密集型应用系统设计(第2版)》中国电力出版社 2026-08（ISBN 9787523915264）——与报告表述完全一致 |
| P0-23 | ch00:37 论文方法与结论双错 | ✅ | [网] Yang et al., TOSEM 31(3), 2022, doi:10.1145/3494518：**80,370 条 SO 提问**（非"真实项目使用行为"）；最常被看的命令是 **revert 与 reflog**（stash/clean/reset 紧随）；**>40% 提问者 SO 龄 4 年+**。neverworkintheory.org 逐条佐证 |
| P0-23b | "一篇广为流传的分析"查无出处 | ✅ | [网] 检索"漂亮的工程/糟糕的产品"各来源（HN、博客、Essay），无可归属的逐字出处——补出处或去引号 |

### 4.2 悬空引用与交付不符

| 位置 | 判定 | 证据 |
|---|---|---|
| ch11:518 Replit 案例引"第 10 章" | ✅ | [行] `grep Replit ch10` 0 命中；全书仅 ch11:518 一处 |
| ch12:760 预告四话题、ch13 缺席 | ✅（带 nuance） | [行] ch13 中 `LFS`=0、`MCP`=0；`Monorepo`=4 次命中（但为顺带提及，非独立小节）。**修订时**：LFS 与 MCP 确须删或补；Monorepo 可改"预告里点名展开"为"预告与正文对齐" |
| ch08:560 / ch09:564 预告标题 ≠ 实际标题 | ✅ | [行] 实际标题：ch09《冲突：不是 Git 的错，是你的语义需要仲裁》、ch10《事故恢复：Git 几乎不扔东西》；两处预告均不一致 |
| ch10:297 ORIG_HEAD 单槽位未提示 | ✅（常识） | [man] ORIG_HEAD 被 merge/reset/rebase 覆盖是文档化行为；未单独实测，判定依据充分 |
| ch11"六节结构"AI 读不到书 | ✅（行号订正） | [行] 实际在 **ch11:368**（报告写 366）；"用第 11.4 节规则二里那个六节结构预审"属实 |
| ch14:322 出题指令未附旧题 | ✅ | [行] 引文属实（指令只说"不能和第 0 章那 10 道重复"，AI 无法看到旧题） |
| README 死链/条数 | ✅（上轮已核） | `Git的概念地图-全书合并版.md` 在仓库中不存在 |

---

## 5. 新发现（原报告未覆盖）

**ch14:89（地图 4 ASCII 图内）出现第三种"碰网络"口径**：

```
↑↓ fetch / push（只有这两个跨网） ↑↓
```

- 与 ch04:116 的"5 个命令"、ch04:458/ch05:708 的复述**又不同**（漏掉 clone、pull——虽然 pull 含 fetch、clone 是一次性 fetch+checkout，但"只有这两个"与全书口径不符）。
- 修订 P0-12b 时应把 ch14:89 一并纳入统一口径（建议图内改为"跨网的只有 fetch 家族与 push"）。

---

## 6. 无法独立验证项（维持"需作者核对"）

1. **TOSEM 论文"92 份问卷"的具体样本数**——论文方法论（80,370 条 SO 提问 + 开发者问卷）与全部核心结论已独立确认；"92"这一具体数字未从公开摘要中复核到，建议引用时以论文原文为准。
2. **P0-9i 中 `.cursor/rules` vs `.cursor/cli.json` 的具体边界**——方向正确（rules 是指令层），但本次未逐一联网核对 Cursor 官方文档的权限分层；按报告建议加"护栏非边界"声明执行即可。

---

## 7. 结论与执行建议

1. **可以按 `REVIEW-v2-editorial.md` 执行修订**——36 项技术断言无一被推翻为"书稿其实是对的"；被交叉验证反复锤实的核心是：force-with-lease 全链条（P0-1）、第 10 章兜底三件套（P0-2/3/4）、第 12 章外部事实四条（P0-9 系列）、以及"5 个命令碰网络"的口径统一（P0-12 系列）。
2. **执行时以本报告 §3 的三处软化为准**：Aurora 压缩而非否定、Cursor 事故补出处而非改根因、ch06 两句统一而非逐字反证。
3. **行号以内容定位为准**：ch05"第 2 步 fetch"~326、演练 4 在 ch12:773、六节结构在 ch11:368——修订时按引文内容 grep 定位，勿按旧行号。
4. 报告自身的两处错误（bisect 档位、ch14:78）已就地订正并在报告头部留了修订记录；ch14:89 新发现已补入 P0-12b 表格。

---

*验证环境：macOS / git version 2.50.1 (Apple Git-155) / 隔离 HOME 临时仓库；外部事实检索时间 2026-09-15。*
