import type { WatchlistData } from "./watchlist";

import latest from "./sessions/2026-03-12.json";
import bullish from "./sessions/2026-02-25.json";
import bearish from "./sessions/2026-02-26.json";
import mixed from "./sessions/2026-03-05.json";
import reversal from "./sessions/2026-03-04.json";

/* ------------------------------------------------------------------ */
/*  Session metadata                                                   */
/* ------------------------------------------------------------------ */

export interface Session {
  id: string;
  date: string;
  label: string;
  regime: "bullish" | "bearish" | "mixed";
  description: string;
  data: WatchlistData;
}

export const sessions: Session[] = [
  {
    id: "latest",
    date: "2026-03-12",
    label: "Latest Session",
    regime: "bearish",
    description: "Broad selloff with QQQ -1.17% — all signals bearish",
    data: latest as unknown as WatchlistData,
  },
  {
    id: "bullish-trend",
    date: "2026-02-25",
    label: "Bullish Trend Day",
    regime: "bullish",
    description: "Strong uptrend with 85% confidence — MAs aligned, above VWAP",
    data: bullish as unknown as WatchlistData,
  },
  {
    id: "bearish-trend",
    date: "2026-02-26",
    label: "Bearish Trend Day",
    regime: "bearish",
    description: "Reversal from prior bullish session — momentum turned negative",
    data: bearish as unknown as WatchlistData,
  },
  {
    id: "mixed-choppy",
    date: "2026-03-05",
    label: "Mixed / Choppy",
    regime: "mixed",
    description: "Low-conviction session — regime score near zero, narrow ranges",
    data: mixed as unknown as WatchlistData,
  },
  {
    id: "reversal",
    date: "2026-03-04",
    label: "Divergence Day",
    regime: "mixed",
    description: "Mixed regime but individual stocks diverged sharply from benchmarks",
    data: reversal as unknown as WatchlistData,
  },
];

export const defaultSession = sessions[0];
