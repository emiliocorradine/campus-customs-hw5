import { useState } from "react";
import { agentTitle } from "../agents";
import { KIND_LABEL, money } from "../feed";
import type { ApprovalRequest } from "../types";

interface Props {
  requests: ApprovalRequest[];
  onDecide: (id: number, decision: "approve" | "reject", name: string) => Promise<void>;
}

/** Pending approvals as trade slips. Nothing happens until a human signs and presses a button. */
export function TradeSlips({ requests, onDecide }: Props) {
  return (
    <section className="panel">
      <h2 className="panel-title">
        Slips to Sign <span className="count">{requests.length}</span>
      </h2>
      {requests.length === 0 && <p className="quiet">No slips waiting. Agents can only request; you sign.</p>}
      <div className="slips">
        {requests.map((r) => <Slip key={r.id} req={r} onDecide={onDecide} />)}
      </div>
    </section>
  );
}

function Slip({ req, onDecide }: { req: ApprovalRequest; onDecide: Props["onDecide"] }) {
  const [name, setName] = useState("");
  const [pending, setPending] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const signed = name.trim().length > 0;

  async function decide(decision: "approve" | "reject") {
    setPending(decision);
    setError(null);
    try {
      await onDecide(req.id, decision, name.trim());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending(null);
    }
  }

  const rows: [string, string][] = [];
  if (req.ticket_id != null) rows.push(["TICKET", `#${req.ticket_id}`]);
  if (req.kind === "invoice_payment") rows.push(["INVOICE", `#${req.ref_id}`]);
  if (req.kind === "rent_payment") rows.push(["LEASE", `#${req.ref_id}`]);
  if (req.vendor_id != null) rows.push(["VENDOR", `#${req.vendor_id}`]);
  if (req.sku) rows.push(["ITEM", `${req.sku}${req.size ? ` / ${req.size}` : ""} × ${req.qty ?? "?"}`]);
  if (req.unit_price != null) rows.push(["UNIT", money(req.unit_price)]);
  rows.push(["DESK", agentTitle(req.requested_by)]);

  const movesCash = req.kind === "invoice_payment" || req.kind === "rent_payment" || req.kind === "purchase_order";

  return (
    <article className="slip">
      <header className="slip-head">
        <span>TRADE SLIP · REQ {String(req.id).padStart(4, "0")}</span>
        <span className="slip-kind">{KIND_LABEL[req.kind] ?? req.kind}</span>
      </header>
      <div className="slip-amount">{money(req.amount)}</div>
      {movesCash && <div className="slip-warn">Approving pays this out of checking.</div>}
      <dl className="slip-rows">
        {rows.map(([k, v]) => (
          <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
        ))}
      </dl>
      {req.reason && <p className="slip-reason">“{req.reason}”</p>}
      <label className="sign">
        <span>Sign here (your name)</span>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="x ____________" maxLength={60} />
      </label>
      <div className="slip-actions">
        <button className="btn-approve" disabled={!signed || pending !== null} onClick={() => decide("approve")}>
          {pending === "approve" ? "Filing…" : "Approve"}
        </button>
        <button className="btn-reject" disabled={!signed || pending !== null} onClick={() => decide("reject")}>
          {pending === "reject" ? "Filing…" : "Reject"}
        </button>
      </div>
      {error && <p className="slip-error">{error}</p>}
    </article>
  );
}
