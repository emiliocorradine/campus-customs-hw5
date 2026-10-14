"""The Campus Customs agent team (Pydantic AI).

Five agents share one MCP connection (the campus-customs server over stdio). Each agent
only sees its own tools (config.AGENT_TOOLS, never a human-only tool), plus a `delegate`
tool so any agent can ask any other agent for help.
Every step of every run is appended to output/audit_trail.json via agent.iter().
"""

import shutil
import uuid
from functools import cache

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.toolsets import AbstractToolset
from pydantic_ai.usage import RunUsage

from audit import append_audit, entries_for_node, make_entry
from config import (
    AGENT_NAMES,
    AGENT_RETRIES,
    AGENT_TOOLS,
    HUMAN_ONLY_TOOLS,
    MAX_DELEGATION_DEPTH,
    MCP_ARGS,
    MCP_COMMAND,
    MCP_CWD,
    ORIGINAL_DB,
    PROMPTS_DIR,
    WORKING_DB,
    build_model,
    ticket_usage_limits,
)
from models import AgentName, AgentReport, BossDecision, TicketDeps


# ---------- Tools shared by every agent ----------

@cache
def _mcp_server() -> MCPToolset[TicketDeps]:
    """The campus-customs MCP server (same command as .mcp.json).

    One connection is shared by all agents, so a ticket run (including delegated
    calls) reuses one server process instead of starting one per agent.
    """
    return MCPToolset(
        StdioTransport(command=MCP_COMMAND, args=MCP_ARGS, cwd=str(MCP_CWD)),
        id="campus-customs",
    )


def shop_toolset(agent_name: str) -> AbstractToolset[TicketDeps]:
    """The MCP tools this agent may use (AGENT_TOOLS), never any human-only tool."""
    allowed = AGENT_TOOLS[agent_name] - HUMAN_ONLY_TOOLS
    return _mcp_server().filtered(lambda ctx, tool_def: tool_def.name in allowed)


async def delegate(ctx: RunContext[TicketDeps], to_agent: AgentName, task: str) -> dict:
    """Ask another Campus Customs agent to do part of the work and return its report.

    Use it when the work belongs to another agent's scope (see your instructions).
    The other agent has the same shop tools you do, so give it a specific, self-contained
    task: the ticket id, the SKU/size/qty/lease/invoice ids involved, and exactly what you
    need back.

    Inputs:
        to_agent: "boss", "inventory", "accounting", "facilities" or "customer_service".
            You cannot delegate to yourself.
        task: what you need, in one short paragraph.

    Returns:
        The other agent's report (AgentReport, or BossDecision from the boss), or
        {"error": "refused", ...} if it is a self-call or the delegation depth limit is reached.
    """
    me = ctx.deps.agent_name
    if to_agent == me:
        return {"error": "refused", "detail": "you cannot delegate to yourself; do the work or pick another agent"}
    if to_agent not in AGENT_NAMES:
        return {"error": "invalid input", "detail": f"to_agent must be one of {list(AGENT_NAMES)}"}
    depth = ctx.deps.depth + 1
    if depth > MAX_DELEGATION_DEPTH:
        return {
            "error": "refused",
            "detail": f"delegation depth limit ({MAX_DELEGATION_DEPTH}) reached; finish with the facts you have",
        }
    child = TicketDeps(
        run_id=ctx.deps.run_id,
        ticket_id=ctx.deps.ticket_id,
        agent_name=to_agent,
        depth=depth,
        call_chain=[*ctx.deps.call_chain, me],
    )
    # ctx.usage is shared, so the per-ticket request/token limits cover the whole delegation tree.
    output = await _run_agent(to_agent, task, child, usage=ctx.usage)
    return output.model_dump() if hasattr(output, "model_dump") else {"reply": output}


# ---------- Agent construction ----------

