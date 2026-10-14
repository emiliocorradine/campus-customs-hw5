// The Problem 7 backend. This is the ONLY place the URL appears.
export const API_BASE = "http://localhost:8000";

// How often the board polls /events while a run is on the desk.
export const POLL_MS = 2000;

// When no run is on the desk, refresh slips, cash and tickets (and spot runs started elsewhere) this often.
export const IDLE_POLL_MS = 4000;
