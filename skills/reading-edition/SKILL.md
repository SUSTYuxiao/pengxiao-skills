---
name: reading-edition
description: 把技术 Markdown 报告转成单文件自包含的 HTML 阅读版：受众自适应、结论前置、按需折叠、信息零丢失，md 为唯一事实基线。Use when the user asks to 把报告/文档转成 HTML 阅读版、可视化版本，或同步修订已有 HTML 阅读版。
version: 0.3.0
---

# reading-edition

把一份技术 Markdown 报告转换成给人读的单文件 HTML 阅读版。与 eli5 的分工：eli5 向零基础读者解释一个概念；本 skill 转换既有报告——受众未知、信息已定，一次到位。

Source: $ARGUMENTS（完整 md 正文或本地文件路径均可）

本质要求：受众自适应、结论前置、按需折叠、信息零丢失、单文件自包含、措辞客观、md 是唯一事实基线。

产物落源 md 同目录、同名 .html（如 docs/report/x.md → docs/report/x.html），是面向用户的交付物，不使用 runtime 目录。

受众判断与结构规划自己设定；细则按需读 references/ 下与当前上下文匹配的进一步要求，交付前对照 rigor.md 自检修正，一次性交付。
