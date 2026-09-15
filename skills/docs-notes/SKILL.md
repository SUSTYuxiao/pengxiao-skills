---
name: docs-notes
description: 项目文档与调查笔记（docs / notes）规范的接入器与维护入口：docs 只记当前事实（目标/边界/模块/契约/操作/限制），notes 只记因果与证据（调查/决策/踩坑），按主题检索、防重复调查。当用户要求把文档规范接入某项目或某 skill、建立 docs/notes 体系、写调查笔记、沉淀踩坑与决策结论、更新 docs-notes skill 本身时触发。借鉴 DSH 文章思想，并非其官方规范或源码复刻。
version: 0.3.1
group: engineering
---

# docs-notes：项目文档与调查笔记

一份规范、两种载体：本 skill 是**接入器与维护入口**。接入普通项目时，把 `references/DOCS_NOTES.md` 复制到目标权威根（自包含，目标项目不依赖本 skill 的其他文件）；接入其他 skill 时，只把 `references/agents-reference.md` 里的自维护约定模板复制进目标 SKILL.md——无托管块、无版本标记、无分发源声明，复制后即目标自有内容，由目标 git 维护。

借鉴声明：借鉴 DSH 文章思想，并非 DSH 官方规范或源码复刻，已按团队实际裁剪，不依赖外部原文或 PDF 路径。

## 两条操作线

| 线 | 触发 | 改哪里 |
|---|---|---|
| 接入 | 用户要求把规范装进目标项目 / 其他 skill | 目标项目的权威根 + 其 AGENTS.md |
| 维护 | 用户要求改规范本身 | 仅本 skill 源码（源仓库） |

普通业务执行**不加载本 skill**：目标项目的日常 docs / notes 写作由其入口文件承载；维护约定仅在维护对应 skill 时读取。

## 接入流程

1. **定目标**：与用户确认目标（普通项目，或本仓某个 skill）与权威根目录——规范文件放哪、docs / notes 布局放哪；用户未指定权威根就先问，不猜。`readlink -f` 解析真实路径后再判定：指向权威源码（本仓源仓库，或目标项目 / skill 真身，`~/.agents/skills` 等软链落到真身即合法）可接入；分发安装副本不能作写入目标，可作模板读取来源；无法确认权威源 → 如实报告并询问，不编造"正确目标"。目标已有 docs 目录 / Trellis spec / ADR / 设计文档体系一律复用（已有 ADR 能承接结论的不补 notes 新层），不另建平行体系。
2. **选载体**：接入普通项目 → 把 `references/DOCS_NOTES.md` 复制到权威根（只填文末"本项目布局"节，骨架示例的 `{{...}}` 属规范内容保留），并把 `references/agents-reference.md` 的项目片段并入目标 AGENTS.md（`{DOCS_NOTES_PATH}` 换成规范相对目标根的真实相对路径；目标已有同主题无标记块的指令不默默替换，报告冲突；无 AGENTS.md 则仅在用户授权范围内创建）；接入其他 skill → 把 `references/agents-reference.md` 的自维护约定模板复制进目标 SKILL.md（占位符只留布局行），目标已有 AGENTS.md 再同步引用。建 docs / notes 内容时骨架见规范第 4 / 5 节，有真实内容才落盘。
3. **写入并保护本地修改**：同义并入不重排，冲突交用户裁决，无变更即 no-op；禁止整块替换、禁止仅凭版本号判断改动归属。更新协议细节见 `references/agents-reference.md`，不在本文件展开。
4. **验收**：实际被引用的文件存在（尚未按需创建的 docs / notes 目录只要求路径合法）；无机器绝对路径；README / docs 人类入口能真实找到目标、边界、架构、操作、限制——缺导航补链接，缺内容如实报告，不编造，不以"目录存在"判达标。

接入完成后，目标项目不依赖本 skill 源文件或任何机器绝对路径。

## 维护

仅当用户明确要求改规范本身时走本节，且只在**源仓库**操作。源仓库判定：git 仓库且同时含 `pskills/` 与 `skills/`；路径是软链先解析到真身再判定。

1. 改 `references/DOCS_NOTES.md`。自包含是铁律：目标项目只复制这一份，禁止引用 skill 内其他文件。
2. `references/agents-reference.md` 中项目片段保持 `docs-notes:begin/end` 标记块结构（合并定位依据），块标记版本随块内容变化递增，可与 release 版本不同；自维护约定模板无标记块，复制后归目标所有，不随本 skill 更新。
3. 递增本文件 frontmatter `version`；托管块内容有变时同步递增对应 begin 标记版本。
4. 行为级变化同步本仓 README.md 的 skill 清单。
5. 已接入的项目不自动跟进，由各项目重跑接入流程更新副本（按更新协议执行）。

## 红线

- 分发安装副本（`.pengxiao-skills/`、`~/.pengxiao-skills/` 等安装拷贝）不作为接入目标写入；软链先解析到真身，写入目标须指向权威源码。
- 不默认接入本仓库自身——本仓是 skill 源，不是业务目标；用户点名才做。
- 不建空目录空文档；不要求每次任务产 note。
- 任务计划、执行日志、会话记录不进 docs / notes。
- 只做 markdown 规范：不新增脚本、hooks、CI。

## 维护约定（仅维护时读取，日常使用本 skill 不加载）

- docs 记当前事实（本 skill 即 SKILL.md + references/），notes/ 记因果与证据（一主题一文件）。
- 只有能避免重复调查或踩坑时才写 note，不建空文档；写前按主题查重。
- note 保留状态（pending / active / superseded）、证据、结论、失效条件四要素，其余字段按需；被实质推翻的旧 note 标 superseded 并链接新 note，保留不删。
- 旧结论用于当前判断前，核验其适用性与关键证据；笔记不授权危险操作、不存凭证。