def _context_instructions(ctx: RunContext[TicketDeps]) -> str:
    d = ctx.deps
    chain = " -> ".join([*d.call_chain, d.agent_name])
    ticket = f"#{d.ticket_id}" if d.ticket_id is not None else "none (not a ticket run)"
    return (
        f"## Run context\n"
        f"- You are the `{d.agent_name}` agent. Use \"{d.agent_name}\" for requested_by / author_agent.\n"
        f"- Ticket: {ticket}\n"
        f"- Delegation: depth {d.depth} of max {MAX_DELEGATION_DEPTH}; call chain: {chain}\n"
        f"- Do not delegate back to an agent already in the call chain unless you need something new."
    )


@cache
def _model():
    return build_model()


@cache
def get_agent(name: str) -> Agent:
    """Build (once) the agent with this name."""
    if name not in AGENT_NAMES:
        raise ValueError(f"unknown agent {name!r}")
    prompt_path = PROMPTS_DIR / f"{name}.md"

    agent = Agent(
        _model(),
        name=name,
        deps_type=TicketDeps,
        output_type=BossDecision if name == "boss" else AgentReport,
        toolsets=[shop_toolset(name)],
        tools=[delegate],
        retries=AGENT_RETRIES,
    )

    @agent.instructions
    def role_prompt() -> str:
        # Read on every run so edits to prompts/*.md apply without restarting.
        return prompt_path.read_text(encoding="utf-8")

    agent.instructions(_context_instructions)
    return agent


# ---------- Running agents (every step audited) ----------

# run_id -> every agent's full (untruncated) output in that run, in finish order.
# In memory only; the audit trail keeps the short versions permanently.
RUN_REPORTS: dict[str, list[dict]] = {}


async def _run_agent(name: str, prompt: str, deps: TicketDeps, *, usage: RunUsage | None = None,
                     output_type: type | None = None):
    """Run one agent with agent.iter(), appending every step to the audit trail."""
    agent = get_agent(name)
    extra = {"output_type": output_type} if output_type is not None else {}
    try:
        async with agent.iter(prompt, deps=deps, usage=usage, usage_limits=ticket_usage_limits(), **extra) as run:
            async for node in run:
                append_audit(entries_for_node(node, deps))
            output = run.result.output
        RUN_REPORTS.setdefault(deps.run_id, []).append({
            "agent": name,
            "depth": deps.depth,
            "called_by": deps.call_chain[-1] if deps.call_chain else None,
            "output": output.model_dump() if hasattr(output, "model_dump") else output,
        })
        return output
    except Exception as exc:
        append_audit([make_entry(deps, "error", result=f"{type(exc).__name__}: {exc}")])
        raise


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


async def run_ticket(ticket_id: int, run_id: str | None = None) -> BossDecision:
    """Have the Boss handle one ticket end to end (delegating as needed).

    run_id lets a caller (e.g. the API) hand out the id before the run starts.
    Does NOT reset the database; call reset_working_db() before a full run.
    """
    deps = TicketDeps(run_id=run_id or new_run_id(), ticket_id=ticket_id, agent_name="boss")
    append_audit([make_entry(deps, "run_start", args={"ticket_id": ticket_id})])
    prompt = (
        f"Handle ticket #{ticket_id}. Start with get_ticket({ticket_id}). "
        "Follow your instructions, delegate to the right agents, and return your BossDecision."
    )
    try:
        decision = await _run_agent("boss", prompt, deps)
    except UsageLimitExceeded as exc:
        append_audit([make_entry(deps, "limit_reached", result=str(exc))])
        decision = BossDecision(
            ticket_id=ticket_id,
            decision="escalate_to_human",
            summary="Stopped before finishing: the per-ticket request/token limit was reached.",
            rationale=str(exc),
            next_steps_for_human=["Review the audit trail for this run_id and finish the ticket by hand."],
        )
    append_audit([make_entry(deps, "run_end", result=decision)])
    return decision


async def ping(agent_name: str = "boss", message: str = "Reply OK") -> str:
    """Health check: one plain-text reply from an agent, audited like any other run."""
    deps = TicketDeps(run_id=new_run_id(), ticket_id=None, agent_name=agent_name)
    return await _run_agent(agent_name, message, deps, output_type=str)


def reset_working_db() -> None:
    """Copy the original DB over the working copy (run before a full ticket run).

    The original file is only read, never written.
    """
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
