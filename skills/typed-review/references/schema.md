# YAML 契约

以下只描述 v1 最小契约。生成新配置时不要添加 runner 未实现的字段。

```yaml
config_version: 1

state_prefix: |
  可选。写入审核对象、读者和材料边界，先于输入内容拼入 state。

runtime:
  base_url_env: JEV_BASE_URL      # 也可用 TYPESAFE_BASE_URL
  api_key_env: JEV_API_KEY        # 本地 laya 可用 local-no-auth 占位
  model: jev-latest
  timeout_seconds: 15
  concurrency: 4

inputs:
  report:
    path: docs/report.md          # 相对 YAML 所在目录
    max_bytes: 200000             # 可选，默认 1000000

checks:
  - id: evidence_without_source
    input: report
    severity: warning             # warning 或 blocker
    message: 事实性结论缺少可追溯证据。
    question:
      type: noul                  # noul / choice / score
      instructions: "The text states a measurable factual claim without showing its source, command, data, or concrete example."
    flag_when:
      metric: noul                # noul / score / confidence / probability / choice
      operator: ">="              # >= > <= < ==
      value: 0.70
    uncertain_when:               # 可选；命中时优先于 pass/flag
      metric: noul
      gte: 0.40
      lte: 0.60
```

## 字段规则

- `inputs` 是映射；key 是输入 ID，`path` 指向本地文件。
- `checks[].input` 必须引用已有输入 ID。
- `question.type=noul` 只允许 `instructions`。
- `question.type=choice` 的 `criteria` 是映射，key 是选项名，value 是选项说明。
- `question.type=score` 的 `criteria` 是列表，从低到高描述刻度。
- `metric=probability` 时必须提供 `choice`，表示取该选项概率。
- `metric=choice` 时 `value` 是期望选项名，只支持 `==`。
- `uncertain_when` 只支持数值型 metric 与 `gte` / `lte`。

## 初始阈值

以下是保守起始档，不是通用最优阈值：

- `noul`：`flag_when >= 0.70`；`uncertain_when 0.55–0.70`。
- `choice`：先判断期望选项；`confidence <= 0.50` 时进入 uncertain。
- `score`：先定义刻度方向，再用真实正反例回放选择阈值。

mock 样例只验证协议和状态机。阈值校准要使用带人工结论的真实正反例，并记录规则版本、requested model、actual model、分数与人工预期。

## 结果状态

- `pass`：规则未命中，且不在不确定区。
- `flag`：规则命中，需要处理。
- `uncertain`:模型结果落在配置的不确定区，需要人工复核。
- `error`：请求、响应或配置执行失败。
- `not_sent`：dry-run 模式，所有规则均未发送。

## 退出码

- `0`：全部 pass。
- `1`：存在 flag 或 uncertain。
- `2`：配置、输入或执行错误。
- `3`：dry-run 未发送。
