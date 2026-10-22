# note：skill 自身维护目录收敛到 .skill-meta/

**版本**: v0.4.3  
**日期**: 2026-10-22

## 问题

原 `skills/docs-notes/` 顶层有两类文件混在一起：

1. **分发模板**（`references/`）：要复制到目标项目的规范
2. **skill 自身维护笔记**（顶层 `notes/`）：设计依据、根因、演进记录

布局不清晰，目录职责混淆。

## 决策

创建 `.skill-meta/` 作为 skill 自身维护目录统一收口：

- 迁移路径：`notes/` → `.skill-meta/notes/`
- 后续可扩展：`.skill-meta/docs/`（如有 skill 自身文档）、`.skill-meta/spec/`（如有行为契约）
- 不分发到目标项目，只服务本 skill 开发维护

## 结构

```
skills/docs-notes/
├── SKILL.md              # 入口与路由
├── references/           # 分发模板
└── .skill-meta/         # skill 自身维护目录（不分发）
    └── notes/           # 设计笔记与根因
```

## 依据

- 遵循 docs-notes 自身规范：结构清晰、职责分离
- `.skill-meta/` 命名明确表达"skill 内部元数据"，避免与目标项目的 `docs/ notes/` 混淆
- 后续所有 pengxiao-skills 仓库的 skill 可遵循同一惯例

## 影响范围

- **skill 内部引用**：无，index.md 引用都是相对路径
- **已接入目标项目**：无影响，目标项目用的是自己的 DOCS_NOTES.md，不回读 skill 源
- **SKILL.md**：增加结构说明段落，版本号升至 0.4.3
