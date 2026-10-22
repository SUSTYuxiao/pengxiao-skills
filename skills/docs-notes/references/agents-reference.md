# AGENTS / SKILL 接入片段（docs-notes）

本文件是接入器的模板参考，不是目标项目运行依赖；只在接入或更新目标时读取。核心规范与维护规则在 `DOCS_NOTES.md`，四份写作参考（`docs.md`、`spec.md`、`notes.md`、`lessons.md`）留在本 skill，不复制到目标。

## 1. 作用域与目标类型

- 作用域是整个项目根，或用户明确指定的子目录（含其他 skill 所在目录）。作用域内固定 `AGENTS.md`、`DOCS_NOTES.md`、`docs/index.md`、`spec/index.md`、`notes/index.md`；`LESSONS.md` 或既有短章节按需，不默认建 `lessons/` 目录。
- 普通项目与子目录默认同结构；其他 skill 同样建完整作用域，但使用**无托管副本**：`DOCS_NOTES.md` 删除 `docs-notes:spec:begin/end` 两行、顶部"托管说明"整段注释、版本与分发源指针；其 `AGENTS.md` 片段也必须删除 `docs-notes:begin/end` 两行与任何托管/版本指针，两份文件都不得残留上游标记，之后由目标 Git 单通道维护。目标 `SKILL.md` 的维护节最多只链接作用域 `AGENTS.md`，不重复路由正文。
- 父层 `AGENTS.md` 保留且仍适用；子作用域片段只约束其下目录，不重写父层规则。跨目录任务按实际改动范围分别读对应作用域的 `AGENTS.md` 与规范。
- 路径一律相对作用域根书写；已有入口路径、现 `LESSONS.md` 或既有 lesson 章节按实际动态引用。没有 lessons 载体时删除模板中的 lesson 行，不留悬空链接。

## 2. 可直接插入的短模板

以下标记块可直接并入作用域 `AGENTS.md`（默认入口、无 lesson 版本）。接入已有布局时，把 `spec/index.md`、`docs/index.md`、`notes/index.md` 三处链接动态替换为实际已有入口的相对路径（例如 `spec/SPEC.md`），不新建第二入口；没有 lesson 载体时整行删除。

### 平铺模式短模板（默认，适用于已有项目）

以下标记块可直接并入作用域 `AGENTS.md`（默认入口、无 lesson 版本）：

<!-- docs-notes:begin v0.5.0（本块由 pengxiao-skills 的 docs-notes skill 维护，勿把项目自有指令写进块内） -->

## 文档与调查笔记（docs-notes）

- 本目录范围遵循 [DOCS_NOTES.md](DOCS_NOTES.md)：固定 `docs/`、`spec/`、`notes/` 三个必备目录并纳入 Git，lessons 按需。
- 开工按任务读入口：[spec](spec/index.md) 用于代码、配置、行为变更前必读的契约；[docs](docs/index.md) 用于现状、架构、操作、边界；[notes](notes/index.md) 用于证据、根因与既有结论。
- 改动前按本次操作匹配 [防错经验](LESSONS.md)。
- 维护与收尾：事实改 `docs/`，契约改 `spec/`，证据与根因进 `notes/`，触发 → 动作经验按需进 lessons；新增 / 移动 / 删除文档同步入口，收尾核验链接与失效条件；只读任务不写，写入受任务授权约束。

<!-- docs-notes:end -->

可选替换项：

- 默认入口是 `docs/index.md`、`spec/index.md`、`notes/index.md`；已有其他入口路径时在原位沿用，并同步写入 `DOCS_NOTES.md` 文末"本项目布局"。
- 第三条是可选的 lesson 深读引导：存在 lesson 载体时才保留，把链接换成真实相对链接或章节锚点（如 `LESSONS.md`、`docs/standards.md#lessons`）；不存在时整行删除，不留悬空链接。


### 统一目录模式短模板（推荐新项目）

统一目录模式下使用以下模板（路径相对 `doc-note/`）：

<!-- docs-notes:begin v0.5.0（本块由 pengxiao-skills 的 docs-notes skill 维护，勿把项目自有指令写进块内） -->

