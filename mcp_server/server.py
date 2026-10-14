"""Campus Customs MCP server.

The shared tool layer every Campus Customs agent uses. It talks only to the
working copy data/campus_customs_new.db. The original data/campus_customs.db
is the reset source and is never opened here.

Tool groups:
  - Read tools: SELECT only, over a read-only connection.
  - Request tools: record approval requests, drafts and ticket status. No money moves.
  - decide_approval: HUMAN-ONLY. The only tool that moves money. The backend
    filters it out of every agent's toolset.

To add a tool: write one function, decorate it with @mcp.tool, query through
the helpers below, and give it a docstring (agents read it to pick tools).
"""

import calendar
import sqlite3
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs_new.db"

# The shop has one cash account; every payment comes out of it.
PAY_ACCOUNT = "checking"
DUE_SOON_DAYS = 7
TICKET_STATUSES = ("open", "in_progress", "awaiting_approval", "resolved", "closed")
AGENT_NAMES = ("boss", "inventory", "accounting", "facilities", "customer_service")

# Tables the server adds on startup (the original DB doesn't have them).
SCHEMA = """
CREATE TABLE IF NOT EXISTS approval_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,          -- invoice_payment | rent_payment | purchase_order | price_override
    ticket_id INTEGER,
    ref_id INTEGER,              -- invoices.id or leases.id for payments
    vendor_id INTEGER,
    sku TEXT,
    size TEXT,
    qty INTEGER,
    unit_price REAL,
    amount REAL,
    reason TEXT,
    requested_by TEXT,
    status TEXT NOT NULL DEFAULT 'pending',   -- pending | approved | rejected
    decided_by TEXT,
    result_note TEXT
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    author_agent TEXT NOT NULL
);
"""

mcp = FastMCP("campus-customs")


# ---------------------------------------------------------------------------
# Shared DB helpers
# ---------------------------------------------------------------------------

def _connect_ro() -> sqlite3.Connection:
    """Open the working DB read-only; rows come back as dict-like Rows."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Working database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _connect_rw() -> sqlite3.Connection:
    """Open the working DB for writing (request tools and decide_approval only).

    mode=rw never creates a file, so a missing working DB fails loudly.
    isolation_level=None lets callers run explicit BEGIN IMMEDIATE transactions.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Working database not found: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=rw", uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def ensure_schema() -> None:
    """Create approval_requests and drafts if they don't exist (runs on startup)."""
    with closing(_connect_rw()):
        pass


def _fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """Run a SELECT and return the first row as a dict, or None."""
    with closing(_connect_ro()) as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def _fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT and return every row as a dict."""
    with closing(_connect_ro()) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _shop_today() -> date | None:
    """The shop's 'today' from desk.date_today (never the system clock)."""
    row = _fetch_one("SELECT date_today FROM desk LIMIT 1")
    return date.fromisoformat(row["date_today"]) if row else None


def _margin_pct(price: float, cost: float) -> float:
    """Gross margin as a percent of price, rounded to 2 decimals."""
    return round((price - cost) / price * 100, 2)


def _money_eq(a: float, b: float) -> bool:
    return round(a, 2) == round(b, 2)


