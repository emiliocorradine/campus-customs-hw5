"""Campus Customs backend: FastAPI routes for the React dashboard.

Start from inside backend/:
    uvicorn main:app --reload --port 8000

Shop facts come only through the campus-customs MCP server (one stdio client held for
the app's lifetime). The backend never queries SQLite. Money only changes through
POST /approvals/{id}/approve, which calls the human-only MCP tool decide_approval.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel, Field

from agents import RUN_REPORTS, new_run_id, reset_working_db, run_ticket
from audit import append_audit, make_entry, read_audit
from config import AGENT_NAMES, MCP_ARGS, MCP_COMMAND, MCP_CWD
from models import TicketDeps

FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
EVENTS_DEFAULT_LIMIT = 200

# Tool error kinds -> HTTP status codes.
ERROR_STATUS = {"not found": 404, "refused": 409, "invalid input": 422}


# ---------- MCP client (backend / human side) ----------

class ShopTools:
    """One stdio connection to the MCP server, opened at startup and closed at shutdown."""

    def __init__(self) -> None:
        self.client = Client(StdioTransport(command=MCP_COMMAND, args=MCP_ARGS, cwd=str(MCP_CWD)))

    async def call(self, tool: str, args: dict | None = None) -> dict:
        """Call an MCP tool. Tool-level errors ({"error": ...}) become HTTP errors."""
        result = await self.client.call_tool(tool, args or {}, raise_on_error=False)
        if result.is_error:
            text = result.content[0].text if result.content else "tool failed"
            raise HTTPException(status_code=502, detail={"error": "tool failed", "tool": tool, "detail": text})
        data = result.structured_content
        if data is None and result.content:
            data = json.loads(result.content[0].text)
        if isinstance(data, dict) and "error" in data:
            raise HTTPException(status_code=ERROR_STATUS.get(data["error"], 400), detail=data)
        return data


tools = ShopTools()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with tools.client:
        yield


app = FastAPI(title="Campus Customs backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Background ticket runs ----------

# ticket_id -> {"run_id", "started_at", "task"} while a run is in progress.
active_runs: dict[int, dict] = {}
# run_id -> {"run_id", "ticket_id", "state", "started_at", "finished_at", "decision", "error"} (this server's runs).
runs: dict[str, dict] = {}
# ticket_id -> run_id of its most recent run.
last_run_by_ticket: dict[int, str] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _run_in_background(ticket_id: int, run_id: str) -> None:
    record = runs[run_id]
    try:
        decision = await run_ticket(ticket_id, run_id=run_id)
        record.update(state="finished", decision=decision.model_dump())
    except Exception as exc:  # already recorded by the agent's audit "error" step
        deps = TicketDeps(run_id=run_id, ticket_id=ticket_id, agent_name="boss")
        append_audit([make_entry(deps, "run_failed", result=f"{type(exc).__name__}: {exc}")])
        record.update(state="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        record["finished_at"] = _now()
        active_runs.pop(ticket_id, None)


def _runs_in_progress() -> list[dict]:
    return [{"ticket_id": t, "run_id": r["run_id"], "started_at": r["started_at"]} for t, r in active_runs.items()]


# ---------- Routes ----------

class ApprovalBody(BaseModel):
    approved_by: str = Field(min_length=1, description="The human's name.")
    note: str | None = None


@app.get("/tickets")
async def list_tickets():
    """All tickets: id, type, subject, requester, status (open/resolved) and the detailed ticket_status."""
    data = await tools.call("list_tickets")
    tickets = [
        {
            "id": t["id"],
            "type": t["type"],
            "subject": t["subject"],
            "requester": t["requester"],
            "status": "resolved" if t["status"] in ("resolved", "closed") else "open",
            "ticket_status": t["status"],
            "running": t["id"] in active_runs,
            "last_run_id": last_run_by_ticket.get(t["id"]),
        }
        for t in data["tickets"]
    ]
    return {"count": len(tickets), "tickets": tickets}


@app.post("/tickets/{ticket_id}/run", status_code=202)
async def run_ticket_route(ticket_id: int):
    """Start the agent team on one ticket in the background and return its run_id right away."""
    if ticket_id in active_runs:
        raise HTTPException(status_code=409, detail={
            "error": "refused", "detail": f"ticket {ticket_id} is already running",
            "run_id": active_runs[ticket_id]["run_id"],
        })
    run_id = new_run_id()
    # Claim the slot before any await, so two quick clicks can't both start a run.
    active_runs[ticket_id] = {"run_id": run_id, "started_at": _now(), "task": None}
    try:
        await tools.call("get_ticket", {"ticket_id": ticket_id})  # 404 if the ticket doesn't exist
    except Exception:
        active_runs.pop(ticket_id, None)
        raise
    runs[run_id] = {"run_id": run_id, "ticket_id": ticket_id, "state": "running",
                    "started_at": active_runs[ticket_id]["started_at"], "finished_at": None,
                    "decision": None, "error": None}
    last_run_by_ticket[ticket_id] = run_id
    active_runs[ticket_id]["task"] = asyncio.create_task(_run_in_background(ticket_id, run_id))
    return {"ticket_id": ticket_id, "run_id": run_id, "status": "started"}


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    """One run's state and result: the Boss's decision plus every agent's full report."""
    record = runs.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"error": "not found", "run_id": run_id})
    return {**record, "reports": RUN_REPORTS.get(run_id, [])}


