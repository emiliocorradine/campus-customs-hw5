import { AGENTS } from "../agents";
import type { AgentName, AgentReportOutput, BossDecision, RunRecord } from "../types";

interface Props {
  record: RunRecord | null;
  tools: Partial<Record<AgentName, string[]>>;
}

/** After a run: the Chairman's decision, then one short line per agent on what it did. */
export function ClosingReport({ record, tools }: Props) {
  if (!record) return null;
  if (record.state === "running") {
    return (
      <section className="panel report">
        <h2 className="panel-title">Closing Report · Ticket #{record.ticket_id}</h2>
        <p className="quiet">The desks are still working this ticket…</p>
      </section>
    );
  }

  const decision = record.decision;
  const analysts = record.reports.filter((r) => r.agent !== "boss");

  return (
    <section className="panel report">
      <h2 className="panel-title">Closing Report · Ticket #{record.ticket_id}</h2>
      {record.state === "failed" && <p className="slip-error">Run failed: {record.error}</p>}
      {decision && <ChairmanCall d={decision} tools={tools.boss} />}
      <div className="report-rows">
        {analysts.map((r, i) => {
          const out = typeof r.output === "string" ? ({ summary: r.output } as AgentReportOutput) : (r.output as AgentReportOutput);
          return (
            <div className="report-row" key={i} style={{ ["--agent" as string]: AGENTS[r.agent].color }}>
              <div className="report-who">
                {AGENTS[r.agent].title}
                {r.called_by && <small> · called by {AGENTS[r.called_by]?.title ?? r.called_by}</small>}
              </div>
              <p>{out.summary}</p>
              <div className="report-tags">
                {(tools[r.agent] ?? []).map((t) => <span className="chip mini" key={t}><b>{t}</b></span>)}
                {(out.approval_request_ids ?? []).map((id) => <span className="tag" key={`r${id}`}>slip #{id}</span>)}
                {(out.draft_ids ?? []).map((id) => <span className="tag" key={`d${id}`}>draft #{id}</span>)}
                {(out.blockers ?? []).map((b, j) => <span className="tag warn" key={`b${j}`}>{b}</span>)}
              </div>
            </div>
          );
        })}
        {analysts.length === 0 && decision && <p className="quiet">The Chairman handled this one without calling a desk.</p>}
      </div>
    </section>
  );
}

function ChairmanCall({ d, tools }: { d: BossDecision; tools?: string[] }) {
  return (
    <div className="chair-call" style={{ ["--agent" as string]: AGENTS.boss.color }}>
      <div className="report-who">
        The Chairman · <span className="verdict">{d.decision.replace(/_/g, " ").toUpperCase()}</span>
      </div>
      <p>{d.summary}</p>
      <p className="rationale">{d.rationale}</p>
      {d.next_steps_for_human.length > 0 && (
        <ul className="next-steps">
          {d.next_steps_for_human.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      )}
      <div className="report-tags">
        {(tools ?? []).map((t) => <span className="chip mini" key={t}><b>{t}</b></span>)}
        {d.approval_request_ids.map((id) => <span className="tag" key={`r${id}`}>slip #{id}</span>)}
        {d.draft_ids.map((id) => <span className="tag" key={`d${id}`}>draft #{id}</span>)}
      </div>
    </div>
  );
}
