import { useEffect, useRef, type ReactNode } from "react";
import { AGENTS } from "../agents";
import type { ChatLine } from "../feed";

/** The live trader chat: who said what, tool calls as chips, phone calls between desks. */
export function Feed({ lines, controls }: { lines: ChatLine[]; controls?: ReactNode }) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    box.current?.scrollTo({ top: box.current.scrollHeight });
  }, [lines.length]);

  return (
    <section className="panel feed-panel">
      <h2 className="panel-title">
        Squawk Box <span className="feed-controls">{controls}</span>
      </h2>
      <div className="feed" ref={box} aria-live="polite">
        {lines.length === 0 && <p className="quiet">The floor is quiet. Send a ticket to the floor to hear the desks talk.</p>}
        {lines.map((l) => {
          const color = l.agent ? AGENTS[l.agent].color : "var(--brass)";
          return (
            <div key={l.key} className={`msg ${l.kind}`} style={{ ["--agent" as string]: color }}>
              <div className="msg-head">
                <span className="msg-who">{l.agent ? AGENTS[l.agent].title : "FLOOR"}</span>
                {l.ticketId != null && <span className="msg-tkt">#{l.ticketId}</span>}
                <span className="msg-time">{l.time ? l.time.slice(11, 19) : ""}</span>
              </div>
              {l.text && (
                <div className="msg-text">
                  {l.kind === "phone" && <span className="msg-ico">☎ </span>}
                  {l.text}
                </div>
              )}
              {l.chips.length > 0 && (
                <div className="chips">
                  {l.chips.map((c, i) => (
                    <span className="chip" key={i} title={c.args}>
                      <b>{c.tool}</b>
                      {c.args && <span>{c.args}</span>}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
