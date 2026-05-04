"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Area,
  AreaChart,
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
  energyCurve,
  energyPrices,
  energyStorage,
  energySummary,
  type EnergyPriceRow,
  type ForwardContract,
} from "@/data/energy";

const project = projects.find((p) => p.slug === "energy-trading-dashboard")!;

const TABS = ["Snapshot", "Forward Curve & Spreads", "Storage & Fundamentals"] as const;
type Tab = (typeof TABS)[number];

const POSITIVE = "#10b981";
const NEGATIVE = "#f43f5e";
const ACCENT = "#3b82f6";
const MUTED = "#94a3b8";

const fmtPrice = (n: number | null | undefined, digits = 3) =>
  n == null ? "—" : `$${n.toFixed(digits)}`;
const fmtPct = (n: number | null | undefined, digits = 2) =>
  n == null ? "—" : `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`;
const fmtBcf = (n: number | null | undefined) =>
  n == null ? "—" : `${n.toLocaleString(undefined, { maximumFractionDigits: 0 })} Bcf`;

export default function CustomPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Snapshot");

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
        {activeTab === "Snapshot" && <SnapshotTab />}
        {activeTab === "Forward Curve & Spreads" && <CurveTab />}
        {activeTab === "Storage & Fundamentals" && <StorageTab />}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Snapshot tab                                                       */
