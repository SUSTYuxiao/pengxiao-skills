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
      gte: 0.55
      lte: 0.70
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

- 问题方向为“是否存在缺陷”时，`noul` 示例采用 `flag_when >= 0.70` 与闭区间 `uncertain_when 0.55–0.70`。uncertain 优先，因此实际 `<0.55` 为 pass，`0.55–0.70`（含两端）为 uncertain，`>0.70` 为 flag；0.70 不判 flag。方向相反时不能照搬。
- `choice`：在 `flag_when` 写明哪些结果属于问题；示例不确定区可配置为 `metric: confidence, gte: 0, lte: 0.50`。这不是经过校准的通用置信门槛。
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

## 执行参数与实际边界

- `--input ID=PATH` 可重复，覆盖 YAML 中已存在输入的路径；覆盖路径相对调用时工作目录。未覆盖的 `inputs.*.path` 相对 YAML 所在目录。
- 根端点按 `--base-url` → `runtime.base_url_env` 指向的环境变量 → `TYPESAFE_BASE_URL` 取值，无自动云端默认地址；推荐根地址，也接受末尾为 `/v1/systemone` 的完整接口地址并剥离该后缀。支持末尾斜杠；拒绝查询参数或片段。
- 密钥按 `--api-key` → `runtime.api_key_env` 指向的环境变量 → `local-no-auth` 取值。只有允许占位密钥的自管端点可用默认值；需要认证的服务必须配置实际密钥。
- `--concurrency` 覆盖 YAML 并发数；模型与超时在 YAML 配置。dry-run 验证配置并读输入，但不验证端点连通性，输出的 endpoint 为 null。
- `--format json|markdown` 选择输出，`--output PATH` 保存文件；默认 stdout。优先用 JSON 复盘：含各条答案、分数、模型、用量、错误与耗时，但无原文片段、人工标签或配置哈希，后者需另行保存。
- `severity` 只作元数据，不控制执行或退出码。uncertain 优先于 flag；任一请求 error 时整体 error；整体 flag 也可能仅由 uncertain 造成。
- 每个 check 只读取它引用的一个 input；`state_prefix` 拼在每份输入前。多个文件不会自动相互比较，不支持命令型输入、自动分段或自动校准。

已知限制：顶层配置错误的 Markdown 渲染不完整；错误诊断请先使用 JSON。runner 尚无完备的异常响应校验测试，不将本版本直接用作无人值守发布门禁。
