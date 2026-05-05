"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { projects } from "@/data/projects";
import {
  researchBacktest,
  researchSummary,
  researchSwingCurve,
  type ResearchDiagnosticStats,
  type ResearchFoldRow,
} from "@/data/research";

const project = projects.find((p) => p.slug === "intraday-ml-research")!;

const TABS = [
  "Overview",
  "Methodology",
  "Regime Map",
  "Swing Strategy",
  "Diagnostic",
  "Walk-Forward Results",
  "Minute-Bar Backtest",
] as const;
type Tab = (typeof TABS)[number];

const MODEL_COLORS: Record<string, string> = {
  two_stage_hmm: "#10b981",
  single_stage_lgb: "#3b82f6",
  naive_momentum: "#94a3b8",
};

const MODEL_LABELS: Record<string, string> = {
  two_stage_hmm: "Two-Stage (HMM + LGB)",
  single_stage_lgb: "Single-Stage LGB",
  naive_momentum: "Naive Momentum",
};

export default function CustomPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Overview");

  return (
    <>
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <Link
            href="/projects"
            className="mb-8 inline-flex items-center gap-1.5 text-sm text-muted transition-colors duration-200 hover:text-foreground"
          >
            <span>&larr;</span>
            <span>Back to Projects</span>
          </Link>
          <div className="mb-4 flex items-center gap-3">
            <span className="font-mono text-[10px] font-bold tracking-wider text-accent">
              {project.code}
            </span>
            <span className="rounded-full bg-accent/8 px-2.5 py-0.5 font-mono text-xs font-medium text-accent">
              {project.category}
            </span>
            <span className="text-sm text-muted">{project.period}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            {project.title}
          </h1>
          <p className="mt-3 text-lg text-muted">{project.subtitle}</p>
          <div className="mt-5 flex flex-wrap gap-1.5">
            {project.tags.map((tag) => (
              <span
                key={tag}
                className="rounded bg-card px-2 py-0.5 font-mono text-[11px] text-muted"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="sticky top-[57px] z-40 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl gap-0 px-6 overflow-x-auto">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`relative whitespace-nowrap px-4 py-3 text-sm transition-colors duration-200 ${
                activeTab === tab
                  ? "font-medium text-foreground"
                  : "text-muted hover:text-foreground"
              }`}
            >
              {tab}
              {activeTab === tab && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-6 py-12">
        {activeTab === "Overview" && <OverviewTab />}
        {activeTab === "Methodology" && <MethodologyTab />}
        {activeTab === "Regime Map" && <RegimeMapTab />}
        {activeTab === "Swing Strategy" && <SwingTab />}
        {activeTab === "Diagnostic" && <DiagnosticTab />}
        {activeTab === "Walk-Forward Results" && <WalkForwardTab />}
        {activeTab === "Minute-Bar Backtest" && <BacktestTab />}
      </div>
    </>
  );
}

function OverviewTab() {
  return (
    <div className="grid gap-10 md:grid-cols-3">
      <div className="md:col-span-2 space-y-8">
        <SectionHeading>Overview</SectionHeading>
        <p className="text-base leading-7 text-muted">{project.summary}</p>

        {project.sections.slice(0, 1).map((s) => (
          <div key={s.title}>
            <h2 className="mb-2 text-lg font-semibold tracking-tight">
              {s.title}
            </h2>
            <p className="text-sm leading-7 text-muted">{s.content}</p>
          </div>
        ))}

        <ScopeCard />
      </div>

      <aside>
        <div className="sticky top-24 rounded-lg border border-border bg-card p-6 shadow-sm">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
            Key Highlights
          </h3>
          <ul className="mt-4 space-y-3">
            {project.highlights.map((h) => (
              <li
                key={h}
                className="flex items-start gap-3 text-sm text-muted"
              >
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                {h}
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}

function MethodologyTab() {
  return (
    <div className="space-y-10">
      <SectionHeading>Methodology</SectionHeading>
      {project.sections.map((s) => (
        <div key={s.title}>
          <h2 className="mb-2 text-lg font-semibold tracking-tight">
            {s.title}
          </h2>
          <p className="text-sm leading-7 text-muted">{s.content}</p>
        </div>
      ))}

      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
          Pipeline modules
        </h3>
        <pre className="mt-3 overflow-x-auto rounded bg-background/50 p-4 text-xs leading-relaxed text-muted">
{`research/
  data/         alpaca_client.py        Alpaca historical bars (alpaca-py)
                fetch_bars.py           CLI: monthly parquet backfill
                universe.py             rolling-60d β screen vs SPY
  features/     intraday.py             per-bar features
                windowing.py            5-min non-overlapping windows
  models/       regime_hmm.py           GaussianHMM (K=3,4)
                regime_hdbscan.py       non-parametric Stage-1
                forecaster_lgb.py       per-regime LightGBM
                baselines.py            single-stage LGB, naive momentum
  evaluation/   walkforward.py          purged k-fold + 5d embargo
                metrics.py              accuracy, Brier, log-loss, IC, MAE
                backtest.py             minute-bar 1bp/side cost
                regime_strategy.py      *regime-swing state machine*
  pipeline/     build_panel.py          bars → features → windows → panel
                train_and_evaluate.py   walk-forward train + score
  export/       export_dashboard.py     writes src/data/research/*.json`}
        </pre>
      </div>
    </div>
  );
}

function RegimeMapTab() {
  const K = 4;
  const cells = Array.from({ length: K }, (_, i) => i);
  return (
    <div className="space-y-8">
      <SectionHeading>Regime Map</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        After fitting, raw HMM states are relabeled by mean forward 5-minute
        return so label 0 is the most bearish regime and label {K - 1} the
        most bullish. The Swing Strategy uses these posterior probabilities
        directly: enter long when p<sub>{K - 1}</sub> ≥ entry threshold,
        exit when p<sub>{K - 1}</sub> falls below exit threshold or p<sub>0</sub>
        rises above flip threshold.
      </p>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {cells.map((k) => (
          <div
            key={k}
            className="rounded-lg border border-border bg-card p-5"
            style={{
              borderColor:
                k === 0
                  ? "rgba(239, 68, 68, 0.4)"
                  : k === K - 1
                    ? "rgba(16, 185, 129, 0.4)"
                    : undefined,
            }}
          >
            <div className="font-mono text-[10px] uppercase tracking-wider text-muted">
              Regime {k}
            </div>
            <div className="mt-2 text-lg font-semibold">
              {k === 0
                ? "Trending Down"
                : k === 1
                  ? "Mean-Reverting"
                  : k === 2
                    ? "High-Vol Breakout"
                    : "Trending Up"}
            </div>
            <div className="mt-3 text-xs leading-5 text-muted">
              {k === 0 &&
                "Negative mean fwd return; high realized vol; price below VWAP; OFI persistent sell."}
              {k === 1 &&
                "Near-zero mean fwd return; moderate vol; oscillation around VWAP."}
              {k === 2 &&
                "Wide ranges; elevated Parkinson vol; β spike vs SPY; news / macro often co-located."}
              {k === 3 &&
                "Positive mean fwd return; trending above VWAP; OFI persistent buy."}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SwingTab() {
  const swing = researchSummary.regime_swing;
  const series = researchSwingCurve.series;
  const cfg = swing?.config;
  const oos = swing?.oos_aggregate;
  const folds = swing?.folds || [];
  const perSymbol = swing?.per_symbol || [];

  const hasResults = oos && Object.keys(oos).length > 0;

  return (
    <div className="space-y-8">
      <SectionHeading>Regime-Swing Strategy</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Headline strategy. <strong className="text-foreground">Enter</strong>{" "}
        the top-N names by Stage-2 forecast when the bullish regime posterior
        crosses the entry threshold. <strong className="text-foreground">Hold</strong>{" "}
        through the regime block — no per-bar repositioning.{" "}
        <strong className="text-foreground">Exit</strong> when the bullish
        posterior falls below the exit threshold or the bearish posterior
        flips dominant. All thresholds are configurable via the CLI for
        re-tuning on new data.
      </p>

      {!hasResults ? (
        <EmptyState
          title="Regime-swing results not yet populated"
          body="Run research/pipeline/train_and_evaluate.py on the full panel, then research/export/export_dashboard.py."
        />
      ) : (
        <>
          <SwingHeadline oos={oos!} />
          {cfg && <SwingConfigCard cfg={cfg} />}

          <div className="rounded-lg border border-border bg-card p-6">
            <h3 className="mb-3 text-sm font-semibold tracking-tight">
              Out-of-sample equity curve (stitched across folds)
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={40} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${((v as number) * 100).toFixed(1)}%`} />
                  <Tooltip formatter={(v) => `${((v as number) * 100).toFixed(2)}%`} />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="net_equity"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.18}
                    name="Net (incl. costs)"
                  />
                  <Area
                    type="monotone"
                    dataKey="gross_equity"
                    stroke="#94a3b8"
                    fill="#94a3b8"
                    fillOpacity={0.05}
                    name="Gross"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <SwingFoldTable folds={folds} />
          {perSymbol.length > 0 && <SwingPerSymbolTable rows={perSymbol} />}
        </>
      )}
    </div>
  );
}

function SwingHeadline({ oos }: { oos: NonNullable<typeof researchSummary.regime_swing.oos_aggregate> }) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      <Stat2 label="Annualized Return" value={`${(oos.ann_return * 100).toFixed(1)}%`} accent={oos.ann_return >= 0} />
      <Stat2 label="Sharpe (daily)" value={oos.sharpe?.toFixed(2) ?? "—"} accent={(oos.sharpe ?? 0) >= 0} />
      <Stat2 label="Max Drawdown" value={`${(oos.max_drawdown * 100).toFixed(1)}%`} accent={false} />
      <Stat2 label="Calmar" value={oos.calmar?.toFixed(2) ?? "—"} accent={(oos.calmar ?? 0) >= 0} />
      <Stat2 label="Daily Hit Rate" value={`${(oos.hit_rate_daily * 100).toFixed(1)}%`} />
      <Stat2 label="Annual Vol" value={`${(oos.ann_vol * 100).toFixed(1)}%`} />
      <Stat2 label="Total Return" value={`${(oos.total_return * 100).toFixed(1)}%`} accent={oos.total_return >= 0} />
      <Stat2 label="OOS Days" value={String(oos.n_days)} />
    </div>
  );
}

function SwingConfigCard({ cfg }: { cfg: NonNullable<typeof researchSummary.regime_swing.config> }) {
  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
        Strategy parameters
      </h3>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-3 lg:grid-cols-4">
        <Stat label="Entry long p" value={cfg.entry_long_p.toFixed(2)} />
        <Stat label="Exit long p" value={cfg.exit_long_p.toFixed(2)} />
        <Stat label="Flip-out long p" value={cfg.exit_long_on_bear_p.toFixed(2)} />
        <Stat label="Top-N selection" value={cfg.top_n_per_regime > 0 ? String(cfg.top_n_per_regime) : "all"} />
        <Stat label="Short enabled" value={cfg.short_enabled ? "yes" : "no"} />
        <Stat label="Cost / side" value={`${cfg.cost_bps_per_side.toFixed(1)} bps`} />
        <Stat label="Flatten at close" value={cfg.flatten_at_close ? "yes" : "no"} />
        <Stat label="Vol target" value={cfg.vol_target_annual ? `${(cfg.vol_target_annual * 100).toFixed(0)}%` : "off"} />
      </dl>
      <p className="mt-4 text-xs leading-relaxed text-muted">
        Re-tune on new data:{" "}
        <code className="rounded bg-background/40 px-1.5 py-0.5 font-mono">
          python -m research.pipeline.train_and_evaluate --entry-long-p 0.65 --exit-long-p 0.30 --top-n 3
        </code>
      </p>
    </div>
  );
}

function SwingFoldTable({
  folds,
}: {
  folds: NonNullable<typeof researchSummary.regime_swing.folds>;
}) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold tracking-tight">
        Per-fold breakdown
      </h3>
      <div className="overflow-x-auto rounded-lg border border-border bg-card">
        <table className="min-w-full divide-y divide-border text-xs">
          <thead className="bg-card/50">
            <tr>
              <Th>Fold</Th>
              <Th right>Days</Th>
              <Th right>Ann. Return</Th>
              <Th right>Sharpe</Th>
              <Th right>Max DD</Th>
              <Th right>Hit %</Th>
              <Th right>Hold (bars)</Th>
              <Th right>In-Position</Th>
              <Th right>Trades</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {folds.map((f) => (
              <tr key={f.fold}>
                <Td>{f.fold}</Td>
                <Td right>{f.n_days}</Td>
                <Td right colored={f.ann_return}>
                  {(f.ann_return * 100).toFixed(2)}%
                </Td>
                <Td right colored={f.sharpe}>
                  {f.sharpe?.toFixed(2) ?? "—"}
                </Td>
                <Td right>{(f.max_drawdown * 100).toFixed(2)}%</Td>
                <Td right>{(f.hit_rate_daily * 100).toFixed(1)}%</Td>
                <Td right>{f.avg_holding_period_bars.toFixed(1)}</Td>
                <Td right>{(f.frac_time_in_position * 100).toFixed(1)}%</Td>
                <Td right>{f.n_trades_total}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SwingPerSymbolTable({
  rows,
}: {
  rows: NonNullable<typeof researchSummary.regime_swing.per_symbol>;
}) {
  const sorted = [...rows].sort((a, b) => b.total_return - a.total_return);
  return (
    <div>
      <h3 className="mb-3 mt-2 text-sm font-semibold tracking-tight">
        Per-symbol contribution (summed across folds)
      </h3>
      <div className="overflow-x-auto rounded-lg border border-border bg-card">
        <table className="min-w-full divide-y divide-border text-xs">
          <thead className="bg-card/50">
            <tr>
              <Th>Symbol</Th>
              <Th right>Bars Held</Th>
              <Th right>Total Return</Th>
              <Th right>Avg Bar (bps)</Th>
              <Th right>Hit %</Th>
              <Th right>Folds Active</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {sorted.map((r) => (
              <tr key={r.symbol}>
                <Td>{r.symbol}</Td>
                <Td right>{r.n_in_position}</Td>
                <Td right colored={r.total_return}>
                  {(r.total_return * 100).toFixed(2)}%
                </Td>
                <Td right colored={r.avg_return_bps}>
                  {r.avg_return_bps.toFixed(2)}
                </Td>
                <Td right>{(r.hit_rate * 100).toFixed(1)}%</Td>
                <Td right>{r.n_folds}</Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DiagnosticTab() {
  const d = researchSummary.diagnostic;
  const sweep = researchSummary.sweep_top || [];
  if (!d || Object.keys(d).length === 0) {
    return (
      <EmptyState
        title="Diagnostic not yet populated"
        body="Run python -m research.pipeline.diagnose, then re-export."
      />
    );
  }

  const rows: { label: string; key: keyof typeof d; subtle?: boolean }[] = [
    { label: "Buy & Hold (basket, no cost)", key: "buy_and_hold_zero_cost", subtle: true },
    { label: "Basket only when bullish (1 bp)", key: "basket_when_bullish_p50" },
    { label: "Swing default (1 bp)", key: "swing_default_1bp" },
    { label: "Swing default GROSS (0 bp)", key: "swing_default_0bp_gross", subtle: true },
    { label: "Swing best-sweep (1 bp)", key: "swing_best_sweep_1bp" },
    { label: "Swing best-sweep GROSS (0 bp)", key: "swing_best_sweep_0bp_gross", subtle: true },
  ];

  const regimes = d.regime_diagnostics || {};

  return (
    <div className="space-y-10">
      <SectionHeading>Strategy Diagnostic</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Honest comparison of the swing strategy against simpler benchmarks
        and against a zero-cost variant. The gap between <em>net</em> (1 bp/side)
        and <em>gross</em> (0 bp) rows is the cost drag attributable to turnover.
        The per-regime block at the bottom shows whether the &quot;bullish&quot; HMM
        label still has a positive realized forward return out-of-sample —
        which is the most basic test of regime-strategy viability.
      </p>

      <div>
        <h3 className="mb-3 text-sm font-semibold tracking-tight">
          Net vs. gross comparison
        </h3>
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-card/50">
              <tr>
                <Th>Strategy</Th>
                <Th right>Days</Th>
                <Th right>Ann. Return</Th>
                <Th right>Sharpe</Th>
                <Th right>Max DD</Th>
                <Th right>Hit %</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((r) => {
                const s = d[r.key] as ResearchDiagnosticStats | undefined;
                if (!s) return null;
                return (
                  <tr key={r.label} className={r.subtle ? "opacity-60" : ""}>
                    <Td>{r.label}</Td>
                    <Td right>{s.n_days}</Td>
                    <Td right colored={s.ann_return}>
                      {(s.ann_return * 100).toFixed(2)}%
                    </Td>
                    <Td right colored={s.sharpe}>
                      {s.sharpe?.toFixed(2) ?? "—"}
                    </Td>
                    <Td right>{(s.max_dd * 100).toFixed(2)}%</Td>
                    <Td right>
                      {s.hit_rate_daily != null
                        ? `${(s.hit_rate_daily * 100).toFixed(1)}%`
                        : "—"}
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold tracking-tight">
          Per-regime out-of-sample diagnostics
        </h3>
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="min-w-full divide-y divide-border text-sm">
            <thead className="bg-card/50">
              <tr>
                <Th>Regime</Th>
                <Th right>Hard mean (bps)</Th>
                <Th right>Posterior-weighted (bps)</Th>
                <Th right>N rows</Th>
                <Th right>Frac of OOS</Th>
                <Th right>1-step persistence</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Object.entries(regimes).map(([k, v]) => (
                <tr key={k}>
                  <Td>{k}</Td>
                  <Td right colored={v.hard_mean_bps}>
                    {v.hard_mean_bps.toFixed(2)}
                  </Td>
                  <Td right>{v.weighted_mean_bps.toFixed(2)}</Td>
                  <Td right>{v.n_hard_assigned.toLocaleString()}</Td>
                  <Td right>{(v.frac_of_oos * 100).toFixed(1)}%</Td>
                  <Td right>{v.persistence_one_step.toFixed(3)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs leading-relaxed text-muted">
          Regimes are sticky (1-step persistence ≥ 0.89) — the HMM does
          identify persistent intraday states. Realized hard-assigned mean
          forward returns are small (≲ 0.25 bps per 5-min window). At 1 bp/side
          transaction cost, this signal is below the cost floor.
        </p>
      </div>

      {sweep.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold tracking-tight">
            Top {sweep.length} sweep configurations (out of 144 evaluated)
          </h3>
          <div className="overflow-x-auto rounded-lg border border-border bg-card">
            <table className="min-w-full divide-y divide-border text-xs">
              <thead className="bg-card/50">
                <tr>
                  <Th right>Entry</Th>
                  <Th right>Exit</Th>
                  <Th right>Flip</Th>
                  <Th right>Top-N</Th>
                  <Th right>Sharpe</Th>
                  <Th right>Ann. Ret</Th>
                  <Th right>Max DD</Th>
                  <Th right>Trades / fold</Th>
                  <Th right>Avg hold (b)</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {sweep.map((s, i) => (
                  <tr key={i}>
                    <Td right>{s.config.entry_long_p.toFixed(2)}</Td>
                    <Td right>{s.config.exit_long_p.toFixed(2)}</Td>
                    <Td right>{s.config.exit_long_on_bear_p.toFixed(2)}</Td>
                    <Td right>
                      {s.config.top_n_per_regime > 0
                        ? s.config.top_n_per_regime
                        : "all"}
                    </Td>
                    <Td right colored={s.agg.sharpe}>
                      {s.agg.sharpe.toFixed(2)}
                    </Td>
                    <Td right colored={s.agg.ann_return}>
                      {(s.agg.ann_return * 100).toFixed(2)}%
                    </Td>
                    <Td right>{(s.agg.max_drawdown * 100).toFixed(1)}%</Td>
                    <Td right>{s.agg.avg_n_trades.toFixed(0)}</Td>
                    <Td right>{s.agg.avg_holding_bars.toFixed(0)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs leading-relaxed text-muted">
            None of the 144 swept configurations produces a positive
            net-of-cost Sharpe — the gross signal exists but is dominated
            by transaction costs at minute-bar frequency. See the report
            (research/REPORT.md) for the full analysis.
          </p>
        </div>
      )}
    </div>
  );
}

function BacktestTab() {
  const series = researchBacktest.series;
  const models = researchBacktest.models;

  return (
    <div className="space-y-8">
      <SectionHeading>Minute-Bar Backtest (legacy)</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Original strategy: per-bar long/short/flat based on the 5-min forecast,
        threshold ±5 bps, 1 bp per-side cost. Useful as a forecast-quality
        diagnostic but burns through transaction costs at this frequency. The
        Swing Strategy tab is the production-relevant headline.
      </p>

      {series.length === 0 ? (
        <EmptyState
          title="Backtest curves not yet populated"
          body="Run research/pipeline/train_and_evaluate.py followed by research/export/export_dashboard.py to populate this chart."
        />
      ) : (
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={40} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${((v as number) * 100).toFixed(1)}%`} />
                <Tooltip formatter={(v) => `${((v as number) * 100).toFixed(2)}%`} />
                <Legend />
                {models.map((m) => (
                  <Area
                    key={m}
                    type="monotone"
                    dataKey={m}
                    stroke={MODEL_COLORS[m] || "#64748b"}
                    fill={MODEL_COLORS[m] || "#64748b"}
                    fillOpacity={0.08}
                    name={MODEL_LABELS[m] || m}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}

function WalkForwardTab() {
  const folds = researchSummary.folds;
  const agg = researchSummary.forecast_aggregate;

  return (
    <div className="space-y-8">
      <SectionHeading>Walk-Forward Forecast Quality</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        {researchSummary.config.n_splits}-fold expanding-window walk-forward
        with {researchSummary.config.embargo_days}-day purged embargo.
        Metrics below characterize the *forecast quality* of each model on
        every 5-minute window — not realized strategy P&amp;L. The Swing
        Strategy tab translates these forecasts into actual trades.
      </p>

      {Object.keys(agg).length === 0 ? (
        <EmptyState
          title="Walk-forward metrics not yet populated"
          body={researchSummary.data_caveat}
        />
      ) : (
        <>
          <AggMetricsTable agg={agg} />
          <div>
            <h3 className="mb-3 mt-8 text-sm font-semibold tracking-tight">
              Per-fold breakdown
            </h3>
            <FoldTable folds={folds} />
            <div className="mt-8 h-64 rounded-lg border border-border bg-card p-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={folds.map((f) => ({
                    fold: f.fold,
                    two_stage_hmm: f.two_stage_hmm.directional_accuracy,
                    single_stage_lgb: f.single_stage_lgb.directional_accuracy,
                    naive_momentum: f.naive_momentum.directional_accuracy,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
                  <XAxis dataKey="fold" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} domain={[0.4, 0.65]} tickFormatter={(v) => `${((v as number) * 100).toFixed(0)}%`} />
                  <Tooltip formatter={(v) => `${((v as number) * 100).toFixed(2)}%`} />
                  <Legend />
                  {Object.keys(MODEL_LABELS).map((m) => (
                    <Line
                      key={m}
                      type="monotone"
                      dataKey={m}
                      stroke={MODEL_COLORS[m]}
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      name={MODEL_LABELS[m]}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
          Data caveat
        </h3>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          {researchSummary.data_caveat}
        </p>
      </div>
    </div>
  );
}

// --- shared helpers --------------------------------------------------------

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <span className="h-5 w-0.5 rounded-full bg-accent" />
      <h2 className="text-xl font-semibold tracking-tight">{children}</h2>
    </div>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-card/50 p-8 text-center">
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="mt-2 text-xs leading-relaxed text-muted">{body}</p>
    </div>
  );
}

function ScopeCard() {
  const s = researchSummary.scope;
  const c = researchSummary.config;
  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
        Scope
      </h3>
      <dl className="mt-4 grid grid-cols-2 gap-4 text-xs sm:grid-cols-3">
        <Stat label="Universe" value={`${s.universe_size} symbols`} />
        <Stat label="Sample window" value={`${s.start} → ${s.end}`} />
        <Stat label="Bar frequency" value="1-minute (Alpaca IEX)" />
        <Stat label="Window size" value={`${c.window_size_min} min`} />
        <Stat
          label="Forecast horizons"
          value={c.forecast_horizons_min.map((h) => `${h}m`).join(", ")}
        />
        <Stat
          label="CV"
          value={`${c.n_splits} folds, ${c.embargo_days}d embargo`}
        />
      </dl>
      <div className="mt-5 text-xs text-muted">
        High-beta universe ({s.high_beta.length}):{" "}
        <span className="font-mono text-[11px]">{s.high_beta.join(", ")}</span>
      </div>
      <div className="mt-2 text-xs text-muted">
        Covariates: <span className="font-mono">{s.covariates.join(", ")}</span>
        {" · "}VXX is used as an Alpaca-native VIX proxy.
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] font-mono uppercase tracking-wider text-muted">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-foreground">{value}</dd>
    </div>
  );
}

function Stat2({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  const color =
    accent === undefined
      ? "text-foreground"
      : accent
        ? "text-emerald-400"
        : "text-rose-400";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-[10px] font-mono uppercase tracking-wider text-muted">
        {label}
      </div>
      <div className={`mt-1.5 text-xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function Th({ children, right }: { children: React.ReactNode; right?: boolean }) {
  return (
    <th
      className={`px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-muted ${right ? "text-right" : "text-left"}`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  right,
  colored,
}: {
  children: React.ReactNode;
  right?: boolean;
  colored?: number;
}) {
  let cls = "";
  if (colored !== undefined && !Number.isNaN(colored)) {
    cls = colored >= 0 ? "text-emerald-400" : "text-rose-400";
  }
  return (
    <td className={`px-3 py-2 font-mono ${right ? "text-right" : ""} ${cls}`}>
      {children}
    </td>
  );
}

function AggMetricsTable({
  agg,
}: {
  agg: Record<string, Record<string, number>>;
}) {
  const models = Object.keys(agg);
  const metricCols = useMemo(() => {
    const set = new Set<string>();
    models.forEach((m) => Object.keys(agg[m]).forEach((k) => set.add(k)));
    return Array.from(set);
  }, [agg, models]);

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card">
      <table className="min-w-full divide-y divide-border text-sm">
        <thead className="bg-card/50">
          <tr>
            <th className="px-4 py-2 text-left font-mono text-[10px] uppercase tracking-wider text-muted">
              Model
            </th>
            {metricCols.map((c) => (
              <th
                key={c}
                className="px-4 py-2 text-right font-mono text-[10px] uppercase tracking-wider text-muted"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {models.map((m) => (
            <tr key={m}>
              <td className="px-4 py-2 font-medium">
                <span
                  className="mr-2 inline-block h-2 w-2 rounded-full"
                  style={{ background: MODEL_COLORS[m] || "#64748b" }}
                />
                {MODEL_LABELS[m] || m}
              </td>
              {metricCols.map((c) => (
                <td
                  key={c}
                  className="px-4 py-2 text-right font-mono text-xs text-muted"
                >
                  {fmtMetric(c, agg[m][c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FoldTable({ folds }: { folds: ResearchFoldRow[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card">
      <table className="min-w-full divide-y divide-border text-xs">
        <thead className="bg-card/50">
          <tr>
            <Th>Fold</Th>
            <Th>Test window</Th>
            <Th right>Two-Stage acc</Th>
            <Th right>Two-Stage Brier</Th>
            <Th right>Single-Stage acc</Th>
            <Th right>Naive acc</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {folds.map((f) => (
            <tr key={f.fold}>
              <Td>{f.fold}</Td>
              <Td>
                {f.test_start} → {f.test_end}
              </Td>
              <Td right>{pct(f.two_stage_hmm.directional_accuracy)}</Td>
              <Td right>{f.two_stage_hmm.brier?.toFixed(4) ?? "—"}</Td>
              <Td right>{pct(f.single_stage_lgb.directional_accuracy)}</Td>
              <Td right>{pct(f.naive_momentum.directional_accuracy)}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function pct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(2)}%`;
}

function fmtMetric(name: string, v: number): string {
  if (v == null || Number.isNaN(v)) return "—";
  if (name === "directional_accuracy") return pct(v);
  if (name === "brier" || name === "log_loss") return v.toFixed(4);
  if (name === "ic") return v.toFixed(3);
  if (name === "mae_bps") return `${v.toFixed(2)} bps`;
  return v.toFixed(4);
}