/* ------------------------------------------------------------------ */
function SnapshotTab() {
  const fm = energySummary.front_month;
  const contango = energySummary.curve.contango;
  const storage = energySummary.storage;

  const last30 = useMemo(() => energyPrices.slice(-30), []);
  const dayUp = (fm?.change_d_pct ?? 0) >= 0;

  return (
    <div className="space-y-10">
      <SectionHeading>Snapshot</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Henry Hub ({fm?.ticker ?? "NG=F"}) front-month NYMEX natural gas futures, daily close
        from yfinance. The forward curve is built from dated NYMEX contracts (NG{`{M}{YY}`}.NYM)
        for the next 18 delivery months. Calendar spreads and storage analytics on the
        Forward Curve and Storage tabs.
      </p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat
          label="Front-month close"
          value={fmtPrice(fm?.close ?? null, 3)}
          sub={fm ? `as of ${fm.asof}` : undefined}
        />
        <Stat
          label="Day Δ"
          value={fmtPct(fm?.change_d_pct ?? null)}
          sub={fm?.change_d != null ? fmtPrice(fm.change_d, 3) : undefined}
          tone={dayUp ? "positive" : "negative"}
        />
        <Stat
          label="Week Δ"
          value={fmtPct(fm?.change_w_pct ?? null)}
          tone={(fm?.change_w_pct ?? 0) >= 0 ? "positive" : "negative"}
        />
        <Stat
          label="30-day realized vol"
          value={
            fm?.vol_30d_annualized == null
              ? "—"
              : `${(fm.vol_30d_annualized * 100).toFixed(1)}%`
          }
          sub="annualized"
        />
      </div>

      {/* 30-day price chart */}
      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">
            Front-month — last 30 trading days
          </h3>
          <span className="font-mono text-[11px] text-muted">$/MMBtu</span>
        </div>
        <div className="h-64">
          <ResponsiveContainer>
            <LineChart data={last30} margin={{ top: 5, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="date"
                tick={{ fill: MUTED, fontSize: 11 }}
                tickFormatter={(d: string) => d.slice(5)}
                interval={Math.max(0, Math.floor(last30.length / 8) - 1)}
              />
              <YAxis
                tick={{ fill: MUTED, fontSize: 11 }}
                domain={["auto", "auto"]}
                tickFormatter={(v: number) => v.toFixed(2)}
              />
              <Tooltip
                contentStyle={{
                  background: "#0b1220",
                  border: "1px solid #1f2937",
                  fontSize: 12,
                }}
                labelStyle={{ color: "#cbd5e1" }}
                formatter={(v) => [`$${(v as number).toFixed(3)}`, "Close"]}
              />
              <Line
                type="monotone"
                dataKey="close"
                stroke={ACCENT}
                strokeWidth={1.8}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Mini panels: curve summary + storage tile */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="mb-3 text-sm font-semibold tracking-tight">Curve shape</h3>
          <div className="space-y-2 text-sm">
            <Row
              label="Front (M1)"
              value={fmtPrice(contango.m1, 3)}
            />
            <Row
              label="Second (M2)"
              value={fmtPrice(contango.m2, 3)}
            />
            <Row
              label="M2 − M1"
              value={contango.spread == null ? "—" : `$${contango.spread >= 0 ? "+" : ""}${contango.spread.toFixed(3)}`}
              tone={(contango.spread ?? 0) >= 0 ? "muted" : "negative"}
            />
            <Row
              label="Shape"
              value={contango.label}
              tone={contango.label === "contango" ? "muted" : contango.label === "backwardation" ? "positive" : "muted"}
            />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="mb-3 text-sm font-semibold tracking-tight">Storage (EIA)</h3>
          {!storage.available ? (
            <EmptyEIAState />
          ) : (
            <div className="space-y-2 text-sm">
              <Row label="Latest" value={fmtBcf(storage.latest)} sub={storage.asof ? `week ending ${storage.asof}` : undefined} />
              <Row
                label="Weekly Δ"
                value={
                  storage.weekly_change == null
                    ? "—"
                    : `${storage.weekly_change.delta >= 0 ? "+" : ""}${storage.weekly_change.delta.toFixed(0)} Bcf (${storage.weekly_change.label})`
                }
                tone={storage.weekly_change?.label === "build" ? "positive" : "negative"}
              />
              <Row
                label="YoY Δ"
                value={
                  storage.yoy == null
                    ? "—"
                    : `${storage.yoy.delta >= 0 ? "+" : ""}${storage.yoy.delta.toFixed(0)} Bcf`
                }
                sub={storage.yoy?.pct == null ? undefined : `${storage.yoy.pct >= 0 ? "+" : ""}${storage.yoy.pct.toFixed(1)}%`}
              />
              <Row
                label="z vs 5-yr avg (same week)"
                value={storage.zscore == null ? "—" : storage.zscore.toFixed(2)}
              />
            </div>
          )}
        </div>
      </div>

      <NotesBox>
        Front-month price + history sourced from yfinance ({"NG=F"}). Spot price + storage
        report sourced from the U.S. Energy Information Administration (series {"NG.RNGWHHD.D"}{" "}
        and {"NG.NW2_EPG0_SWO_R48_BCF.W"}). Pre-built JSON pipeline; rerun{" "}
        <code className="font-mono text-[12px] text-foreground">python -m energy.pipeline.run</code>{" "}
        to refresh.
      </NotesBox>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Forward curve tab                                                  */
/* ------------------------------------------------------------------ */
function CurveTab() {
  const contracts = energyCurve.contracts;
  const contango = energyCurve.contango;
  const widow = energyCurve.widow_maker;
  const winter = energyCurve.winter_strip;
  const sw = energyCurve.summer_winter;

  const data = contracts.map((c: ForwardContract) => ({
    label: c.expiry_label,
    close: c.close,
  }));

  return (
    <div className="space-y-10">
      <SectionHeading>Forward Curve & Spreads</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        The natural gas forward curve is the canonical seasonal asset in commodity markets:
        Nov–Mar contracts trade at a premium to shoulder months because winter heating demand
        depletes storage. The H–J spread (March vs. April) is the &ldquo;widow-maker&rdquo;
        — a long position pays off if a late-winter cold snap forces storage withdrawals
        right at the heating-season tail.
      </p>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">
            Forward curve — next {contracts.length} delivery months
          </h3>
          <span className="font-mono text-[11px] text-muted">$/MMBtu</span>
        </div>
        <div className="h-72">
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 5, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="label"
                tick={{ fill: MUTED, fontSize: 11 }}
                interval={0}
                angle={-30}
                textAnchor="end"
                height={50}
              />
              <YAxis
                tick={{ fill: MUTED, fontSize: 11 }}
                domain={["auto", "auto"]}
                tickFormatter={(v: number) => v.toFixed(2)}
              />
              <Tooltip
                contentStyle={{
                  background: "#0b1220",
                  border: "1px solid #1f2937",
                  fontSize: 12,
                }}
                labelStyle={{ color: "#cbd5e1" }}
                formatter={(v) => [`$${(v as number).toFixed(3)}`, "Close"]}
              />
              <Line
                type="monotone"
                dataKey="close"
                stroke={ACCENT}
                strokeWidth={1.8}
                dot={{ r: 2.5, fill: ACCENT }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Curve shape"
          value={contango.label}
          sub={
            contango.spread == null
              ? undefined
              : `M2 − M1 = $${contango.spread >= 0 ? "+" : ""}${contango.spread.toFixed(3)}`
          }
        />
        <Stat
          label={`H–J ${widow ? widow.year : ""} (Mar−Apr)`}
          value={
            widow == null
              ? "—"
              : `$${widow.spread >= 0 ? "+" : ""}${widow.spread.toFixed(3)}`
          }
          sub="widow-maker"
          tone={(widow?.spread ?? 0) >= 0 ? "positive" : "negative"}
        />
        <Stat
          label="Winter strip"
          value={winter == null ? "—" : `$${winter.average.toFixed(3)}`}
          sub={winter ? `${winter.contracts[0]} – ${winter.contracts[winter.contracts.length - 1]}` : undefined}
        />
        <Stat
          label="Summer–winter Δ"
          value={
            sw == null
              ? "—"
              : `$${sw.diff >= 0 ? "+" : ""}${sw.diff.toFixed(3)}`
          }
          sub={sw ? `winter ${sw.winter_avg.toFixed(2)} vs summer ${sw.summer_avg.toFixed(2)}` : undefined}
        />
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <h3 className="mb-3 text-sm font-semibold tracking-tight">Contracts</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border text-[11px] uppercase tracking-wider text-muted">
              <tr>
                <Th>Symbol</Th>
                <Th>Delivery</Th>
                <Th align="right">Close ($/MMBtu)</Th>
                <Th align="right">Δ vs M1</Th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((c: ForwardContract, i: number) => {
                const m1 = contracts[0]?.close ?? c.close;
                const diff = c.close - m1;
                return (
                  <tr key={c.symbol} className="border-b border-border/40">
                    <Td mono>{c.symbol}</Td>
                    <Td>{c.expiry_label}</Td>
                    <Td align="right" mono>
                      ${c.close.toFixed(3)}
                    </Td>
                    <Td align="right" mono>
                      <span
                        className={
                          i === 0
                            ? "text-muted"
                            : diff >= 0
                              ? "text-emerald-400"
                              : "text-rose-400"
                        }
                      >
                        {i === 0 ? "—" : `${diff >= 0 ? "+" : ""}${diff.toFixed(3)}`}
                      </span>
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <NotesBox>
        Spreads computed from the latest available close of each contract. The widow-maker is
        only defined when both March and April contracts are present in the next 18 months
        of the curve. Winter strip averages the next five Nov–Mar contracts; summer–winter
        compares the next seven Apr–Oct contracts to those five.
      </NotesBox>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Storage tab                                                        */
/* ------------------------------------------------------------------ */
function StorageTab() {
  const storage = energyStorage;

  if (!storage.available) {
    return (
      <div className="space-y-10">
        <SectionHeading>Storage & Fundamentals</SectionHeading>
        <EmptyEIAState />
        <NotesBox>
          The weekly Lower-48 working gas storage report is the canonical fundamentals
          signal for U.S. natural gas. The page is wired up but the EIA fetch is gated on
          a free API key. Register at{" "}
          <a
            className="text-accent hover:underline"
            href="https://www.eia.gov/opendata/register.php"
            target="_blank"
            rel="noopener noreferrer"
          >
            eia.gov/opendata/register.php
          </a>{" "}
          and add <code className="font-mono text-[12px] text-foreground">EIA_API_KEY=...</code>{" "}
          to <code className="font-mono text-[12px] text-foreground">.env</code>, then rerun{" "}
          <code className="font-mono text-[12px] text-foreground">python -m energy.pipeline.run</code>.
        </NotesBox>
      </div>
    );
  }

  // Build the chart series: x = week_of_year, lines for current year, year-ago, 5-yr mean,
  // band for 5-yr min..max.
  const envByWeek = new Map(storage.envelope.map((e) => [e.week_of_year, e]));
  const weeks = Array.from({ length: 53 }, (_, i) => i + 1);

  const latestYear = storage.weekly.length > 0 ? storage.weekly[storage.weekly.length - 1].year : null;
  const currentRows = new Map(
    storage.weekly.filter((w) => w.year === latestYear).map((w) => [w.week_of_year, w.value]),
  );
  const yearAgoRows = new Map(
    storage.weekly
      .filter((w) => latestYear != null && w.year === latestYear - 1)
      .map((w) => [w.week_of_year, w.value]),
  );

  const chartData = weeks.map((w) => {
    const env = envByWeek.get(w);
    return {
      week: w,
      min: env?.min ?? null,
      max: env?.max ?? null,
      band: env ? env.max - env.min : null,
      mean: env?.mean ?? null,
      current: currentRows.get(w) ?? null,
      yearAgo: yearAgoRows.get(w) ?? null,
    };
  });

  return (
    <div className="space-y-10">
      <SectionHeading>Storage & Fundamentals</SectionHeading>
      <p className="text-sm leading-7 text-muted">
        Weekly Lower-48 working gas in underground storage from the EIA. The 5-year envelope
        (min–max band, mean line) is the standard reference for whether the market is
        supply-loose or supply-tight. A storage z-score &gt; +1 (above the 5-year band)
        typically pressures front-month prices; &lt; −1 means below average for that week of
        the year and supports prices.
      </p>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Latest" value={fmtBcf(storage.latest)} sub={storage.asof ?? undefined} />
        <Stat
          label="Weekly Δ"
          value={
            storage.weekly_change == null
              ? "—"
              : `${storage.weekly_change.delta >= 0 ? "+" : ""}${storage.weekly_change.delta.toFixed(0)} Bcf`
          }
          sub={storage.weekly_change?.label}
          tone={storage.weekly_change?.label === "build" ? "positive" : "negative"}
        />
        <Stat
          label="YoY Δ"
          value={
            storage.yoy == null
              ? "—"
              : `${storage.yoy.delta >= 0 ? "+" : ""}${storage.yoy.delta.toFixed(0)} Bcf`
          }
          sub={storage.yoy?.pct == null ? undefined : `${storage.yoy.pct >= 0 ? "+" : ""}${storage.yoy.pct.toFixed(1)}%`}
        />
        <Stat
          label="z vs 5-yr (same week)"
          value={storage.zscore == null ? "—" : storage.zscore.toFixed(2)}
          tone={
            storage.zscore == null
              ? "muted"
              : storage.zscore > 0.5
                ? "negative"
                : storage.zscore < -0.5
                  ? "positive"
                  : "muted"
          }
        />
      </div>

      <div className="rounded-lg border border-border bg-card p-5">
        <div className="mb-4 flex items-baseline justify-between">
          <h3 className="text-sm font-semibold tracking-tight">
            Working gas in storage — current year vs 5-year envelope
          </h3>
          <span className="font-mono text-[11px] text-muted">Bcf · week of year</span>
        </div>
        <div className="h-80">
          <ResponsiveContainer>
            <ComposedChart data={chartData} margin={{ top: 5, right: 12, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis
                dataKey="week"
                tick={{ fill: MUTED, fontSize: 11 }}
                ticks={[1, 9, 18, 27, 36, 45, 53]}
              />
              <YAxis
                tick={{ fill: MUTED, fontSize: 11 }}
                tickFormatter={(v: number) => `${(v / 1000).toFixed(1)}k`}
                domain={["auto", "auto"]}
              />
              <Tooltip
                contentStyle={{
                  background: "#0b1220",
                  border: "1px solid #1f2937",
                  fontSize: 12,
                }}
                labelStyle={{ color: "#cbd5e1" }}
                formatter={(v, name) => {
                  const key = name as string;
                  const label =
                    key === "current"
                      ? `Current (${latestYear ?? ""})`
                      : key === "yearAgo"
                        ? `Year ago (${(latestYear ?? 0) - 1})`
                        : key === "mean"
                          ? "5-yr mean"
                          : key === "min"
                            ? "5-yr min"
                            : key === "band"
                              ? "5-yr range"
                              : key;
                  const val = v as number | null;
                  return [val == null ? "—" : `${val.toFixed(0)} Bcf`, label];
                }}
                labelFormatter={(w) => `Week ${w}`}
              />
              {/* 5-yr min..max band drawn as stacked baseline + band */}
              <Area
                type="monotone"
                dataKey="min"
                stackId="env"
                stroke="transparent"
                fill="transparent"
              />
              <Area
                type="monotone"
                dataKey="band"
                stackId="env"
                stroke="transparent"
                fill={MUTED}
                fillOpacity={0.18}
              />
              <Line type="monotone" dataKey="mean" stroke={MUTED} strokeWidth={1.2} dot={false} strokeDasharray="4 3" />
              <Line type="monotone" dataKey="yearAgo" stroke="#a78bfa" strokeWidth={1.4} dot={false} />
              <Line type="monotone" dataKey="current" stroke={ACCENT} strokeWidth={2} dot={false} />
              <ReferenceLine y={0} stroke="#1f2937" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-[11px] text-muted">
          <Legend swatch={ACCENT} label={`Current ${latestYear ?? ""}`} />
          <Legend swatch="#a78bfa" label={`Year ago ${(latestYear ?? 0) - 1}`} />
          <Legend swatch={MUTED} label="5-yr mean (dashed)" />
          <Legend swatch={MUTED} label="5-yr min–max band" opacity={0.4} />
        </div>
      </div>

      <NotesBox>
        Source: U.S. EIA Weekly Natural Gas Storage Report (series{" "}
        <code className="font-mono text-[12px] text-foreground">NG.NW2_EPG0_SWO_R48_BCF.W</code>).
        Envelope computed as same-week-of-year (min, p25, mean, p75, max) over the prior five
        calendar years; the current year is excluded so the band is a true historical baseline.
        z-score uses the same-week historical std.
      </NotesBox>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Shared atoms                                                       */
/* ------------------------------------------------------------------ */

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
    <div className="flex items-baseline justify-between">
      <span className="text-muted">{label}</span>
      <span className="text-right">
        <span className={`font-mono ${valueClass}`}>{value}</span>
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

function EmptyEIAState() {
  return (
    <div className="text-sm text-muted">
      EIA storage data not loaded. Set{" "}
      <code className="font-mono text-[12px] text-foreground">EIA_API_KEY</code> in{" "}
      <code className="font-mono text-[12px] text-foreground">.env</code> and rerun the
      pipeline.
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
      <span
        className="h-2 w-3 rounded-sm"
        style={{ background: swatch, opacity }}
      />
      {label}
    </span>
  );
}

// suppress unused-import warning when the EnergyPriceRow type isn't otherwise referenced
export type { EnergyPriceRow };
