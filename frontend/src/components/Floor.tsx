import { AGENTS, ANALYSTS } from "../agents";
import { clip, type Call } from "../feed";
import type { AgentName } from "../types";
import { Avatar } from "./Avatars";

interface Props {
  active: AgentName | null;           // who is talking right now
  calls: Call[];                      // open phone lines (delegations in progress)
  worked: Set<AgentName>;             // who has touched the current ticket
  lastWords: Partial<Record<AgentName, string>>;
  toolCounts: Partial<Record<AgentName, number>>;
  ticketLabel: string | null;
}

/** The trading floor: the Chairman's corner office on top, four analyst desks below. */
export function Floor({ active, calls, worked, lastWords, toolCounts, ticketLabel }: Props) {
  const onCallWith = (a: AgentName): { dir: "out" | "in"; other: AgentName } | null => {
    for (let i = calls.length - 1; i >= 0; i--) {
      if (calls[i].from === a) return { dir: "out", other: calls[i].to };
      if (calls[i].to === a) return { dir: "in", other: calls[i].from };
    }
    return null;
  };

  const status = (a: AgentName) => (active === a ? "live" : worked.has(a) ? "worked" : "idle");
  const boss = onCallWith("boss");

  return (
    <section className="floor" aria-label="The trading floor">
      <div className={`office ${status("boss")}`} style={{ ["--agent" as string]: AGENTS.boss.color }}>
        <div className="office-window" aria-hidden="true">
          {Array.from({ length: 14 }).map((_, i) => <span key={i} style={{ height: `${30 + ((i * 37) % 60)}%` }} />)}
        </div>
        <div className="office-avatar"><Avatar agent="boss" /></div>
        <div className="office-body">
          <div className="nameplate">THE CHAIRMAN</div>
          <div className="desk-role">{AGENTS.boss.role}</div>
          <p className="desk-words">
            {lastWords.boss ? clip(lastWords.boss, 180) : ticketLabel ? `Watching ${ticketLabel}.` : "Waiting for a ticket to cross the desk."}
          </p>
          <div className="desk-meta">
            {active === "boss" && <span className="live-dot">ON AIR</span>}
            {boss && <PhoneBadge dir={boss.dir} other={boss.other} />}
            {toolCounts.boss ? <span className="meta">{toolCounts.boss} tool calls</span> : null}
          </div>
        </div>
      </div>

      <PhoneLine calls={calls} />

      <div className="desks">
        {ANALYSTS.map((a) => {
          const call = onCallWith(a);
          return (
            <div key={a} className={`desk ${status(a)}`} style={{ ["--agent" as string]: AGENTS[a].color }}>
              <div className="desk-lamp" aria-hidden="true" />
              <div className="desk-avatar"><Avatar agent={a} /></div>
              <div className="desk-body">
                <div className="nameplate small">{AGENTS[a].title.toUpperCase()}</div>
                <div className="desk-role">{AGENTS[a].role}</div>
                <p className="desk-words">{lastWords[a] ? clip(lastWords[a], 120) : status(a) === "idle" ? "Phones quiet." : "…"}</p>
                <div className="desk-meta">
                  {active === a && <span className="live-dot">ON AIR</span>}
                  {call && <PhoneBadge dir={call.dir} other={call.other} />}
                  {toolCounts[a] ? <span className="meta">{toolCounts[a]} tool calls</span> : null}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function PhoneBadge({ dir, other }: { dir: "out" | "in"; other: AgentName }) {
  return (
    <span className={`phone-badge ${dir}`}>
      <PhoneIcon /> {dir === "out" ? `calling ${AGENTS[other].title} →` : `← on the line with ${AGENTS[other].title}`}
    </span>
  );
}

/** The chain of open delegations, e.g. The Chairman ──☎──▶ Stock Desk ──☎──▶ Treasury. */
function PhoneLine({ calls }: { calls: Call[] }) {
  if (calls.length === 0) {
    return <div className="phone-line idle"><PhoneIcon /> No lines open</div>;
  }
  const chain: AgentName[] = [calls[0].from, ...calls.map((c) => c.to)];
  return (
    <div className="phone-line live" aria-live="polite">
      {chain.map((a, i) => (
        <span key={`${a}-${i}`} className="hop">
          {i > 0 && <span className="wire" aria-hidden="true"><PhoneIcon /></span>}
          <span className="hop-name" style={{ color: AGENTS[a].color }}>{AGENTS[a].title}</span>
        </span>
      ))}
    </div>
  );
}

function PhoneIcon() {
  return (
    <svg className="phone-icon" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">
      <path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z" />
    </svg>
  );
}
