---
name: docs-notes
description: 项目知识规范接入与整理：把自包含的 docs（当前事实）/ spec（可验证契约）/ notes（证据与根因）/ lessons（按需）规范接入普通项目、指定子目录或其他 skill，并支持更新已接入副本、显式整理（含必要的既有布局迁移）与维护本 skill 自身。目标项目日常写作只依赖其自带的 DOCS_NOTES.md 与 AGENTS.md，不回读本 skill。当用户要求接入或更新文档规范、显式整理文档与调查笔记、迁移已有 docs/spec/ADR 布局，或维护 docs-notes skill 本身时触发。
version: 0.4.2
group: engineering
---

# docs-notes：项目知识规范接入与整理

本 skill 是**接入器与整理维护入口**，不承载目标项目的日常规范。接入时把自包含的 `references/DOCS_NOTES.md` 复制到目标作用域，并按 `references/agents-reference.md` 写入简短路由片段。目标项目日常写作只依赖自己的 `DOCS_NOTES.md` 与 `AGENTS.md`，不回读本 skill，也不依赖四份写作参考运行。

- 接入/维护对象：普通项目根、用户明确指定的子目录，或本仓某个 skill。
- 目标默认结构：`AGENTS.md`、`DOCS_NOTES.md`、`docs/index.md`、`spec/index.md`、`notes/index.md`；`LESSONS.md` 或既有短章节按需。
- 四份写作参考只留在本 skill，不复制到目标项目，避免文档膨胀；它们是专项指导，可用于接入补齐、整理中遇到具体写法问题，或由其它任务显式引用，不需要执行整个 skill。

## 按任务路由（只读必要 ref）

| 任务 | 读 |
|---|---|
| 接入项目 / 子目录 / 其他 skill，或更新已接入副本 | `references/agents-reference.md`、`references/DOCS_NOTES.md` |
| 显式整理文档 / 周期整理（含必要布局迁移） | `references/maintenance.md` + 本文件；目标作用域只读入口与核心 `DOCS_NOTES.md` |
| 只改本规范自身 | 本文件；按需再读相关 ref |

四份写作参考（`references/docs.md`、`spec.md`、`notes.md`、`lessons.md`）不进主路由：只在接入补齐、整理具体写法问题或其它任务显式引用时按需读，不要求执行整个 skill，也不是目标项目的运行依赖。目标日常写 docs / spec / notes / lessons 由作用域自带的 `DOCS_NOTES.md` 指导，不回读源 skill。

## 接入流程

1. **定作用域**：与用户确认项目根或明确子目录；解析软链到真实路径，分发安装副本不能作写入目标。目标明确时不重问，已有布局先清点。
2. **装核心**：把 `references/DOCS_NOTES.md` 复制到作用域根。普通项目可选托管块；其他 skill 的自有副本必须删除托管标记、顶部“托管说明……”整段注释、版本与分发源指针。
3. **写路由**：按 `references/agents-reference.md` 的短模板并入作用域 `AGENTS.md`；保留块外内容与本地修改，重复接入原位三方合并，不追加第二块；无变更 no-op。
4. **建三目录**：`docs/ spec/ notes/` 必备，入口默认小写 `index.md`，已有入口沿用；lessons 按核心规范判定后接入，不默认建 `lessons/` 目录。
5. **验收入口**：链接、路径、失效条件一致；无机器绝对路径、无未替换待填项；子目录作用域只约束其内，父层 `AGENTS.md` 仍适用。
6. **接入补齐（按需）**：目标某层已有内容需要按写法细化时，只按需读对应写作 ref（`docs.md` / `spec.md` / `notes.md` / `lessons.md`），不改目标的日常运行依赖。

## 整理与维护

显式整理是一次有界 pass，包含核心规范齐备检查与必要的布局迁移；仅在目标范围与写授权内运行，不自行建 scheduler、hooks、CI、提交或推送。详细流程见 `references/maintenance.md`。

仅在源仓库维护本 skill，已接入目标不自动跟进。改行为级内容时递增 `SKILL.md` 版本，并同步 `README.md` 与根 `AGENTS.md` 的简介行；模板块标记版本随块内容递增。详细合并 / 升级规则见 `references/agents-reference.md`。

## 红线

- 只读任务不写；写入受任务授权约束，不自动发布、提交、推送或改全局配置。
- 不把四份写作 ref 复制进目标；不建空目录空文档；不要求每次任务产 note；目标日常写作不回读源 skill。
- 不声称所有宿主都会自动加载 `AGENTS.md`：接入后核验宿主实际发现范围，父会话发现不了子入口时只在已授权父路径加导航，未授权则如实报告。
- Trellis 退出是需明确授权的按需专项，不是普通整理的默认动作；未获授权时只做只读清点与报告，不删运行时或框架工具。保留 spec 与业务历史。
