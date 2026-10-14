import { stampFor } from "../feed";
import type { RunRecord, Ticket } from "../types";

interface Props {
  tickets: Ticket[];
  selected: number | null;
  onSelect: (id: number) => void;
  onRun: (id: number) => void;
  busy: boolean;                       // some ticket is on the desk
  results: Record<number, RunRecord>;
}

/** Each ticket is a paper deal ticket with a rubber status stamp. */
export function DealTickets({ tickets, selected, onSelect, onRun, busy, results }: Props) {
  return (
    <section className="panel">
      <h2 className="panel-title">Deal Tickets</h2>
      <div className="deals">
        {tickets.map((t) => {
          const stamp = stampFor(t.ticket_status, t.running);
          const last = results[t.id];
          const isSel = selected === t.id;
          return (
            <article
              key={t.id}
              className={`deal ${isSel ? "selected" : ""}`}
              onClick={() => onSelect(t.id)}
              tabIndex={0}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelect(t.id)}
              aria-pressed={isSel}
            >
              <div className="deal-head">
                <div>
                  <span className="deal-no">No. {t.id}</span>
                  <span className="deal-type">{t.type.replace(/_/g, " ")}</span>
                </div>
                <span className={`stamp ${stamp.tone}`}>{stamp.label}</span>
              </div>
              <div className="deal-row"><span>CLIENT</span><b>{t.requester}</b></div>
              <div className="deal-row"><span>ASK</span><b>{t.subject}</b></div>
              {last?.decision && (
                <div className="deal-row"><span>LAST CALL</span><b>{last.decision.decision.replace(/_/g, " ")}</b></div>
              )}
              {last?.state === "failed" && <div className="deal-row bad"><span>LAST RUN</span><b>failed</b></div>}
              {isSel && (
                <button
                  className="btn-run"
                  disabled={busy || t.running}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRun(t.id);
                  }}
                >
                  {t.running ? "On the desk…" : busy ? "Desk busy" : "▶ Send to the floor"}
                </button>
              )}
            </article>
          );
        })}
        {tickets.length === 0 && <p className="quiet">No tickets on the board.</p>}
      </div>
    </section>
  );
}