## 文档与调查笔记（docs-notes）

- 本目录范围遵循 [DOCS_NOTES.md](doc-note/DOCS_NOTES.md)：固定 `doc-note/docs/`、`doc-note/spec/`、`doc-note/notes/` 三个必备目录并纳入 Git，lessons 按需。
- 开工按任务读入口：[spec](doc-note/spec/index.md) 用于代码、配置、行为变更前必读的契约；[docs](doc-note/docs/index.md) 用于现状、架构、操作、边界；[notes](doc-note/notes/index.md) 用于证据、根因与既有结论。
- 改动前按本次操作匹配 [防错经验](doc-note/LESSONS.md)。
- 维护与收尾：事实改 `doc-note/docs/`，契约改 `doc-note/spec/`，证据与根因进 `doc-note/notes/`，触发 → 动作经验按需进 lessons；新增 / 移动 / 删除文档同步入口，收尾核验链接与失效条件；只读任务不写，写入受任务授权约束。

<!-- docs-notes:end -->

可选替换项同平铺模式，只需在路径前加 `doc-note/` 前缀。
- 接入其他 skill 或明确自维护目标时，使用同一模板但删除 `docs-notes:begin/end` 两行；`DOCS_NOTES.md` 同时删除 `docs-notes:spec:begin/end`、顶部托管说明、版本与分发源指针。两份文件均无托管标记，随后由目标 Git 单通道维护；`SKILL.md` 维护节只写"文档与调查约定见本 skill 作用域 `AGENTS.md`"。

## 3. 合并与升级规则

1. **先定位再合并**：在目标查找现有 `docs-notes:begin/end` 或 `docs-notes:spec:begin/end` 标记块；只对已有块做原位三方合并，不追加第二块。取不到旧模板时只列候选变更并报告，不覆盖。
2. **本地优先**：块外内容与块内本地修改原样保留；同一句有本地改写时以本地为准。无标记块但已有同主题指令不静默替换，报告真实冲突交用户裁决。
3. **逐项比对**：按 bullet / 段落对照旧模板、新模板与目标现状，判断新增、删除、改写；不凭版本号整块覆盖。无差异即 no-op，不做无意义重写。
4. **版本标记**：托管块标记版本随块内容变化递增，可与 skill release 版本不同；`DOCS_NOTES.md` 的 `docs-notes:spec:*` 版本同理。skill 自有副本删除全部标记与版本，不再接收上游合并。
5. **更新顺序**：先更新自包含核心 `DOCS_NOTES.md`，再并入 `AGENTS.md` 短模板，最后补三目录入口；`SKILL.md` 只保留 `AGENTS.md` 链接。

## 4. 宿主发现范围核验

`AGENTS.md` 是接入核心，但**不假定所有宿主自动加载**：不同平台对子目录入口的发现范围不同。接入后按宿主实际机制核验能否发现本作用域的 `AGENTS.md`（查看注册/扫描目录、用新会话或重启验证，并如实记录结果）。

- 父会话能发现子作用域入口时，无需额外导航。
- 父会话不能发现子入口、且用户已授权父路径时，才在父 `AGENTS.md` 加一行导航；未授权父路径写入时如实报告限制，不擅改。
- 本文件的临时接入模拟只验证文件与链接结构，不宣称真实宿主自动加载通过。

## 5. 接入与验收入口

1. 解析软链到真实路径；分发安装副本（`.pengxiao-skills/`、`~/.pengxiao-skills/` 等）不能作写入目标，只可读模板。
2. 清点已有 `docs/`、Trellis spec、ADR、设计文档、入口与未提交改动；真实冲突交用户裁决。
3. 复制自包含核心到作用域根；按需并入短模板；建 `docs/ spec/ notes/` 与入口（默认小写 `index.md`，既有入口沿用，空层写"暂无记录"）。
4. 验收：三层入口存在且链接可达；无未替换待填项与机器绝对路径；无第二份托管块；父层内容保留；目标明确时不重问；只读任务不写入。
