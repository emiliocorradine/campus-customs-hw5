import { agentTitle, isAgent } from "./agents";
import type { AgentName, FeedEvent } from "./types";

export const money = (n: number | null | undefined) =>
  n == null ? "—" : n.toLocaleString("en-US", { style: "currency", currency: "USD" });

/** Audit args/results are short JSON strings and may be cut off; parse if we can. */
export function tryJson(text: string | null): Record<string, unknown> | null {
  if (!text) return null;
  try {
    const v = JSON.parse(text);
    return v && typeof v === "object" ? (v as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Pull one string field out of possibly-truncated JSON text. */
export function field(text: string | null, key: string): string | null {
  const parsed = tryJson(text);
  if (parsed && typeof parsed[key] === "string") return parsed[key] as string;
  const m = text?.match(new RegExp(`"${key}"\\s*:\\s*"((?:[^"\\\\]|\\\\.)*)`));
  return m ? m[1].replace(/\\"/g, '"') : null;
}

export function clip(text: string | null | undefined, n = 140): string {
  if (!text) return "";
  return text.length > n ? text.slice(0, n - 1) + "…" : text;
}

/** Short "arg=value" text for a tool chip, e.g. "sku=CC-TEE-WHITE · size=S". */
export function chipArgs(args: string | null): string {
  const parsed = tryJson(args);
  if (!parsed) return clip(args, 60);
  return Object.entries(parsed)
    .filter(([k]) => !["reason", "requested_by", "author_agent", "body"].includes(k))
    .map(([k, v]) => `${k}=${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join(" · ");
}

export type ChatKind = "system" | "says" | "calls" | "phone" | "report" | "decision" | "alert" | "result";

export interface Chip {
  tool: string;
  args: string;
}

export interface ChatLine {
  key: string;
  seq: number;
  time: string | null;
  ticketId: number | null;
  runId: string | null;
  agent: AgentName | null;
  kind: ChatKind;
  text: string;
  chips: Chip[];
  to?: AgentName;
}

/** Turn audit steps into trader-chat lines. Consecutive tool calls by one agent share a line. */
export function toChat(events: FeedEvent[]): ChatLine[] {
  const lines: ChatLine[] = [];
  for (const e of events) {
    const agent = isAgent(e.agent) ? e.agent : null;
    const base = { key: `e${e.seq}`, seq: e.seq, time: e.time, ticketId: e.ticket_id, runId: e.run_id, agent, chips: [] as Chip[] };
    switch (e.step) {
      case "run_start":
        lines.push({ ...base, kind: "system", text: `Ticket #${e.ticket_id} hits the floor.` });
        break;
      case "user_prompt":
        if ((e.depth ?? 0) > 0) lines.push({ ...base, kind: "says", text: `Picks up the line: “${clip(e.args, 220)}”` });
        else if (e.ticket_id != null) lines.push({ ...base, kind: "says", text: `Pulls ticket #${e.ticket_id} onto the desk.` });
        else lines.push({ ...base, kind: "says", text: clip(e.args, 220) });
        break;
      case "model_response":
        if (e.result) lines.push({ ...base, kind: "says", text: clip(e.result, 320) });
        break;
      case "tool_call": {
        if (e.tool === "delegate") {
          const to = isAgent(e.delegated_to) ? e.delegated_to : undefined;
          const task = field(e.args, "task");
          lines.push({ ...base, kind: "phone", to, text: `Rings ${agentTitle(e.delegated_to)}${task ? `: “${clip(task, 200)}”` : "."}` });
          break;
        }
        const chip = { tool: e.tool ?? "tool", args: chipArgs(e.args) };
        const prev = lines[lines.length - 1];
        if (prev && prev.kind === "calls" && prev.agent === agent && prev.runId === e.run_id) prev.chips.push(chip);
        else lines.push({ ...base, kind: "calls", text: "", chips: [chip] });
        break;
      }
      case "tool_result":
        if (e.tool === "delegate") {
          const summary = field(e.result, "summary");
          const err = field(e.result, "error");
          lines.push({ ...base, kind: "result", text: err ? `Line refused: ${field(e.result, "detail") ?? err}` : `Hears back${summary ? `: ${clip(summary, 200)}` : "."}` });
        } else {
          const err = field(e.result, "error");
          lines.push({ ...base, kind: "result", text: `${e.tool} ${err ? `✗ ${err}: ${field(e.result, "detail") ?? ""}` : "→ " + clip(e.result, 150)}` });
        }
        break;
      case "tool_retry":
        lines.push({ ...base, kind: "alert", text: `Retry on ${e.tool ?? "tool"}: ${clip(e.result, 160)}` });
        break;
      case "final_output": {
        const summary = field(e.result, "summary") ?? clip(e.result, 260);
        lines.push({ ...base, kind: "report", text: summary });
        break;
      }
      case "run_end": {
        const decision = field(e.result, "decision");
        const summary = field(e.result, "summary");
        lines.push({ ...base, kind: "decision", text: `Final call: ${decision ? decision.replace(/_/g, " ").toUpperCase() : "done"}${summary ? ` — ${clip(summary, 220)}` : ""}` });
        break;
      }
      case "limit_reached":
      case "error":
      case "run_failed":
        lines.push({ ...base, kind: "alert", text: `${e.step.replace("_", " ")}: ${clip(e.result, 220)}` });
        break;
    }
  }
  return lines;
}

export interface Call {
  from: AgentName;
  to: AgentName;
}

/** Open phone lines right now: delegate calls that haven't returned yet. */
export function openCalls(runEvents: FeedEvent[]): Call[] {
  const stack: Call[] = [];
  for (const e of runEvents) {
    if (e.tool !== "delegate" || !isAgent(e.agent)) continue;
    if (e.step === "tool_call" && isAgent(e.delegated_to)) stack.push({ from: e.agent, to: e.delegated_to });
    if (e.step === "tool_result") {
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].from === e.agent) {
          stack.splice(i, 1);
          break;
        }
      }
    }
  }
  return stack;
}

/** Each agent's tools used in a run (for the closing report). */
export function toolsByAgent(runEvents: FeedEvent[]): Partial<Record<AgentName, string[]>> {
  const out: Partial<Record<AgentName, string[]>> = {};
  for (const e of runEvents) {
    if (e.step !== "tool_call" || !isAgent(e.agent) || !e.tool) continue;
    const list = (out[e.agent] ??= []);
    if (!list.includes(e.tool)) list.push(e.tool);
  }
  return out;
}

/** Last thing each agent said in a run (shown on its desk). */
export function lastWords(runEvents: FeedEvent[]): Partial<Record<AgentName, string>> {
  const out: Partial<Record<AgentName, string>> = {};
  for (const line of toChat(runEvents)) {
    if (!line.agent || line.kind === "result") continue;
    out[line.agent] = line.kind === "calls" ? `Working ${line.chips.map((c) => c.tool).join(", ")}` : line.text;
  }
  return out;
}

export function stampFor(ticketStatus: string, running: boolean): { label: string; tone: string } {
  if (running) return { label: "ON THE DESK", tone: "live" };
  if (ticketStatus === "awaiting_approval") return { label: "AWAITING APPROVAL", tone: "await" };
  if (ticketStatus === "resolved" || ticketStatus === "closed") return { label: "RESOLVED", tone: "done" };
  return { label: "OPEN", tone: "open" };
}

export const KIND_LABEL: Record<string, string> = {
  invoice_payment: "PAY VENDOR INVOICE",
  rent_payment: "PAY RENT",
  purchase_order: "PURCHASE ORDER",
  price_override: "PRICE OVERRIDE",
};
