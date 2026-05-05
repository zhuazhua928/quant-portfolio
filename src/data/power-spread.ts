// Static imports of the JSON artifacts produced by `python -m power_spread.pipeline.run`.
// All four files are read at build time so the Next.js page is fully static.

import pipelineJson from "./power-spread/pipeline.json";
import summaryJson from "./power-spread/summary.json";
import modelsJson from "./power-spread/models.json";
import equityJson from "./power-spread/equity.json";
import decisionsJson from "./power-spread/decisions.json";
import sensitivityJson from "./power-spread/sensitivity.json";
import metadataJson from "./power-spread/metadata.json";

export interface PipelineStage {
  key: string;
  name: string;
  role: string;
  files: string[];
  inputs: string[];
  outputs: string[];
}

export interface PipelinePayload {
  stages: PipelineStage[];
  paper: {
    title: string;
    authors: string;
    venue: string;
    doi: string;
  };
  scope: {
    market: string;
    instruments: string;
    window: string;
    oos_start: string;
    calibration_windows: number[];
    thresholds: number[];
    cost_per_mwh: number;
    cost_sweep: number[];
  };
}

export interface ModelRecord {
  config_id: string;
  model: string;
  window: number | null;
  x_cols: string[];
  lag_set: number[];
  mu: number | null;
  n: number;
  p: number | null;
  q0: number | null;
  q1: number | null;
  n_days: number;
  total_profit: number | null;
  ann_return_dollars: number | null;
  ann_return_pct: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  calmar: number | null;
  var_5pct: number | null;
  hit_rate: number | null;
}

export interface SummaryPayload {
  asof: string;
  best: ModelRecord;
  scope: {
    market: string;
    window_start: string;
    window_end: string;
    oos_start: string;
    n_oos_days: number;
    avg_da_price: number;
    avg_rt_price: number;
    avg_spread: number;
    spread_std: number;
    spread_pos_share: number;
  };
  paper_reference: {
    best_polish_arx_p: number;
    best_polish_arx_profit_pln: number;
    best_polish_arx_var5_pln: number;
    naive_balancing_polish_profit_pln: number;
    note: string;
  };
}

export interface EquityRow {
  date: string;
  pnl_best: number | null;
  eq_best: number | null;
  eq_da: number | null;
  eq_rt: number | null;
  eq_arx_levels: number | null;
  eq_arx_spread: number | null;
  eq_probit: number | null;
}

export interface EquityPayload {
  best_config_id: string;
  rows: EquityRow[];
}

export interface DecisionRow {
  date: string;
  y_hat: number;
  y_true: number;
  correct: number;
  spread: number;
}

export interface DecisionsPayload {
  best_config_id: string;
  rows: DecisionRow[];
}

export interface CostSweepRow {
  cost: number;
  total_profit: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  ann_return_pct: number | null;
}

export interface ThresholdSweepRow {
  config_id: string;
  mu: number;
  p: number | null;
  q0: number | null;
  q1: number | null;
  total_profit: number | null;
  sharpe: number | null;
}

export interface SensitivityPayload {
  cost_sweep: CostSweepRow[];
  threshold_sweep: ThresholdSweepRow[];
}

export interface MetadataPayload {
  asof: string;
  data: {
    n_hourly_rows: number;
    expected_hourly_rows: number;
    missing_hours_pct: number;
    n_daily_rows: number;
    first_date: string;
    last_date: string;
  };
  configs: {
    config_id: string;
    model: string;
    window: number;
    x_cols: string[];
    lag_set: number[];
  }[];
  wind_solar_caveat: string;
}

export const pipelinePayload = pipelineJson as unknown as PipelinePayload;
export const summaryPayload = summaryJson as unknown as SummaryPayload;
export const modelsPayload = modelsJson as unknown as { rows: ModelRecord[] };
export const equityPayload = equityJson as unknown as EquityPayload;
export const decisionsPayload = decisionsJson as unknown as DecisionsPayload;
export const sensitivityPayload = sensitivityJson as unknown as SensitivityPayload;
export const metadataPayload = metadataJson as unknown as MetadataPayload;
