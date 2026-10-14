# Campus Customs — Harness

## Intro

- **Working DB (all tools and agents read and write here):** `data/campus_customs_new.db`
- **Original / reset source (never written):** `data/campus_customs.db`. Before a full run, copy it over the working DB.
- **Integrity check (Problem 2):** both files have SHA-256 `23686a90…f360a`, so they're identical.
- **Shop "today":** `desk.date_today` = **2026-08-31**. All overdue checks use this date, not the system clock.
- **Starting cash:** `checking` = **$3,400.00**

## Tables

### desk
Fields: `date_today` TEXT, `notes` TEXT (1 row, no key)
Why it matters: defines "today" for every overdue and due-soon decision.

### tickets
Fields: `id` INTEGER PK, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id` FK→leases.id, `invoice_id` FK→invoices.id, `status`, `notes`, `created_at`
Why it matters: the work queue. The Boss reads each ticket and routes it to the right agent.

### inventory
Fields: `sku` TEXT, `name`, `size` TEXT, `qty` INTEGER, `location`. PK (`sku`, `size`)
Why it matters: Inventory checks stock by SKU and size here and spots shortfalls.

### pricing
Fields: `sku` TEXT PK (matches inventory.sku and tickets.sku), `unit_cost` REAL, `list_price` REAL
Why it matters: Accounting uses it for margin checks, discount floors and purchase-order cost.

### vendors
Fields: `id` INTEGER PK, `name`, `specialty`, `lead_days` INTEGER
Why it matters: gives restock lead times. There's no SKU column, so vendors are matched to products by `specialty`.

### invoices
Fields: `id` INTEGER PK, `vendor_id` FK→vendors.id, `amount` REAL, `due_date`, `status`, `description`
Why it matters: a vendor with an open unpaid invoice won't ship. It's also the source of overdue bills.

### leases
Fields: `id` INTEGER PK, `space_name`, `landlord`, `monthly_rent` REAL, `next_due`, `notes`
Why it matters: Facilities tracks rent amounts and due dates against `desk.date_today`.

### cash_accounts
Fields: `name` TEXT PK, `balance` REAL, `date`
Why it matters: the only source of cash. A payment must never push the balance below zero.

### payments
Fields: `id` INTEGER PK, `kind`, `ref_id` (→ invoices.id or leases.id depending on `kind`), `amount`, `account` (→ cash_accounts.name), `paid_at`, `approved_by`
Why it matters: the audit log of human-approved payments. It starts empty.

## Open tickets

### #101 — customer_order: Bulldog tee (Tauhid Zaman)
- inventory `CC-TEE-WHITE` / S → **qty 0** (shortfall 1)
- pricing `CC-TEE-WHITE` → cost $8, list $28
- vendors #1 Bulldog Print Co (apparel reprint) → lead 5 days
- invoices #501 (linked on the ticket) → vendor 1, **$840, due 2026-08-28, open → 3 days overdue; vendor blocked**
- cash_accounts `checking` $3,400 → paying #501 needs human approval and leaves $2,560

### #102 — rent_notice: Rent due (Elm City Properties)
- leases #1 Chapel Street shop → **$2,400, next_due 2026-09-02** (due in 2 days, not yet overdue)
- `tickets.requester` matches `leases.landlord`
- cash_accounts `checking` $3,400 → paying rent needs human approval and leaves $1,000 (or $160 if #501 is also paid)

### #103 — price_override: Bulk hoodie discount (Yale AI Club)
- inventory `CC-HOOD-NAVY` / M → **qty 8 of 20 requested (shortfall 12)**
- pricing `CC-HOOD-NAVY` → cost $22, list $58 (20 × list = $1,160, 62% margin; $22 is the floor)
- vendors #1 Bulldog Print Co → lead 5 days, **blocked by invoice #501**
- cash_accounts → a 12-unit restock costs $264 at cost, more than the $160 left after paying #501 and rent

## MCP tools

Server: `mcp_server/server.py` (FastMCP). Read-only connection to `data/campus_customs_new.db`.

- **check_stock** — reads `inventory` — unlocks ticket **101** — It looks up `CC-TEE-WHITE`/S by SKU and size and, given the requested qty, returns `can_fulfill=false` with `shortfall=1`, so the agents know a restock is needed.
- **get_lease_status** — reads `leases` (+ `desk.date_today`) — unlocks ticket **102** — It compares lease 1's `next_due` (2026-09-02) to the shop's today (2026-08-31) and returns `days_until_due=2`, `status="due_soon"`, plus the $2,400 rent.
- **get_sku_pricing** — reads `pricing` — unlocks ticket **103** — It gives the $22 cost floor, the $1,160 total and 62.07% margin at list for 20 hoodies, and scores any proposed bulk price (total, margin, `below_cost`), so agents can weigh the discount without the tool deciding for them.

## Agents

Pydantic AI, model `gpt-6-luna` via Portkey (`backend/config.py`, one constant), Responses API. Code: `backend/agents.py`; prompts: `backend/prompts/<agent>.md`.

All agents share one connection to the `campus-customs` MCP server over stdio (`MCPToolset` + `StdioTransport`, same command as `.mcp.json`). Each agent's view is filtered to **only its own tools** (`AGENT_TOOLS` in `backend/config.py`), and no agent gets `decide_approval`. Every agent also has `delegate(to_agent, task)` to call any other agent. Self-calls are refused, and so is going deeper than 3. Usage (`ctx.usage`) is shared, so the limits cover the whole delegation tree.

| Agent | Role | MCP tools (exactly these, plus `delegate`) | Output |
|---|---|---|---|
| **Boss** | Reads each ticket, routes it, weighs cash across all open tickets (cash figures come from Accounting), makes the final call, sets the ticket status | `get_today`, `get_ticket`, `list_open_tickets`, `list_pending_approvals`, `update_ticket_status` | `BossDecision` |
| **Inventory** | Stock by SKU/size, shortfalls, which vendor restocks, lead time, blocked status; requests restock POs | `get_today`, `get_ticket`, `check_stock`, `get_sku_pricing`, `list_vendors`, `get_vendor_status`, `request_purchase_order` | `AgentReport` |
| **Accounting** | Cash, invoices and margins; requests payments and price overrides | `get_today`, `get_ticket`, `get_cash_balance`, `get_invoice`, `get_vendor_status`, `get_sku_pricing`, `list_pending_approvals`, `request_payment`, `request_price_override` | `AgentReport` |
| **Facilities** | Leases, rent amount and due date, the shop space (delegates the rent request to Accounting) | `get_today`, `get_ticket`, `get_lease_status`, `get_cash_balance` | `AgentReport` |
| **Customer Service** | Honest message drafts only | `get_today`, `get_ticket`, `check_stock`, `get_sku_pricing`, `save_draft` | `AgentReport` |

Entry points: `run_ticket(ticket_id)` (Boss handles one ticket), `ping(agent, message)` (health check), `reset_working_db()` (run before a full run).

## MCP tools (full set, Problem 5)

| Tool | Kind | Tables |
|---|---|---|
| `check_stock` | read | inventory |
| `get_lease_status` | read | leases, desk |
| `get_sku_pricing` | read | pricing |
| `get_today` | read | desk |
| `get_ticket` | read | tickets |
| `list_tickets` | read (backend only, Problem 7) | tickets |
| `list_open_tickets` | read | tickets, desk |
| `list_vendors` | read | vendors, invoices |
| `get_vendor_status` | read | vendors, invoices, desk |
| `get_invoice` | read | invoices, vendors, desk |
| `get_cash_balance` | read | cash_accounts, approval_requests |
| `list_pending_approvals` | read | approval_requests |
| `list_approval_requests` | read (backend only, Problem 9) | approval_requests |
| `list_payments` | read (backend only, Problem 9) | payments |
| `request_payment` | request (no money moves) | approval_requests, invoices, leases, payments, cash_accounts |
| `request_purchase_order` | request (no money moves until approved; refused if vendor blocked or cash short) | approval_requests, vendors, invoices, inventory, pricing, cash_accounts |
| `request_price_override` | request | approval_requests, pricing |
| `save_draft` | request (nothing is sent) | drafts |
| `update_ticket_status` | request | tickets |
| `decide_approval` | **HUMAN-ONLY**, moves money: invoice/rent payments and purchase orders (PO → payments row kind `purchase_order`, status `executed`); price overrides move no cash | approval_requests, payments, cash_accounts, invoices, leases, vendors, pricing |

New tables created by the server on startup: `approval_requests`, `drafts`.

## Safety

- **Human approval for all money and discounts:** agents can only create requests. Only `decide_approval`, which a human calls, pays, orders or discounts.
- **No negative cash:** `request_payment` and `request_purchase_order` refuse if balance minus pending cash requests < amount. `decide_approval` re-checks cash inside the same transaction that pays an invoice, rent or purchase order.
- **No double pay:** paid invoices, rent already paid today, and duplicate pending requests are all refused.
- **No price below cost:** `request_price_override` refuses below `unit_cost`, and `decide_approval` re-checks it.
- **Drafts only:** `save_draft` is the only message tool. There is no send tool.
- **No invented data:** every fact comes from an MCP tool; missing rows return `{"error": "not found"}`. The backend never queries SQLite.
- **Least-privilege tools:** each agent sees only the MCP tools for its role (table above). `decide_approval` is in no agent's toolset and refuses agent names as `approved_by`.
- **Append-only audit:** every `agent.iter()` step is appended to `output/audit_trail.json`. The code never wipes the file, and a damaged file is never overwritten. Any model name other than `gpt-6-luna` in a logged field is replaced with `[redacted]`. (The file was reset to `[]` once by hand after the setup tests, before any ticket run.)
- **Reset before runs:** `reset_working_db()` copies `campus_customs.db` over `campus_customs_new.db`. The original is only read.
- **One model:** `gpt-6-luna` via Portkey, set in one constant. The key comes from `.env` and is never logged.
- **Token and delegation limits:** per ticket, 30 requests and 150,000 total tokens, shared across delegations (raised from 60,000 in Problem 9, after ticket 101's first run hit the old limit). Delegation depth is at most 3, and self-calls are refused.

## Backend routes

`backend/main.py` (FastAPI). Start it from `backend/` with `uvicorn main:app --reload --port 8000`. CORS allows `http://localhost:5173`. Every shop fact goes through the MCP server, and the backend never queries SQLite.

