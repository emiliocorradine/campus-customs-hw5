# Campus Customs MCP server

`server.py` is the shared tool layer every Campus Customs agent (Boss, Inventory, Accounting, Facilities, Customer Service) uses for shop data. It's built with FastMCP and is the **only** code that touches the database. The backend never queries SQLite itself.

## Database

- **Uses:** `data/campus_customs_new.db`, the working copy. The path is resolved relative to `server.py`, so it works from any directory.
- **Never touches:** `data/campus_customs.db`. That file stays as the untouched reset source.
- **On startup** it creates two tables if they don't exist: `approval_requests` and `drafts`.
- "Today" for the shop is `desk.date_today`, never the system clock. Payment dates use it too.
- If a SKU, size or ID doesn't exist, a tool returns `{"error": "not found", ...}`. Refusals return `{"error": "refused", "detail": ...}`. Tools never invent values.

## Tools

### Read (SELECT only, read-only connection)
| Tool | Tables | What it does |
|---|---|---|
| `check_stock(sku, size, qty_requested=None)` | inventory | On-hand qty and location; with `qty_requested`, also `can_fulfill` and `shortfall`. |
| `get_lease_status(lease_id)` | leases, desk | Rent, next due, `days_until_due`, status `overdue` / `due_soon` (0–7 days) / `not_due`. |
| `get_sku_pricing(sku, qty, proposed_unit_price=None)` | pricing | Cost, list, totals, margin %; with a proposed price, also `below_cost`. |
| `get_today()` | desk | The shop's date. |
| `get_ticket(ticket_id)` | tickets | One ticket, all fields. |
| `list_tickets()` | tickets | Every ticket, any status (used by the backend's `GET /tickets`). |
| `list_open_tickets()` | tickets, desk | Every ticket not resolved/closed. |
| `list_vendors()` | vendors, invoices | All vendors with specialty, lead time and `blocked`. |
| `get_vendor_status(vendor_id)` | vendors, invoices, desk | `blocked` (open unpaid invoice), open invoices, `arrival_if_ordered_today` = today + lead_days. |
| `get_invoice(invoice_id)` | invoices, vendors, desk | Invoice details and `days_overdue`. |
| `get_cash_balance()` | cash_accounts, approval_requests | Balance, pending cash requests (payments + POs), `available_after_pending`. |
| `list_pending_approvals()` | approval_requests | Requests waiting for a human. |
| `list_approval_requests()` | approval_requests | Every request, any status (backend only). |
| `list_payments()` | payments | Every payment made, plus `total_paid` (backend only). |

### Request (records a request; no money moves)
| Tool | Tables | What it does / refuses |
|---|---|---|
| `request_payment(payment_type, ref_id, amount, ticket_id, reason, requested_by)` | approval_requests, invoices, leases, payments, cash_accounts | Invoice or rent payment request. Refuses: wrong amount, already paid, already requested, or not enough cash after pending requests. |
| `request_purchase_order(vendor_id, sku, size, qty, ticket_id, reason, requested_by)` | approval_requests, vendors, invoices, inventory, pricing, cash_accounts | Restock request, cost = unit_cost × qty. Refuses if the vendor is blocked or available cash doesn't cover it. |
| `request_price_override(ticket_id, sku, qty, unit_price, reason, requested_by)` | approval_requests, pricing | Discount request. Refuses below unit_cost, or if the price isn't below list. |
| `save_draft(ticket_id, recipient, subject, body, author_agent)` | drafts | Saves a message draft. There is no send tool. |
| `update_ticket_status(ticket_id, status)` | tickets | open / in_progress / awaiting_approval / resolved / closed. |

### Human-only (filtered out of every agent's toolset; called by the backend's approve/reject routes)
| Tool | Tables | What it does |
|---|---|---|
| `decide_approval(request_id, decision, approved_by, note=None)` | approval_requests, payments, cash_accounts, invoices, leases, vendors, pricing | Approve/reject. **Invoice/rent payments**, in one transaction: refuse if cash < amount; else insert into `payments`, lower `cash_accounts.balance`, and mark the invoice paid or move the lease's `next_due` forward one month (status `approved`). **Purchase orders**, in one transaction: refuse if cash < amount; else insert a `payments` row (kind `purchase_order`, ref_id = request id), lower the balance, status `executed`. **Price overrides** move no cash (status `approved`). Agent names are refused as `approved_by`. |

More tools may be added in later problems.

## Run

```bash
pip install -r requirements.txt
python mcp_server/server.py      # stdio; same command as .mcp.json
```
