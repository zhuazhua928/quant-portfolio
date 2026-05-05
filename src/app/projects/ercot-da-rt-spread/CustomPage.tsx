"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { projects } from "@/data/projects";
import {
  decisionsPayload,
  equityPayload,
  metadataPayload,
  modelsPayload,
  pipelinePayload,
  sensitivityPayload,
  summaryPayload,
  type ModelRecord,
  type PipelineStage,
} from "@/data/power-spread";

const project = projects.find((p) => p.slug === "ercot-da-rt-spread")!;

const TABS = [
  "Pipeline",
  "Replication",
  "Equity Curve",
  "Decisions",
  "Sensitivity",
  "Methodology",
] as const;
type Tab = (typeof TABS)[number];

const POSITIVE = "#10b981";
const NEGATIVE = "#f43f5e";
const ACCENT = "#3b82f6";
const MUTED = "#94a3b8";
const PURPLE = "#a78bfa";
const AMBER = "#f59e0b";

const fmtUsd = (n: number | null | undefined, digits = 0) =>
  n == null ? "—" : `$${n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits })}`;
const fmtNum = (n: number | null | undefined, digits = 2) =>
  n == null ? "—" : n.toFixed(digits);
const fmtPct = (n: number | null | undefined, digits = 2) =>
  n == null ? "—" : `${(n * 100).toFixed(digits)}%`;

export default function CustomPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Pipeline");

  return (
    <>
      {/* Header */}
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

      {/* Tab bar */}
      <div className="sticky top-[57px] z-40 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl gap-0 overflow-x-auto px-6">
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
        {activeTab === "Pipeline" && <PipelineTab />}
        {activeTab === "Replication" && <ReplicationTab />}
        {activeTab === "Equity Curve" && <EquityTab />}
        {activeTab === "Decisions" && <DecisionsTab />}
        {activeTab === "Sensitivity" && <SensitivityTab />}
        {activeTab === "Methodology" && <MethodologyTab />}
      </div>
    </>
  );
}

