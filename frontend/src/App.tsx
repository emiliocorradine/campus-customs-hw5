import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { isAgent } from "./agents";
import { lastWords, openCalls, toChat, toolsByAgent } from "./feed";
import { IDLE_POLL_MS, POLL_MS } from "./config";
import type { AgentName, ApprovalsResponse, Cash, FeedEvent, RunRecord, Ticket } from "./types";
import { Ticker } from "./components/Ticker";
import { CashBoard } from "./components/CashBoard";
import { DealTickets } from "./components/DealTickets";
import { TradeSlips } from "./components/TradeSlips";
import { Floor } from "./components/Floor";
import { Feed } from "./components/Feed";
import { ClosingReport } from "./components/ClosingReport";

const MAX_EVENTS = 1500;

/** Merge new audit events in, keeping each seq once and in order. */
function mergeEvents(prev: FeedEvent[], next: FeedEvent[]): FeedEvent[] {
  if (next.length === 0) return prev;
  const bySeq = new Map(prev.map((e) => [e.seq, e]));
  for (const e of next) bySeq.set(e.seq, e);
  return [...bySeq.values()].sort((a, b) => a.seq - b.seq).slice(-MAX_EVENTS);
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [cash, setCash] = useState<Cash | null>(null);
  const [approvals, setApprovals] = useState<ApprovalsResponse | null>(null);
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [active, setActive] = useState<{ ticketId: number; runId: string } | null>(null);
  const [results, setResults] = useState<Record<number, RunRecord>>({});
  const [online, setOnline] = useState<boolean | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const [feedScope, setFeedScope] = useState<"ticket" | "all">("ticket");
  const since = useRef(0);
  const polling = useRef(false);

  const refreshBoard = useCallback(async () => {
    const [t, c, a] = await Promise.all([api.tickets(), api.cash(), api.approvals()]);
    setTickets(t.tickets);
    setCash(c);
    setApprovals(a);
    return t.tickets;
  }, []);

  const pullEvents = useCallback(async () => {
    const r = await api.events(since.current);
    since.current = Math.max(since.current, r.next_since);
    setEvents((prev) => mergeEvents(prev, r.events));
    return r;
  }, []);

  const loadRun = useCallback(async (runId: string) => {
    const rec = await api.run(runId);
    setResults((prev) => ({ ...prev, [rec.ticket_id]: rec }));
    return rec;
  }, []);

  // First load: board, recent feed, any run already on the desk, and the last result per ticket.
  useEffect(() => {
    (async () => {
      try {
        const ts = await refreshBoard();
        const r = await pullEvents();
        setOnline(true);
        // ?ticket=102 opens the board with that ticket selected (used for screenshots and links).
        const wanted = Number(new URLSearchParams(window.location.search).get("ticket"));
        setSelected((s) => s ?? (ts.some((t) => t.id === wanted) ? wanted : ts[0]?.id ?? null));
        const running = r.runs_in_progress[0];
        if (running) setActive({ ticketId: running.ticket_id, runId: running.run_id });
        ts.filter((t) => t.last_run_id).forEach((t) => loadRun(t.last_run_id!).catch(() => undefined));
      } catch (e) {
        setOnline(false);
        setNotice(`Can't reach the backend: ${(e as Error).message}`);
      }
    })();
  }, [refreshBoard, pullEvents, loadRun]);

  // While a ticket is on the desk: poll /events every POLL_MS, plus tickets and slips.
  useEffect(() => {
    if (!active) return;
    let stopped = false;
    const tick = async () => {
      if (polling.current) return;
      polling.current = true;
      try {
        const r = await pullEvents();
        const [t, a] = await Promise.all([api.tickets(), api.approvals()]);
        if (stopped) return;
        setTickets(t.tickets);
        setApprovals(a);
        setOnline(true);
        if (!r.runs_in_progress.some((x) => x.run_id === active.runId)) {
          await loadRun(active.runId);
          setCash(await api.cash());
          setActive(null);
          setNotice(`Ticket #${active.ticketId} is off the desk. See the closing report.`);
        }
      } catch {
        setOnline(false);
      } finally {
        polling.current = false;
      }
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      stopped = true;
      clearInterval(id);
    };
  }, [active, pullEvents, loadRun]);

  // While idle: keep slips, cash, tickets and the feed fresh, and pick up runs started elsewhere
  // (another tab, or a script calling POST /tickets/{id}/run).
  useEffect(() => {
    if (active) return;
    let stopped = false;
    const tick = async () => {
      if (polling.current) return;
      polling.current = true;
      try {
        const r = await pullEvents();
        await refreshBoard();
        if (stopped) return;
        setOnline(true);
        const running = r.runs_in_progress[0];
        if (running) {
          setSelected(running.ticket_id);
          setActive({ ticketId: running.ticket_id, runId: running.run_id });
        }
      } catch {
        setOnline(false);
      } finally {
        polling.current = false;
      }
    };
    const id = setInterval(tick, IDLE_POLL_MS);
    return () => {
      stopped = true;
      clearInterval(id);
    };
  }, [active, pullEvents, refreshBoard]);

  async function runTicket(id: number) {
    setNotice(null);
    try {
      const r = await api.runTicket(id);
      setSelected(id);
      setActive({ ticketId: id, runId: r.run_id });
      setTickets((ts) => ts.map((t) => (t.id === id ? { ...t, running: true } : t)));
      setResults((prev) => ({
        ...prev,
        [id]: { run_id: r.run_id, ticket_id: id, state: "running", started_at: "", finished_at: null, decision: null, error: null, reports: [] },
      }));
    } catch (e) {
      setNotice((e as Error).message);
    }
  }

  async function decide(id: number, decision: "approve" | "reject", name: string) {
    const res = decision === "approve" ? await api.approve(id, name) : await api.reject(id, name);
    setNotice(res.result_note);
    await refreshBoard(); // cash refreshes here, so an approved payment visibly drops the LED
  }

  async function resetFloor() {
    setConfirmReset(false);
    try {
      const r = await api.reset();
      setResults({});
      await refreshBoard();
      setNotice(`Floor reset: ${r.detail}`);
    } catch (e) {
      setNotice((e as Error).message);
    }
  }

  // ----- Derived view of the run in focus (the live one, else the selected ticket's last run) -----
  const focusRunId = active?.runId ?? (selected != null ? results[selected]?.run_id : undefined);
  const runEvents = useMemo(() => events.filter((e) => e.run_id && e.run_id === focusRunId), [events, focusRunId]);
  const liveAgent: AgentName | null = useMemo(() => {
    if (!active) return null;
    for (let i = runEvents.length - 1; i >= 0; i--) if (isAgent(runEvents[i].agent)) return runEvents[i].agent as AgentName;
    return "boss";
  }, [active, runEvents]);
  const calls = useMemo(() => (active ? openCalls(runEvents) : []), [active, runEvents]);
  const worked = useMemo(() => new Set(runEvents.map((e) => e.agent).filter(isAgent)), [runEvents]);
  const words = useMemo(() => lastWords(runEvents), [runEvents]);
  const tools = useMemo(() => toolsByAgent(runEvents), [runEvents]);
  const toolCounts = useMemo(() => {
    const out: Partial<Record<AgentName, number>> = {};
    for (const e of runEvents) if (e.step === "tool_call" && isAgent(e.agent)) out[e.agent] = (out[e.agent] ?? 0) + 1;
    return out;
  }, [runEvents]);

  const feedEvents = feedScope === "all" || selected == null ? events : events.filter((e) => e.ticket_id === selected);
  const chat = useMemo(() => toChat(feedEvents).slice(-300), [feedEvents]);
  const selectedTicket = tickets.find((t) => t.id === selected) ?? null;
  const focusTicketId = active?.ticketId ?? selected;

  return (
    <div className="app">
      <Ticker cash={cash} tickets={tickets} approvals={approvals} />

      <header className="masthead">
        <div className="brand">
          <h1>The Floor</h1>
          <p>Campus Customs · agent trading desk{cash ? ` · shop date ${cash.as_of}` : ""}</p>
          <span className={`wire-status ${online === false ? "down" : "up"}`}>
            {online === false ? "● BACKEND OFFLINE" : active ? `● LIVE · TICKET #${active.ticketId}` : "● WIRE CONNECTED"}
          </span>
        </div>
        <CashBoard cash={cash} />
        <div className="reset-box">
          {!confirmReset ? (
            <button className="btn-reset" disabled={!!active} onClick={() => setConfirmReset(true)} title={active ? "Wait for the run to finish" : ""}>
              Reset floor
            </button>
          ) : (
            <div className="confirm">
              <span>Copy the original DB over the working copy? Pending slips and payments are wiped.</span>
              <div>
                <button className="btn-reject" onClick={resetFloor}>Yes, reset</button>
                <button className="btn-ghost" onClick={() => setConfirmReset(false)}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      </header>

      {notice && (
        <div className="notice" role="status">
          {notice}
          <button className="btn-ghost" onClick={() => setNotice(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      <main className="grid">
        <div className="col-left">
          <DealTickets
            tickets={tickets}
            selected={selected}
            onSelect={setSelected}
            onRun={runTicket}
            busy={!!active}
            results={results}
          />
          <TradeSlips requests={approvals?.requests ?? []} onDecide={decide} />
        </div>

        <div className="col-center">
          <Floor
            active={liveAgent}
            calls={calls}
            worked={worked}
            lastWords={words}
            toolCounts={toolCounts}
            ticketLabel={focusTicketId != null ? `ticket #${focusTicketId}` : null}
          />
          <ClosingReport record={selected != null && !active ? results[selected] ?? null : active ? results[active.ticketId] ?? null : null} tools={tools} />
        </div>

        <div className="col-right">
          <Feed
            lines={chat}
            controls={
              <>
                <button className={`seg ${feedScope === "ticket" ? "on" : ""}`} onClick={() => setFeedScope("ticket")}>
                  {selectedTicket ? `#${selectedTicket.id}` : "Ticket"}
                </button>
                <button className={`seg ${feedScope === "all" ? "on" : ""}`} onClick={() => setFeedScope("all")}>All</button>
              </>
            }
          />
        </div>
      </main>
    </div>
  );
}
