export type AgentName = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";

export interface Ticket {
  id: number;
  type: string;
  subject: string;
  requester: string;
  status: "open" | "resolved";
  ticket_status: string;
  running: boolean;
  last_run_id: string | null;
}

export interface FeedEvent {
  seq: number;
  time: string | null;
  run_id: string | null;
  ticket_id: number | null;
  agent: string | null;
  depth: number | null;
  step: string;
  tool: string | null;
  args: string | null;
  result: string | null;
  delegated_to: string | null;
}

export interface RunInProgress {
  ticket_id: number;
  run_id: string;
  started_at: string;
}

export interface EventsResponse {
  since: number;
  next_since: number;
  count: number;
  events: FeedEvent[];
  runs_in_progress: RunInProgress[];
}

export interface ApprovalRequest {
  id: number;
  kind: string;
  ticket_id: number | null;
  ref_id: number | null;
  vendor_id: number | null;
  sku: string | null;
  size: string | null;
  qty: number | null;
  unit_price: number | null;
  amount: number | null;
  reason: string | null;
  requested_by: string | null;
  status: string;
}

export interface ApprovalsResponse {
  count: number;
  pending_payment_total: number;
  requests: ApprovalRequest[];
}

export interface Cash {
  account: string;
  balance: number;
  as_of: string;
  pending_payment_requests: number;
  available_after_pending: number;
}

export interface BossDecision {
  ticket_id: number;
  decision: string;
  summary: string;
  rationale: string;
  agents_consulted: AgentName[];
  approval_request_ids: number[];
  draft_ids: number[];
  cash_committed: number;
  ticket_status: string | null;
  next_steps_for_human: string[];
}

export interface AgentReportOutput {
  agent: AgentName;
  summary: string;
  facts?: string[];
  actions_taken?: string[];
  approval_request_ids?: number[];
  draft_ids?: number[];
  blockers?: string[];
  needs_human?: boolean;
  recommendation?: string;
}

export interface RunReport {
  agent: AgentName;
  depth: number;
  called_by: AgentName | null;
  output: AgentReportOutput | BossDecision | string;
}

export interface RunRecord {
  run_id: string;
  ticket_id: number;
  state: "running" | "finished" | "failed";
  started_at: string;
  finished_at: string | null;
  decision: BossDecision | null;
  error: string | null;
  reports: RunReport[];
}

export interface DecisionResult {
  request_id: number;
  kind: string;
  status: string;
  decided_by: string;
  result_note: string;
  new_balance?: number;
}
