import type { AgentName } from "./types";

export interface AgentMeta {
  title: string;
  role: string;
  color: string;
}

// Everyone on the floor is an original character: a desk name, a role and a signature color.
export const AGENTS: Record<AgentName, AgentMeta> = {
  boss: { title: "The Chairman", role: "Corner office · makes the final call", color: "#e3c26b" },
  inventory: { title: "Stock Desk", role: "Inventory · stock, vendors, restock POs", color: "#3dff8a" },
  accounting: { title: "Treasury", role: "Accounting · cash, invoices, discounts", color: "#ffb000" },
  facilities: { title: "Real Estate", role: "Facilities · leases & rent", color: "#5cc8ff" },
  customer_service: { title: "Client Relations", role: "Customer Service · drafts only", color: "#ff7eb6" },
};

export const ANALYSTS: AgentName[] = ["inventory", "accounting", "facilities", "customer_service"];

export function isAgent(name: string | null | undefined): name is AgentName {
  return !!name && name in AGENTS;
}

export function agentTitle(name: string | null | undefined): string {
  return isAgent(name) ? AGENTS[name].title : name ?? "Floor";
}
