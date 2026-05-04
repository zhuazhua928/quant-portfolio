import raw from "./watchlist.json";

/* ------------------------------------------------------------------ */
/*  Type definitions                                                   */
/* ------------------------------------------------------------------ */

export interface RegimeSignal {
  score: number;
  detail: string;
}

export interface RegimeDetails {
  QQQ?: Record<string, RegimeSignal>;
  QQQ_composite?: number;
  SPY?: Record<string, RegimeSignal>;
  SPY_composite?: number;
  composite?: number;
}

export interface Regime {
  label: "bullish" | "bearish" | "mixed";
  confidence: number;
  explanation: string;
  details: RegimeDetails;
}

export interface RankedSymbol {
  symbol: string;
  rank: number;
  score: number;
  factors: Record<string, number>;
  explanation: string;
}

export interface Ranking {
  ranked: RankedSymbol[];
  topBullish: RankedSymbol[];
  topBearish: RankedSymbol[];
}

export interface SymbolFeatures {
  symbol: string;
  last_price: number;
  bar_count: number;
  data_as_of: string;
  ma_5: number | null;
  ma_10: number | null;
  ma_20: number | null;
  ma_60: number | null;
  golden_cross: boolean;
  death_cross: boolean;
  rsi: number | null;
  vwap: number | null;
  ret_5m: number | null;
  ret_15m: number | null;
  ret_30m: number | null;
  ret_dtd: number | null;
  ret_5m_xs_qqq: number | null;
  ret_15m_xs_qqq: number | null;
  ret_30m_xs_qqq: number | null;
  ret_dtd_xs_qqq: number | null;
  ret_5m_xs_spy: number | null;
  ret_15m_xs_spy: number | null;
  ret_30m_xs_spy: number | null;
  ret_dtd_xs_spy: number | null;
  rvol: number | null;
  orb_high: number | null;
  orb_low: number | null;
  orb_status: "above" | "below" | "inside" | "undefined";
}

export interface ChartPoint {
  t: string;
  c: number;
  v: number | null;
  m5: number | null;
  m20: number | null;
}

export interface Alert {
  symbol: string;
  type: string;
  severity: "high" | "medium" | "low";
  message: string;
}

export interface MLRegimeResult {
  label: number;
  label_name: string;
  posterior: Record<string, number>; // p_0, p_1, ...
  timestamp: string;
  n_windows: number;
}

export interface MLRegime {
  market: MLRegimeResult | null;
  per_symbol: Record<string, MLRegimeResult | null>;
  trained_at?: string | null;
  n_components?: number | null;
}

export interface WatchlistData {
  scanDate: string;
  regime: Regime;
  mlRegime?: MLRegime | null;
  ranking: Ranking;
  symbols: SymbolFeatures[];
  charts: Record<string, ChartPoint[]>;
  alerts: Alert[];
}

/* ------------------------------------------------------------------ */
/*  Export typed data                                                   */
/* ------------------------------------------------------------------ */

export const watchlistData = raw as unknown as WatchlistData;
