# AI Prompts Log — Homework 5: Campus Customs Multi-Agent Operations

## Problem 1 — Vibe coder prompts
**Prompt:**

````
I'm starting Homework 5 for my AI course: "Campus Customs Multi-Agent Operations." I'll be working ONLY inside the existing hw5/ folder. It already exists, so do NOT create a new folder, and do not put any files outside hw5/.

## Scenario
Campus Customs is a shop run by an agentic team. Tickets land on a board: customer orders, rent, unpaid bills, discount requests, and anything else the shop has to handle. Over this homework I will build three pieces that talk to each other:
1. An MCP server (mcp_server/)
2. A FastAPI backend with a multi-agent team (backend/)
3. A React dashboard (frontend/) where a human can watch the agents work and approve requests

The team has full connectivity: any agent may delegate a task to any other agent for help. The agents are:
- Boss: reads each ticket, decides who should work on it, and makes the final call
- Inventory: checks stock by SKU and size, spots shortfalls, and figures out which vendor can restock
- Accounting: watches cash and invoices, checks margins, and prepares payments or purchase orders for human approval
- Facilities: handles the shop space, sites, leases, rent, etc.
- Customer Service: drafts messages for customers

## Data
data.zip is already in hw5/. Do not download anything. If data/campus_customs.db doesn't exist yet, unzip data.zip so it does. That file is the ORIGINAL shop database. Its tables are: desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, invoices.
- Make a copy called data/campus_customs_new.db. This is the working copy. The MCP server and backend must point at it.
- NEVER modify data/campus_customs.db. It is the reset source.

## Shop rules (every later piece of code must respect these)
- desk.date_today is "today" for the shop. Use it, not the system clock, to decide what is overdue.
- Vendor lead times come from the vendors table.
- A vendor will not ship new product while it still has an open unpaid invoice.
- Human approval is required for ANY payment. When a payment is made, update the relevant tables.
- If there isn't enough cash, the pay tool must refuse. No negative balances.
- Cash only goes out. Revenue isn't modeled, so no money comes in.
- Before a full run to resolve tickets, reset the working DB to the original values (copy campus_customs.db over campus_customs_new.db).
- Do NOT email customers or call real vendors. Drafts stay on the board.
- AI calls use PORTKEY_API_KEY (read from .env, never hardcoded). Every agent must use ONLY the model gpt-6-luna through Portkey. No other model name may appear anywhere in the code, config, or runs.

## Required layout (use these exact names; don't rename, duplicate, or add parallel versions)
hw5/
├── AI_prompts.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .mcp.json
├── README.md
├── data/
│   ├── campus_customs.db
│   └── campus_customs_new.db
├── mcp_server/
│   ├── server.py
│   └── README.md
├── frontend/
├── backend/
│   ├── main.py
│   ├── models.py
│   └── prompts/
│       ├── boss.md
│       ├── inventory.md
│       ├── accounting.md
│       ├── facilities.md
│       └── customer_service.md
└── output/
    ├── harness.md
    ├── mcp_smoke.json
    ├── desk_tickets.html
    ├── design.md
    ├── resolved_tickets.json
    ├── resolved_board.html
    ├── audit_trail.json
    └── github_url.txt

Before creating any file, check whether it already exists and reuse it. If something seems to need a file not on this list, ask me first.

## What to do NOW (Problem 1 only)
1. Confirm you're in hw5/ and list what's already there.
2. Make sure data/campus_customs.db exists (unzip if needed) and create data/campus_customs_new.db as a copy. List the tables in the working copy to confirm all 9 are present.
3. Create .gitignore (include .env, __pycache__/, node_modules/, venvs) and .env.example with PORTKEY_API_KEY= (no real value).
4. Create AI_prompts.md. It's the log of the prompts I type to you, and I'll keep it updated throughout the homework. Use one section per problem, with this structure:

   ## Problem N — <Title>
   **Prompt:**
   <the prompt I typed, verbatim>
   **Follow-up prompt (if needed):**
   <verbatim, or "None">
   **What was lacking after the first prompt:**
   <one sentence>

   Fill in Problem 1 ("Vibe coder prompts") with THIS prompt pasted verbatim. Leave the follow-up and "what was lacking" fields for me to complete.

Don't start the MCP server, backend, agents, or frontend yet. Each of those is a separate problem I'll prompt you for. When you're done, show me the folder tree and the contents of AI_prompts.md.
````

