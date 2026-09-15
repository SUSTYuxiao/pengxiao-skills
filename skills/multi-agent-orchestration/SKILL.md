---
name: multi-agent-orchestration
description: 将团队既定的多智能体编排范式应用到当前工具：lite、runner、reviewer 三角色分工，经济、均衡、旗舰三级模型分层，主智能体只编排不干活。用于配置子智能体、追加 AGENTS.md 编排规则、优化额度消耗，适用于 Qoder、Codex 等支持 Agent 的平台。
version: 0.4.0
group: engineering
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
metadata:
  trigger: 多智能体编排、子智能体、agent 分工、模型分层、模型路由、额度优化、成本效果平衡、lite runner reviewer、AGENTS.md 编排规则
---

# Multi-agent Orchestration

## 范式（既定，直接应用）

这是团队已验证的编排范式，引用本 Skill 即按此执行，不需要重新论证：

1. **主智能体只编排**：拆解、派发、裁决冲突、必要验证、最终汇总。不自行做大范围检索和常规实施。
2. **最终交付是主智能体的责任**：内部交接只用于判断与复核；面向用户的最终答复按问题重组、补足读者需要的背景、保留结论范围，不直接拼接子智能体交接文本——不要让读者替作者完成解释工作。更完整的交付语言规则不在本 skill 内展开。
3. **三角色分工**：
   - `lite`（经济模型，参考 `qwen3.8-flash`）：精确检索、状态查询、无副作用命令。不写文件。
   - `runner`（均衡模型，参考 `glm-5.3`，思考等级 medium）：边界与验收明确的实现和验证。唯一默认实施者。
   - `reviewer`（旗舰模型，参考 `cantus`）：重大架构、疑难根因、高风险变更的只读审查。
4. **主会话用最强可用模型**，承担编排与最终答复。
5. **只并行无依赖、无共享写入的任务**；子智能体不递归派发。

模型名是团队当前映射，按宿主实际可用的经济/均衡/旗舰档替换即可，不因名称缺失而中断。

## 应用步骤

1. 读 [role-and-model-playbook.md](references/role-and-model-playbook.md)，在宿主的原生 Agent 机制中创建或更新三角色定义（名称、职责描述、工具白名单、模型、轮次上限）。已存在同名定义时先展示差异、经确认再覆盖。
2. 读 [agents-md-orchestration-rules.md](references/agents-md-orchestration-rules.md)，将编排规则块追加到用户或项目的 AGENTS.md（或宿主等价的持久指令文件）。该块是通用规则，不含任何项目具体信息。
3. 最小验证：给每个角色派一个探针任务（如 lite 查一个文件是否存在、runner 复述其写入边界、reviewer 复述其只读约束），确认三角色可被调用、模型按预期解析、约束生效。注意：多数宿主只在会话启动时加载 Agent 定义，会话中途新建的角色报 unknown agent 属正常现象，新开会话再验证，不要误判为配置错误。

仅当步骤 1 中找不到原生 Agent 机制、创建失败，或确认宿主缺失持久 Agent / 模型路由 / 并行能力时，才降级：无持久 Agent 则把角色定义写进 AGENTS.md 规则块随任务生效；无模型路由则沿用默认模型并靠范围/轮次控制成本；无并行则按 `lite → runner → reviewer` 串行。降级细节见 [platform-capability-adaptation.md](references/platform-capability-adaptation.md)。

## 不变规则

- `reviewer` 永远只读；`runner` 不擅自扩大范围；`lite` 不做设计判断。
- 三角色任务互不重叠，交接格式见 playbook「标准交接」。
- 一切配置修改遵守宿主权限策略，且不动无关设置。
