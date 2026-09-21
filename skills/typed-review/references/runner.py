#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "PyYAML>=6.0",
#   "typesafe-sdk==0.7.0",
# ]
# ///
"""TypeSafe/JEV YAML 检查 runner。"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any

import yaml

CONFIG_VERSION = 1
QUESTION_TYPES = {"noul", "choice", "score"}
NUMERIC_METRICS = {"noul", "score", "confidence", "probability"}
OPERATORS = {">=", ">", "<=", "<", "=="}
SEVERITIES = {"warning", "blocker"}


class ConfigError(ValueError):
    """配置或输入错误。"""


@dataclass(frozen=True)
class Runtime:
    base_url_env: str
    api_key_env: str
    model: str
    timeout_seconds: float
    concurrency: int


@dataclass(frozen=True)
class InputSpec:
    path: Path
    max_bytes: int


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    input_id: str
    severity: str
    message: str
    question: dict[str, Any]
    flag_when: dict[str, Any]
    uncertain_when: dict[str, Any] | None


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} 必须是映射")
    return value


def require_string(mapping: dict[str, Any], key: str, name: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{name}.{key} 必须是非空字符串")
    return value


def require_number(mapping: dict[str, Any], key: str, name: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ConfigError(f"{name}.{key} 必须是有限数字")
    return float(value)


def load_config(path: Path, input_overrides: list[str]) -> tuple[dict[str, InputSpec], list[CheckSpec], Runtime, str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = require_mapping(raw, "配置")
    if root.get("config_version") != CONFIG_VERSION:
        raise ConfigError("config_version 只支持 1")

    runtime_raw = require_mapping(root.get("runtime", {}), "runtime")
    runtime = Runtime(
        base_url_env=runtime_raw.get("base_url_env", "JEV_BASE_URL"),
        api_key_env=runtime_raw.get("api_key_env", "JEV_API_KEY"),
        model=runtime_raw.get("model", "jev-latest"),
        timeout_seconds=require_number({"timeout_seconds": runtime_raw.get("timeout_seconds", 15)}, "timeout_seconds", "runtime"),
        concurrency=int(require_number({"concurrency": runtime_raw.get("concurrency", 4)}, "concurrency", "runtime")),
    )
    if not runtime.base_url_env or not runtime.api_key_env:
        raise ConfigError("runtime 环境变量名不能为空")
    if runtime.timeout_seconds <= 0:
        raise ConfigError("runtime.timeout_seconds 必须大于 0")
    if runtime.concurrency <= 0:
        raise ConfigError("runtime.concurrency 必须大于 0")

    inputs_raw = require_mapping(root.get("inputs"), "inputs")
    inputs: dict[str, InputSpec] = {}
    for input_id, value in inputs_raw.items():
        if not isinstance(input_id, str) or not input_id:
            raise ConfigError("inputs key 必须是非空字符串")
        spec = require_mapping(value, f"inputs.{input_id}")
        path_value = require_string(spec, "path", f"inputs.{input_id}")
        max_bytes = int(require_number({"max_bytes": spec.get("max_bytes", 1_000_000)}, "max_bytes", f"inputs.{input_id}"))
        if max_bytes <= 0:
            raise ConfigError(f"inputs.{input_id}.max_bytes 必须大于 0")
        inputs[input_id] = InputSpec(path=(path.parent / path_value).resolve(), max_bytes=max_bytes)

    overrides: dict[str, str] = {}
    for item in input_overrides:
        if "=" not in item:
            raise ConfigError(f"--input 格式应为 ID=PATH: {item}")
        input_id, path_value = item.split("=", 1)
        if input_id not in inputs:
            raise ConfigError(f"--input 引用了不存在的输入: {input_id}")
        overrides[input_id] = path_value
    for input_id, path_value in overrides.items():
        inputs[input_id] = InputSpec(path=Path(path_value).expanduser().resolve(), max_bytes=inputs[input_id].max_bytes)

    checks_raw = root.get("checks")
    if not isinstance(checks_raw, list) or not checks_raw:
        raise ConfigError("checks 必须是非空列表")
    checks: list[CheckSpec] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(checks_raw):
        name = f"checks[{index}]"
        raw_check = require_mapping(value, name)
        check_id = require_string(raw_check, "id", name)
        if check_id in seen_ids:
            raise ConfigError(f"check id 重复: {check_id}")
        seen_ids.add(check_id)
        input_id = require_string(raw_check, "input", name)
        if input_id not in inputs:
            raise ConfigError(f"{name}.input 不存在: {input_id}")
        severity = raw_check.get("severity", "warning")
        if severity not in SEVERITIES:
            raise ConfigError(f"{name}.severity 只支持 warning/blocker")
        message = require_string(raw_check, "message", name)
        question = require_mapping(raw_check.get("question"), f"{name}.question")
        question_type = require_string(question, "type", f"{name}.question")
        if question_type not in QUESTION_TYPES:
            raise ConfigError(f"{name}.question.type 只支持 noul/choice/score")
        require_string(question, "instructions", f"{name}.question")
        if question_type in {"choice", "score"}:
            criteria = question.get("criteria")
            if question_type == "choice":
                if not isinstance(criteria, dict) or not criteria:
                    raise ConfigError(f"{name}.question.criteria 必须是非空映射")
                if any(not isinstance(k, str) or not k for k in criteria):
                    raise ConfigError(f"{name}.question.criteria 选项名必须是非空字符串")
            elif not isinstance(criteria, list) or not criteria:
                raise ConfigError(f"{name}.question.criteria 必须是非空列表")
        flag_when = validate_condition(require_mapping(raw_check.get("flag_when"), f"{name}.flag_when"), f"{name}.flag_when", question_type)
        uncertain_raw = raw_check.get("uncertain_when")
        uncertain_when = None
        if uncertain_raw is not None:
            uncertain_when = validate_uncertain(require_mapping(uncertain_raw, f"{name}.uncertain_when"), f"{name}.uncertain_when", question_type)
        checks.append(CheckSpec(check_id, input_id, severity, message, question, flag_when, uncertain_when))

    state_prefix = root.get("state_prefix", "")
    if not isinstance(state_prefix, str):
        raise ConfigError("state_prefix 必须是字符串")
    return inputs, checks, runtime, state_prefix


def validate_condition(raw: dict[str, Any], name: str, question_type: str) -> dict[str, Any]:
    metric = require_string(raw, "metric", name)
    operator = require_string(raw, "operator", name)
    if operator not in OPERATORS:
        raise ConfigError(f"{name}.operator 只支持 >= > <= < ==")
    if metric == "choice":
        if operator != "==":
            raise ConfigError(f"{name}.choice 只支持 ==")
        if question_type != "choice":
            raise ConfigError(f"{name}.choice metric 只能用于 choice question")
        value = require_string(raw, "value", name)
        return {**raw, "value": value}
    if metric not in NUMERIC_METRICS:
        raise ConfigError(f"{name}.metric 不支持: {metric}")
    value = require_number(raw, "value", name)
    if metric in {"noul", "confidence", "probability"} and not 0 <= value <= 1:
        raise ConfigError(f"{name}.value 必须在 0 到 1 之间")
    if metric == "probability":
        require_string(raw, "choice", name)
        if question_type != "choice":
            raise ConfigError(f"{name}.probability 只能用于 choice question")
    if metric == "confidence" and question_type not in {"choice", "score"}:
        raise ConfigError(f"{name}.confidence 只能用于 choice/score question")
    if metric == "noul" and question_type != "noul":
        raise ConfigError(f"{name}.noul 只能用于 noul question")
    if metric == "score" and question_type != "score":
        raise ConfigError(f"{name}.score 只能用于 score question")
    return {**raw, "value": value}


def validate_uncertain(raw: dict[str, Any], name: str, question_type: str) -> dict[str, Any]:
    metric = require_string(raw, "metric", name)
    if metric not in NUMERIC_METRICS:
        raise ConfigError(f"{name}.metric 不支持: {metric}")
    if metric == "confidence" and question_type not in {"choice", "score"}:
        raise ConfigError(f"{name}.confidence 只能用于 choice/score question")
    if metric == "noul" and question_type != "noul":
        raise ConfigError(f"{name}.noul 只能用于 noul question")
    if metric == "score" and question_type != "score":
        raise ConfigError(f"{name}.score 只能用于 score question")
    if metric == "probability":
        require_string(raw, "choice", name)
        if question_type != "choice":
            raise ConfigError(f"{name}.probability 只能用于 choice question")
    low = require_number(raw, "gte", name)
    high = require_number(raw, "lte", name)
    if low > high:
        raise ConfigError(f"{name}.gte 不能大于 lte")
    return {**raw, "gte": low, "lte": high}


def read_inputs(specs: dict[str, InputSpec], state_prefix: str) -> dict[str, str]:
    states: dict[str, str] = {}
    for input_id, spec in specs.items():
        if not spec.path.is_file():
            raise ConfigError(f"输入文件不存在: {spec.path}")
        size = spec.path.stat().st_size
        if size > spec.max_bytes:
            raise ConfigError(f"输入超过 max_bytes: {spec.path} ({size} > {spec.max_bytes})")
        text = spec.path.read_text(encoding="utf-8")
        states[input_id] = state_prefix + text if state_prefix else text
    return states


def compare(value: Any, operator: str, threshold: Any) -> bool:
    if operator == "==":
        return value == threshold
    if operator == ">=":
        return float(value) >= float(threshold)
    if operator == ">":
        return float(value) > float(threshold)
    if operator == "<=":
        return float(value) <= float(threshold)
    if operator == "<":
        return float(value) < float(threshold)
    raise ConfigError(f"未知 operator: {operator}")


def answer_metric(answer: dict[str, Any], condition: dict[str, Any]) -> Any:
    metric = condition["metric"]
    if metric == "choice":
        return answer.get("choice")
    if metric == "probability":
        value = answer.get("probabilities", {}).get(condition["choice"])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ConfigError(f"响应缺少选项概率: {condition['choice']}")
        return float(value)
    if metric not in answer:
        raise ConfigError(f"响应缺少 metric {metric}")
    return float(answer[metric])


def classify(answer: dict[str, Any], check: CheckSpec) -> tuple[str, Any]:
    value = answer_metric(answer, check.flag_when)
    if check.uncertain_when is not None:
        uncertain_value = answer_metric(answer, check.uncertain_when)
        if float(check.uncertain_when["gte"]) <= float(uncertain_value) <= float(check.uncertain_when["lte"]):
            return "uncertain", value
    return ("flag" if compare(value, check.flag_when["operator"], check.flag_when["value"]) else "pass"), value


def build_question(raw: dict[str, Any]):
    # 延迟导入：dry-run 不需要加载 SDK。
    from typesafe_sdk import Choice, Noul, Score

    question_type = raw["type"]
    instructions = raw["instructions"]
    if question_type == "noul":
        return Noul(instructions=instructions)
    if question_type == "choice":
        return Choice(instructions=instructions, criteria=raw["criteria"])
    return Score(instructions=instructions, criteria=raw["criteria"])


async def send_checks(
    checks: list[CheckSpec],
    states: dict[str, str],
    runtime: Runtime,
    base_url: str,
    api_key: str,
) -> list[dict[str, Any]]:
    # 延迟导入：避免把 SDK 导入问题伪装成配置错误。
    from typesafe_sdk import AsyncTypeSafeClient

    semaphore = asyncio.Semaphore(runtime.concurrency)

    async with AsyncTypeSafeClient(
        base_url=base_url,
        api_key=api_key,
        timeout=runtime.timeout_seconds,
    ) as client:
        async def run_one(check: CheckSpec) -> dict[str, Any]:
            started = time.perf_counter()
            try:
                async with semaphore:
                    response = await client.system_one(
                        state=states[check.input_id],
                        questions={check.check_id: build_question(check.question)},
                        model=runtime.model,
                        timeout=runtime.timeout_seconds,
                    )
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                answer = response.answers[check.check_id]
                answer_data = answer.model_dump(exclude_none=True)
                status, value = classify(answer_data, check)
                usage = response.usage.model_dump(exclude_none=True)
                return {
                    "id": check.check_id,
                    "input": check.input_id,
                    "severity": check.severity,
                    "status": status,
                    "metric": check.flag_when["metric"],
                    "value": value,
                    "threshold": check.flag_when["value"],
                    "operator": check.flag_when["operator"],
                    "message": check.message,
                    "answer": answer_data,
                    "model": response.model,
                    "usage": usage,
                    "duration_ms": elapsed_ms,
                    "error": None,
                }
            except Exception as exc:  # 每条规则独立失败，不拖垮整批请求。
                elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                return {
                    "id": check.check_id,
                    "input": check.input_id,
                    "severity": check.severity,
                    "status": "error",
                    "metric": check.flag_when["metric"],
                    "value": None,
                    "threshold": check.flag_when["value"],
                    "operator": check.flag_when["operator"],
                    "message": check.message,
                    "answer": None,
                    "model": runtime.model,
                    "usage": None,
                    "duration_ms": elapsed_ms,
                    "error": f"{type(exc).__name__}: {exc}",
                }

        return list(await asyncio.gather(*(run_one(check) for check in checks)))


def dry_run_results(checks: list[CheckSpec], states: dict[str, str], runtime: Runtime) -> list[dict[str, Any]]:
    return [
        {
            "id": check.check_id,
            "input": check.input_id,
            "severity": check.severity,
            "status": "not_sent",
            "metric": check.flag_when["metric"],
            "value": None,
            "threshold": check.flag_when["value"],
            "operator": check.flag_when["operator"],
            "message": check.message,
            "state_chars": len(states[check.input_id]),
            "model": runtime.model,
        }
        for check in checks
    ]


def summarize(results: list[dict[str, Any]], sent: bool) -> tuple[str, dict[str, int]]:
    counts = {status: sum(item["status"] == status for item in results) for status in ("pass", "flag", "uncertain", "error", "not_sent")}
    if not sent:
        return "not_sent", counts
    if counts["error"]:
        return "error", counts
    if counts["flag"] or counts["uncertain"]:
        return "flag", counts
    return "pass", counts


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Typed Review 结果",
        "",
        f"- 总体状态：`{payload['status']}`",
        f"- 规则数：{len(payload['checks'])}；pass {summary['pass']}，flag {summary['flag']}，uncertain {summary['uncertain']}，error {summary['error']}，not_sent {summary['not_sent']}",
        f"- requested model：`{payload['requested_model']}`；actual models：`{', '.join(payload['actual_models']) or '-'}`",
        "",
        "| 规则 | 状态 | 严重度 | 判断值 | 阈值 | 说明 |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in payload["checks"]:
        lines.append(
            f"| `{item['id']}` | `{item['status']}` | {item['severity']} | "
            f"{item['value'] if item['value'] is not None else '-'} | {item['threshold']} | {item['message']} |"
        )
    return "\n".join(lines) + "\n"


def write_output(payload: dict[str, Any], output: str | None, output_format: str) -> None:
    if output_format == "markdown":
        text = render_markdown(payload)
        data = text.encode("utf-8")
    else:
        data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if output:
        path = Path(output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    else:
        sys.stdout.buffer.write(data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="YAML 配置路径")
    parser.add_argument("--input", action="append", default=[], metavar="ID=PATH", help="覆盖某个输入路径，可重复")
    parser.add_argument("--base-url", help="覆盖 runtime.base_url_env")
    parser.add_argument("--api-key", help="覆盖 runtime.api_key_env")
    parser.add_argument("--concurrency", type=int, help="覆盖 runtime.concurrency")
    parser.add_argument("--send", action="store_true", help="实际发送请求；缺省为 dry-run")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="结果输出文件；缺省输出 stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    try:
        config_path = args.config.expanduser().resolve()
        inputs, checks, runtime, state_prefix = load_config(config_path, args.input)
        if args.concurrency is not None:
            if args.concurrency <= 0:
                raise ConfigError("--concurrency 必须大于 0")
            runtime = Runtime(runtime.base_url_env, runtime.api_key_env, runtime.model, runtime.timeout_seconds, args.concurrency)
        states = read_inputs(inputs, state_prefix)

        if not args.send:
            results = dry_run_results(checks, states, runtime)
            status, summary = summarize(results, sent=False)
            actual_models: list[str] = []
            base_url = None
        else:
            base_url = args.base_url or os.environ.get(runtime.base_url_env) or os.environ.get("TYPESAFE_BASE_URL")
            api_key = args.api_key or os.environ.get(runtime.api_key_env) or "local-no-auth"
            if not base_url:
                raise ConfigError(f"缺少 base_url：请设置 {runtime.base_url_env} 或使用 --base-url")
            results = await_or_run(send_checks(checks, states, runtime, base_url, api_key))
            status, summary = summarize(results, sent=True)
            actual_models = sorted({item.get("model") for item in results if item.get("model")})

        payload = {
            "schema_version": 1,
            "status": status,
            "config": str(config_path),
            "endpoint": base_url,
            "requested_model": runtime.model,
            "actual_models": actual_models,
            "started_at": started_at,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "summary": summary,
            "checks": results,
        }
        write_output(payload, args.output, args.format)
        if status == "error":
            return 2
        if status == "not_sent":
            return 3
        return 1 if status == "flag" else 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "status": "error",
            "started_at": started_at,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "summary": {"pass": 0, "flag": 0, "uncertain": 0, "error": 1, "not_sent": 0},
            "error": f"{type(exc).__name__}: {exc}",
        }
        write_output(payload, args.output, args.format)
        return 2


def await_or_run(coroutine):
    # Python 3.10 下没有 asyncio.run 与 await 表达式合写的问题；包一层便于测试。
    return asyncio.run(coroutine)


if __name__ == "__main__":
    raise SystemExit(main())
