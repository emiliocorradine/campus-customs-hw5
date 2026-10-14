"""Append-only audit trail (output/audit_trail.json), one entry per agent step.

Entries come from the nodes of agent.iter(). The file is a JSON array that only grows:
it is never wiped, and a damaged file is never overwritten.
"""

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.messages import RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart, UserPromptPart

import config
from config import AUDIT_TEXT_CHARS
from models import TicketDeps

# PydanticAI's structured-output tool carries the agent's final answer; it isn't a shop tool.
OUTPUT_TOOL_PREFIX = "final_result"

_lock = threading.Lock()

# Model-like names in the project model's family (e.g. a provider's deployment name such as
# "<MODEL_NAME>-something" inside an error message). Built from config.MODEL_NAME's prefix so
# no other model name is ever written into the code.
_MODEL_FAMILY = config.MODEL_NAME.split("-")[0]
_MODEL_NAME_RE = re.compile(rf"\b{re.escape(_MODEL_FAMILY)}(?:-[\w.:]+)+", re.IGNORECASE)


def _redact_models(text: str) -> str:
    """Replace any model name other than the project's model (config.MODEL_NAME) with "[redacted]"."""
    def swap(match: re.Match) -> str:
        name = match.group(0).rstrip(".")  # don't treat a sentence-ending period as part of the name
        return (name if name == config.MODEL_NAME else "[redacted]") + match.group(0)[len(name):]
    return _MODEL_NAME_RE.sub(swap, text)


def _short(value: object) -> str | None:
    """Compact JSON (or text), other model names redacted, cut to AUDIT_TEXT_CHARS."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o))
        except (TypeError, ValueError):
            text = str(value)
    text = _redact_models(text)
    return text if len(text) <= AUDIT_TEXT_CHARS else text[: AUDIT_TEXT_CHARS - 1] + "…"


def make_entry(deps: TicketDeps, step: str, *, tool: str | None = None, args: object = None,
               result: object = None, delegated_to: str | None = None, tokens: int | None = None) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": deps.run_id,
        "ticket_id": deps.ticket_id,
        "agent": deps.agent_name,
        "depth": deps.depth,
        "step": step,
        "tool": tool,
        "args": _short(args),
        "result": _short(result),
        "delegated_to": delegated_to,
        "tokens": tokens,
    }


def append_audit(entries: list[dict], path: Path | None = None) -> None:
    """Read the array, add entries, write it back atomically. Old entries are never removed."""
    if not entries:
        return
    path = path or config.AUDIT_PATH
    with _lock:
        existing: list = []
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8") or "[]")
            except json.JSONDecodeError:
                raise RuntimeError(f"{path.name} is not valid JSON; refusing to overwrite it")
            if not isinstance(existing, list):
                raise RuntimeError(f"{path.name} is not a JSON array; refusing to overwrite it")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(existing + entries, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)  # atomic swap: a crash mid-write can't leave a half-written trail


def read_audit(path: Path | None = None) -> list[dict]:
    """Read the whole trail under the same lock as append_audit.

    On Windows a file can't be swapped in while another reader has it open, so readers
    in this process must not overlap with the atomic replace.
    """
    path = path or config.AUDIT_PATH
    with _lock:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8") or "[]")
    return data if isinstance(data, list) else []


def entries_for_node(node: object, deps: TicketDeps) -> list[dict]:
    """Turn one agent.iter() node into audit entries.

    - ModelRequestNode: the prompt sent to the model, plus tool results from the previous step.
    - CallToolsNode: the model's reply (tool calls and text) and its token count.
    - End: the agent's final output.
    """
    entries: list[dict] = []
    if Agent.is_model_request_node(node):
        for part in node.request.parts:
            if isinstance(part, UserPromptPart):
                entries.append(make_entry(deps, "user_prompt", args=part.content))
            elif isinstance(part, ToolReturnPart) and not part.tool_name.startswith(OUTPUT_TOOL_PREFIX):
                entries.append(make_entry(deps, "tool_result", tool=part.tool_name, result=part.content))
            elif isinstance(part, RetryPromptPart):
                entries.append(make_entry(deps, "tool_retry", tool=part.tool_name, result=part.model_response()))
    elif Agent.is_call_tools_node(node):
        response = node.model_response
        tokens = response.usage.total_tokens if response.usage else None
        tool_calls = [p for p in response.parts if isinstance(p, ToolCallPart)]
        texts = [p.content for p in response.parts if isinstance(p, TextPart) and p.content.strip()]
        entries.append(make_entry(deps, "model_response", result=" ".join(texts) or None, tokens=tokens,
                                  args={"tool_calls": [c.tool_name for c in tool_calls]} if tool_calls else None))
        for call in tool_calls:
            if call.tool_name.startswith(OUTPUT_TOOL_PREFIX):
                continue
            args = call.args_as_dict()
            entries.append(make_entry(
                deps, "tool_call", tool=call.tool_name, args=args,
                delegated_to=args.get("to_agent") if call.tool_name == "delegate" else None,
            ))
    elif Agent.is_end_node(node):
        entries.append(make_entry(deps, "final_output", result=node.data.output))
    return entries