@app.get("/events")
async def events(since: int = Query(0, ge=0, description="Return entries with seq > since."),
                 limit: int = Query(EVENTS_DEFAULT_LIMIT, ge=1, le=1000)):
    """Audit-trail entries newer than `since` (seq is the 1-based position in the trail)."""
    trail = read_audit()
    newer = [
        {
            "seq": i,
            "time": e.get("timestamp"),
            "run_id": e.get("run_id"),
            "ticket_id": e.get("ticket_id"),
            "agent": e.get("agent"),
            "depth": e.get("depth"),
            "step": e.get("step"),
            "tool": e.get("tool"),
            "args": e.get("args"),
            "result": e.get("result"),
            "delegated_to": e.get("delegated_to"),
        }
        for i, e in enumerate(trail, start=1)
        if i > since
    ][-limit:]
    return {"since": since, "next_since": len(trail), "count": len(newer), "events": newer,
            "runs_in_progress": _runs_in_progress()}


@app.get("/approvals")
async def approvals(all: bool = Query(False, description="true = every request, any status")):
    """Approval requests waiting for a human (or, with ?all=true, every request ever made)."""
    return await tools.call("list_approval_requests" if all else "list_pending_approvals")


@app.get("/payments")
async def payments():
    """Every payment made (human-approved), plus the total paid."""
    return await tools.call("list_payments")


async def _decide(request_id: int, decision: str, body: ApprovalBody) -> dict:
    who = body.approved_by.strip()
    if not who or who.lower() in AGENT_NAMES:
        raise HTTPException(status_code=403, detail={"error": "refused", "detail": "approved_by must be a human's name"})
    args = {"request_id": request_id, "decision": decision, "approved_by": who}
    if body.note:
        args["note"] = body.note
    return await tools.call("decide_approval", args)


@app.post("/approvals/{request_id}/approve")
async def approve(request_id: int, body: ApprovalBody):
    """Human approves a request. The ONLY route that can move money."""
    return await _decide(request_id, "approve", body)


@app.post("/approvals/{request_id}/reject")
async def reject(request_id: int, body: ApprovalBody):
    """Human rejects a request. Nothing moves."""
    return await _decide(request_id, "reject", body)


@app.get("/cash")
async def cash():
    """Current checking balance (plus pending payment requests)."""
    data = await tools.call("get_cash_balance")
    checking = next((a for a in data["accounts"] if a["name"] == "checking"), None)
    if checking is None:
        raise HTTPException(status_code=404, detail={"error": "not found", "account": "checking"})
    return {
        "account": "checking",
        "balance": checking["balance"],
        "as_of": checking["date"],
        "pending_payment_requests": data["pending_payment_requests"],
        "available_after_pending": data["available_after_pending"],
    }


@app.post("/reset")
async def reset():
    """Copy data/campus_customs.db over data/campus_customs_new.db. Refused while a run is in progress.

    The audit trail is not touched.
    """
    if active_runs:
        raise HTTPException(status_code=409, detail={
            "error": "refused", "detail": "a ticket run is in progress", "runs_in_progress": _runs_in_progress(),
        })
    reset_working_db()
    return {"status": "reset", "detail": "campus_customs_new.db now matches campus_customs.db"}