- `GET /tickets` — all tickets (id, type, subject, requester, status `open`/`resolved`, plus the detailed `ticket_status` and `running`), via `list_tickets`.
- `POST /tickets/{ticket_id}/run` — starts `run_ticket` in the background and returns a `run_id` right away (202). Refuses (409) if that ticket is already running; 404 if the ticket doesn't exist.
- `GET /runs/{run_id}` — (added in Problem 8 for the dashboard) one run's state (`running`/`finished`/`failed`), the Boss's full decision, and each agent's full report, so the board can show a per-agent summary. In memory only, for runs started by this server.
- `GET /events?since=<n>` — audit-trail entries with `seq > n` (time, run_id, ticket, agent, depth, step, tool, args, short result, delegated_to), plus `next_since` and the runs in progress.
- `GET /approvals` — pending approval requests, via `list_pending_approvals`. `GET /approvals?all=true` — every request, any status, via `list_approval_requests`.
- `GET /payments` — every payment made plus `total_paid`, via `list_payments` (added in Problem 9 for the cash check).
- `POST /approvals/{request_id}/approve` — body `{"approved_by": "<human name>"}`. Calls the human-only `decide_approval`. **The only route that can move money** (invoice, rent, and purchase-order payments). Agent names are refused (403); unknown ids return 404.
- `POST /approvals/{request_id}/reject` — same body; rejects the request through `decide_approval`. Nothing moves.
- `GET /cash` — checking balance, its date, pending payment requests and `available_after_pending`, via `get_cash_balance`.
- `POST /reset` — copies `data/campus_customs.db` over `data/campus_customs_new.db`. Refused (409) while a run is in progress. Doesn't touch `audit_trail.json`.

