import type { WatchlistData } from "./watchlist";

import s2026_05_01 from "./sessions/2026-05-01.json";
import s2026_04_30 from "./sessions/2026-04-30.json";
import s2026_04_29 from "./sessions/2026-04-29.json";
import s2026_04_28 from "./sessions/2026-04-28.json";
import s2026_04_27 from "./sessions/2026-04-27.json";
import s2026_04_24 from "./sessions/2026-04-24.json";
import s2026_04_23 from "./sessions/2026-04-23.json";
import s2026_04_22 from "./sessions/2026-04-22.json";
import s2026_04_21 from "./sessions/2026-04-21.json";
import s2026_04_20 from "./sessions/2026-04-20.json";
import s2026_04_17 from "./sessions/2026-04-17.json";
import s2026_04_16 from "./sessions/2026-04-16.json";
import s2026_04_15 from "./sessions/2026-04-15.json";
import s2026_04_14 from "./sessions/2026-04-14.json";
import s2026_04_13 from "./sessions/2026-04-13.json";
import s2026_04_10 from "./sessions/2026-04-10.json";
import s2026_04_09 from "./sessions/2026-04-09.json";
import s2026_04_08 from "./sessions/2026-04-08.json";
import s2026_04_07 from "./sessions/2026-04-07.json";
import s2026_04_06 from "./sessions/2026-04-06.json";
import s2026_04_02 from "./sessions/2026-04-02.json";
import s2026_04_01 from "./sessions/2026-04-01.json";
import s2026_03_31 from "./sessions/2026-03-31.json";
import s2026_03_30 from "./sessions/2026-03-30.json";
import s2026_03_27 from "./sessions/2026-03-27.json";
import s2026_03_26 from "./sessions/2026-03-26.json";
import s2026_03_25 from "./sessions/2026-03-25.json";
import s2026_03_24 from "./sessions/2026-03-24.json";
import s2026_03_23 from "./sessions/2026-03-23.json";
import s2026_03_20 from "./sessions/2026-03-20.json";
import s2026_03_13 from "./sessions/2026-03-13.json";
import s2026_03_12 from "./sessions/2026-03-12.json";
import s2026_03_05 from "./sessions/2026-03-05.json";
import s2026_03_04 from "./sessions/2026-03-04.json";
import s2026_02_26 from "./sessions/2026-02-26.json";
import s2026_02_25 from "./sessions/2026-02-25.json";

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
    date: "2026-05-01",
    label: "Latest Session",
    regime: "bearish",
    description: "Bearish composite (conf 0.26), 7 alerts; HMM tag High-Vol Breakout",
    data: s2026_05_01 as unknown as WatchlistData,
  },
  {
    id: "2026-04-30",
    date: "2026-04-30",
    label: "Apr 30",
    regime: "bullish",
    description: "Bullish composite (conf 0.21), 8 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_30 as unknown as WatchlistData,
  },
  {
    id: "2026-04-29",
    date: "2026-04-29",
    label: "Apr 29",
    regime: "mixed",
    description: "Mixed composite (conf 0.05), 9 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_29 as unknown as WatchlistData,
  },
  {
    id: "2026-04-28",
    date: "2026-04-28",
    label: "Apr 28",
    regime: "bullish",
    description: "Bullish composite (conf 0.33), 4 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_28 as unknown as WatchlistData,
  },
  {
    id: "2026-04-27",
    date: "2026-04-27",
    label: "Apr 27",
    regime: "mixed",
    description: "Mixed composite (conf 0.07), 7 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_27 as unknown as WatchlistData,
  },
  {
    id: "2026-04-24",
    date: "2026-04-24",
    label: "Apr 24",
    regime: "bullish",
    description: "Bullish composite (conf 0.36), 7 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_24 as unknown as WatchlistData,
  },
  {
    id: "2026-04-23",
    date: "2026-04-23",
    label: "Apr 23",
    regime: "mixed",
    description: "Mixed composite (conf 0.00), 10 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_23 as unknown as WatchlistData,
  },
  {
    id: "2026-04-22",
    date: "2026-04-22",
    label: "Apr 22",
    regime: "bullish",
    description: "Bullish composite (conf 0.46), 10 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_22 as unknown as WatchlistData,
  },
  {
    id: "2026-04-21",
    date: "2026-04-21",
    label: "Apr 21",
    regime: "mixed",
    description: "Mixed composite (conf 0.04), 9 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_21 as unknown as WatchlistData,
  },
  {
    id: "2026-04-20",
    date: "2026-04-20",
    label: "Apr 20",
    regime: "bullish",
    description: "Bullish composite (conf 0.24), 4 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_20 as unknown as WatchlistData,
  },
  {
    id: "2026-04-17",
    date: "2026-04-17",
    label: "Apr 17",
    regime: "bullish",
    description: "Bullish composite (conf 0.58), 6 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_17 as unknown as WatchlistData,
  },
  {
    id: "2026-04-16",
    date: "2026-04-16",
    label: "Apr 16",
    regime: "bullish",
    description: "Bullish composite (conf 0.27), 10 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_16 as unknown as WatchlistData,
  },
  {
    id: "2026-04-15",
    date: "2026-04-15",
    label: "Apr 15",
    regime: "bullish",
    description: "Bullish composite (conf 0.49), 8 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_15 as unknown as WatchlistData,
  },
  {
    id: "2026-04-14",
    date: "2026-04-14",
    label: "Apr 14",
    regime: "bullish",
    description: "Bullish composite (conf 0.78), 10 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_14 as unknown as WatchlistData,
  },
  {
    id: "2026-04-13",
    date: "2026-04-13",
    label: "Apr 13",
    regime: "bullish",
    description: "Bullish composite (conf 0.84), 12 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_13 as unknown as WatchlistData,
  },
  {
    id: "2026-04-10",
    date: "2026-04-10",
    label: "Apr 10",
    regime: "mixed",
    description: "Mixed composite (conf 0.02), 4 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_10 as unknown as WatchlistData,
  },
  {
    id: "2026-04-09",
    date: "2026-04-09",
    label: "Apr 9",
    regime: "bullish",
    description: "Bullish composite (conf 0.45), 11 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_09 as unknown as WatchlistData,
  },
  {
    id: "2026-04-08",
    date: "2026-04-08",
    label: "Apr 8",
    regime: "mixed",
    description: "Mixed composite (conf 0.19), 10 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_08 as unknown as WatchlistData,
  },
  {
    id: "2026-04-07",
    date: "2026-04-07",
    label: "Apr 7",
    regime: "bullish",
    description: "Bullish composite (conf 0.61), 10 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_07 as unknown as WatchlistData,
  },
  {
    id: "2026-04-06",
    date: "2026-04-06",
    label: "Apr 6",
    regime: "bullish",
    description: "Bullish composite (conf 0.49), 5 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_06 as unknown as WatchlistData,
  },
  {
    id: "2026-04-02",
    date: "2026-04-02",
    label: "Apr 2",
    regime: "bullish",
    description: "Bullish composite (conf 0.75), 14 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_02 as unknown as WatchlistData,
  },
  {
    id: "2026-04-01",
    date: "2026-04-01",
    label: "Apr 1",
    regime: "mixed",
    description: "Mixed composite (conf 0.19), 6 alerts; HMM tag High-Vol Breakout",
    data: s2026_04_01 as unknown as WatchlistData,
  },
  {
    id: "2026-03-31",
    date: "2026-03-31",
    label: "Mar 31",
    regime: "bullish",
    description: "Bullish composite (conf 0.74), 15 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_31 as unknown as WatchlistData,
  },
  {
    id: "2026-03-30",
    date: "2026-03-30",
    label: "Mar 30",
    regime: "bearish",
    description: "Bearish composite (conf 0.50), 16 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_30 as unknown as WatchlistData,
  },
  {
    id: "2026-03-27",
    date: "2026-03-27",
    label: "Mar 27",
    regime: "bearish",
    description: "Bearish composite (conf 0.70), 7 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_27 as unknown as WatchlistData,
  },
  {
    id: "2026-03-26",
    date: "2026-03-26",
    label: "Mar 26",
    regime: "mixed",
    description: "Mixed composite (conf 0.15), 13 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_26 as unknown as WatchlistData,
  },
  {
    id: "2026-03-25",
    date: "2026-03-25",
    label: "Mar 25",
    regime: "bearish",
    description: "Bearish composite (conf 0.22), 5 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_25 as unknown as WatchlistData,
  },
  {
    id: "2026-03-24",
    date: "2026-03-24",
    label: "Mar 24",
    regime: "bullish",
    description: "Bullish composite (conf 0.55), 5 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_24 as unknown as WatchlistData,
  },
  {
    id: "2026-03-23",
    date: "2026-03-23",
    label: "Mar 23",
    regime: "bearish",
    description: "Bearish composite (conf 0.40), 13 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_23 as unknown as WatchlistData,
  },
  {
    id: "2026-03-20",
    date: "2026-03-20",
    label: "Mar 20",
    regime: "mixed",
    description: "Mixed composite (conf 0.10), 13 alerts; HMM tag High-Vol Breakout",
    data: s2026_03_20 as unknown as WatchlistData,
  },
  {
    id: "2026-03-13-bearish",
    date: "2026-03-13",
    label: "Bearish Session",
    regime: "bearish",
    description: "Bearish session — QQQ below VWAP by 0.57%, SPY below opening range",
    data: s2026_03_13 as unknown as WatchlistData,
  },
  {
    id: "2026-03-12-bearish",
    date: "2026-03-12",
    label: "Broad Selloff",
    regime: "bearish",
    description: "Broad selloff with QQQ -1.17% — all signals bearish",
    data: s2026_03_12 as unknown as WatchlistData,
  },
  {
    id: "2026-03-05-mixed",
    date: "2026-03-05",
    label: "Mixed / Choppy",
    regime: "mixed",
    description: "Low-conviction session — regime score near zero, narrow ranges",
    data: s2026_03_05 as unknown as WatchlistData,
  },
  {
    id: "2026-03-04-mixed",
    date: "2026-03-04",
    label: "Divergence Day",
    regime: "mixed",
    description: "Mixed regime but individual stocks diverged sharply from benchmarks",
    data: s2026_03_04 as unknown as WatchlistData,
  },
  {
    id: "2026-02-26-bearish",
    date: "2026-02-26",
    label: "Bearish Trend Day",
    regime: "bearish",
    description: "Reversal from prior bullish session — momentum turned negative",
    data: s2026_02_26 as unknown as WatchlistData,
  },
  {
    id: "2026-02-25-bullish",
    date: "2026-02-25",
    label: "Bullish Trend Day",
    regime: "bullish",
    description: "Strong uptrend with 85% confidence — MAs aligned, above VWAP",
    data: s2026_02_25 as unknown as WatchlistData,
  },
]

export const defaultSession = sessions[0];
