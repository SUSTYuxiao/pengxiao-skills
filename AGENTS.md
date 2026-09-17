# AGENTS.md

## 项目定位

个人 Agent Skills 仓库（张鹏霄）。唯一产物是 skill，通过 `pskills` CLI（light 拷贝 + 软链激活）分发到各业务项目复用。本仓不独立运行，而是被 clone / 拷贝到宿主项目的 `.pengxiao-skills/`（skill 在其 `skills/` 子目录下），再由软链激活到 agent 目录（`.agents/skills/` 或 `.qoder/skills/`、`.claude/skills/`）供其 agent 加载。

## 项目结构

```
pengxiao-skills/
├── AGENTS.md              # 本文件：仓库自述（定位 / 结构 / 运行环境 / 机制）
├── README.md              # 面向人：一键引入提示词 + Skills 清单 + 常用命令
├── pyproject.toml         # pskills CLI 打包（uv tool install 入口）
├── pskills/               # 分发 CLI（sync / add / rm / list）
│   ├── __init__.py
│   └── cli.py             # 单文件实现，移植自 ytalgo-data-skills ytskills 并简化
├── notes/                 # 研究笔记（如 reader-first 前置研究：问题定义 / 证据强度 / 决策与失效条件），不入分发
├── temp/                  # 临时评估产物（如 temp/reader-first/，主会话按需创建），不入分发
└── skills/                # 全部 skill（唯一产物区）
    ├── multi-agent-orchestration/  # 多智能体编排范式落地（Qoder / Codex 等）
    ├── reader-first/              # 回复与报告的组织、审阅，以及全局交付底线的显式安装
    ├── eli5/                       # 极简 HTML 图解（大图、少字）
    ├── docs-notes/                 # 项目文档与调查笔记规范接入器，自包含 DOCS_NOTES.md
    ├── reading-edition/            # 技术 Markdown 报告转单文件自包含 HTML 阅读版（迁自 odps 项目）
    └── personal-memory/            # 用户个人记忆库接入（读规范 / 接入 / 导出 / 整理上浮），数据根固定 ~/.personal-memory
```

`notes/` 与 `temp/` 是仓库内研究与评估区，不是分发产物；`pskills` 只识别并分发 `skills/`。调查依据保存在 notes，长期验收标准随 skill 分发，可重建的试验结果放 temp。

## 目标运行环境

- **宿主布局**：`pskills sync` 把 skill 拷贝到业务项目 `.pengxiao-skills/`（只含 `skills/` 与 `.version`），并把选定 skill 软链到 agent 目录的 `skills/<skill>`（指向 `../../.pengxiao-skills/skills/<skill>`）。项目根有 `.agents/` 时只链它（Qoder 与 Codex 同读），否则链已存在的 `.qoder/` 与 `.claude/`，都不存在兜底 `.qoder/`
- **加载机制**：宿主 agent 扫描其 `skills/` 目录，透过软链读 `<skill>/SKILL.md` 的 frontmatter（`name` / `description` / `version`）注册，按 `description` 匹配触发；**Qoder 需重启 / 新开窗口**重扫后软链 skill 才生效
- **全局模式**：`pskills sync -g` 实体放 `~/.pengxiao-skills/`，软链激活到 `~/.agents/skills` 与 `~/.claude/skills`，跨项目共享、无 git 参与

## Skill 机制

每个 skill 是 `skills/` 下一个含 `SKILL.md` 的子目录，YAML frontmatter 声明 `name` / `description` / `version`。`pskills` 以"含 `SKILL.md`"识别 skill，新增 skill 只需放进 `skills/`，无需改代码。`references/` 存放运行时引用的领域知识与脚本；skill 要自包含：依赖的样本或数据放进 skill 子目录（如 `skills/docs-notes/references/DOCS_NOTES.md`），不引用宿主项目路径。本仓无 group 概念、无激活黑名单。

## 分发与同步

只有 light 拷贝一种模式，无 subtree 反哺。**默认推荐用户级安装**（`pskills sync -g`，跨项目共享）；项目级仅在需为单项目锁定版本时使用：

- `pskills sync`：唯一数据入口。首次 = clone 上游 → 拷贝全部 skill 到 `.pengxiao-skills/skills/` → 选定项建软链（`.version` 写来源 commit）；后续 = 重新拷贝覆盖更新，交互终端弹多选确认激活集（新 skill 默认不勾）
- `pskills add` / `rm`：增删软链激活（`add` 无参且 tty 进交互多选，只增不减；`rm` 只删软链不删实体）
- `pskills list`：列 skill（version + git 更新时间 + 激活状态）
- 全部命令支持 `-g/--global`（作用于 `~/.pengxiao-skills/`）、`--repo` / `--branch`（临时指定上游，默认本仓 `main` 分支）、`--config-dir`（强制指定单个 agent 目录）、`--dry-run`
- CLI 自升级并入 `sync`：上游 `pyproject.toml` 版本更新时自动 `uv tool install --reinstall`（下次运行生效）