def _add_one_month(d: date) -> date:
    """Same day next month, clamped to the month's last day (Jan 31 -> Feb 28)."""
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _open_invoices(conn: sqlite3.Connection, vendor_id: int) -> list[dict]:
    """Invoices for a vendor that are not paid yet (these block new shipments)."""
    rows = conn.execute(
        "SELECT id, amount, due_date, status, description FROM invoices "
        "WHERE vendor_id = ? AND status != 'paid' ORDER BY due_date",
        (vendor_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _pending_payment_total(conn: sqlite3.Connection) -> float:
    """Money already asked for but not yet decided: pending payment and purchase-order requests
    (both take cash out when a human approves them)."""
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM approval_requests "
        "WHERE status = 'pending' AND kind IN ('invoice_payment', 'rent_payment', 'purchase_order')"
    ).fetchone()
    return round(row[0], 2)


def _balance(conn: sqlite3.Connection, account: str = PAY_ACCOUNT) -> float | None:
    row = conn.execute("SELECT balance FROM cash_accounts WHERE name = ?", (account,)).fetchone()
    return None if row is None else row[0]


def _insert_request(conn: sqlite3.Connection, **fields) -> int:
    """Insert one pending approval request and return its id."""
    cols = ", ".join(fields)
    marks = ", ".join("?" for _ in fields)
    cur = conn.execute(f"INSERT INTO approval_requests ({cols}) VALUES ({marks})", tuple(fields.values()))
    return cur.lastrowid


def _get_request(conn: sqlite3.Connection, request_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,)).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool
def check_stock(sku: str, size: str, qty_requested: int | None = None) -> dict:
    """Check on-hand stock for one SKU in one size (read-only, table: inventory).

    Inputs:
        sku: product SKU, e.g. "CC-TEE-WHITE".
        size: size code, e.g. "S", "M", "L", "XL", or "OS" for one-size items.
        qty_requested: optional quantity a customer wants.

    Returns:
        {sku, name, size, qty_on_hand, location}. If qty_requested is given,
        also can_fulfill (bool) and shortfall (max(0, qty_requested - qty_on_hand)).
        If the SKU/size pair does not exist: {"error": "not found", "sku", "size"}.
    """
    sku, size = sku.strip().upper(), size.strip().upper()
    if qty_requested is not None and qty_requested < 0:
        return {"error": "invalid input", "detail": "qty_requested must be >= 0"}

    row = _fetch_one(
        "SELECT sku, name, size, qty AS qty_on_hand, location "
        "FROM inventory WHERE sku = ? AND size = ?",
        (sku, size),
    )
    if row is None:
        return {"error": "not found", "sku": sku, "size": size}

    if qty_requested is not None:
        row["qty_requested"] = qty_requested
        row["can_fulfill"] = row["qty_on_hand"] >= qty_requested
        row["shortfall"] = max(0, qty_requested - row["qty_on_hand"])
    return row


@mcp.tool
def get_lease_status(lease_id: int) -> dict:
    """Get a lease's rent and whether it is overdue (read-only, tables: leases, desk).

    "Today" is desk.date_today, not the system clock.

    Inputs:
        lease_id: leases.id, e.g. 1.

    Returns:
        {id, space_name, landlord, monthly_rent, next_due, date_today,
         days_until_due, status}, where days_until_due = next_due - date_today
        in days and status is "overdue" (< 0), "due_soon" (0-7) or "not_due" (> 7).
        If the lease does not exist: {"error": "not found", "lease_id"}.
    """
    row = _fetch_one(
        "SELECT id, space_name, landlord, monthly_rent, next_due "
        "FROM leases WHERE id = ?",
        (lease_id,),
    )
    if row is None:
        return {"error": "not found", "lease_id": lease_id}

    today = _shop_today()
    if today is None:
        return {"error": "not found", "detail": "desk.date_today is missing"}

    days = (date.fromisoformat(row["next_due"]) - today).days
    row["date_today"] = today.isoformat()
    row["days_until_due"] = days
    row["status"] = "overdue" if days < 0 else "due_soon" if days <= 7 else "not_due"
    return row


@mcp.tool
def get_sku_pricing(sku: str, qty: int, proposed_unit_price: float | None = None) -> dict:
    """Get cost, list price and margins for a quantity of one SKU (read-only, table: pricing).

    Reports numbers only. It does NOT approve or reject a discount; agents decide.

    Inputs:
        sku: product SKU, e.g. "CC-HOOD-NAVY".
        qty: number of units (> 0).
        proposed_unit_price: optional discounted price per unit to evaluate (> 0).

    Returns:
        {sku, unit_cost, list_price, qty, total_at_list, margin_pct_at_list}.
        If proposed_unit_price is given, also total_at_proposed,
        margin_pct_at_proposed and below_cost (bool).
        Margins are (price - unit_cost) / price * 100.
        If the SKU does not exist: {"error": "not found", "sku"}.
    """
    sku = sku.strip().upper()
    if qty <= 0:
        return {"error": "invalid input", "detail": "qty must be > 0"}
    if proposed_unit_price is not None and proposed_unit_price <= 0:
        return {"error": "invalid input", "detail": "proposed_unit_price must be > 0"}

    row = _fetch_one(
        "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
    )
    if row is None:
        return {"error": "not found", "sku": sku}

    cost, price = row["unit_cost"], row["list_price"]
    row["qty"] = qty
    row["total_at_list"] = round(price * qty, 2)
    row["margin_pct_at_list"] = _margin_pct(price, cost)

    if proposed_unit_price is not None:
        row["proposed_unit_price"] = proposed_unit_price
        row["total_at_proposed"] = round(proposed_unit_price * qty, 2)
        row["margin_pct_at_proposed"] = _margin_pct(proposed_unit_price, cost)
        row["below_cost"] = proposed_unit_price < cost
    return row


# ---------------------------------------------------------------------------
# Read tools (SELECT only)
# ---------------------------------------------------------------------------

