# Campus Customs — Multi-Agent Operations (Homework 5)

Campus Customs is a campus apparel shop run by a team of **5 AI agents**:
- **Boss** ("The Chairman")
- **Inventory** ("Stock Desk")
- **Accounting** ("Treasury")
- **Facilities** ("Real Estate")
- **Customer Service** ("Client Relations")

They work tickets from a shared board (customer orders, rent, unpaid bills, discount requests) and can delegate to each other.

- **MCP server** (`mcp_server/server.py`, FastMCP): the only code that touches the shop database. It provides read tools, request tools and one human-only `decide_approval` tool.
- **Backend** (`backend/`, FastAPI + Pydantic AI): runs the agent team (model `gpt-6-luna` via Portkey), streams every step to an append-only audit trail, and exposes the routes the board uses.
- **Board** (`frontend/`, React + Vite + TypeScript): "The Floor", a 1980s trading-floor dashboard where a human watches the agents work and signs approval slips.

Every payment, purchase order and discount waits for a human signature. Cash can never go negative.

## Run it

**a. Install and configure**
```bash
pip install -r requirements.txt
cp .env.example .env        # then put your key in .env:  PORTKEY_API_KEY=...
```

**b. Start from a clean database**
- `data/campus_customs.db` is the original, and the reset source. Never edit it.
- `data/campus_customs_new.db` is the working copy. The repo ships it in its **final state after the graded run**, as evidence.
- For a clean run, copy the original over the working copy, or call `POST /reset` once the backend is up:
```bash
cp data/campus_customs.db data/campus_customs_new.db
```

**c. MCP server**
- `python mcp_server/server.py` (stdio) starts automatically with the backend; you don't start it by hand.
- `.mcp.json` also registers it as `campus-customs` for Claude Code when the project is opened here.

**d. Backend** (port 8000)
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**e. Board** (port 5173)
```bash
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

**f. Full run**
1. Reset the DB (step b, or the **Reset floor** button).
2. Run the tickets in order **101 → 102 → 103** with **Send to the floor**.
3. When a slip appears under **Slips to Sign**, type your name and Approve or Reject it. Agents can only request; you sign.

## Outputs (`output/`)

- `harness.md` — the reference: tables, open tickets, MCP tools, agents and their tools, backend routes, dashboard, safety rules, and the full-run summary.
- `mcp_smoke.json` — smoke test of the first 3 MCP tools over a real stdio connection, with DB hashes before and after.
- `desk_tickets.html` — the plan (Expected), what actually happened (Actual), the cash ledger and the reflection, one tab each.
- `design.md` — the dashboard's look, layout and design reasoning.
- `resolved_tickets.json` — per ticket: final status, outcome, each agent's contribution, and the human approvals.
- `resolved_board.html` — offline screenshots of the board for tickets 101, 102 and 103 after the run.
- `audit_trail.json` — append-only log of every agent step (agent, tool, args, short result, delegation, tokens).
- `github_url.txt` — the URL of this repository.

`AI_prompts.md` logs every prompt used to build the project, problem by problem.
