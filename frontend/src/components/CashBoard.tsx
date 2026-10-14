import { useEffect, useRef, useState } from "react";
import { money } from "../feed";
import type { Cash } from "../types";

/** Big LED-style balance. Flashes red (and shows the drop) whenever the balance goes down. */
export function CashBoard({ cash }: { cash: Cash | null }) {
  const prev = useRef<number | null>(null);
  const [drop, setDrop] = useState<number | null>(null);

  useEffect(() => {
    if (cash == null) return;
    const before = prev.current;
    prev.current = cash.balance;
    if (before != null && cash.balance < before) {
      setDrop(before - cash.balance);
      const t = setTimeout(() => setDrop(null), 3200);
      return () => clearTimeout(t);
    }
  }, [cash]);

  return (
    <div className={`cashboard ${drop ? "dropped" : ""}`} aria-live="polite">
      <div className="cash-label">CHECKING · CASH ON HAND</div>
      <div className="led">{cash ? money(cash.balance) : "$—"}</div>
      <div className="cash-sub">
        {drop ? (
          <span className="cash-drop">▼ {money(drop)} paid out</span>
        ) : (
          <>
            <span>PENDING {money(cash?.pending_payment_requests ?? 0)}</span>
            <span>AVAIL {money(cash?.available_after_pending)}</span>
          </>
        )}
      </div>
    </div>
  );
}
