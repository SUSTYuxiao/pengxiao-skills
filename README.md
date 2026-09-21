# pengxiao-skills

个人 Agent Skills 仓库（https://github.com/SUSTYuxiao/pengxiao-skills），通过 `pskills` CLI 分发到各项目复用。

## 一键引入

默认装到**用户级**、跨项目共享。把下面这段发给你任意会话里的 agent，它会自动完成安装与激活：

```
帮我用 pskills CLI 引入个人 Agent Skills：先执行 `uv tool install git+ssh://git@github.com:SUSTYuxiao/pengxiao-skills.git` 安装全局命令，再执行 `pskills sync -g` 完成用户级安装与软链激活（实体在 ~/.pengxiao-skills，激活到 ~/.agents/skills 与 ~/.claude/skills，跨项目共享、不入任何 git；交互多选要激活的 skill，非交互默认全选）。完成后执行 `pskills list -g` 汇报安装与激活结果。若远端 clone 失败或落后于本地，可改用 `--repo <本机已有的仓库克隆路径> --branch main` 临时从本地同步。
```

仅当某项目需要锁定独立版本时，才在该项目根目录执行 `pskills sync` 做项目级安装（实体进项目的 `.pengxiao-skills/`，`.version` 记来源 commit）。

## Skills

| Skill | 版本 | 说明 |
|---|---|---|
| `multi-agent-orchestration` | 0.4.0 | 把既定的多智能体编排范式落到当前工具：lite / runner / reviewer 三角色分工，经济 / 均衡 / 旗舰三级模型分层，主智能体只编排不干活；适用 Qoder / Codex 等支持 Agent 的平台 |
| `eli5` | 0.1.0 | 把任意主题讲成"给 5 岁小孩听"的极简 HTML 图解（大图、少字） |
| `docs-notes` | 0.3.2 | 项目文档与调查笔记规范接入器：docs 记当前事实，notes 记因果与证据，按主题检索防重复调查；把自包含 DOCS_NOTES.md 装进目标项目，或把自维护约定并入其他 skill（自身设计决策见其 notes/） |
| `reader-first` | 0.1.0 | 组织和审阅回复与报告，让读者无需替作者补齐解释；提供全局交付底线的显式检查与安装入口 |
| `typed-review` | 0.1.0 | 把代码、文章或报告的自定义审核要求固化为 YAML，并通过 uv 驱动的 TypeSafe/JEV runner 并发输出结构化检查结果 |
| `reading-edition` | 0.3.3 | 把技术 Markdown 报告转单文件自包含 HTML 阅读版——受众自适应、结论前置、按需折叠、信息零丢失；分布优先纯 CSS 占比条，Tailwind 仅内联编译产物，轻量图表脚本需严格视觉验收 |
| `personal-memory` | 1.0.0 | 用户个人记忆库接入：读规范 / 接入 / 导出 / 整理上浮四路由，数据根固定 `~/.personal-memory`（INDEX.md 按需导航，缺失不自动初始化、不默认扫 raw） |

reader-first 的前置研究结论（问题定义、证据来源与强度、候选发现、方案决策、失效条件）见 [notes/reader-first-research.md](notes/reader-first-research.md)；其评估产物在 `temp/reader-first/`（临时目录，不入分发）。

## 引入模式

只有 light 拷贝一种模式（无 subtree 反哺）：

- **用户级（默认推荐）**：`pskills sync -g` —— 实体放 `~/.pengxiao-skills/`，软链激活到 `~/.agents/skills/` 与 `~/.claude/skills/`，跨项目共享、不入任何 git。
- **项目级（按需）**：`pskills sync` —— clone 上游后**拷贝** skill 到项目 `.pengxiao-skills/skills/`（`.version` 记来源 commit）；后续 `sync` 重新拷贝覆盖更新。适合为单个项目锁定版本。

软链激活到哪个 agent 目录：项目根有 `.agents/` 时只激活它（Qoder 与 Codex 都从 `.agents/skills/` 读）；没有则自动检测已存在的 `.qoder/` 与 `.claude/` 并对每个建链；都不存在兜底建 `.qoder/skills/`。`--config-dir` 可强制指定单个目录。

## 常用命令

| 场景 | 命令 | 说明 |
|---|---|---|
| 首次安装 CLI | `uv tool install git+ssh://git@github.com:SUSTYuxiao/pengxiao-skills.git` | 装全局 `pskills` 命令（仅首次或手动升级时用） |
| 后续升级 CLI | 任意一次 `pskills sync`（含 `-g`） | sync 时自动比对上游版本并重装 CLI 自身（勿用 `uv tool upgrade`，对 git 源锁 commit） |
| 安装 / 更新（用户级，默认） | `pskills sync -g` | 实体入 `~/.pengxiao-skills/` 并激活到用户级 agent 目录 |
| 项目级引入 / 更新 | `pskills sync` | 拷贝全部 skill 到项目 `.pengxiao-skills/` 并激活；交互终端弹多选确认激活集（新 skill 默认不勾） |
| 列出 skill | `pskills list` | 显示 version、git 更新时间与激活状态 |
| 激活 | `pskills add <skill>` 或 `pskills add --all` | 建软链（无参交互选择，只增不减） |
| 取消激活 | `pskills rm <skill>` | 移除软链（不删实体） |

以上命令默认作用于项目级，`-g` 作用于用户级；`--repo` / `--branch` 可临时指定上游（默认本仓远端 `main` 分支，本机路径不作默认值）。
