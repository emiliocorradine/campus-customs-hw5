"""Shared settings for the Campus Customs agent team: model, Portkey, MCP server, limits, paths."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# homework 5/.env wins; the course folder's .env is a fallback for a missing key.
# load_dotenv never overrides a variable that is already set.
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT.parent / ".env")
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

# ---------- Model (the ONLY model used anywhere in this project) ----------
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

# ---------- Paths ----------
PROMPTS_DIR = BACKEND_DIR / "prompts"
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
ORIGINAL_DB = PROJECT_ROOT / "data" / "campus_customs.db"      # reset source, read-only
WORKING_DB = PROJECT_ROOT / "data" / "campus_customs_new.db"   # what the MCP server uses

# ---------- MCP server (same server as .mcp.json, launched over stdio) ----------
# sys.executable = the interpreter running the backend, so the server gets the same packages.
MCP_COMMAND = sys.executable
MCP_ARGS = ["mcp_server/server.py"]
MCP_CWD = PROJECT_ROOT
# Tools only a human may call. They are filtered out of every agent's toolset.
HUMAN_ONLY_TOOLS = frozenset({"decide_approval"})

# Least privilege: the MCP tools each agent may see (every agent also gets `delegate`).
AGENT_TOOLS: dict[str, frozenset[str]] = {
    "boss": frozenset({
        "get_today", "get_ticket", "list_open_tickets", "list_pending_approvals", "update_ticket_status",
    }),
    "inventory": frozenset({
        "get_today", "get_ticket", "check_stock", "get_sku_pricing", "list_vendors", "get_vendor_status",
        "request_purchase_order",
    }),
    "accounting": frozenset({
        "get_today", "get_ticket", "get_cash_balance", "get_invoice", "get_vendor_status", "get_sku_pricing",
        "list_pending_approvals", "request_payment", "request_price_override",
    }),
    "facilities": frozenset({
        "get_today", "get_ticket", "get_lease_status", "get_cash_balance",
    }),
    "customer_service": frozenset({
        "get_today", "get_ticket", "check_stock", "get_sku_pricing", "save_draft",
    }),
}

# ---------- Agents and limits ----------
AGENT_NAMES = ("boss", "inventory", "accounting", "facilities", "customer_service")
REQUEST_LIMIT = 30            # model requests per ticket, across all delegated agents
TOTAL_TOKENS_LIMIT = 150_000  # tokens per ticket, across all delegated agents (raised from 60,000 by the user in Problem 9)
MAX_DELEGATION_DEPTH = 3      # boss (0) -> 1 -> 2 -> 3, no deeper
AGENT_RETRIES = 2
AUDIT_TEXT_CHARS = 300


def ticket_usage_limits() -> UsageLimits:
    return UsageLimits(request_limit=REQUEST_LIMIT, total_tokens_limit=TOTAL_TOKENS_LIMIT)


def build_model() -> OpenAIResponsesModel:
    """OpenAI-compatible client pointed at Portkey (same setup as Homework 4).

    Uses the Responses API (/v1/responses): on /v1/chat/completions this model
    rejects function tools unless reasoning is turned off.
    The key comes from .env and is never written into code, logged or printed.
    """
    portkey_api_key = os.environ.get("PORTKEY_API_KEY")
    if not portkey_api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing. Copy .env.example to .env and add your key.")
    client = AsyncOpenAI(
        api_key=portkey_api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": portkey_api_key},
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