@mcp.tool
def get_today() -> dict:
    """Get the shop's "today" (read-only, table: desk).

    Use this date for every due/overdue/arrival calculation. Never use the real clock.

    Returns:
        {date_today, notes}, or {"error": "not found"} if desk is empty.
    """
    row = _fetch_one("SELECT date_today, notes FROM desk LIMIT 1")
    return row if row else {"error": "not found", "detail": "desk has no row"}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Get one ticket with all its fields (read-only, table: tickets).

    Inputs:
        ticket_id: tickets.id, e.g. 101.

    Returns:
        {id, type, requester, subject, sku, size, qty, lease_id, invoice_id,
         status, notes, created_at}. If missing: {"error": "not found", "ticket_id"}.
    """
    row = _fetch_one("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    return row if row else {"error": "not found", "ticket_id": ticket_id}


@mcp.tool
def list_tickets() -> dict:
    """List every ticket on the board, whatever its status (read-only, table: tickets).

    Returns:
        {count, tickets: [{id, type, requester, subject, status, created_at}]}.
    """
    tickets = _fetch_all(
        "SELECT id, type, requester, subject, status, created_at FROM tickets ORDER BY id"
    )
    return {"count": len(tickets), "tickets": tickets}


@mcp.tool
def list_open_tickets() -> dict:
    """List every ticket that is not resolved or closed (read-only, tables: tickets, desk).

    Use it to see the whole board, e.g. to weigh cash across all tickets.

    Returns:
        {date_today, count, tickets: [ticket rows]}.
    """
    tickets = _fetch_all(
        "SELECT * FROM tickets WHERE status NOT IN ('resolved', 'closed') ORDER BY id"
    )
    today = _shop_today()
    return {"date_today": today.isoformat() if today else None, "count": len(tickets), "tickets": tickets}


@mcp.tool
def list_vendors() -> dict:
    """List every vendor with its specialty, lead time and blocked flag (read-only, tables: vendors, invoices).

    Vendors have no SKU column: match a product to a vendor by `specialty`
    (e.g. apparel -> "apparel reprint", mugs -> "mugs and small goods").

    Returns:
        {vendors: [{id, name, specialty, lead_days, open_invoice_count, blocked}]}.
        blocked = true means the vendor has an open unpaid invoice and won't ship.
    """
    with closing(_connect_ro()) as conn:
        vendors = [dict(r) for r in conn.execute("SELECT * FROM vendors ORDER BY id").fetchall()]
        for v in vendors:
            v["open_invoice_count"] = len(_open_invoices(conn, v["id"]))
            v["blocked"] = v["open_invoice_count"] > 0
    return {"vendors": vendors}


@mcp.tool
def get_vendor_status(vendor_id: int) -> dict:
    """Check whether a vendor can ship and when an order would arrive (read-only, tables: vendors, invoices, desk).

    A vendor with any open (unpaid) invoice is blocked and will not ship new product.

    Inputs:
        vendor_id: vendors.id, e.g. 1.

    Returns:
        {id, name, specialty, lead_days, date_today, blocked, open_invoices: [...],
         arrival_if_ordered_today (date_today + lead_days), can_ship_now}.
        If blocked, the open invoice must be paid (with human approval) before any order ships.
        If missing: {"error": "not found", "vendor_id"}.
    """
    today = _shop_today()
    if today is None:
        return {"error": "not found", "detail": "desk.date_today is missing"}
    with closing(_connect_ro()) as conn:
        row = conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
        if row is None:
            return {"error": "not found", "vendor_id": vendor_id}
        vendor = dict(row)
        open_invoices = _open_invoices(conn, vendor_id)
    for inv in open_invoices:
        inv["days_overdue"] = max(0, (today - date.fromisoformat(inv["due_date"])).days)
    vendor.update(
        date_today=today.isoformat(),
        blocked=bool(open_invoices),
        open_invoices=open_invoices,
        arrival_if_ordered_today=(today + timedelta(days=vendor["lead_days"])).isoformat(),
        can_ship_now=not open_invoices,
    )
    return vendor


@mcp.tool
def get_invoice(invoice_id: int) -> dict:
    """Get one invoice and how many days overdue it is (read-only, tables: invoices, vendors, desk).

    Inputs:
        invoice_id: invoices.id, e.g. 501.

    Returns:
        {id, vendor_id, vendor_name, amount, due_date, status, description,
         date_today, days_overdue (0 if not overdue or already paid), is_overdue}.
        If missing: {"error": "not found", "invoice_id"}.
    """
    row = _fetch_one(
        "SELECT i.*, v.name AS vendor_name FROM invoices i "
        "LEFT JOIN vendors v ON v.id = i.vendor_id WHERE i.id = ?",
        (invoice_id,),
    )
    if row is None:
        return {"error": "not found", "invoice_id": invoice_id}
    today = _shop_today()
    if today is None:
        return {"error": "not found", "detail": "desk.date_today is missing"}
    late = (today - date.fromisoformat(row["due_date"])).days
    unpaid = row["status"] != "paid"
    row["date_today"] = today.isoformat()
    row["days_overdue"] = max(0, late) if unpaid else 0
    row["is_overdue"] = unpaid and late > 0
    return row


@mcp.tool
def get_cash_balance() -> dict:
    """Get cash on hand and how much is already asked for (read-only, tables: cash_accounts, approval_requests).

    Cash only goes out (revenue is not modeled). Balances may never go negative.

    Returns:
        {accounts: [{name, balance, date}], total_balance,
         pending_payment_requests (sum of payment requests awaiting a human),
         available_after_pending (checking balance minus pending payment requests)}.
    """
    ensure_schema()
    with closing(_connect_ro()) as conn:
        accounts = [dict(r) for r in conn.execute("SELECT * FROM cash_accounts ORDER BY name").fetchall()]
        pending = _pending_payment_total(conn)
        checking = _balance(conn)
    if not accounts:
        return {"error": "not found", "detail": "cash_accounts is empty"}
    return {
        "accounts": accounts,
        "total_balance": round(sum(a["balance"] for a in accounts), 2),
        "pending_payment_requests": pending,
        "available_after_pending": None if checking is None else round(checking - pending, 2),
    }


@mcp.tool
def list_pending_approvals() -> dict:
    """List approval requests still waiting for a human decision (read-only, table: approval_requests).

    Returns:
        {count, pending_payment_total, requests: [approval_requests rows with status "pending"]}.
    """
    ensure_schema()
    with closing(_connect_ro()) as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM approval_requests WHERE status = 'pending' ORDER BY id"
        ).fetchall()]
        pending = _pending_payment_total(conn)
    return {"count": len(rows), "pending_payment_total": pending, "requests": rows}


@mcp.tool
def list_approval_requests() -> dict:
    """List every approval request, whatever its status (read-only, table: approval_requests).

    Returns:
        {count, requests: [approval_requests rows]}, status is pending / approved / executed / rejected.
    """
    ensure_schema()
    rows = _fetch_all("SELECT * FROM approval_requests ORDER BY id")
    return {"count": len(rows), "requests": rows}


@mcp.tool
def list_payments() -> dict:
    """List every payment made from the shop's cash (read-only, table: payments).

    Payments only exist after a human approved them with decide_approval.

    Returns:
        {count, total_paid, payments: [{id, kind, ref_id, amount, account, paid_at, approved_by}]}.
        kind is "invoice" (ref_id = invoices.id), "rent" (ref_id = leases.id) or
        "purchase_order" (ref_id = approval_requests.id).
    """
    rows = _fetch_all("SELECT * FROM payments ORDER BY id")
    return {"count": len(rows), "total_paid": round(sum(r["amount"] for r in rows), 2), "payments": rows}


# ---------------------------------------------------------------------------
# Request tools: record requests, drafts and status. No money moves here.
# ---------------------------------------------------------------------------

def _check_requester(requested_by: str) -> dict | None:
    if requested_by not in AGENT_NAMES:
        return {"error": "invalid input", "detail": f"requested_by must be one of {list(AGENT_NAMES)}"}
    return None


def _ticket_exists(conn: sqlite3.Connection, ticket_id: int) -> bool:
    return conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is not None


@mcp.tool
def request_payment(
    payment_type: Literal["invoice", "rent"],
    ref_id: int,
    amount: float,
    ticket_id: int,
    reason: str,
    requested_by: str,
) -> dict:
    """Ask a human to approve paying an invoice or rent. Does NOT move money
    (tables: approval_requests, invoices, leases, cash_accounts, payments).

    Inputs:
        payment_type: "invoice" (ref_id = invoices.id) or "rent" (ref_id = leases.id).
        ref_id: the invoice or lease id.
        amount: must equal invoices.amount or leases.monthly_rent exactly.
        ticket_id: the ticket this payment resolves.
        reason: one or two sentences a human approver can read.
        requested_by: your agent name, e.g. "accounting".

    Refuses (returns {"error": ...}) if: the invoice/lease doesn't exist, the amount
    doesn't match the DB, the invoice is already paid, this rent was already paid
    today, a pending request for the same item exists, or checking balance minus
    pending payment requests is less than the amount (no negative cash).

    Returns:
        {request_id, status: "pending", kind, ref_id, amount, available_after_this_request}.
    """
    if err := _check_requester(requested_by):
        return err
    today = _shop_today()
    if today is None:
        return {"error": "not found", "detail": "desk.date_today is missing"}
    kind = f"{payment_type}_payment"

    with closing(_connect_rw()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            if not _ticket_exists(conn, ticket_id):
                conn.execute("ROLLBACK")
                return {"error": "not found", "ticket_id": ticket_id}

            if payment_type == "invoice":
                item = conn.execute("SELECT amount, status FROM invoices WHERE id = ?", (ref_id,)).fetchone()
                if item is None:
                    conn.execute("ROLLBACK")
                    return {"error": "not found", "invoice_id": ref_id}
                if item["status"] == "paid":
                    conn.execute("ROLLBACK")
                    return {"error": "refused", "detail": f"invoice {ref_id} is already paid"}
                expected = item["amount"]
            else:
                item = conn.execute("SELECT monthly_rent FROM leases WHERE id = ?", (ref_id,)).fetchone()
                if item is None:
                    conn.execute("ROLLBACK")
                    return {"error": "not found", "lease_id": ref_id}
                paid_today = conn.execute(
                    "SELECT 1 FROM payments WHERE kind = 'rent' AND ref_id = ? AND paid_at = ?",
                    (ref_id, today.isoformat()),
                ).fetchone()
                if paid_today:
                    conn.execute("ROLLBACK")
                    return {"error": "refused", "detail": f"rent for lease {ref_id} was already paid on {today}"}
                expected = item["monthly_rent"]

            if not _money_eq(amount, expected):
                conn.execute("ROLLBACK")
                return {"error": "refused", "detail": f"amount {amount} does not match the database amount {expected}"}

            dup = conn.execute(
                "SELECT id FROM approval_requests WHERE kind = ? AND ref_id = ? AND status = 'pending'",
                (kind, ref_id),
            ).fetchone()
            if dup:
                conn.execute("ROLLBACK")
                return {"error": "refused", "detail": f"already requested: pending request {dup['id']}"}

            balance = _balance(conn)
            pending = _pending_payment_total(conn)
            if balance is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "account": PAY_ACCOUNT}
            if balance - pending < expected:
                conn.execute("ROLLBACK")
                return {
                    "error": "refused",
                    "detail": "not enough cash",
                    "balance": balance,
                    "pending_payment_requests": pending,
                    "amount": expected,
                }

            request_id = _insert_request(
                conn, kind=kind, ticket_id=ticket_id, ref_id=ref_id, amount=expected,
                reason=reason, requested_by=requested_by,
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    return {
        "request_id": request_id,
        "status": "pending",
        "kind": kind,
        "ref_id": ref_id,
        "amount": expected,
        "available_after_this_request": round(balance - pending - expected, 2),
        "note": "Awaiting human approval. No money has moved.",
    }


@mcp.tool
def request_purchase_order(
    vendor_id: int,
    sku: str,
    size: str,
    qty: int,
    ticket_id: int,
    reason: str,
    requested_by: str,
) -> dict:
    """Ask a human to approve a restock purchase order. Does NOT move money or stock now
    (tables: approval_requests, vendors, invoices, inventory, pricing).

    cost = pricing.unit_cost x qty. If a human approves it, the PO is paid from checking.

    Inputs:
        vendor_id: vendors.id that will make the product (match by specialty).
        sku, size: the inventory item to restock.
        qty: units to order (> 0).
        ticket_id: the ticket this order serves.
        reason: one or two sentences a human approver can read.
        requested_by: your agent name, e.g. "accounting".

    Refuses if: the vendor is blocked by an open unpaid invoice, the vendor or
    SKU/size doesn't exist, qty <= 0, the same order is already pending, or
    checking balance minus pending requests is less than the cost (no negative cash).

    Returns:
        {request_id, status: "pending", vendor_id, sku, size, qty, unit_cost, amount,
         arrival_if_approved_today, cash_available_after_pending, covered_by_available_cash}.
    """
    if err := _check_requester(requested_by):
        return err
    if qty <= 0:
        return {"error": "invalid input", "detail": "qty must be > 0"}
    sku, size = sku.strip().upper(), size.strip().upper()
    today = _shop_today()
    if today is None:
        return {"error": "not found", "detail": "desk.date_today is missing"}

    with closing(_connect_rw()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            if not _ticket_exists(conn, ticket_id):
                conn.execute("ROLLBACK")
                return {"error": "not found", "ticket_id": ticket_id}
            vendor = conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone()
            if vendor is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "vendor_id": vendor_id}
            blocking = _open_invoices(conn, vendor_id)
            if blocking:
                conn.execute("ROLLBACK")
                return {
                    "error": "refused",
                    "detail": f"vendor {vendor_id} is blocked by open unpaid invoice(s)",
                    "open_invoice_ids": [i["id"] for i in blocking],
                }
            if conn.execute("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone() is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "sku": sku, "size": size}
            price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
            if price is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "detail": f"no pricing row for {sku}"}
            dup = conn.execute(
                "SELECT id FROM approval_requests WHERE kind = 'purchase_order' AND status = 'pending' "
                "AND vendor_id = ? AND sku = ? AND size = ? AND ticket_id = ?",
                (vendor_id, sku, size, ticket_id),
            ).fetchone()
            if dup:
                conn.execute("ROLLBACK")
                return {"error": "refused", "detail": f"already requested: pending request {dup['id']}"}

            amount = round(price["unit_cost"] * qty, 2)
            balance = _balance(conn)
            if balance is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "account": PAY_ACCOUNT}
            available = round(balance - _pending_payment_total(conn), 2)
            if available < amount:
                conn.execute("ROLLBACK")
                return {
                    "error": "refused",
                    "detail": "not enough cash",
                    "balance": balance,
                    "cash_available_after_pending": available,
                    "amount": amount,
                }
            request_id = _insert_request(
                conn, kind="purchase_order", ticket_id=ticket_id, vendor_id=vendor_id, sku=sku,
                size=size, qty=qty, unit_price=price["unit_cost"], amount=amount,
                reason=reason, requested_by=requested_by,
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    return {
        "request_id": request_id,
        "status": "pending",
        "vendor_id": vendor_id,
        "sku": sku,
        "size": size,
        "qty": qty,
        "unit_cost": price["unit_cost"],
        "amount": amount,
        "arrival_if_approved_today": (today + timedelta(days=vendor["lead_days"])).isoformat(),
        "cash_available_after_pending": available,
        "covered_by_available_cash": available is not None and available >= amount,
        "note": "Awaiting human approval. Nothing has been ordered.",
    }


@mcp.tool
def request_price_override(
    ticket_id: int,
    sku: str,
    qty: int,
    unit_price: float,
    reason: str,
    requested_by: str,
) -> dict:
    """Ask a human to approve a discounted unit price (tables: approval_requests, pricing).

    Inputs:
        ticket_id: the ticket asking for the discount.
        sku: product SKU.
        qty: units the discount applies to (> 0).
        unit_price: proposed price per unit. Must be >= unit_cost and < list_price.
        reason: one or two sentences a human approver can read.
        requested_by: your agent name, e.g. "accounting".

    Refuses if: unit_price is below unit_cost, is not actually a discount,
    the SKU doesn't exist, or the same override is already pending.

    Returns:
        {request_id, status: "pending", sku, qty, unit_price, list_price, unit_cost,
         amount (unit_price x qty), margin_pct, discount_pct}.
    """
    if err := _check_requester(requested_by):
        return err
    if qty <= 0 or unit_price <= 0:
        return {"error": "invalid input", "detail": "qty and unit_price must be > 0"}
    sku = sku.strip().upper()

    with closing(_connect_rw()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            if not _ticket_exists(conn, ticket_id):
                conn.execute("ROLLBACK")
                return {"error": "not found", "ticket_id": ticket_id}
            price = conn.execute("SELECT unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)).fetchone()
            if price is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "sku": sku}
            if unit_price < price["unit_cost"]:
                conn.execute("ROLLBACK")
                return {"error": "refused", "detail": f"unit_price {unit_price} is below unit_cost {price['unit_cost']}"}
            if unit_price >= price["list_price"]:
                conn.execute("ROLLBACK")
                return {"error": "refused", "detail": f"unit_price {unit_price} is not below list_price {price['list_price']}"}
            dup = conn.execute(
                "SELECT id FROM approval_requests WHERE kind = 'price_override' AND status = 'pending' "
                "AND ticket_id = ? AND sku = ?",
                (ticket_id, sku),
            ).fetchone()
            if dup:
                conn.execute("ROLLBACK")
                return {"error": "refused", "detail": f"already requested: pending request {dup['id']}"}

            amount = round(unit_price * qty, 2)
            request_id = _insert_request(
                conn, kind="price_override", ticket_id=ticket_id, sku=sku, qty=qty,
                unit_price=unit_price, amount=amount, reason=reason, requested_by=requested_by,
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    return {
        "request_id": request_id,
        "status": "pending",
        "sku": sku,
        "qty": qty,
        "unit_price": unit_price,
        "list_price": price["list_price"],
        "unit_cost": price["unit_cost"],
        "amount": amount,
        "margin_pct": _margin_pct(unit_price, price["unit_cost"]),
        "discount_pct": round((1 - unit_price / price["list_price"]) * 100, 2),
        "note": "Awaiting human approval.",
    }


@mcp.tool
def save_draft(ticket_id: int, recipient: str, subject: str, body: str, author_agent: str) -> dict:
    """Save a message draft on the board (table: drafts). Nothing is sent: there is no send tool.

    Inputs:
        ticket_id: the ticket the message is about.
        recipient: who it is for (name from the ticket, e.g. the requester).
        subject, body: the message text. Only state facts that came from tools.
        author_agent: your agent name, e.g. "customer_service".

    Returns:
        {draft_id, ticket_id, recipient, status: "draft (not sent)"}.
    """
    if author_agent not in AGENT_NAMES:
        return {"error": "invalid input", "detail": f"author_agent must be one of {list(AGENT_NAMES)}"}
    if not (recipient.strip() and subject.strip() and body.strip()):
        return {"error": "invalid input", "detail": "recipient, subject and body are required"}
    with closing(_connect_rw()) as conn:
        if not _ticket_exists(conn, ticket_id):
            return {"error": "not found", "ticket_id": ticket_id}
        cur = conn.execute(
            "INSERT INTO drafts (ticket_id, recipient, subject, body, author_agent) VALUES (?, ?, ?, ?, ?)",
            (ticket_id, recipient.strip(), subject.strip(), body, author_agent),
        )
    return {"draft_id": cur.lastrowid, "ticket_id": ticket_id, "recipient": recipient.strip(),
            "status": "draft (not sent)"}


@mcp.tool
def update_ticket_status(ticket_id: int, status: str) -> dict:
    """Set a ticket's status (table: tickets).

    Inputs:
        ticket_id: tickets.id.
        status: one of "open", "in_progress", "awaiting_approval", "resolved", "closed".

    Returns:
        {ticket_id, old_status, new_status}.
    """
    if status not in TICKET_STATUSES:
        return {"error": "invalid input", "detail": f"status must be one of {list(TICKET_STATUSES)}"}
    with closing(_connect_rw()) as conn:
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"error": "not found", "ticket_id": ticket_id}
        conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
    return {"ticket_id": ticket_id, "old_status": row["status"], "new_status": status}


# ---------------------------------------------------------------------------
# HUMAN-ONLY: the only tool that moves money. Never given to an agent.
# ---------------------------------------------------------------------------

@mcp.tool
def decide_approval(
    request_id: int,
    decision: Literal["approve", "reject"],
    approved_by: str,
    note: str | None = None,
) -> dict:
    """HUMAN-ONLY. Approve or reject a pending approval request
    (tables: approval_requests, payments, cash_accounts, invoices, leases, vendors, pricing).

    Approving a payment runs in ONE transaction: refuse if cash < amount; otherwise
    insert into payments (paid_at = desk.date_today), lower cash_accounts.balance,
    and mark the invoice paid or move the lease's next_due forward one month.
    Approving a purchase order also pays it in ONE transaction: refuse if cash < amount;
    otherwise insert a payments row (kind 'purchase_order', ref_id = the request id),
    lower cash_accounts.balance, and set the request status to 'executed'.
    Approving a price override moves no cash; it only records the decision.

    Inputs:
        request_id: approval_requests.id (must be pending).
        decision: "approve" or "reject".
        approved_by: the human's name. Agent names are refused.
        note: optional comment.

    Returns:
        {request_id, kind, status, result_note, ...} or {"error": ...}. On refusal nothing changes.
    """
    who = approved_by.strip()
    if not who or who.lower() in AGENT_NAMES:
        return {"error": "refused", "detail": "approved_by must be a human's name"}
    today = _shop_today()
    if today is None:
        return {"error": "not found", "detail": "desk.date_today is missing"}

    def refuse(detail: str) -> dict:
        conn.execute("ROLLBACK")
        return {"error": "refused", "request_id": request_id, "detail": detail}

    with closing(_connect_rw()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            req = _get_request(conn, request_id)
            if req is None:
                conn.execute("ROLLBACK")
                return {"error": "not found", "request_id": request_id}
            if req["status"] != "pending":
                return refuse(f"request is already {req['status']}")

            kind = req["kind"]
            extra: dict = {}
            if decision == "reject":
                status, result = "rejected", f"Rejected by {who}."

            elif kind in ("invoice_payment", "rent_payment"):
                amount = req["amount"]
                if kind == "invoice_payment":
                    inv = conn.execute("SELECT amount, status FROM invoices WHERE id = ?", (req["ref_id"],)).fetchone()
                    if inv is None:
                        return refuse(f"invoice {req['ref_id']} not found")
                    if inv["status"] == "paid":
                        return refuse(f"invoice {req['ref_id']} is already paid")
                    if not _money_eq(inv["amount"], amount):
                        return refuse("request amount no longer matches the invoice")
                else:
                    lease = conn.execute("SELECT monthly_rent, next_due FROM leases WHERE id = ?", (req["ref_id"],)).fetchone()
                    if lease is None:
                        return refuse(f"lease {req['ref_id']} not found")
                    if not _money_eq(lease["monthly_rent"], amount):
                        return refuse("request amount no longer matches the lease rent")

                balance = _balance(conn)
                if balance is None:
                    return refuse(f"cash account {PAY_ACCOUNT} not found")
                if balance < amount:
                    return refuse(f"not enough cash: balance {balance} < amount {amount}")

                cur = conn.execute(
                    "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    ("invoice" if kind == "invoice_payment" else "rent", req["ref_id"], amount,
                     PAY_ACCOUNT, today.isoformat(), who),
                )
                new_balance = round(balance - amount, 2)
                conn.execute(
                    "UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                    (new_balance, today.isoformat(), PAY_ACCOUNT),
                )
                if kind == "invoice_payment":
                    conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (req["ref_id"],))
                    result = f"Paid invoice {req['ref_id']} (${amount:,.2f}) on {today}. Balance now ${new_balance:,.2f}."
                else:
                    new_due = _add_one_month(date.fromisoformat(lease["next_due"])).isoformat()
                    conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (new_due, req["ref_id"]))
                    result = (f"Paid rent for lease {req['ref_id']} (${amount:,.2f}) on {today}; "
                              f"next_due {lease['next_due']} -> {new_due}. Balance now ${new_balance:,.2f}.")
                    extra["new_next_due"] = new_due
                extra.update(payment_id=cur.lastrowid, new_balance=new_balance)
                status = "approved"

            elif kind == "purchase_order":
                # Approving a PO pays the vendor for it, in this same transaction.
                if _open_invoices(conn, req["vendor_id"]):
                    return refuse(f"vendor {req['vendor_id']} is still blocked by an open unpaid invoice")
                vendor = conn.execute("SELECT lead_days FROM vendors WHERE id = ?", (req["vendor_id"],)).fetchone()
                if vendor is None:
                    return refuse(f"vendor {req['vendor_id']} not found")
                amount = req["amount"]
                balance = _balance(conn)
                if balance is None:
                    return refuse(f"cash account {PAY_ACCOUNT} not found")
                if balance < amount:
                    return refuse(f"not enough cash: balance {balance} < amount {amount}")
                cur = conn.execute(
                    "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
                    "VALUES ('purchase_order', ?, ?, ?, ?, ?)",
                    (request_id, amount, PAY_ACCOUNT, today.isoformat(), who),
                )
                new_balance = round(balance - amount, 2)
                conn.execute(
                    "UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                    (new_balance, today.isoformat(), PAY_ACCOUNT),
                )
                arrival = (today + timedelta(days=vendor["lead_days"])).isoformat()
                status = "executed"
                result = (f"PO executed by {who}: {req['qty']} x {req['sku']} {req['size']} from vendor "
                          f"{req['vendor_id']}, paid ${amount:,.2f} on {today}, expected arrival {arrival}. "
                          f"Balance now ${new_balance:,.2f}.")
                extra.update(expected_arrival=arrival, payment_id=cur.lastrowid, new_balance=new_balance)

            elif kind == "price_override":
                price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (req["sku"],)).fetchone()
                if price is None:
                    return refuse(f"no pricing row for {req['sku']}")
                if req["unit_price"] < price["unit_cost"]:
                    return refuse("unit_price is below unit_cost")
                status = "approved"
                result = f"Price override approved by {who}: {req['qty']} x {req['sku']} at ${req['unit_price']:,.2f}."

            else:
                return refuse(f"unknown request kind {kind!r}")

            if note:
                result = f"{result} Note: {note}"
            conn.execute(
                "UPDATE approval_requests SET status = ?, decided_by = ?, result_note = ? WHERE id = ?",
                (status, who, result, request_id),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    return {"request_id": request_id, "kind": kind, "status": status, "decided_by": who,
            "result_note": result, **extra}


if __name__ == "__main__":
    ensure_schema()
    mcp.run()
