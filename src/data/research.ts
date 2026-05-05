import summaryJson from "./research/summary.json";
import backtestJson from "./research/backtest.json";
import swingCurveJson from "./research/regime_swing_curve.json";

export interface ResearchSummary {
  scope: {
    universe_size: number;
    high_beta: string[];
    covariates: string[];
    start: string;
    end: string;
  };
  config: {
    n_splits: number;
    embargo_days: number;
    window_size_min: number;
    forecast_horizons_min: number[];
    cost_bps_per_side: number;
    signal_threshold_bps: number;
  };
  forecast_aggregate: Record<string, Record<string, number>>;
  folds: ResearchFoldRow[];
  regime_swing: ResearchRegimeSwing;
  diagnostic: ResearchDiagnostic;
  sweep_top: ResearchSweepEntry[];
  data_caveat: string;
}

export interface ResearchDiagnosticStats {
  n_days: number;
  total_return: number;
  ann_return: number;
  ann_vol?: number;
  sharpe: number;
  max_dd: number;
  hit_rate_daily?: number;
}

export interface ResearchRegimeDiagnostic {
  hard_mean_bps: number;
  weighted_mean_bps: number;
  n_hard_assigned: number;
  frac_of_oos: number;
  persistence_one_step: number;
}

export interface ResearchDiagnostic {
  buy_and_hold_zero_cost?: ResearchDiagnosticStats;
  basket_when_bullish_p50?: ResearchDiagnosticStats;
  swing_default_1bp?: ResearchDiagnosticStats;
  swing_default_0bp_gross?: ResearchDiagnosticStats;
  swing_best_sweep_1bp?: ResearchDiagnosticStats;
  swing_best_sweep_0bp_gross?: ResearchDiagnosticStats;
  regime_diagnostics?: Record<string, ResearchRegimeDiagnostic>;
}

export interface ResearchSweepEntry {
  config: ResearchSwingConfig;
  agg: {
    n_days: number;
    total_return: number;
    ann_return: number;
    ann_vol: number;
    sharpe: number;
    max_drawdown: number;
    calmar: number;
    hit_rate_daily: number;
    avg_n_trades: number;
    avg_holding_bars: number;
    avg_frac_in_position: number;
  };
}

export interface ResearchFoldRow {
  fold: number;
  train_n: number;
  test_n: number;
  train_start: string;
  test_start: string;
  test_end: string;
  two_stage_hmm: ResearchFoldMetrics;
  single_stage_lgb: ResearchFoldMetrics;
  naive_momentum: ResearchFoldMetrics;
}

export interface ResearchFoldMetrics {
  n: number;
  directional_accuracy: number;
  brier: number;
  log_loss: number;
  mae_bps: number;
  ic: number;
}

export interface ResearchBacktestPoint {
  date: string;
  [model: string]: number | null | string;
}

export interface ResearchBacktest {
  models: string[];
  series: ResearchBacktestPoint[];
}

export interface ResearchSwingConfig {
  entry_long_p: number;
  entry_short_p: number;
  exit_long_p: number;
  exit_long_on_bear_p: number;
  exit_short_p: number;
  exit_short_on_bull_p: number;
  top_n_per_regime: number;
  short_enabled: boolean;
  cost_bps_per_side: number;
  flatten_at_close: boolean;
  vol_target_annual: number | null;
}

export interface ResearchSwingFold {
  fold: number;
  n_days: number;
  total_return: number;
  ann_return: number;
  ann_vol: number;
  sharpe: number;
  max_drawdown: number;
  calmar: number;
  hit_rate_daily: number;
  avg_holding_period_bars: number;
  frac_time_in_position: number;
  n_trades_total: number;
  avg_daily_turnover: number;
}

export interface ResearchSwingPerSymbol {
  symbol: string;
  n_in_position: number;
  total_return: number;
  avg_return_bps: number;
  hit_rate: number;
  turnover_per_day: number;
  n_folds: number;
}

export interface ResearchRegimeSwing {
  config: ResearchSwingConfig;
  oos_aggregate: {
    n_days: number;
    total_return: number;
    ann_return: number;
    ann_vol: number;
    sharpe: number;
    max_drawdown: number;
    calmar: number;
    hit_rate_daily: number;
  };
  folds: ResearchSwingFold[];
  per_symbol: ResearchSwingPerSymbol[];
}

export interface ResearchSwingCurvePoint {
  date: string;
  net_equity?: number | null;
  gross_equity?: number | null;
}

export interface ResearchSwingCurve {
  columns: string[];
  series: ResearchSwingCurvePoint[];
}

export const researchSummary = summaryJson as unknown as ResearchSummary;
export const researchBacktest = backtestJson as unknown as ResearchBacktest;
export const researchSwingCurve = swingCurveJson as unknown as ResearchSwingCurve;
