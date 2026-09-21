config_version: 1

state_prefix: |
  审核对象是一篇面向未参与调查读者的技术文章或报告。对每个问题，只判断该问题
  描述的问题是否存在；只依据材料本身判断，不用外部知识补证。读者需要理解对象、
  范围、证据、结论和未覆盖项，并据此决策。

runtime:
  base_url_env: JEV_BASE_URL
  api_key_env: JEV_API_KEY
  model: jev-latest
  timeout_seconds: 20
  concurrency: 5

inputs:
  report:
    path: docs/report.md
    max_bytes: 200000

checks:
  - id: independent_context_missing
    input: report
    severity: warning
    message: 对象、背景或范围对未参与调查的读者不自足。
    question:
      type: noul
      instructions: "For a reader who did not participate in the investigation, the document assumes unexplained context, or omits the object, background, scope, or reader relevance needed to understand it."
    flag_when:
      metric: noul
      operator: ">="
      value: 0.70
    uncertain_when:
      metric: noul
      gte: 0.55
      lte: 0.70

  - id: question_alignment_missing
    input: report
    severity: warning
    message: 结构没有围绕读者需要回答的问题组织。
    question:
      type: noul
      instructions: "The document is organized around the author's investigation sequence, internal handoff material, or a fixed template instead of the question the intended reader needs answered."
    flag_when:
      metric: noul
      operator: ">="
      value: 0.70
    uncertain_when:
      metric: noul
      gte: 0.55
      lte: 0.70

  - id: evidence_explanation_missing
    input: report
    severity: warning
    message: 证据材料被罗列，但没有解释它如何支撑结论。
    question:
      type: noul
      instructions: "The document presents numbers, logs, citations, or technical terms as evidence, but does not explain how that evidence supports the conclusion or decision for the intended reader."
    flag_when:
      metric: noul
      operator: ">="
      value: 0.70
    uncertain_when:
      metric: noul
      gte: 0.55
      lte: 0.70

  - id: decision_detail_missing
    input: report
    severity: warning
    message: 影响理解或决策的必要信息被省略，或重复内容掩盖了重点。
    question:
      type: noul
      instructions: "The document omits an explanation, cause, risk, limitation, or next decision needed by the intended reader, or repeats padding so much that the decision-relevant point is obscured."
    flag_when:
      metric: noul
      operator: ">="
      value: 0.70
    uncertain_when:
      metric: noul
      gte: 0.55
      lte: 0.70

  - id: factual_scope_overclaim
    input: report
    severity: warning
    message: 事实、推断或未验证项被混写，结论范围超过材料。
    question:
      type: noul
      instructions: "The document states a conclusion as fact, universal, fully verified, or broader than the supplied evidence supports, without keeping the applicable scope and unverified limitations next to the claim."
    flag_when:
      metric: noul
      operator: ">="
      value: 0.70
    uncertain_when:
      metric: noul
      gte: 0.55
      lte: 0.70