## Dashboard

React + Vite + TypeScript in `frontend/` ("The Floor"). Start it with `npm run dev` from `frontend/` (port 5173), with the backend on port 8000. The API URL is one constant, in `frontend/src/config.ts`. The look, layout, agent characters, tickets, slips, cash board and feed are described in **[design.md](design.md)**. The board polls `/events` every 2 s during a run and refreshes slips, cash and tickets every 4 s when idle. Approve/Reject needs a typed name, so nothing is auto-approved.

## Full run

Problem 9, shop date 2026-08-31. Started with `POST /reset` (checking $3,400.00). Run order: **101 → 102 → 103**, each run started like the board's Run button (`POST /tickets/{id}/run`). Every slip was approved by the human in the browser; no agent and no script approved anything.

| Ticket | Runs | How the runs ended | Slips (all approved by the human) | Final status |
|---|---|---|---|---|
| 101 | 3 (max) | run 1: token limit (64,815 > 60,000; the cap was then raised to 150,000) · run 2: awaiting_approval · run 3: 30-request limit | #1 invoice 501 $840.00 · #2 PO 1 tee $8.00 · #3 duplicate PO $8.00 · #4 rent $2,400.00 (for 102) | resolved, closed by the human with `update_ticket_status` |
| 102 | 1 | escalate_to_human (lease due date had moved to 2026-10-02 because rent was already paid; draft #4 to the landlord) | none in its own run (rent paid as #4 during 101's run 3) | resolved, closed by the human |
| 103 | 2 (max) | both awaiting_approval; 12-unit PO ($264) refused by the tool for cash | #5 price override 20 × $52.20 · #6 overlapping override 8 × $52.20 (no cash) | resolved, closed by the human |

**Cash summary** (from the `payments` table via `list_payments`):

| Pay # | Kind | For | Amount | Balance after |
|---|---|---|---|---|
| — | start | after reset | | $3,400.00 |
| 1 | invoice | invoice 501 (ticket 101) | −$840.00 | $2,560.00 |
| 2 | purchase_order | request #2, 1 × CC-TEE-WHITE S (101) | −$8.00 | $2,552.00 |
| 3 | purchase_order | request #3, the same tee again (101, duplicate) | −$8.00 | $2,544.00 |
| 4 | rent | lease 1 (ticket 102) | −$2,400.00 | $144.00 |
| | **total** | | **−$3,256.00** | **$144.00** |

$3,400.00 − $3,256.00 = **$144.00** = `cash_accounts.checking` ✓. The plan expected $152.00; the $8.00 gap is the duplicate tee PO.

**Lessons from the run:**
- Agents can only see *pending* requests. They can't see executed POs or paid rent, which caused the duplicate PO, the overlapping discount, and 102's "due date conflict".
- The Boss pulled other tickets' work into each run, which drove the limits.
- The DB was **not** reset afterwards; its final state is the evidence. Results are in `resolved_tickets.json` and `resolved_board.html`.
