# typed-review

把用户的审核要求固化成 YAML，并通过 TypeSafe/JEV 标准端点并发执行封闭问题检查。适合发布前代码 review 辅助、文章低质量检查、报告自定义验收，以及 reader-first 交付审阅。

## 快速使用

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

`reader-first.yaml` 里的 `noul >= 0.70` 与 `0.55–0.70` uncertain 只是保守起始档，不是校准结论。mock 样例适合验证链路和状态机；要调整阈值，应保存真实正反例和人工结论，重放不同阈值后比较误报、漏报与 uncertain 占比。升级为 blocker 前，建议正反例各有 20 个以上。

## 退出码

| 退出码 | 含义 |
|---:|---|
| 0 | 全部规则为 pass |
| 1 | 存在 flag 或 uncertain，需要人工处理 |
| 2 | 配置、输入或执行错误 |
| 3 | dry-run，请求未发送 |

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