**Follow-up prompt (if needed):**

<!-- TODO: fill in -->

**What was lacking after the first prompt:**

<!-- TODO: fill in -->

## Problem 2 — Study the Campus Customs database
**Prompt:**

````
Problem 2: Study the Campus Customs database. Work only inside hw5/.

1. Working copy: data/campus_customs_new.db should already exist from Problem 1. Check it. If it's missing, or differs from the original (compare file hashes), recreate it by copying data/campus_customs.db over it. Never write to data/campus_customs.db. Everything in this problem is READ-ONLY: no INSERT/UPDATE/DELETE on either file.

2. Study every table: desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, invoices. For each one, show me:
   - its fields (name, type, primary/foreign keys)
   - the row count and 2–3 sample rows
   - which other tables it links to, and through which fields (even if there's no formal foreign key, point out columns that clearly match, like SKU, vendor_id, lease_id, invoice_id)
   Also show me desk.date_today, since that's "today" for the shop.

3. Study the 3 open tickets. For each one, trace how it connects to the other tables:
   - what the ticket is asking for, and which agent(s) would likely own it (Boss, Inventory, Accounting, Facilities, Customer Service)
   - every related row it touches (e.g., SKU/size in inventory → pricing → vendor and lead time → open invoices → cash_accounts; or lease → rent due vs. desk.date_today)
   - any shop rule that will matter: overdue vs. date_today, a vendor blocked by an open unpaid invoice, not enough cash, payment needs human approval, drafts only (no real emails)
   Don't resolve anything yet. Just map the links.

4. Create output/harness.md. This file will keep growing in later problems, so structure it with clear headers. For now, include:
   - a short intro (DB path used, working copy vs. original, desk.date_today)
   - a "Tables" section with one subsection per table: a list of its fields + ONE short line on why that table matters to the agents
   - an "Open tickets" section: one short entry per open ticket showing the tables/rows it links to

5. Update AI_prompts.md: add a "## Problem 2 — Study the Campus Customs database" section using the same structure as Problem 1, with this prompt pasted verbatim. Leave the follow-up and "what was lacking" fields for me.

When you're done, give me a short summary of the 3 open tickets and how each links across tables. Then show me output/harness.md.
````

**Follow-up prompt (if needed):**

<!-- TODO: fill in -->

**What was lacking after the first prompt:**

<!-- TODO: fill in -->

## Problem 3 — Build the MCP server
**Prompt:**

````
Problem 3: Build the MCP server. Work only inside hw5/ and don't create any new folders besides what the layout already has.

## Goal
Write an MCP server in mcp_server/server.py using FastMCP. It talks ONLY to data/campus_customs_new.db (the working copy). Never touch data/campus_customs.db. Every agent in this homework will use the tools in this server, and I'll add more tools in later problems, so keep the code easy to extend (one shared DB helper, one function per tool). In this problem, do NOT connect, register, or run the server against any agent. Just write it. A syntax/import check (python -m py_compile mcp_server/server.py) is fine.

## Rules for the tools
- Names must be clear and descriptive.
- NEVER invent data. Every value returned must come straight from the database or be simple arithmetic on database values. If a SKU, size, or ID isn't found, return a clear error like {"error": "not found", ...}. No defaults, guesses, or placeholder numbers.
- All three tools are READ-ONLY (SELECT only). No payments or writes in this problem.
- Resolve the DB path relative to server.py (../data/campus_customs_new.db) so it works from any working directory. Open connections read-only with sqlite3 (uri "file:...?mode=ro"), with row_factory so results come back as dicts.
- "Today" for the shop is desk.date_today, never the system clock.
- Each tool gets a docstring that says what it does, its inputs, and what it returns. The agents will read these docstrings to choose tools.

## The 3 tools
1. check_stock(sku: str, size: str, qty_requested: int | None = None)
   - Reads: inventory
   - Returns sku, name, size, qty_on_hand, location. If qty_requested is given, also return can_fulfill (bool) and shortfall (max(0, qty_requested - qty_on_hand)).
   - Unlocks ticket 101 (CC-TEE-WHITE, size S). It will also be reused for 103.

2. get_lease_status(lease_id: int)
   - Reads: leases (plus desk.date_today for "today")
   - Returns id, space_name, landlord, monthly_rent, next_due, date_today, days_until_due (next_due minus date_today, in days), and status: "overdue" if days_until_due < 0, "due_soon" if 0–7, otherwise "not_due".
   - Unlocks ticket 102 (lease_id 1).

3. get_sku_pricing(sku: str, qty: int, proposed_unit_price: float | None = None)
   - Reads: pricing
   - Returns sku, unit_cost, list_price, qty, total_at_list, margin_pct_at_list. If proposed_unit_price is given, also return total_at_proposed, margin_pct_at_proposed, and below_cost (bool). The tool reports numbers only. It does NOT approve or reject a discount; the agents decide.
   - Unlocks ticket 103 (CC-HOOD-NAVY, size M, qty 20, bulk discount request).

## Other files
- requirements.txt: make sure fastmcp is listed (create the file if it doesn't exist yet; don't duplicate entries).
- mcp_server/README.md (short): what the MCP server is for (the shared tool layer every Campus Customs agent uses), which database file it uses (data/campus_customs_new.db, with campus_customs.db kept untouched as the reset source), and the 3 tools with a one-line description each. Note that more tools will be added later.
- output/harness.md: add a new section "## MCP tools" below the existing content (don't rewrite what's already there). One entry per tool, in this format:
  - **check_stock** — reads `inventory` — unlocks ticket **101** — <one sentence on why it's the right tool for that ticket>
  - **get_lease_status** — reads `leases` (+ `desk.date_today`) — unlocks ticket **102** — <one sentence>
  - **get_sku_pricing** — reads `pricing` — unlocks ticket **103** — <one sentence>
- AI_prompts.md: add "## Problem 3 — Build the MCP server" in the same structure as earlier problems, with this prompt pasted verbatim. Leave the follow-up and "what was lacking" fields for me.

When you're done, show me server.py, the new harness section, and mcp_server/README.md, plus the py_compile result.
````

**Follow-up prompt (if needed):**

<!-- TODO: fill in -->

**What was lacking after the first prompt:**

<!-- TODO: fill in -->

## Problem 4 — Connect and smoke-test the MCP server
**Prompt:**

````
Problem 4 (part A): Connect my MCP server to you (Claude Code). Work only inside hw5/.

1. Check that mcp_server/server.py ends with:
   if __name__ == "__main__":
       mcp.run()
   so it starts as a stdio server. Add it only if it's missing; don't change the tools.
2. Create .mcp.json at the hw5/ project root (this is where Claude Code reads project-scoped MCP servers) with exactly one server named "campus-customs":
   {
     "mcpServers": {
       "campus-customs": {
         "command": "python",
         "args": ["mcp_server/server.py"]
       }
     }
   }
   Keep the path relative to the project root (no absolute Windows paths), so
````

**Follow-up prompt (if needed):**

````
Problem 4 (part A, follow-up): My previous prompt was cut off after "Keep the path relative to the project root (no absolute Windows paths), so". Here's the rest. Work only inside homework 5/.

1. Finish the .mcp.json check. Keeping the path relative means it still works when the repo is cloned from GitHub. My folder name has a space ("homework 5"), and a relative path avoids quoting problems, so don't change .mcp.json to an absolute path. Leave it as it is now.
2. Check which Python the "python" command points to (`where python`). If "python" isn't the right command on my machine (e.g. it's "py" or a venv), tell me before changing .mcp.json.
3. Install the dependencies into that same Python: run `pip install -r requirements.txt` from homework 5/. You have my permission to install. Confirm with `python -c "import fastmcp; print(fastmcp.__version__)"`.
4. Startup check: run `python -c "import ast; ast.parse(open('mcp_server/server.py').read())"` from homework 5/, and confirm the 3 tools are check_stock, get_lease_status, get_sku_pricing.
5. Update AI_prompts.md under "## Problem 4 — Connect and smoke-test the MCP server". Keep the first prompt exactly as logged (cut off, since that's what I actually typed), and put this prompt verbatim in the "Follow-up prompt" field. Fill in "What was lacking after the first prompt" with: "The first prompt was cut off mid-sentence, so fastmcp was never
````

**What was lacking after the first prompt:**

The first prompt was cut off mid-sentence, so fastmcp was never installed and the MCP server couldn't start.

**Follow-up prompt 2:**

````
Problem 4 (part B): Test the campus-customs MCP tools. Do everything yourself from this session; I am not restarting or opening anything.

1. In AI_prompts.md, under Problem 4, replace the cut-off "What was lacking" sentence and its TODO with:
   "The first prompt was cut off mid-sentence, so fastmcp was never installed and the MCP server couldn't start."

2. Record the SHA-256 of homework 5/data/campus_customs_new.db.

3. Test the tools through a real MCP connection: write a temporary Python script that uses fastmcp's Client to start the server over stdio exactly as .mcp.json does (command "python", args ["mcp_server/server.py"], working directory homework 5/). Then call:
   - check_stock(sku="CC-TEE-WHITE", size="S", qty_requested=1)  → ticket 101
   - get_lease_status(lease_id=1)  → ticket 102
   - get_sku_pricing(sku="CC-HOOD-NAVY", qty=20)  → ticket 103
   Do not import server.py or query SQLite directly. Put the script in a temp folder, NOT in homework 5/, and delete it when done.

4. Check the outputs against the database:
   - 101: qty_on_hand 0, shortfall 1
   - 102: monthly_rent 2400, days_until_due 2, status "due_soon"
   - 103: unit_cost 22, list_price 58, total_at_list 1160
   If anything differs, fix the tool, not the data.

5. Record the SHA-256 again. It must be unchanged.

6. Save homework 5/output/mcp_smoke.json with: the server name, the config file, the database path, the hash before and after, and a "tests" list. Each test needs: the ticket number, this prompt, the tool name, the arguments, the exact tool output, and matches_db (true/false).

7. Add this prompt to AI_prompts.md under Problem 4 as "Follow-up prompt 2", word for word.

Finally, show me mcp_smoke.json.
````

## Problem 5 — Build the agent team and grow the MCP tools
**Prompt:**

````
Problem 5: Build the agent team and grow the MCP tools. Work only in homework 5/. If this prompt doesn't end with "END OF PROMPT", stop and tell me it was cut off.

RULES: Shop facts come ONLY from MCP tools over data/campus_customs_new.db (no second tool layer, never query SQLite from the backend). Never invent data. Never touch data/campus_customs.db. Only model: gpt-6-luna via Portkey with PORTKEY_API_KEY from .env. Copy the Portkey + Pydantic AI setup from ../homework 4 (read-only). Model name in ONE constant. Never log the key.

1. MCP SERVER (mcp_server/server.py). Keep the 3 existing tools. On startup create tables IF NOT EXISTS: approval_requests (id, kind, ticket_id, ref_id, vendor_id, sku, size, qty, unit_price, amount, reason, requested_by, status, decided_by, result_note) and drafts (id, ticket_id, recipient, subject, body, author_agent). Dates = desk.date_today. Add tools:
- Read: get_today, get_ticket, list_open_tickets, list_vendors, get_vendor_status (blocked if open unpaid invoice; arrival = today + lead_days), get_invoice (days overdue), get_cash_balance, list_pending_approvals
- Request (no money moves): request_payment (invoice or rent; amount must match DB; refuse if already paid/requested or not enough cash), request_purchase_order (cost = unit_cost × qty; refuse if vendor blocked), request_price_override (refuse below unit_cost), save_draft (no send tool exists), update_ticket_status
- HUMAN-ONLY decide_approval(request_id, approve/reject, approved_by): for payments, in one transaction, refuse if cash < amount; else insert into payments, lower cash_accounts, mark invoice paid or move lease next_due forward 1 month.
Update mcp_server/README.md to list every tool and its table.

2. AGENTS (Pydantic AI, in backend/). config.py (model, Portkey, limits), models.py (TicketDeps, AgentReport, BossDecision), agents.py (5 agents + run_ticket(ticket_id)), audit.py, and prompts/boss.md, inventory.md, accounting.md, facilities.md, customer_service.md. Each prompt is detailed: role, scope, tools and when to use them, shop rules, who to delegate to, what to return, when to ask a human, never-do list.
- Boss: routes tickets, makes the final call, weighs cash across all tickets.
- Inventory: stock by SKU/size, shortfalls, vendor + lead time + blocked status.
- Accounting: cash, invoices, margins; requests payments/POs/discounts.
- Facilities: leases and rent due.
- Customer Service: honest drafts only.
Every agent gets the MCP server (MCPServerStdio) minus decide_approval, and a delegate(to_agent, task) tool to call any other agent (shared ctx.usage; refuse self-calls and depth > 3).
Limits: UsageLimits request_limit 30, total_tokens_limit 60000 per ticket.
Audit: use agent.iter() and APPEND every step to output/audit_trail.json (timestamp, run_id, ticket_id, agent, step type, tool, args, short result, delegated_to, tokens). Never wipe the file.
Add pydantic-ai and python-dotenv to requirements.txt. Leave main.py endpoints for later.

3. CHECK: import everything, confirm no agent has decide_approval, make ONE live Boss call ("Reply OK") to prove Portkey works and that it appends to the audit file. Don't run the tickets. If anything wrote to the DB, reset it from campus_customs.db.

4. DOCS: In output/harness.md add (below existing content) "Agents" (each agent + its tools), "MCP tools" (every tool + table it uses), and a short "Safety" list: human approval for all money and discounts, no negative cash, no double pay, no price below cost, drafts only, no invented data, least-privilege tools, append-only audit, reset before runs, one model, token and delegation limits.
In AI_prompts.md add "## Problem 5 — Build the agent team and grow the MCP tools" with this prompt verbatim.

Show me a short summary when done.
END OF PROMPT
````

**Follow-up prompt 1:**

````
Problem 5 follow-up: two fixes. Work only in homework 5/.

1. output/audit_trail.json: the error logged from the failed first call contains the model name "[redacted]", and my assignment deducts points for any model other than gpt-6-luna showing up in runs. These are setup tests, not real runs, so do a one-time cleanup: reset the file to an empty JSON array []. The append-only behavior in audit.py stays exactly as is. Also make sure that from now on, logged errors replace any model name other than gpt-6-luna with "[redacted]".

2. Least privilege: harness.md says each agent only gets the tools for its role, but every agent has all 16 MCP tools. Filter each agent's MCP toolset to:
- Boss: get_today, get_ticket, list_open_tickets, list_pending_approvals, update_ticket_status
- Inventory: get_today, get_ticket, check_stock, get_sku_pricing, list_vendors, get_vendor_status, request_purchase_order
- Accounting: get_today, get_ticket, get_cash_balance, get_invoice, get_vendor_status, get_sku_pricing, list_pending_approvals, request_payment, request_price_override
- Facilities: get_today, get_ticket, get_lease_status, get_cash_balance
- Customer Service: get_today, get_ticket, check_stock, get_sku_pricing, save_draft
Every agent still keeps delegate, and none gets decide_approval. Update the Agents section of harness.md to match.

Check without model calls: print each agent's tool list. Make sure the DB hash still matches the original (reset it if not).

Add this prompt to AI_prompts.md under Problem 5 as "Follow-up prompt 1", verbatim. Fill in "What was lacking after the first prompt" with: "The first prompt didn't specify per-agent tool lists, so every agent got every tool, and a failed test call logged a non-allowed model name in the audit trail."

END OF PROMPT
````

**What was lacking after the first prompt:**

The first prompt didn't specify per-agent tool lists, so every agent got every tool, and a failed test call logged a non-allowed model name in the audit trail.

## Problem 6 — Plan the three tickets
**Prompt:**

````
Problem 6: Plan the three tickets. Work only in homework 5/. If this prompt doesn't end with "END OF PROMPT", stop and tell me.

Build output/desk_tickets.html: ONE self-contained file (inline CSS/JS, no internet, opens with a double click). Tabs: 101, 102, 103, Cache, Reflection. Cache and Reflection just say "Coming in a later problem." Each ticket tab shows the ticket facts at the top, then an "Expected" section (text below, copied exactly), then an empty "Actual" section with a placeholder "To fill after the agents run." Clean and readable. Don't run any agents or touch the DB.

Context for all tabs (put at the top of the page): Today is 2026-08-31. Cash is $3,400. Priorities: rent first (we can't lose the shop), then invoice 501 (it blocks our only apparel vendor), then restocks. Paying rent + 501 = $3,240, which leaves $160. All payments, POs and discounts wait for my approval.

TICKET 101 — Tauhid Zaman wants 1 Bulldog tee, size S
Expected:
- Boss calls Inventory first, because this is a stock question.
- Inventory: check_stock(CC-TEE-WHITE, S, 1) → 0 in stock, short 1. list_vendors → Bulldog Print Co does apparel. get_vendor_status(1) → blocked by open invoice 501.
- Inventory delegates to Accounting, because the vendor won't ship until 501 is paid.
- Accounting: get_invoice(501) → $840, 3 days overdue. get_cash_balance → $3,400. request_payment(invoice 501, $840) → pending my approval.
- After I approve, Inventory can request_purchase_order(vendor 1, tee S, qty 1) → $8, about 5 days lead time. Before that, the PO would be refused.
- Boss calls Customer Service: save_draft to Tauhid saying it's out of stock and being restocked. No promised date.
- Boss: update_ticket_status → waiting_approval.
- Not called: Facilities (nothing to do with space or rent).

TICKET 102 — Elm City Properties: rent due
Expected:
- Boss calls Facilities first, because leases are its job.
- Facilities: get_lease_status(1) → $2,400 due 2026-09-02, due in 2 days (due_soon). get_cash_balance → $3,400, enough.
- Facilities delegates to Accounting to prepare the payment.
- Accounting: request_payment(rent, lease 1, $2,400) → pending my approval. Cash after: $1,000 (or $160 if 501 is also paid).
- Boss: update_ticket_status → waiting_approval.
- Not called: Inventory (no product), Customer Service (no customer message needed).

TICKET 103 — Yale AI Club: 20 navy hoodies, size M, bulk discount
Expected:
- Boss calls Inventory first, because we have to know if we can even fill the order.
- Inventory: check_stock(CC-HOOD-NAVY, M, 20) → 8 in stock, short 12. get_vendor_status(1) → blocked by invoice 501. Restocking 12 would cost $264, more than the $160 left after rent and 501, so no PO now.
- Boss calls Accounting for the discount.
- Accounting: get_sku_pricing(CC-HOOD-NAVY, 8, proposed price) → cost $22, list $58. request_price_override for a modest discount (up to 10%, about $52.20 each, never below $22) on the 8 in stock → pending my approval.
- Boss calls Customer Service: save_draft to the club offering the 8 now at the discounted price, and the other 12 later. No promised date.
- Boss: update_ticket_status → waiting_approval.
- Not called: Facilities.

Add this prompt to AI_prompts.md as "## Problem 6 — Plan the three tickets", verbatim. Show me the page when done.
END OF PROMPT
````

**Follow-up prompt 1:**

````
Problem 6 follow-up: three fixes. Work only in homework 5/. If this prompt doesn't end with "END OF PROMPT", stop and tell me.

1. In output/desk_tickets.html, change "waiting_approval" to "awaiting_approval" everywhere, to match the tool.
2. In ticket 103's Expected section, replace the Inventory bullet's cash part with: "Inventory asks Accounting whether a restock fits the budget. Accounting says it costs $264, more than the $160 left after rent and 501, so no PO now." Add a line at the top of the page: "Run order: 101, then 102, then 103."
3. In backend/prompts/accounting.md, add this rule: "Bulk discounts: at most 10% off list price, never below unit_cost. Anything bigger needs a human to decide."

Don't run agents. Keep the DB matching the original.
Add this prompt to AI_prompts.md under Problem 6 as "Follow-up prompt 1", verbatim. Fill in "What was lacking after the first prompt" with: "The first plan used a status name the tool doesn't accept and assumed Inventory could see cash, and the 10% discount cap wasn't in Accounting's prompt."
END OF PROMPT
````

**What was lacking after the first prompt:**

The first plan used a status name the tool doesn't accept and assumed Inventory could see cash, and the 10% discount cap wasn't in Accounting's prompt.

## Problem 7 — Backend routes
**Prompt:**

````
Problem 7: Backend routes. Work only in homework 5/. If this prompt doesn't end with "END OF PROMPT", stop and tell me.

In backend/main.py, build a FastAPI app that the React dashboard (next problem) will call at http://localhost:8000. It must start from inside backend/ with:
  uvicorn main:app --reload --port 8000
Make the imports work when run that way. Add CORS for the frontend dev server (http://localhost:5173).

Rules: shop facts come ONLY through the MCP server tools, never by querying SQLite from the backend. Money only changes through the approve route.

Routes:
1. GET /tickets → all 3 tickets with id, type, subject, requester and status (open or resolved). If no MCP tool lists ALL tickets, add list_tickets to the MCP server (reads tickets) and update mcp_server/README.md.
2. POST /tickets/{ticket_id}/run → runs the agent team on that ticket (run_ticket). Run it in the background so the request doesn't hang. Return a run_id right away. Refuse a second run on the same ticket while one is still running.
3. GET /events?since=<n> → recent entries from output/audit_trail.json (agent, step, tool, short result, ticket, time), so the board can refresh. "since" returns only newer entries.
4. GET /approvals → pending approval requests (list_pending_approvals).
5. POST /approvals/{request_id}/approve and /reject with body {"approved_by": "<human name>"} → calls the human-only MCP tool decide_approval. This is the ONLY route that changes cash. Agent names are refused as approvers.
6. GET /cash → current checking balance (get_cash_balance).
7. POST /reset → copies data/campus_customs.db over data/campus_customs_new.db. Refuse while a run is in progress. Don't touch audit_trail.json.

Test: start the server with the exact command above and call every GET route, POST /reset, and approve/reject on a nonexistent id (it should return a clean error). Do NOT call /run, because that spends tokens. Make sure the DB matches the original at the end.

In output/harness.md add a "Backend routes" section with one line per route: method + URL — what it does.
Add this prompt to AI_prompts.md as "## Problem 7 — Backend routes", verbatim.
Show me the route list and test results.
END OF PROMPT
````

**Follow-up prompt (if needed):**

<!-- TODO: fill in -->

**What was lacking after the first prompt:**

<!-- TODO: fill in -->

## Problem 8 — Agent dashboard
**Prompt:**

````
Problem 8: Agent dashboard. Work only in homework 5/. If this prompt doesn't end with "END OF PROMPT", stop and tell me.

Build the dashboard in frontend/ with React + Vite + TypeScript. It calls the Problem 7 backend at http://localhost:8000 (put the URL in ONE constant). The backend already allows the origin http://localhost:5173; confirm that. The board starts with: npm run dev (from frontend/).

MUST DO
- List all 3 tickets with their status (GET /tickets).
- Pick a ticket and start the team on it (POST /tickets/{id}/run). Disable the button while it runs.
- While it runs, poll GET /events?since=n every 2s and show live what each agent says and which tools it calls.
- When the run finishes, mark the ticket's result, and show a short summary per agent of what it did on that ticket.
- Show pending approvals (GET /approvals) with Approve / Reject. Ask the human to type their name; send it as approved_by. Never auto-approve.
- Show the checking balance (GET /cash). Refresh it after every approval so it visibly drops after an approved payment.
- A Reset button (POST /reset) with a confirm step.

LOOK: "The Floor", a 1980s Wall Street trading floor. All characters are ORIGINAL: no real actors, no movie characters, names or quotes.
- Dark charcoal/navy background, Quotron-style green and amber monospace numbers, brass/gold accents, a serif headline font.
- A scrolling ticker tape across the top: cash balance, open tickets, pending approvals.
- The Boss = "The Chairman": a corner-office card with an original CSS/SVG avatar (slicked-back hair, suspenders, power tie). He's bigger than the rest because he makes the final call.
- The analysts sit at desks below, each with its own original avatar and color: Inventory = "Stock Desk", Accounting = "Treasury", Facilities = "Real Estate", Customer Service = "Client Relations". The active agent's desk lights up, and delegations show as an arrow or "phone call" between desks.
- The live feed reads like a trader chat: agent name, the message, and tool calls as small chips.
- Tickets look like deal tickets (number, client, ask, status stamp: OPEN / AWAITING APPROVAL / RESOLVED).
- Approvals look like a trade slip you sign. The cash display is a big LED-style number that flashes red when it drops.
- Keep it readable: good contrast, works on a laptop screen. If AGENTS.md asks for a different style, this page's style wins for this problem.

TEST: npm install, npm run build with no errors, then start the backend and npm run dev, and screenshot the page in a headless browser. Do NOT click Run (it spends tokens). Make sure the DB matches the original at the end (POST /reset).

Write output/design.md: the look, the layout, how each agent is shown differently, how tickets, approvals and cash appear, and why, including the creative choices that make it feel like a real desk people would enjoy using.
Add this prompt to AI_prompts.md as "## Problem 8 — Agent dashboard", verbatim.
Show me the screenshot when done.
END OF PROMPT
````

**Follow-up prompt (if needed):**

<!-- TODO: fill in -->

**What was lacking after the first prompt:**

<!-- TODO: fill in -->

## Problem 9 — Resolve the tickets
**Prompt:**

````
Problem 9: Resolve the tickets. Work only in homework 5/. If this prompt doesn't end with "END OF PROMPT", stop and tell me.

0. FIX FIRST: in the MCP tool decide_approval, approving a purchase_order must also pay it: in one transaction, refuse if cash < amount (no negative balance), otherwise insert a payments row (kind 'purchase_order'), lower cash_accounts, and set the status to 'executed'. Price overrides still move no cash. Update mcp_server/README.md and harness.md to match.

1. RESET: start the backend (uvicorn main:app --reload --port 8000 from backend/) and the board (npm run dev from frontend/), then POST /reset. Record the starting checking balance (should be $3,400). Open http://localhost:5173 in my default browser. Don't wipe audit_trail.json; it only appends.

2. RUN in order 101, then 102, then 103. Start each run the same way the board's Run button does. Watch /events and /approvals.
- When a slip appears, STOP and tell me: "Slip #X: <kind> $<amount> for ticket <id>. Approve it in the browser." Wait until I say done. NEVER call approve/reject yourself; only I approve.
- After my approvals, run the same ticket again so the team sees the result and the Boss can finish it. Repeat until the Boss marks it resolved, at most 3 runs per ticket. If a ticket can't be resolved, or hits a token limit, stop and tell me. Don't raise limits on your own.

3. CHECK THE CASH from the DB (through the backend/MCP): every row in payments, and the final cash_accounts balance. Starting balance minus the sum of payments must equal the ending balance exactly. Flag anything that doesn't match.

4. output/desk_tickets.html (keep every Expected section unchanged):
- Each ticket tab, Actual section: which agents worked, in what order, what they delegated to whom, which MCP tools they called, what was approved, and the final status. Add one line on how it differed from Expected.
- Cash tab: starting balance after reset; for each ticket, every payment (kind, what it paid, amount, approved by) and why; balance after each ticket; ending balance. Numbers taken from the payments table, and the totals must add up.

5. output/resolved_tickets.json: for each ticket: id, final status, short outcome, what each agent contributed, human approvals (request id, kind, amount, approved_by).

6. output/resolved_board.html: one double-clickable page with a screenshot of the React board for EACH resolved ticket (101, 102, 103 selected, showing its feed/summary). Take them with a headless browser while the servers are still up, and embed the images in the HTML as base64 so it works offline.

7. output/harness.md: make sure it covers tables, MCP tools, the five agents, API routes, the dashboard (point to design.md) and safety rules. Add a short "Full run" section: run order, number of runs per ticket, and the cash summary.

8. AI_prompts.md: add "## Problem 9 — Resolve the tickets" with this prompt verbatim.

Stop both servers at the end. Don't reset the DB at the end; the final state is the evidence. Show me the cash summary.
END OF PROMPT
````

**Follow-up prompt 1:**

````
Keep the current state. No reset, no code changes. Finish Problem 9:

1. Ticket 101: stop here. Record it as done by the agents but not marked resolved (token limit on run 1, request limit on run 3, duplicate $8 PO). Then set its status to resolved yourself through the update_ticket_status MCP tool, with the note "Closed by human after 3 runs: invoice paid, tee ordered, customer draft saved."
2. Run 102 once (rent is already paid, so the team should just confirm and resolve it), then run 103 once. If a slip appears, tell me the amount and wait for me. Max 2 runs each.
3. Write everything from the original Problem 9 prompt: the Actual sections and Cash tab in output/desk_tickets.html (every payment from the payments table, including the duplicate $8, ending balance must match the DB), output/resolved_tickets.json, output/resolved_board.html with a screenshot for each ticket, and the "Full run" section in harness.md.
4. Add this prompt to AI_prompts.md under Problem 9 as "Follow-up prompt 1", verbatim. Fill in "What was lacking" with: "Agents couldn't see already-executed requests, so they ordered the same tee twice, and the Boss worked on other tickets and hit the limits."
Stop both servers at the end. Show me the cash summary.
````

**What was lacking after the first prompt:**

Agents couldn't see already-executed requests, so they ordered the same tee twice, and the Boss worked on other tickets and hit the limits.

## Problem 10 — Reflection
**Prompt:**

````
Problem 10: Reflection. Put the text from reflection_draft.md (in homework 5/) into the Reflection tab of output/desk_tickets.html, with my wording kept and a heading for each section. Replace every [FILL: ...] with the real facts from the 103 Actual tab and the Cash tab; invent nothing. Don't change other tabs. Then delete reflection_draft.md. Add this prompt to AI_prompts.md as "## Problem 10 — Reflection", verbatim.
````

**Follow-up prompt (if needed):**

<!-- TODO: fill in -->

**What was lacking after the first prompt:**

<!-- TODO: fill in -->
