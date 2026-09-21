---
name: typed-review
description: 根据用户自定义审核要求生成或维护静态检查 YAML，并用 uv 驱动的 Python runner 并发调用 TypeSafe/JEV 标准端点，输出代码、文章或报告的结构化检查结果。当用户要构建发布前 review、文章质量审核、总结报告验收或 reader-first 结果检查工作流时使用。
version: 0.1.0
---

# typed-review：可复现的 TypeSafe/JEV 审核工作流

本 skill 把一次性审核诉求沉淀成两个稳定产物：一份静态 YAML 规则，以及一个可由 `uv run` 直接执行的 runner。它不做通用静态分析，也不替用户修改文章或代码；只输出 `pass`、`flag`、`uncertain`、`error` 和 `not_sent`。

## 使用流程

1. 先读用户给出的审核对象和验收要求，把要求拆成少量、可判定的封闭问题。
2. 复制 `examples/reader-first.yaml` 或按 `references/schema.md` 生成 YAML：
   - 每条规则一个问题；
   - 不同输入、chunk 或 diff hunk 分开请求；
   - `severity` 由规则配置决定，不把模型置信度当严重程度；
   - threshold 必须显式写入，不隐藏在 runner 里。
3. 用 dry-run 确认输入、规则和 endpoint：
   ```bash
   uv run references/runner.py examples/reader-first.yaml --input report=/path/to/report.md
   ```
4. 需要实际检查时加 `--send`：
   ```bash
   uv run references/runner.py examples/reader-first.yaml \
     --input report=/path/to/report.md \
     --base-url "$JEV_BASE_URL" --send
   ```
5. 只解释结果，不自动改文。`flag` 表示规则命中；`uncertain` 表示需要人工或更强模型复核；`error` 表示执行失败，不得当作通过。

## 生成规则

- 问题必须窄化到可判定事实，例如“结论是否超出材料范围”，不要写“文章质量是否不好”。
- 中文审核规则要用中文材料校准阈值；CJK 效果不能直接沿用英文示例。
- `noul` 用 `noul` 概率判断；`choice` 需明确使用 `choice`、`confidence` 或某个选项的 `probability`；`score` 需明确使用 `score` 或 `confidence`。
- 对发布有阻断影响的规则先设为 `warning`，积累真实误报和漏报证据后再升为 `blocker`。
- 默认一个 check 一个请求，便于并发和定位；不要把多个独立对象塞进同一个 state。

## 阈值校准

首轮生成可以使用保守起始档，但必须把它当作未校准默认值，而不是模型天然正确的业务阈值：

- `noul`：`flag_when >= 0.70`，`uncertain_when 0.55–0.70`；低于 `0.55` 才视为 pass。
- `choice`：先判断期望选项，再把 `confidence <= 0.50` 的结果放入 uncertain；没有人工样本前不要直接 blocker。
- `score`：没有通用默认阈值，必须先写明刻度方向和业务含义，再用样本回放确定。
- mock 或构造样例只用来验证请求、响应和状态机；阈值选择至少要有少量真实正反例，升级 blocker 前建议各有 20 个以上历史样本。
- 保留每次回放的规则版本、requested model、actual model、分数和人工结论；用误报、漏报和 uncertain 占比选择阈值，而不是只看单个案例。
- 阈值调整后要重放旧样本，确认没有把原本可判定的结果大量推入 uncertain。

## 产物边界

- skill 内 runner 可直接运行；如审核配置要独立交付，把 `runner.py` 与 YAML 放到同一个交付目录。
- 不提交密钥。endpoint 和 API key 优先通过环境变量或命令行注入。
- 数据安全隔离由用户负责；处理非公开内容时推荐本地或自管内网部署。详见 `README.md`。

## 参考

- `references/schema.md`：YAML 契约和退出码。
- `references/runner.py`：uv 内联依赖 runner。
- `examples/reader-first.yaml`：面向 reader-first 报告的最小示例。
