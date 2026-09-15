# pengxiao-skills

个人 Agent Skills 仓库（https://github.com/SUSTYuxiao/pengxiao-skills），通过 `pskills` CLI 分发到各项目复用。

## 一键引入

把下面这段发给你项目里的 agent，它会自动完成安装与引入：

```
帮我用 pskills CLI 引入个人 Agent Skills：先执行 `uv tool install git+ssh://git@github.com/SUSTYuxiao/pengxiao-skills.git` 安装全局命令，再在本项目根目录执行 `pskills sync` 完成首次引入与软链激活（light 拷贝；交互多选要激活的 skill，非交互默认全选；自动识别项目里已有的 .agents / .qoder / .claude 目录，分别激活到各自的 skills/）。若远端尚未推送最新内容导致 clone 失败，改用 `pskills sync --repo /Users/pengxiao/code/pengxiao-skills --branch main` 从本地仓库同步。完成后执行 `pskills list` 汇报引入与激活结果。
```

## Skills

| Skill | 版本 | 说明 |
|---|---|---|
| `multi-agent-orchestration` | 0.3.0 | 把既定的多智能体编排范式落到当前工具：lite / runner / reviewer 三角色分工，经济 / 均衡 / 旗舰三级模型分层，主智能体只编排不干活；适用 Qoder / Codex 等支持 Agent 的平台 |
| `eli5` | 0.1.0 | 把任意主题讲成"给 5 岁小孩听"的极简 HTML 图解（大图、少字） |
| `docs-notes` | 0.2.1 | 项目文档与调查笔记规范接入器：docs 记当前事实，notes 记因果与证据，按主题检索防重复调查；把自包含 DOCS_NOTES.md 装进目标项目或 skill |

## 引入模式

只有 light 拷贝一种模式（无 subtree 反哺）：

- **项目级**：`pskills sync` —— clone 上游后**拷贝** skill 到项目 `.pengxiao-skills/skills/`（`.version` 记来源 commit）；后续 `sync` 重新拷贝覆盖更新。
- **全局**：`pskills sync -g` —— 实体放 `~/.pengxiao-skills/`，软链激活到 `~/.agents/skills/` 与 `~/.claude/skills/`，跨项目共享、不入任何 git。

软链激活到哪个 agent 目录：项目根有 `.agents/` 时只激活它（Qoder 与 Codex 都从 `.agents/skills/` 读）；没有则自动检测已存在的 `.qoder/` 与 `.claude/` 并对每个建链；都不存在兜底建 `.qoder/skills/`。`--config-dir` 可强制指定单个目录。

## 常用命令

| 场景 | 命令 | 说明 |
|---|---|---|
| 首次安装 CLI | `uv tool install git+ssh://git@github.com/SUSTYuxiao/pengxiao-skills.git` | 装全局 `pskills` 命令（仅首次或手动升级时用） |
| 后续升级 CLI | `pskills sync` | sync 时自动比对上游版本并重装 CLI 自身（勿用 `uv tool upgrade`，对 git 源锁 commit） |
| 首次引入 / 更新 | `pskills sync` | 拷贝全部 skill 到 `.pengxiao-skills/` 并激活；交互终端弹多选确认激活集（新 skill 默认不勾） |
| 列出 skill | `pskills list` | 显示 version、git 更新时间与激活状态 |
| 激活 | `pskills add <skill>` 或 `pskills add --all` | 建软链（无参交互选择，只增不减） |
| 取消激活 | `pskills rm <skill>` | 移除软链（不删实体） |

以上项目级命令均支持 `-g` 作用于全局；`--repo` / `--branch` 可临时指定上游（默认本仓 `main` 分支）。
