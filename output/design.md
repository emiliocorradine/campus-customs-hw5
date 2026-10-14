# The Floor — Dashboard Design

The Campus Customs agent dashboard (`frontend/`, React + Vite + TypeScript) is styled as **"The Floor"**: a 1980s Wall Street trading floor. Five AI agents work tickets the way a trading desk works orders: a chairman in the corner office, four analysts at desks, phones between them, paper tickets, and slips a human must sign. Every character, name and line is original. No real people, actors or film characters are used or referenced.

Run it with `npm run dev` from `frontend/` (port 5173), with the backend running at `http://localhost:8000`. That URL lives in one constant, `src/config.ts`.

---

## 1. The look

| Element | Choice | Why |
|---|---|---|
| Background | Charcoal-navy (`#0d1118` → `#1a2740` glow) with faint horizontal scan lines | Evokes an after-hours floor and old CRT terminals; dark enough that the green/amber numbers glow. |
| Numbers | Quotron-style **monospace** (Consolas) in **phosphor green** (good / money on hand) and **amber** (pending, attention), each with a soft text glow | 1980s quote terminals showed green and amber on black. Monospace also lines digits up, so amounts are easy to compare. |
| Accents | **Brass/gold** borders, nameplates and the headline gradient | Brass reads as "corner office, old money". It frames important things (the Chairman, the cash board) without fighting the data colors. |
| Headlines | A high-contrast **serif** (Bodoni MT → Didot → Georgia fallback), set in gold | Financial-newspaper mastheads and engraved nameplates. It marks titles as titles, so body text and data stay sans/mono. |
| Paper | Deal tickets and trade slips are cream paper with ruled lines and dark ink | Physical paper on a dark desk is instantly recognizable as "a thing you act on", unlike the read-only glowing screens. |
| Red | Used only for alarms: the cash drop, pending-approval count, Reject, errors | Keeps red meaningful: if something is red, money moved or something needs you. |

Fonts are system fonts with fallbacks, so the page needs no internet. Text contrast is high (warm off-white `#ece6d6` on navy; dark ink on cream paper). The ticker pauses on hover and stops entirely for users who prefer reduced motion.

---

## 2. Layout

