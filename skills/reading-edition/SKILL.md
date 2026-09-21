---
name: reading-edition
description: 把技术 Markdown 报告转成单文件自包含的 HTML 阅读版：受众自适应、结论前置、按需折叠、信息零丢失，md 为唯一事实基线。Use when the user asks to 把报告/文档转成 HTML 阅读版、可视化版本，或同步修订已有 HTML 阅读版。
version: 0.3.3
---

# reading-edition

把一份技术 Markdown 报告转换成给人读的单文件 HTML 阅读版。与 eli5 的分工：eli5 向零基础读者解释一个概念；本 skill 转换既有报告——受众未知、信息已定，一次到位。

Source: $ARGUMENTS（完整 md 正文或本地文件路径均可）

本质要求：受众自适应、结论前置、按需折叠、信息零丢失、单文件自包含、措辞客观、md 是唯一事实基线。

产物落源 md 同目录、同名 .html（如 docs/report/x.md → docs/report/x.html），是面向用户的交付物，不使用 runtime 目录。

受众判断与结构规划自己设定；细则按需读 references/ 下与当前上下文匹配的进一步要求，交付前对照 rigor.md 自检修正，一次性交付。

## 维护约定（仅维护时读取，日常使用本 skill 不加载）

- docs 记当前事实（本 skill 即 SKILL.md + docs/design.md + references/），notes/ 记因果与证据（一主题一文件）。
- 只有能避免重复调查或踩坑时才写 note，不建空文档；写前按主题查重。
- note 保留状态（pending / active / superseded）、证据、结论、失效条件四要素，其余字段按需；被实质推翻的旧 note 标 superseded 并链接新 note，保留不删。
- 旧结论用于当前判断前，核验其适用性与关键证据；笔记不授权危险操作、不存凭证。
