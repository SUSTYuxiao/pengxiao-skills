# 导出契约 — 本平台记忆写入数据根 raw/

任何平台的 agent 向数据根 `~/.personal-memory/raw/` 导出自己的记忆前，遵守以下约定。

## 路径与命名

```
raw/<平台名>/<导出日期 YYYY-MM-DD>/<scope-slug>.md
```

每个记忆作用域（工作区/项目）一个文件，scope-slug 取路径末段 + 短哈希。

## frontmatter schema

```yaml
source: qoder            # 平台名
scope_id: /path/to/ws    # 记忆所属工作区/范围
exported_at: 2026-09-12
origin: platform-native  # platform-native  = 平台自产记忆
                         # user-authored    = 用户手写、存放在该平台的规则/配置
                         # derived-from-wiki = 由本库 wiki 派生的副本
counts: {memory: 41, scenario: 112, keyword: 160}
```

## 四条不变量

1. **只追加**：不删除、不改写、不覆盖既有文件；同日重跑也写新文件名（后缀 -2、-3…）。
2. **不做语义清洗**：不去重、不合并、不筛选、不改写；只做格式清洗（私有格式 → 可读 Markdown）。
3. **保真优先**：宁可附加原始 JSON，不改写原文含义；丢弃的内容必须在文末"未导出声明"列出。
4. **诚实条款**：无法读取的部分（如二进制索引正文）必须在文末声明缺口，不许静默导出有损子集。

## 补充取证产物

除按 scope 的主导出外，允许 `artifact` 类文件（如正文抢救 `memory-bodies.md`）：
frontmatter 用 `artifact:` 标明类型，scope 可为全局（各记录自带 scope_id 字段）；
文末必须声明与主导出文件的关联方式及剩余缺口。

## 上浮约定（供上浮方参考）

上浮只吃 `origin: platform-native` 与 `user-authored` 的条目；`derived-from-wiki` 对上浮透明、不吸收。
