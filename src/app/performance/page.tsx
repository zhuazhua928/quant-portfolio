"use client";

import Section from "@/components/Section";
import MetricCard from "@/components/MetricCard";
import ChartContainer from "@/components/ChartContainer";
import { performanceData, summaryMetrics } from "@/data/performance";
import {
  ResponsiveContainer,
  LineChart,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

const chartMargin = { top: 5, right: 5, bottom: 5, left: 10 };

const axisStyle = {
  fontSize: 11,
  fill: "#64748b",
  fontFamily: "var(--font-geist-mono)",
};

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
}

// Sample every Nth point to keep charts clean
function sample<T>(data: T[], n: number): T[] {
  return data.filter((_, i) => i % n === 0);
}

export default function PerformancePage() {
  const equitySampled = sample(performanceData.equity, 5);
  const drawdownSampled = sample(performanceData.drawdown, 5);
  const rollingSampled = sample(performanceData.rolling, 5);
  const exposureSampled = sample(performanceData.exposure, 7);

  const metricEntries: { label: string; key: keyof typeof summaryMetrics }[] = [
    { label: "Total Return", key: "totalReturn" },
    { label: "Ann. Return", key: "annualizedReturn" },
    { label: "Ann. Volatility", key: "annualizedVol" },
    { label: "Sharpe Ratio", key: "sharpeRatio" },
    { label: "Sortino Ratio", key: "sortinoRatio" },
    { label: "Max Drawdown", key: "maxDrawdown" },
    { label: "Calmar Ratio", key: "calmarRatio" },
    { label: "Win Rate", key: "winRate" },
    { label: "Avg Win", key: "avgWin" },
    { label: "Avg Loss", key: "avgLoss" },
    { label: "Profit Factor", key: "profitFactor" },
    { label: "Avg Holding Period", key: "avgHoldingPeriod" },
  ];

  return (
    <>
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-accent">
            Performance
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Strategy Performance Dashboard
          </h1>
          <p className="mt-4 max-w-2xl text-base text-muted">
            Placeholder metrics and charts. All values below are simulated and
            will be replaced with actual strategy performance data.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Summary Metrics */}
      <Section title="Summary Statistics">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {metricEntries.map((m) => (
            <MetricCard
              key={m.key}
              label={m.label}
              value={summaryMetrics[m.key]}
            />
          ))}
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Charts */}
      <Section title="Equity & Drawdown">
        <div className="space-y-8">
          <ChartContainer title="Equity Curve">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equitySampled} margin={chartMargin}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={axisStyle}
                  interval={Math.floor(equitySampled.length / 6)}
                />
                <YAxis
                  tick={axisStyle}
                  tickFormatter={(v: number) =>
                    `${(v / 1000000).toFixed(2)}M`
                  }
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    fontFamily: "var(--font-geist-mono)",
                    borderColor: "#e2e8f0",
                    borderRadius: 6,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                  }}
                  formatter={(v) => [
                    `$${Number(v).toLocaleString()}`,
                    "Equity",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="equity"
                  stroke="#1e3a5f"
                  strokeWidth={1.5}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>

          <ChartContainer title="Drawdown">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={drawdownSampled} margin={chartMargin}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={axisStyle}
                  interval={Math.floor(drawdownSampled.length / 6)}
                />
                <YAxis
                  tick={axisStyle}
                  tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    fontFamily: "var(--font-geist-mono)",
                    borderColor: "#e2e8f0",
                    borderRadius: 6,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                  }}
                  formatter={(v) => [`${Number(v).toFixed(2)}%`, "Drawdown"]}
                />
                <Area
                  type="monotone"
                  dataKey="drawdown"
                  stroke="#dc2626"
                  fill="#dc2626"
                  fillOpacity={0.1}
                  strokeWidth={1.5}
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      <Section
        title="Rolling Metrics"
        subtitle="63-day rolling Sharpe ratio and annualized volatility."
      >
        <div className="space-y-8">
          <ChartContainer title="Rolling Sharpe Ratio (63d)">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rollingSampled} margin={chartMargin}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={axisStyle}
                  interval={Math.floor(rollingSampled.length / 6)}
                />
                <YAxis tick={axisStyle} />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    fontFamily: "var(--font-geist-mono)",
                    borderColor: "#e2e8f0",
                    borderRadius: 6,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="rollingSharpe"
                  stroke="#1e3a5f"
                  strokeWidth={1.5}
                  dot={false}
                  name="Sharpe"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>

          <ChartContainer title="Rolling Volatility (63d, Annualized)">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rollingSampled} margin={chartMargin}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="date"
                  tickFormatter={formatDate}
                  tick={axisStyle}
                  interval={Math.floor(rollingSampled.length / 6)}
                />
                <YAxis
                  tick={axisStyle}
                  tickFormatter={(v: number) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    fontFamily: "var(--font-geist-mono)",
                    borderColor: "#e2e8f0",
                    borderRadius: 6,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                  }}
                  formatter={(v) => [`${v}%`, "Vol"]}
                />
                <Line
                  type="monotone"
                  dataKey="rollingVol"
                  stroke="#7c3aed"
                  strokeWidth={1.5}
                  dot={false}
                  name="Vol"
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      <Section
        title="Exposure"
        subtitle="Long, short, and net exposure over time."
      >
        <ChartContainer title="Portfolio Exposure (%)">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={exposureSampled} margin={chartMargin}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={axisStyle}
                interval={Math.floor(exposureSampled.length / 6)}
              />
              <YAxis
                tick={axisStyle}
                tickFormatter={(v: number) => `${v}%`}
              />
              <Tooltip
                contentStyle={{
                  fontSize: 12,
                  fontFamily: "var(--font-geist-mono)",
                  borderColor: "#e2e8f0",
                    borderRadius: 6,
                    boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                }}
                formatter={(v) => [`${v}%`]}
              />
              <Line
                type="monotone"
                dataKey="longExposure"
                stroke="#059669"
                strokeWidth={1.5}
                dot={false}
                name="Long"
              />
              <Line
                type="monotone"
                dataKey="shortExposure"
                stroke="#dc2626"
                strokeWidth={1.5}
                dot={false}
                name="Short"
              />
              <Line
                type="monotone"
                dataKey="netExposure"
                stroke="#1e3a5f"
                strokeWidth={1.5}
                dot={false}
                name="Net"
                strokeDasharray="4 2"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      </Section>
    </>
  );
}
