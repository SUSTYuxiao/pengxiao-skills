---
name: docs-notes
description: 项目文档与调查笔记（docs / spec / notes / lessons）规范的接入器与维护入口：作用域内固定 docs 记当前事实、spec 记可验证契约、notes 记证据与根因，lessons 按需；AGENTS.md 作文档路由入口，开工按任务类型路由、变更触发维护、结束验证链接。当用户要求把规范接入某项目或某 skill、建立三目录体系、迁移已有 Trellis/ADR 布局、写调查笔记、整理文档、周期整理、自动整理或维护 docs-notes skill 本身时触发。借鉴 DSH 文章思想，并非其官方规范或源码复刻。
version: 0.4.1
group: engineering
---

# docs-notes：项目文档与调查笔记

本 skill 是**接入器与维护入口**，不承载目标项目的日常规范。接入时把自包含的 `references/DOCS_NOTES.md` 复制到目标作用域，并按 `references/agents-reference.md` 写入简短路由片段。目标项目运行时只依赖自己的 `DOCS_NOTES.md`，不依赖本 skill 或四份写作参考。

- 接入/维护对象：普通项目根、用户明确指定的子目录，或本仓某个 skill。
- 目标默认结构：`AGENTS.md`、`DOCS_NOTES.md`、`docs/index.md`、`spec/index.md`、`notes/index.md`；`LESSONS.md` 或既有短章节按需。
- 四份写作参考只留在本 skill，不复制到目标项目，避免文档膨胀。

## 按任务路由（只读必要 ref）

| 任务 | 读 |
|---|---|
| 接入项目 / 子目录 / 其他 skill，或更新已接入副本 | `references/agents-reference.md`、`references/DOCS_NOTES.md` |
| 写或改 `docs/` | `references/docs.md` |
| 写或改 `spec/` | `references/spec.md` |
| 写或改 `notes/` | `references/notes.md` |
| 写或改 lessons | `references/lessons.md` |
| 整理文档 / 周期整理 / 自动整理 | `references/maintenance.md` + 本文件；目标作用域只读入口与核心 `DOCS_NOTES.md`，按需再读 `notes.md`、`lessons.md`、`docs.md`、`spec.md`，不通读全库 |
| 迁移已有 docs / spec / ADR 布局 | `references/DOCS_NOTES.md` + 相关写作 ref |
| 退出 Trellis（仅此时） | `references/trellis-migration.md` |
| 只改本规范自身 | 本文件 + 相关 ref；不自动接入全源仓 |

## 接入流程

1. **定作用域**：与用户确认项目根或明确子目录；解析软链到真实路径，分发安装副本不能作写入目标。目标明确时不重问，已有布局先清点。
2. **装核心**：把 `references/DOCS_NOTES.md` 复制到作用域根。普通项目可选托管块；其他 skill 的自有副本必须删除托管标记、顶部“托管说明……”整段注释、版本与分发源指针。
3. **写路由**：按 `references/agents-reference.md` 的短模板并入作用域 `AGENTS.md`；保留块外内容与本地修改，重复接入原位三方合并，不追加第二块；无变更 no-op。
4. **建三目录**：`docs/ spec/ notes/` 必备，入口默认小写 `index.md`，已有入口沿用；lessons 按需，不默认建 `lessons/` 目录。
5. **验收入口**：链接、路径、失效条件一致；无机器绝对路径、无未替换待填项；子目录作用域只约束其内，父层 `AGENTS.md` 仍适用。

## 维护

仅在源仓库维护本 skill，已接入目标不自动跟进。周期整理是一次显式调用的一次有界 pass，不是后台能力；它只在目标范围与写授权内运行，不自行建 scheduler、hooks、CI、提交或推送。详细流程见 `references/maintenance.md`。改行为级内容时递增 `SKILL.md` 版本，并同步 `README.md` 与根 `AGENTS.md` 的简介行；模板块标记版本随块内容递增。详细合并 / 升级规则见 `references/agents-reference.md`。

## 红线

- 只读任务不写；写入受任务授权约束，不自动发布、提交、推送或改全局配置。
- 不把四份写作 ref 复制进目标；不建空目录空文档；不要求每次任务产 note。
- 不声称所有宿主都会自动加载 `AGENTS.md`：接入后核验宿主实际发现范围，父会话发现不了子入口时只在已授权父路径加导航，未授权则如实报告。
- Trellis 已完全退出：保留 spec 与业务历史，删除活跃工具，不做归档执行框架、兼容软恢复或全局改动。