```
┌──────────────────────── scrolling ticker tape (cash · avail · open tickets · approvals · each ticket) ───────────────────────┐
│ THE FLOOR (serif masthead)  · shop date · wire status          [ LED CASH BOARD $3,400.00 ]              [ Reset floor ]      │
├──────────────────┬───────────────────────────────────────────────────────────┬──────────────────────────────────────────────┤
│ DEAL TICKETS     │  ┌──────── THE CHAIRMAN · corner office (big) ────────┐   │ SQUAWK BOX (live trader chat)                │
│  No.101 [OPEN]   │  └────────────────────────────────────────────────────┘   │  [#101] [All]                                │
│  No.102 [OPEN]   │  ☎ phone line:  Chairman ──☎──▶ Stock Desk ──☎──▶ Treasury │  STOCK DESK  #101  14:02:11                   │
│  No.103 [OPEN]   │  ┌ STOCK DESK ┐  ┌ TREASURY ┐                              │   [check_stock sku=… size=S]                │
│                  │  ┌ REAL ESTATE┐  ┌ CLIENT RELATIONS ┐                     │  TREASURY   ☎ Rings …                        │
│ SLIPS TO SIGN    │  CLOSING REPORT (after a run): Chairman's call + one line  │  …                                           │
│  trade slips     │  per agent                                                │                                              │
└──────────────────┴───────────────────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

- **Left: the work you can act on.** Tickets to send to the floor, and slips to sign. Both of the human's jobs are in one column.
- **Center: the people.** Who is working, who is on the phone with whom, and, after a run, what each of them did.
- **Right: the record.** A live chat of every step, scoped to the selected ticket or "All".
- **Top: the numbers that matter at a glance.** Tape plus the big LED balance.
- It fits a 1366×768 laptop screen with no horizontal scroll. Under 1180 px wide, the feed moves below the floor.

---

## 3. How each agent is shown

Every agent has an **original SVG avatar**, a **signature color** (used for its desk's top bar, avatar ring, nameplate, chat name and tool chips) and a **desk title** that says what it does.

| Agent | Desk | Avatar (original) | Color | Why |
|---|---|---|---|---|
| Boss | **The Chairman** (corner office) | Slicked-back hair, navy double-breasted suit, red suspenders with gold clips, a red-and-gold power tie, gold pocket square | Gold | He makes the final call, so he gets the **biggest card**: a full-width corner office with a city-skyline window, a 170 px portrait in a gold frame, an engraved brass nameplate, and his words in italic serif, like a memo. |
| Inventory | **Stock Desk** | Curly hair, green trading jacket with an "SD" desk badge, pencil behind the ear | Phosphor green | "Stock" is both inventory and the market; green matches "in stock / available". |
| Accounting | **Treasury** | Green accountant's eyeshade, round glasses, amber bow tie, vest | Amber | Amber is the "money pending" color everywhere on the board, which is exactly Treasury's job. |
| Facilities | **Real Estate** | Voluminous 80s hair, shoulder-pad blazer, pearl earrings and necklace | Sky blue | Leases and rent; blue suggests buildings and calm, long-term commitments. |
| Customer Service | **Client Relations** | Sleek bob, phone headset with mic, rose cardigan | Rose pink | The voice of the shop. The headset says "talks to customers"; the warm color says friendly. |

**Live states**
- **Active agent:** while a run is live, the desk of whoever produced the latest step **lights up** (it glows in its own color, the desk lamp pulses, and an "ON AIR" tag shows). The Chairman's office gets a gold halo when it's his turn.
- **Worked:** desks that already touched this ticket keep a dim lamp, so you can see who got involved.
- **Delegation = a phone call.** When an agent calls `delegate`, the **phone line** strip between the office and the desks shows the open chain, e.g. *The Chairman ─☎─▶ Stock Desk ─☎─▶ Treasury*, with an animated dashed wire. Both desks get a badge: "calling Treasury →" on the caller, "← on the line with Stock Desk" on the callee. The line hangs up when the delegate returns.
- Each desk shows the agent's **latest line** ("Working check_stock, list_vendors" or what it just said) and how many tool calls it made.

---

## 4. Tickets, approvals and cash

### Deal tickets
Each ticket is a cream **deal ticket**:
- the ticket number in serif ("No. 101") with the type underneath;
- **CLIENT** (the requester) and **ASK** (the subject);
- the last decision, if the ticket has been run;
- a rotated rubber **status stamp**:

| Stamp | Ink | Means |
|---|---|---|
| OPEN | orange | not handled yet |
| ON THE DESK | blue, pulsing | agents are working it now |
| AWAITING APPROVAL | red | requests are waiting for a human signature |
| RESOLVED | green | done |

Clicking a ticket selects it. Only the selected ticket shows the **▶ Send to the floor** button, which is disabled ("Desk busy") while any run is in progress, so tickets run one at a time in the planned order (101 → 102 → 103).

### Trade slips (approvals)
Every pending approval is a **trade slip**:
- a request number (REQ 0003) and the kind (PAY VENDOR INVOICE / PAY RENT / PURCHASE ORDER / PRICE OVERRIDE);
- the amount in large type;
- a red warning on slips that pay money out;
- the details: ticket, invoice/lease, vendor, item, unit price and which desk asked;
- the agent's reason, quoted in italic;
- a **"Sign here"** line that takes the human's name in a handwriting font.

**Approve** and **Reject** stay disabled until a name is typed, and that name is sent as `approved_by`. Nothing is ever auto-approved: agents can only *request*, and the UI has no path that approves without a signature and a click. The backend also refuses agent names as approvers.

### Cash
The checking balance sits in a black **LED board** with a brass bezel: big glowing green digits, with pending requests and "available after pending" in amber underneath. It refreshes **after every approval or rejection**. When the balance drops, the board **flashes red** for about three seconds and shows "▼ $840.00 paid out", so the effect of signing a payment is impossible to miss. The same figures also run along the ticker tape.

### Live feed (Squawk Box)
Named after the desk intercom. Each line has:
- the agent's name in its color, the ticket number and the time;
- what the agent said, or its tool calls as **small chips** (`check_stock sku=CC-TEE-WHITE · size=S`), with consecutive calls grouped on one line;
- phone calls ("☎ Rings Treasury: …") in amber, and replies ("Hears back: …");
- reports, and the Chairman's final call highlighted in gold;
- errors in red.

The board polls `GET /events?since=n` every 2 seconds while a run is live, so the chat scrolls in real time.

### Closing report
When a run finishes, the board fetches `GET /runs/{run_id}` and shows:
- **the Chairman's call:** decision stamp, summary, rationale and next steps for the human;
- **one short line per agent:** its own summary, the tools it used, the slips and drafts it created, and any blockers (e.g. "vendor 1 blocked by invoice 501").

The ticket's stamp and "LAST CALL" line update at the same time.

### Reset
"Reset floor" needs a **second, explicit confirmation** that says what it does (copy the original DB over the working copy, wiping pending slips and payments). It's disabled while a run is live. It never touches the audit trail.

---

## 5. Why it feels like a real desk

- **Physical metaphors map onto real actions.** Paper is what you act on (tickets, slips), and screens are what you watch (LED, feed, tape). People know without reading instructions that you *sign* a slip and *send* a ticket.
- **Hierarchy is visible.** The Chairman is bigger, framed in gold and sits above the analysts, so it's obvious who makes the final call.
- **Delegation becomes something you can see.** "Agents delegating via tool calls" is abstract. A phone line lighting up between two desks is not.
- **Consequences are felt.** Signing a payment makes the cash board flash red with the exact amount paid out, so approval doesn't feel like a harmless click.
- **Color carries meaning consistently.** Green means available or done; amber means pending or attention; red means money left or something needs you; gold means the Chairman.
- **Fun without noise.** The ticker, rubber stamps, handwriting signature, eyeshade and suspenders give it personality. The data itself stays in plain, high-contrast monospace, and nothing animates except to say something changed.
- **Honest by design.** Everything on screen comes from the backend: tickets, events, approvals and cash all come through the MCP tools. When there's no data, the board says so ("Phones quiet.", "No slips waiting.") instead of showing placeholders that look real.