/* ==================================================================== */
/*  Pipeline tab — the headline visualization                            */
/* ==================================================================== */
function PipelineTab() {
  const stages = pipelinePayload.stages;
  const [openKey, setOpenKey] = useState<string | null>(stages[0]?.key ?? null);
  const open = stages.find((s) => s.key === openKey) ?? stages[0];

  return (
    <div className="space-y-10">
      <SectionHeading>Backtest Pipeline</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        The replication is a linear pipeline from raw ERCOT and EIA-930 series
        through to model evaluation. Each stage is a separate Python module with
        a single responsibility. Click any stage below to expand the role,
        source files, and the artefacts it produces.
      </p>

      {/* Flow diagram */}
      <div className="relative overflow-x-auto">
        <div className="grid min-w-[980px] grid-cols-7 items-stretch gap-2">
          {stages.map((s, i) => (
            <PipelineCard
              key={s.key}
              stage={s}
              index={i + 1}
              isOpen={s.key === openKey}
              isLast={i === stages.length - 1}
              onClick={() => setOpenKey(s.key === openKey ? null : s.key)}
            />
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="mb-3 flex items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-wider text-accent">
            Stage {stages.findIndex((s) => s.key === open.key) + 1}
          </span>
          <h3 className="text-lg font-semibold tracking-tight">{open.name}</h3>
        </div>
        <p className="text-sm leading-7 text-muted">{open.role}</p>

        <div className="mt-6 grid gap-6 md:grid-cols-3">
          <DetailBlock label="Source files">
            <ul className="space-y-1 font-mono text-[11px] text-foreground">
              {open.files.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </DetailBlock>
          <DetailBlock label="Inputs">
            <ul className="space-y-1 text-[11px] leading-5 text-muted">
              {open.inputs.map((x, i) => (
                <li key={i}>• {x}</li>
              ))}
            </ul>
          </DetailBlock>
          <DetailBlock label="Outputs">
            <ul className="space-y-1 text-[11px] leading-5 text-muted">
              {open.outputs.map((x, i) => (
                <li key={i}>• {x}</li>
              ))}
            </ul>
          </DetailBlock>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="mb-3 text-sm font-semibold tracking-tight">Paper</h3>
          <div className="space-y-1 text-sm">
            <Row label="Title" value={pipelinePayload.paper.title} />
            <Row label="Authors" value={pipelinePayload.paper.authors} />
            <Row label="Venue" value={pipelinePayload.paper.venue} />
            <Row label="DOI" value={pipelinePayload.paper.doi} mono />
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="mb-3 text-sm font-semibold tracking-tight">Scope</h3>
          <div className="space-y-1 text-sm">
            <Row label="Market" value={pipelinePayload.scope.market} />
            <Row label="Instruments" value={pipelinePayload.scope.instruments} />
            <Row label="Window" value={pipelinePayload.scope.window} mono />
            <Row label="OOS start" value={pipelinePayload.scope.oos_start} mono />
            <Row label="Calibration windows (days)" value={pipelinePayload.scope.calibration_windows.join(", ")} mono />
            <Row label="Probit thresholds μ" value={pipelinePayload.scope.thresholds.join(", ")} mono />
            <Row label="Trading cost" value={`$${pipelinePayload.scope.cost_per_mwh.toFixed(2)}/MWh per switch`} mono />
          </div>
        </div>
      </div>

      <NotesBox>
        Run end-to-end with{" "}
        <code className="font-mono text-[12px] text-foreground">python -m power_spread.pipeline.run</code>.
        All seven JSON artefacts are written to <code className="font-mono text-[12px] text-foreground">src/data/power-spread/</code>{" "}
        and consumed at build time — the page is fully static.
      </NotesBox>
    </div>
  );
}

function PipelineCard({
  stage,
  index,
  isOpen,
  isLast,
  onClick,
}: {
  stage: PipelineStage;
  index: number;
  isOpen: boolean;
  isLast: boolean;
  onClick: () => void;
}) {
  return (
    <div className="relative col-span-1">
      <button
        onClick={onClick}
        className={`block h-full w-full rounded-lg border p-3 text-left transition-colors duration-200 ${
          isOpen
            ? "border-accent bg-accent/5"
            : "border-border bg-card hover:border-accent/50"
        }`}
      >
        <div className="font-mono text-[10px] uppercase tracking-wider text-muted">
          {String(index).padStart(2, "0")}
        </div>
        <div className="mt-1 text-sm font-semibold leading-tight text-foreground">
          {stage.name}
        </div>
        <div className="mt-2 line-clamp-3 text-[10.5px] leading-4 text-muted">
          {stage.role}
        </div>
      </button>
      {!isLast && (
        <div className="pointer-events-none absolute right-[-12px] top-1/2 -translate-y-1/2 text-muted">
          <span className="font-mono text-base">›</span>
        </div>
      )}
    </div>
  );
}

function DetailBlock({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted">
        {label}
      </div>
      {children}
    </div>
  );
}

/* ==================================================================== */
/*  Replication tab — paper-vs-mine + full model grid                    */
/* ==================================================================== */
function ReplicationTab() {
  const best = summaryPayload.best;
  const ref = summaryPayload.paper_reference;
  const rows = modelsPayload.rows;

  // sort by total_profit desc, naive last
  const sorted = useMemo(() => {
    return [...rows].sort((a, b) => {
      const isNaiveA = a.model.startsWith("naive");
      const isNaiveB = b.model.startsWith("naive");
      if (isNaiveA !== isNaiveB) return isNaiveA ? 1 : -1;
      return (b.total_profit ?? -Infinity) - (a.total_profit ?? -Infinity);
    });
  }, [rows]);

  return (
    <div className="space-y-10">
      <SectionHeading>Replication Scorecard</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Methodological replication of Maciejowska, Nitka &amp; Weron (2019) on
        ERCOT North Hub, 2022-2025. Markets and currency differ from the paper —
        the table below anchors the reproduced results against the paper&apos;s
        Polish ARX best-row for context, not for direct numerical comparison.
      </p>

      {/* Headline cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Best model" value={best.model.replaceAll("_", " ")} sub={`T = ${best.window} days · X = ${best.x_cols.length ? best.x_cols.join(", ").replaceAll("_mean", "") : "none"}${best.mu != null ? ` · μ = ${best.mu.toFixed(2)}` : ""}`} />
        <Stat label="Total profit" value={fmtUsd(best.total_profit, 0)} sub="OOS, 1 MWh/h notional" tone={(best.total_profit ?? 0) >= 0 ? "positive" : "negative"} />
        <Stat label="Sharpe" value={fmtNum(best.sharpe, 2)} sub={`ann. return ${fmtPct(best.ann_return_pct, 2)}`} />
        <Stat label="Classification p" value={fmtPct(best.p, 1)} sub={`q₀ ${fmtPct(best.q0, 1)} · q₁ ${fmtPct(best.q1, 1)}`} />
      </div>

      {/* Paper anchor */}
      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-3 text-sm font-semibold tracking-tight">Paper anchor (Polish market, ARX_levels best row)</h3>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Row label="p (paper)" value={fmtPct(ref.best_polish_arx_p, 1)} mono />
          <Row label="π (PLN)" value={ref.best_polish_arx_profit_pln.toLocaleString()} mono />
          <Row label="VaR 5% (PLN)" value={ref.best_polish_arx_var5_pln.toLocaleString()} mono />
          <Row label="naive RT (PLN)" value={ref.naive_balancing_polish_profit_pln.toLocaleString()} mono />
        </div>
        <p className="mt-3 text-[11px] leading-5 text-muted">{ref.note}</p>
      </div>

      {/* Full model grid */}
      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-4 text-sm font-semibold tracking-tight">All configurations (sorted by total profit)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead className="border-b border-border text-[10px] uppercase tracking-wider text-muted">
              <tr>
                <Th>Model</Th>
                <Th>T</Th>
                <Th>X</Th>
                <Th>μ</Th>
                <Th align="right">p</Th>
                <Th align="right">q₀</Th>
                <Th align="right">q₁</Th>
                <Th align="right">π ($)</Th>
                <Th align="right">Sharpe</Th>
                <Th align="right">Max DD ($)</Th>
                <Th align="right">VaR 5%</Th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((r) => (
                <tr key={r.config_id} className="border-b border-border/40">
                  <Td mono>{r.model.replaceAll("_", " ")}</Td>
                  <Td mono>{r.window ?? "—"}</Td>
                  <Td mono>{r.x_cols.map((x) => x.replace("_mean", "")).join(",") || "—"}</Td>
                  <Td mono>{r.mu == null ? "—" : r.mu.toFixed(2)}</Td>
                  <Td align="right" mono>{fmtPct(r.p, 1)}</Td>
                  <Td align="right" mono>{fmtPct(r.q0, 1)}</Td>
                  <Td align="right" mono>{fmtPct(r.q1, 1)}</Td>
                  <Td align="right" mono>
                    <span className={(r.total_profit ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                      {fmtNum(r.total_profit, 0)}
                    </span>
                  </Td>
                  <Td align="right" mono>{fmtNum(r.sharpe, 2)}</Td>
                  <Td align="right" mono>{fmtNum(r.max_drawdown, 0)}</Td>
                  <Td align="right" mono>{fmtNum(r.var_5pct, 2)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <NotesBox>
        Profit, max drawdown, and 5% VaR are in $ on a 1-MWh-per-hour notional position
        (24 MWh/day). Sharpe is dollar-Sharpe annualized as μ/σ × √365. The naive-DA
        strategy earns 0 by construction — the relevant benchmark is naive-RT, which is
        always the worst-case competitor for any sign-prediction strategy.
      </NotesBox>
    </div>
  );
}

/* ==================================================================== */
/*  Equity Curve tab                                                     */
/* ==================================================================== */
function EquityTab() {
  const rows = equityPayload.rows;
  const best = summaryPayload.best;

  const chartData = useMemo(
    () =>
      rows.map((r) => ({
        date: r.date,
        eq_best: r.eq_best,
        eq_da: r.eq_da,
        eq_rt: r.eq_rt,
        eq_arx_levels: r.eq_arx_levels,
        eq_arx_spread: r.eq_arx_spread,
        eq_probit: r.eq_probit,
      })),
    [rows],
  );

  const dailyPnl = useMemo(
    () =>
      rows.map((r) => ({
        date: r.date,
        pnl: r.pnl_best ?? 0,
      })),
    [rows],
  );

  return (
    <div className="space-y-10">
      <SectionHeading>Equity Curve</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Cumulative $-P&amp;L over the out-of-sample window vs. the two naive baselines
        and one representative config per model type. The strategy notional is 1 MWh
        per hour committed either to DAM or RTM each hour; daily P&amp;L is the sum
        across the 24 hours, with $0.50/MWh charged whenever the strategy commits to
        RT.
      </p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Total profit" value={fmtUsd(best.total_profit, 0)} tone={(best.total_profit ?? 0) >= 0 ? "positive" : "negative"} />
        <Stat label="Ann. return ($)" value={fmtUsd(best.ann_return_dollars, 0)} sub={`${fmtPct(best.ann_return_pct, 2)} of notional`} />
        <Stat label="Sharpe" value={fmtNum(best.sharpe, 2)} />
        <Stat label="Max drawdown" value={fmtUsd(best.max_drawdown, 0)} tone="negative" sub={`Calmar ${fmtNum(best.calmar, 2)}`} />
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">Cumulative $-P&amp;L (best vs naive)</h3>
          <span className="font-mono text-[11px] text-muted">$ · daily</span>
        </div>
        <div className="h-80">
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 5, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="date"
                tick={{ fill: MUTED, fontSize: 11 }}
                tickFormatter={(d: string) => d.slice(0, 7)}
                interval={Math.max(0, Math.floor(chartData.length / 8) - 1)}
              />
              <YAxis tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(1)}k`} />
              <Tooltip
                contentStyle={{ background: "#0b1220", border: "1px solid #1f2937", fontSize: 12 }}
                labelStyle={{ color: "#cbd5e1" }}
                formatter={(v) => (v == null ? "—" : `$${(v as number).toFixed(0)}`)}
              />
              <Line type="monotone" dataKey="eq_best" stroke={ACCENT} strokeWidth={2} dot={false} name="Best model" />
              <Line type="monotone" dataKey="eq_rt" stroke={NEGATIVE} strokeWidth={1.4} dot={false} name="Naive RT" />
              <Line type="monotone" dataKey="eq_da" stroke={MUTED} strokeWidth={1.2} dot={false} strokeDasharray="4 3" name="Naive DA" />
              <ReferenceLine y={0} stroke="#1f2937" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-muted">
          <Legend swatch={ACCENT} label="Best model" />
          <Legend swatch={NEGATIVE} label="Naive RT (always commit to real-time)" />
          <Legend swatch={MUTED} label="Naive DA (always day-ahead, equity = 0)" />
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">Daily P&amp;L (best model)</h3>
          <span className="font-mono text-[11px] text-muted">$ · per day</span>
        </div>
        <div className="h-56">
          <ResponsiveContainer>
            <BarChart data={dailyPnl} margin={{ top: 5, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(d: string) => d.slice(0, 7)} interval={Math.max(0, Math.floor(dailyPnl.length / 8) - 1)} />
              <YAxis tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(v: number) => `$${v.toFixed(0)}`} />
              <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2937", fontSize: 12 }} labelStyle={{ color: "#cbd5e1" }} formatter={(v) => `$${(v as number).toFixed(2)}`} />
              <Bar dataKey="pnl" fill={ACCENT} />
              <ReferenceLine y={0} stroke="#475569" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">Model-type comparison (one config per model)</h3>
          <span className="font-mono text-[11px] text-muted">cumulative $-P&amp;L</span>
        </div>
        <div className="h-72">
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 5, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="date" tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(d: string) => d.slice(0, 7)} interval={Math.max(0, Math.floor(chartData.length / 8) - 1)} />
              <YAxis tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(v: number) => `$${(v / 1000).toFixed(1)}k`} />
              <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2937", fontSize: 12 }} labelStyle={{ color: "#cbd5e1" }} formatter={(v) => (v == null ? "—" : `$${(v as number).toFixed(0)}`)} />
              <Line type="monotone" dataKey="eq_arx_levels" stroke={ACCENT} strokeWidth={1.6} dot={false} name="ARX levels" />
              <Line type="monotone" dataKey="eq_arx_spread" stroke={PURPLE} strokeWidth={1.6} dot={false} name="ARX spread" />
              <Line type="monotone" dataKey="eq_probit" stroke={AMBER} strokeWidth={1.6} dot={false} name="Probit (μ=0.5)" />
              <Line type="monotone" dataKey="eq_rt" stroke={NEGATIVE} strokeWidth={1.2} dot={false} strokeDasharray="4 3" name="Naive RT" />
              <ReferenceLine y={0} stroke="#1f2937" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-muted">
          <Legend swatch={ACCENT} label="ARX levels" />
          <Legend swatch={PURPLE} label="ARX spread" />
          <Legend swatch={AMBER} label="Probit (μ=0.5)" />
          <Legend swatch={NEGATIVE} label="Naive RT (dashed)" />
        </div>
      </div>
    </div>
  );
}

/* ==================================================================== */
/*  Decisions tab                                                         */
/* ==================================================================== */
function DecisionsTab() {
  const rows = decisionsPayload.rows;
  const totals = useMemo(() => {
    const n = rows.length;
    const da = rows.filter((r) => r.y_hat === 0).length;
    const rt = rows.filter((r) => r.y_hat === 1).length;
    const correct = rows.filter((r) => r.correct === 1).length;
    return { n, da, rt, correct };
  }, [rows]);

  // 12-column calendar grid: group by (year, week-of-year)
  const weeks = useMemo(() => {
    const map = new Map<string, typeof rows>();
    rows.forEach((r) => {
      const d = new Date(r.date);
      const onejan = new Date(d.getFullYear(), 0, 1);
      const w = Math.ceil(((d.getTime() - onejan.getTime()) / 86400000 + onejan.getDay() + 1) / 7);
      const key = `${d.getFullYear()}-${String(w).padStart(2, "0")}`;
      const arr = map.get(key) ?? [];
      arr.push(r);
      map.set(key, arr);
    });
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [rows]);

  return (
    <div className="space-y-10">
      <SectionHeading>Decisions</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Every day in the OOS window the best model picks DA (commit to day-ahead) or
        RT (commit to real-time). Green = correct sign call · red = wrong call. When
        the model and the realized spread agree, the strategy collects the spread
        minus the $0.50/MWh switching cost.
      </p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Total OOS days" value={String(totals.n)} />
        <Stat label="Picked DA" value={String(totals.da)} sub={fmtPct(totals.da / totals.n, 1)} />
        <Stat label="Picked RT" value={String(totals.rt)} sub={fmtPct(totals.rt / totals.n, 1)} />
        <Stat label="Correct sign" value={String(totals.correct)} sub={fmtPct(totals.correct / totals.n, 1)} tone={totals.correct / totals.n > 0.5 ? "positive" : "negative"} />
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">Daily calendar — picked DA vs RT, correct vs wrong</h3>
          <span className="font-mono text-[11px] text-muted">{decisionsPayload.best_config_id}</span>
        </div>
        <div className="overflow-x-auto">
          <div className="flex gap-px">
            {weeks.map(([wkey, days]) => (
              <div key={wkey} className="flex flex-col gap-px">
                {days.map((d) => {
                  const color = d.correct
                    ? d.y_hat === 1
                      ? "#10b981"
                      : "#34d399"
                    : "#f43f5e";
                  return (
                    <div
                      key={d.date}
                      className="h-2.5 w-2.5"
                      style={{ background: color }}
                      title={`${d.date} · ${d.y_hat === 1 ? "RT" : "DA"} · ${d.correct ? "✓" : "✗"} · spread $${d.spread.toFixed(2)}`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-muted">
          <Legend swatch="#10b981" label="Correct, picked RT" />
          <Legend swatch="#34d399" label="Correct, picked DA" />
          <Legend swatch="#f43f5e" label="Wrong sign call" />
        </div>
      </div>
    </div>
  );
}

/* ==================================================================== */
/*  Sensitivity tab                                                      */
/* ==================================================================== */
function SensitivityTab() {
  const cost = sensitivityPayload.cost_sweep;
  const thr = sensitivityPayload.threshold_sweep;

  const thrByMu = useMemo(() => {
    const m = new Map<number, typeof thr>();
    thr.forEach((r) => {
      const arr = m.get(r.mu) ?? [];
      arr.push(r);
      m.set(r.mu, arr);
    });
    return Array.from(m.entries()).sort(([a], [b]) => a - b);
  }, [thr]);

  return (
    <div className="space-y-10">
      <SectionHeading>Sensitivity</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Two robustness checks: (1) how the headline strategy responds to wider or
        tighter trading-cost assumptions, and (2) how the probit threshold μ trades
        accuracy on each side of the decision rule. Paper finding (Sec 4): μ &lt; 0.5
        increases profit because the unconditional Pr(spread &gt; 0) is &lt; 0.5 in
        their data — same expected here.
      </p>

      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-4 text-sm font-semibold tracking-tight">
          Trading-cost sweep (best config)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead className="border-b border-border text-[10px] uppercase tracking-wider text-muted">
              <tr>
                <Th align="right">Cost ($/MWh)</Th>
                <Th align="right">Total profit</Th>
                <Th align="right">Ann. return %</Th>
                <Th align="right">Sharpe</Th>
                <Th align="right">Max DD</Th>
              </tr>
            </thead>
            <tbody>
              {cost.map((r) => (
                <tr key={r.cost} className="border-b border-border/40">
                  <Td align="right" mono>${r.cost.toFixed(2)}</Td>
                  <Td align="right" mono>
                    <span className={(r.total_profit ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                      {fmtUsd(r.total_profit, 0)}
                    </span>
                  </Td>
                  <Td align="right" mono>{fmtPct(r.ann_return_pct, 2)}</Td>
                  <Td align="right" mono>{fmtNum(r.sharpe, 2)}</Td>
                  <Td align="right" mono>{fmtUsd(r.max_drawdown, 0)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-4 text-sm font-semibold tracking-tight">
          Probit threshold μ sweep (across all probit configs)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead className="border-b border-border text-[10px] uppercase tracking-wider text-muted">
              <tr>
                <Th>Config</Th>
                <Th align="right">μ</Th>
                <Th align="right">p</Th>
                <Th align="right">q₀</Th>
                <Th align="right">q₁</Th>
                <Th align="right">Total profit</Th>
                <Th align="right">Sharpe</Th>
              </tr>
            </thead>
            <tbody>
              {thrByMu.map(([mu, group]) =>
                group.map((r) => (
                  <tr key={`${r.config_id}_${mu}`} className="border-b border-border/40">
                    <Td mono>{r.config_id.replace("probit__", "")}</Td>
                    <Td align="right" mono>{r.mu.toFixed(2)}</Td>
                    <Td align="right" mono>{fmtPct(r.p, 1)}</Td>
                    <Td align="right" mono>{fmtPct(r.q0, 1)}</Td>
                    <Td align="right" mono>{fmtPct(r.q1, 1)}</Td>
                    <Td align="right" mono>
                      <span className={(r.total_profit ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}>
                        {fmtUsd(r.total_profit, 0)}
                      </span>
                    </Td>
                    <Td align="right" mono>{fmtNum(r.sharpe, 2)}</Td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ==================================================================== */
/*  Methodology tab                                                       */
/* ==================================================================== */
function MethodologyTab() {
  const meta = metadataPayload;

  return (
    <div className="space-y-10">
      <SectionHeading>Methodology</SectionHeading>

      <div className="space-y-6 text-sm leading-7 text-muted">
        <p>
          Following Maciejowska, Nitka &amp; Weron (2019) Sec. 3, the daily decision
          variable is{" "}
          <code className="font-mono text-[12px] text-foreground">Y_t = 1{`{P¹_t > P⁰_t}`}</code>{" "}
          — sell in real-time when the realized spread is positive, otherwise sell
          day-ahead. The agent does not know{" "}
          <code className="font-mono text-[12px] text-foreground">ΔP_t</code> in advance,
          so the decision is based on a forecast{" "}
          <code className="font-mono text-[12px] text-foreground">ΔP̂_t</code> from
          information available on day{" "}
          <code className="font-mono text-[12px] text-foreground">t-1</code>.
        </p>
        <div className="rounded-lg border border-border bg-card/50 p-4 font-mono text-[12px] leading-6 text-foreground">
          <div>ARX_levels: P⁰_t = αD_t + βX_t + Σ θ_i P⁰_(t-i) + ε_t</div>
          <div>             P¹_t = αD_t + βX_t + Σ θ_i P¹_(t-i) + γ P⁰_(t-1) + ε_t</div>
          <div>             ΔP̂_t = P̂¹_t − P̂⁰_t</div>
          <div className="mt-2">ARX_spread: ΔP_t = αD_t + βX_t + Σ θ_i ΔP_(t-i) + γ P⁰_(t-1) + ε_t</div>
          <div className="mt-2">Probit:     Pr(Y_t = 1) = Φ(αD_t + βX_t + Σ θ_i ΔP_(t-i) + γ P⁰_(t-1))</div>
          <div className="mt-2">Decision (ARX):    Ŷ_t = 1{`{ΔP̂_t > 0}`}</div>
          <div>Decision (Probit): Ŷ_t = 1{`{Φ > μ}`}</div>
          <div className="mt-2">Daily P&amp;L:  π_t = Ŷ_t · (ΔP_t − cost)</div>
        </div>
        <p>
          Walk-forward: for every OOS day{" "}
          <code className="font-mono text-[12px] text-foreground">t</code>, the model
          is refit on the trailing T calendar days{" "}
          <code className="font-mono text-[12px] text-foreground">[t-T, t-1]</code>{" "}
          and used to forecast day t. Calibration window T cycles through{" "}
          {pipelinePayload.scope.calibration_windows.join(", ")} days. Probit thresholds
          μ ∈ {`{${pipelinePayload.scope.thresholds.map((t) => t.toFixed(2)).join(", ")}}`}{" "}
          are applied post-fit.
        </p>
        <p>
          Deterministic dummies <code className="font-mono text-[12px] text-foreground">D_t</code>: const, Mon, Sat, Sun, Holiday (US federal). Lag set L = {`{2, 7}`} (paper&apos;s
          best-performing daily structure). Exogenous{" "}
          <code className="font-mono text-[12px] text-foreground">X_t</code>: subsets of{" "}
          {`{`}demand_fcst, wind, solar{`}`}.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-3 text-sm font-semibold tracking-tight">Data integrity</h3>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 text-sm">
          <Row label="First date" value={meta.data.first_date} mono />
          <Row label="Last date" value={meta.data.last_date} mono />
          <Row label="Hourly rows" value={meta.data.n_hourly_rows.toLocaleString()} mono />
          <Row label="Missing %" value={`${meta.data.missing_hours_pct.toFixed(2)}%`} mono />
        </div>
        <p className="mt-4 text-[12px] leading-6 text-muted">{meta.wind_solar_caveat}</p>
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-3 text-sm font-semibold tracking-tight">References</h3>
        <ul className="space-y-2 text-sm leading-6 text-muted">
          <li>
            Maciejowska, K., Nitka, W. &amp; Weron, T. (2019).{" "}
            <em>Day-Ahead vs. Intraday — Forecasting the Price Spread to Maximize Economic Benefits.</em>{" "}
            <span className="font-mono text-[11px]">Energies 12, 631. doi:10.3390/en12040631</span>
          </li>
          <li>
            ERCOT Public Reports — NP4-180-ER (DAM SPP), NP6-785-ER (RTM SPP).
          </li>
          <li>
            U.S. EIA-930 Hourly Electric Grid Monitor — respondent ERCO; series D
            (demand), DF (demand forecast), NG.WND, NG.SUN.
          </li>
          <li>
            <span className="font-mono text-[11px]">gridstatus</span> Python package
            for ERCOT data ingestion (MIT-licensed).
          </li>
        </ul>
      </div>
    </div>
  );
}

/* ==================================================================== */
/*  Shared atoms                                                         */
/* ==================================================================== */

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <span className="h-5 w-0.5 rounded-full bg-accent" />
      <h2 className="text-xl font-semibold tracking-tight">{children}</h2>
    </div>
  );
}

function Stat({
  label,
  value,
  sub,
  tone = "muted",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "positive" | "negative" | "muted";
}) {
  const valueClass =
    tone === "positive"
      ? "text-emerald-400"
      : tone === "negative"
        ? "text-rose-400"
        : "text-foreground";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted">{label}</div>
      <div className={`mt-2 text-xl font-semibold tracking-tight ${valueClass}`}>{value}</div>
      {sub && <div className="mt-1 text-[11px] text-muted">{sub}</div>}
    </div>
  );
}

function Row({
  label,
  value,
  sub,
  tone = "muted",
  mono,
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "positive" | "negative" | "muted";
  mono?: boolean;
}) {
  const valueClass =
    tone === "positive"
      ? "text-emerald-400"
      : tone === "negative"
        ? "text-rose-400"
        : "text-foreground";
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-muted">{label}</span>
      <span className="text-right">
        <span className={`${mono ? "font-mono" : ""} ${valueClass}`}>{value}</span>
        {sub && <span className="ml-2 font-mono text-[11px] text-muted">{sub}</span>}
      </span>
    </div>
  );
}

function Th({
  children,
  align = "left",
}: {
  children: React.ReactNode;
  align?: "left" | "right";
}) {
  return (
    <th className={`px-2 py-2 font-medium ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}

function Td({
  children,
  align = "left",
  mono,
}: {
  children: React.ReactNode;
  align?: "left" | "right";
  mono?: boolean;
}) {
  return (
    <td
      className={`px-2 py-2 ${align === "right" ? "text-right" : "text-left"} ${
        mono ? "font-mono" : ""
      }`}
    >
      {children}
    </td>
  );
}

function NotesBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card/50 p-4 text-[12px] leading-6 text-muted">
      <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted">
        Notes
      </div>
      {children}
    </div>
  );
}

function Legend({
  swatch,
  label,
  opacity = 1,
}: {
  swatch: string;
  label: string;
  opacity?: number;
}) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-2 w-3 rounded-sm" style={{ background: swatch, opacity }} />
      {label}
    </span>
  );
}
