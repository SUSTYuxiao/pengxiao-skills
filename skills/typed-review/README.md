# typed-review

把用户的审核要求固化成 YAML，并通过 TypeSafe/JEV 标准端点并发执行封闭问题检查。适合发布前代码 review 辅助、文章低质量检查、报告自定义验收，以及 reader-first 交付审阅。

## 快速使用

以下命令从本仓库根执行；复制到其他项目后改为实际 runner 与 YAML 路径。

```bash
# 只展示将执行的输入与规则，不发送网络请求
uv run skills/typed-review/references/runner.py \
  skills/typed-review/examples/reader-first.yaml \
  --input report=/path/to/report.md

# 实际发送到标准 /v1/systemone 端点
export JEV_BASE_URL="http://127.0.0.1:15666"
export JEV_API_KEY="local-no-auth"   # 本地 laya 网关会忽略该值
uv run skills/typed-review/references/runner.py \
  skills/typed-review/examples/reader-first.yaml \
  --input report=/path/to/report.md --send
```

## 数据安全声明

本 skill 不内置隐私扫描、脱敏、密钥检测或发送审批流程。**数据安全隔离由使用者自行负责。**

- 审核非公开代码、文章或报告时，推荐使用本地 laya 或自管内网部署。
- 使用他人部署的 endpoint 前，先确认该服务与网络边界符合自己的数据安全要求。
- 不要把 API key 写入 YAML、命令历史或结果文件。
- runner 的 JSON/Markdown 输出默认不包含原文 state；调试需要由用户显式扩展。

## 阈值校准

`reader-first.yaml` 是五条底线的候选问题示例，不等于完整验收；默认全部为 `warning`。当前示例 `<0.55` 为 pass，`0.55–0.70`（含两端）为 uncertain，`>0.70` 为 flag。虽然 flag 条件写了 `>=0.70`，runner 会先判 uncertain，故边界 0.70 不算 flag。

这些数值只是未校准的起点。mock 验证程序，合成正反例检查规则方向，带人工结论的真实样本才用于效果评估。比较误报、漏报与不确定比例，并用未参与调参的样本验证；不把固定样本数当作可靠性保证。当前没有自动调参工具，样本标签与规则版本需要额外留存。

## 使用成熟度

当前版本用于辅助审阅，不作为无人值守发布门禁。长文可能受服务端输入长度限制；未确认覆盖范围时不能把 pass 解释为全文通过。runner 不自动分段、检测截断或校准阈值；Markdown 顶层错误渲染仍有已知限制，错误诊断优先使用 JSON。

## 退出码

| 退出码 | 含义 |
|---:|---|
| 0 | 全部规则为 pass |
| 1 | 存在 flag 或 uncertain，需要人工处理 |
| 2 | 配置、输入或执行错误 |
| 3 | dry-run，请求未发送 |

`severity` 不影响退出码：全是 warning 的检查仍可能返回 1。不要把退出码 1 直接作为发布阻断条件。

## 产物形态

长期项目建议只保留一个稳定 runner，多个场景各自维护 YAML：

```text
.review/
├── runner.py
├── reader-first.yaml
├── code-review.yaml
└── article-review.yaml
```

独立交付一个审核配置时，可以将 `runner.py` 与 YAML 放在同一个目录，保证交付物自包含。
