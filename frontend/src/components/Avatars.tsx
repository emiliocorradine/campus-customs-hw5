import type { AgentName } from "../types";

// Original characters drawn in SVG. None of them is based on a real person or a film character.

function Face({ skin, cx = 60, cy = 54 }: { skin: string; cx?: number; cy?: number }) {
  return (
    <>
      <rect x={cx - 8} y={cy + 16} width="16" height="14" fill={skin} />
      <ellipse cx={cx - 19} cy={cy + 2} rx="4" ry="6" fill={skin} />
      <ellipse cx={cx + 19} cy={cy + 2} rx="4" ry="6" fill={skin} />
      <ellipse cx={cx} cy={cy} rx="19" ry="23" fill={skin} />
    </>
  );
}

function Eyes({ cy = 52, brow = 0, color = "#1b1b1b" }: { cy?: number; brow?: number; color?: string }) {
  return (
    <>
      <path d={`M47 ${cy - 6 + brow} L55 ${cy - 7}`} stroke={color} strokeWidth="2.2" strokeLinecap="round" />
      <path d={`M65 ${cy - 7} L73 ${cy - 6 + brow}`} stroke={color} strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="51" cy={cy} r="2" fill={color} />
      <circle cx="69" cy={cy} r="2" fill={color} />
    </>
  );
}

