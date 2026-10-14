"""Data shapes for the agent team: run context (deps) and structured agent outputs."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


@dataclass
class TicketDeps:
    """Per-run context passed to every agent through RunContext.deps."""

    run_id: str
    ticket_id: int | None
    agent_name: str
    depth: int = 0                                   # 0 = top-level agent, +1 per delegation
    call_chain: list[str] = field(default_factory=list)


class AgentReport(BaseModel):
    """What a specialist agent (and any delegated call) returns."""

    agent: AgentName
    ticket_id: int | None = None
    summary: str = Field(description="2-4 sentences: what you found and what you did.")
    facts: list[str] = Field(
        default_factory=list,
        description="Shop facts you relied on, each with the tool it came from, e.g. 'qty_on_hand=0 (check_stock)'.",
    )
    actions_taken: list[str] = Field(
        default_factory=list,
        description="Requests, drafts or status changes you made, with their IDs.",
    )
    approval_request_ids: list[int] = Field(default_factory=list)
    draft_ids: list[int] = Field(default_factory=list)
    blockers: list[str] = Field(
        default_factory=list,
        description="Anything stopping the work, e.g. a vendor blocked by an unpaid invoice or not enough cash.",
    )
    needs_human: bool = Field(description="True if a human must approve or decide something.")
    recommendation: str = Field(description="What you recommend the Boss do next.")


class BossDecision(BaseModel):
    """The Boss's final call on one ticket."""

    ticket_id: int
    decision: Literal["resolved", "awaiting_approval", "partially_fulfilled", "declined", "escalate_to_human"]
    summary: str = Field(description="2-4 sentences a shop manager can read.")
    rationale: str = Field(description="Why, including how cash across ALL open tickets was weighed.")
    agents_consulted: list[AgentName] = Field(default_factory=list)
    approval_request_ids: list[int] = Field(default_factory=list)
    draft_ids: list[int] = Field(default_factory=list)
    cash_committed: float = Field(0.0, description="Total of payment requests this ticket created (from tool results).")
    ticket_status: Literal["open", "in_progress", "awaiting_approval", "resolved", "closed"] | None = Field(
        None, description="The status you set with update_ticket_status (None if you didn't set one)."
    )
    next_steps_for_human: list[str] = Field(default_factory=list)
