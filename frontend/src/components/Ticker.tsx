import { money } from "../feed";
import type { ApprovalsResponse, Cash, Ticket } from "../types";

interface Props {
  cash: Cash | null;
  tickets: Ticket[];
  approvals: ApprovalsResponse | null;
}

/** The scrolling tape across the top: cash, open tickets, pending approvals. */
export function Ticker({ cash, tickets, approvals }: Props) {
  const open = tickets.filter((t) => t.status === "open").length;
  const items: { label: string; value: string; tone: "green" | "amber" | "red" }[] = [
    { label: "CASH CHK", value: money(cash?.balance), tone: "green" },
    { label: "AVAIL AFTER PENDING", value: money(cash?.available_after_pending), tone: "green" },
    { label: "OPEN TICKETS", value: String(open), tone: open ? "amber" : "green" },
    { label: "PENDING APPROVALS", value: String(approvals?.count ?? 0), tone: approvals?.count ? "red" : "green" },
    { label: "PENDING $", value: money(approvals?.pending_payment_total ?? 0), tone: approvals?.pending_payment_total ? "amber" : "green" },
    { label: "SHOP DATE", value: cash?.as_of ?? "—", tone: "amber" },
    ...tickets.map((t) => ({
      label: `TKT ${t.id}`,
      value: `${t.requester.toUpperCase()} · ${t.ticket_status.replace(/_/g, " ").toUpperCase()}`,
      tone: (t.status === "resolved" ? "green" : "amber") as "green" | "amber",
    })),
  ];

  const run = items.map((it, i) => (
    <span className="tick" key={i}>
      <span className="tick-label">{it.label}</span>
      <span className={`tick-value ${it.tone}`}>{it.value}</span>
      <span className="tick-sep">◆</span>
    </span>
  ));

  return (
    <div className="ticker" role="marquee" aria-label="Floor ticker">
      <div className="ticker-track">
        <div className="ticker-run">{run}</div>
        <div className="ticker-run" aria-hidden="true">{run}</div>
      </div>
    </div>
  );
}