/** The Chairman: slicked-back hair, double-breasted suit, red suspenders and a power tie. */
function Chairman() {
  const skin = "#e6b48c";
  return (
    <svg viewBox="0 0 120 120" role="img" aria-label="The Chairman">
      <path d="M8 120 C 12 94, 32 84, 60 84 C 88 84, 108 94, 112 120 Z" fill="#17203a" />
      <path d="M42 85 L60 120 L78 85 Z" fill="#f4f1e8" />
      <path d="M47 86 L51 120" stroke="#b0142f" strokeWidth="5" />
      <path d="M73 86 L69 120" stroke="#b0142f" strokeWidth="5" />
      <rect x="45.5" y="99" width="5" height="4" fill="#e3c26b" />
      <rect x="69.5" y="99" width="5" height="4" fill="#e3c26b" />
      <path d="M42 85 L60 120 L36 120 L30 92 Z" fill="#212c4d" />
      <path d="M78 85 L60 120 L84 120 L90 92 Z" fill="#212c4d" />
      <path d="M86 98 L94 96 L92 102 Z" fill="#e3c26b" />
      <path d="M52 84 L60 92 L68 84 L64 82 L56 82 Z" fill="#ffffff" />
      <path d="M57 88 L63 88 L62 93 L58 93 Z" fill="#c4152f" />
      <path d="M58 93 L62 93 L66 114 L60 120 L54 114 Z" fill="#c4152f" />
      <path d="M56 100 L64 96 M55 106 L65 102 M56 112 L65 108" stroke="#e3c26b" strokeWidth="1.2" />
      <Face skin={skin} />
      <path d="M40 50 C 39 29, 51 23, 62 23 C 75 23, 83 31, 81 50 C 78 39, 70 33, 59 33 C 50 33, 44 39, 40 50 Z" fill="#17110c" />
      <path d="M47 31 C 56 26, 69 26, 78 35" stroke="#6d5a46" strokeWidth="1.6" fill="none" />
      <path d="M45 37 C 54 31, 68 31, 79 41" stroke="#4a3b2d" strokeWidth="1.2" fill="none" />
      <Eyes brow={-2} />
      <path d="M57 60 L60 63 L63 60" stroke="#a87652" strokeWidth="1.5" fill="none" />
      <path d="M52 68 C 57 70, 64 70, 69 66" stroke="#7b3a2a" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}

/** Stock Desk: curly hair, green trading jacket with a desk badge, pencil behind the ear. */
function StockDesk() {
  const skin = "#c98e62";
  return (
    <svg viewBox="0 0 120 120" role="img" aria-label="Stock Desk analyst">
      <path d="M12 120 C 16 96, 34 86, 60 86 C 86 86, 104 96, 108 120 Z" fill="#1f6b45" />
      <path d="M46 87 L60 112 L74 87 Z" fill="#dfe9f2" />
      <path d="M58 92 L62 92 L64 110 L60 114 L56 110 Z" fill="#3dff8a" />
      <rect x="78" y="100" width="16" height="11" rx="1.5" fill="#f2efe6" />
      <text x="86" y="108.5" fontSize="7" textAnchor="middle" fontFamily="monospace" fill="#1f6b45">SD</text>
      <Face skin={skin} />
      {[38, 46, 54, 62, 70, 78].map((x) => <circle key={x} cx={x + 2} cy={33} r="7" fill="#2b1d14" />)}
      {[42, 52, 62, 72].map((x) => <circle key={x} cx={x + 2} cy={27} r="7" fill="#2b1d14" />)}
      <rect x="77" y="38" width="18" height="3" rx="1" fill="#f0c419" transform="rotate(-35 86 40)" />
      <Eyes cy={53} />
      <path d="M53 67 C 57 71, 63 71, 67 67" stroke="#6b2f20" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  );
}

/** Treasury: green eyeshade visor, round glasses, amber bow tie and a vest. */
function Treasury() {
  const skin = "#f0c9a6";
  return (
    <svg viewBox="0 0 120 120" role="img" aria-label="Treasury analyst">
      <path d="M12 120 C 16 96, 34 86, 60 86 C 86 86, 104 96, 108 120 Z" fill="#f4f1e8" />
      <path d="M36 92 C 44 88, 52 88, 56 96 L56 120 L32 120 Z" fill="#5a4630" />
      <path d="M84 92 C 76 88, 68 88, 64 96 L64 120 L88 120 Z" fill="#5a4630" />
      <path d="M50 88 L60 93 L50 98 Z M70 88 L60 93 L70 98 Z" fill="#ffb000" />
      <circle cx="60" cy="93" r="2.6" fill="#c98500" />
      <Face skin={skin} />
      <path d="M41 45 C 41 32, 50 27, 60 27 C 70 27, 79 32, 79 45 C 74 41, 67 40, 60 40 C 53 40, 46 41, 41 45 Z" fill="#9a9a9a" />
      <path d="M36 44 L84 44 L78 34 L42 34 Z" fill="rgba(40, 200, 110, 0.75)" />
      <path d="M36 44 L84 44" stroke="#147a42" strokeWidth="2" />
      <circle cx="51" cy="54" r="6.5" fill="none" stroke="#2b2b2b" strokeWidth="1.8" />
      <circle cx="69" cy="54" r="6.5" fill="none" stroke="#2b2b2b" strokeWidth="1.8" />
      <path d="M57.5 54 L62.5 54" stroke="#2b2b2b" strokeWidth="1.8" />
      <circle cx="51" cy="54" r="1.8" fill="#1b1b1b" />
      <circle cx="69" cy="54" r="1.8" fill="#1b1b1b" />
      <path d="M54 68 L66 68" stroke="#7a3b2c" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** Real Estate: big voluminous hair, shoulder-pad blazer, pearl earrings and necklace. */
function RealEstate() {
  const skin = "#8d5a3b";
  return (
    <svg viewBox="0 0 120 120" role="img" aria-label="Real Estate analyst">
      <path d="M20 58 C 10 34, 30 12, 60 12 C 90 12, 110 34, 100 62 C 104 78, 92 88, 84 84 L36 84 C 28 88, 16 78, 20 58 Z" fill="#7a2e1b" />
      <path d="M4 120 C 6 98, 22 86, 44 86 L76 86 C 98 86, 114 98, 116 120 Z" fill="#1f5f99" />
      <path d="M4 104 C 10 92, 22 88, 34 88 L28 102 Z M116 104 C 110 92, 98 88, 86 88 L92 102 Z" fill="#2a74b8" />
      <path d="M48 87 L60 106 L72 87 Z" fill="#f4f1e8" />
      {[50, 55, 60, 65, 70].map((x, i) => <circle key={x} cx={x} cy={93 + (i === 2 ? 3 : i % 2 ? 2 : 0)} r="1.8" fill="#fbf6e9" />)}
      <Face skin={skin} />
      <path d="M40 46 C 40 28, 52 22, 62 23 C 74 24, 82 32, 80 48 C 72 36, 54 34, 40 46 Z" fill="#7a2e1b" />
      <circle cx="40" cy="62" r="2.6" fill="#fbf6e9" />
      <circle cx="80" cy="62" r="2.6" fill="#fbf6e9" />
      <Eyes cy={53} color="#140c08" />
      <path d="M53 66 C 57 70, 63 70, 67 66" stroke="#c43c5a" strokeWidth="2.6" fill="none" strokeLinecap="round" />
    </svg>
  );
}

/** Client Relations: sleek bob haircut, phone headset with a mic, rose cardigan. */
function ClientRelations() {
  const skin = "#f2cfb0";
  return (
    <svg viewBox="0 0 120 120" role="img" aria-label="Client Relations analyst">
      <path d="M12 120 C 16 96, 34 86, 60 86 C 86 86, 104 96, 108 120 Z" fill="#b8467a" />
      <path d="M48 87 L60 104 L72 87 Z" fill="#f4f1e8" />
      <path d="M60 104 L60 120" stroke="#8a2f5a" strokeWidth="2" />
      {[108, 115].map((y) => <circle key={y} cx="64" cy={y} r="1.6" fill="#f4f1e8" />)}
      <path d="M36 60 C 32 34, 46 24, 60 24 C 74 24, 88 34, 84 60 L84 72 L76 72 L76 50 L44 50 L44 72 L36 72 Z" fill="#141018" />
      <Face skin={skin} />
      <path d="M41 48 C 42 32, 52 27, 60 27 C 70 27, 78 32, 79 48 C 70 42, 58 38, 41 48 Z" fill="#141018" />
      <path d="M38 50 C 38 26, 82 26, 82 50" stroke="#2a2a2a" strokeWidth="3.4" fill="none" />
      <rect x="34" y="48" width="8" height="13" rx="3" fill="#2a2a2a" />
      <path d="M38 61 C 40 72, 46 74, 53 72" stroke="#2a2a2a" strokeWidth="2.2" fill="none" />
      <circle cx="54" cy="72" r="2.4" fill="#ff7eb6" />
      <Eyes cy={53} />
      <path d="M53 66 C 57 70, 63 70, 67 66" stroke="#b03a62" strokeWidth="2.2" fill="none" strokeLinecap="round" />
    </svg>
  );
}

export function Avatar({ agent }: { agent: AgentName }) {
  switch (agent) {
    case "boss":
      return <Chairman />;
    case "inventory":
      return <StockDesk />;
    case "accounting":
      return <Treasury />;
    case "facilities":
      return <RealEstate />;
    case "customer_service":
      return <ClientRelations />;
  }
}
