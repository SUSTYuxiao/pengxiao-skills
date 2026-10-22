# 主路由收窄为接入、整理与维护：日常写作交给目标自带规范

状态：active
范围：docs-notes v0.4.1 的定位与 SKILL 主路由边界；不涉及四份写作 ref 的内容本身
核验日期：2026-10-13

证据：
- 2026-10-13 用户裁决（本仓编辑授权）：保留调用名 docs-notes，标题与 description 定位为"项目知识规范接入与整理"；主路由只保留接入/更新、显式整理（含必要布局迁移）、维护本 skill 三类。
- 用户裁决同一轮：移除四条"写或改 docs / spec / notes / lessons"主路由与日常写作触发；日常由目标作用域 `AGENTS.md` → 自包含 `DOCS_NOTES.md` 指导，不回读源 skill。
- 同轮裁决：四份写作 ref 保留为专项指导，可用于接入补齐、整理具体问题或其它任务显式引用，不需要执行整个 skill，也不是目标运行依赖。
- 既有产物：v0.4.1 的 `SKILL.md`、`references/DOCS_NOTES.md`、`references/agents-reference.md`、`references/trellis-migration.md`，以及四份写作 ref（见 `note-skill接入完整结构与更新所有权.md`）。

问题：主路由是否应继续列出四条日常写作入口，让源 skill 承担目标项目的日常文档写作触发？

结论：
1. **调用名与定位**：命令名仍为 `docs-notes`，`description` 与标题改为"项目知识规范接入与整理"，触发词收敛到接入/更新规范、显式整理、迁移既有 docs/spec/ADR 布局、维护本 skill。
2. **主路由三件事**：接入/更新（读 `agents-reference.md` + `DOCS_NOTES.md`）、显式整理（读 `maintenance.md` + 本文件）、维护本 skill 自身。
3. **四份写作 ref 降为专项**：不进主路由，不复制到目标，不作为目标运行依赖；接入补齐、整理遇到具体写法问题或其它任务显式引用时才按需读。
4. **日常写作不回读源 skill**：目标作用域接入后，日常 docs / spec / notes / lessons 写作由自带 `AGENTS.md` 与 `DOCS_NOTES.md` 指导。
5. **整理中的迁移与 Trellis**：既有布局迁移作为整理的一个可选步骤，默认不挪文件，确有收益才迁并改活链接；Trellis 退出是按需专项且工具删除须有授权，不是普通整理默认动作。

不照搬/保留：`DOCS_NOTES.md` 的核心条款不变；四份写作 ref 正文不变；skill 版本按用户固定为 0.4.1，本次只改路由与定位，不改核心模板。

失效条件：用户要求恢复日常写作触发，或宿主日常任务反复因不触发源 skill 而缺失规范时重议。
