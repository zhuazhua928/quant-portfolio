"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { projects } from "@/data/projects";
import { sessions, defaultSession, type Session } from "@/data/sessions";
import type { WatchlistData } from "@/data/watchlist";

import RegimeSummary from "@/app/watchlist/RegimeSummary";
import RankedTable from "@/app/watchlist/RankedTable";
import CandidatePanel from "@/app/watchlist/CandidatePanel";
import AlertFeed from "@/app/watchlist/AlertFeed";
import MiniChart from "@/app/watchlist/MiniChart";

const project = projects.find((p) => p.slug === "intraday-regime-monitor")!;
const WATCHLIST_SYMBOLS = ["TSLA", "NVDA", "PLTR", "MU", "HOOD", "AMD"];

const TABS = ["Overview", "Logic", "Dashboard", "Alerts", "Notes"] as const;
type Tab = (typeof TABS)[number];

export default function CustomPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Overview");
  const [activeSession, setActiveSession] = useState<Session>(defaultSession);

  const sessionData = activeSession.data;
  const { regime, ranking, symbols, charts, alerts } = sessionData;
  const symbolMap = useMemo(
    () => Object.fromEntries(symbols.map((s) => [s.symbol, s])),
    [symbols],
  );

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
        <div className="mx-auto flex max-w-6xl gap-0 px-6">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`relative px-4 py-3 text-sm transition-colors duration-200 ${
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

      {/* Tab content */}
      <div className="mx-auto max-w-6xl px-6 py-12">
        {activeTab === "Overview" && <OverviewTab />}
        {activeTab === "Logic" && <LogicTab />}
        {activeTab === "Dashboard" && (
          <DashboardTab
            session={activeSession}
            sessions={sessions}
            onSessionChange={setActiveSession}
            regime={regime}
            ranking={ranking}
            symbolMap={symbolMap}
            charts={charts}
          />
        )}
        {activeTab === "Alerts" && <AlertsTab alerts={alerts} scanDate={sessionData.scanDate} />}
        {activeTab === "Notes" && <NotesTab />}
      </div>
    </>
  );
}

/* ------------------------------------------------------------------ */
/* Overview tab                                                        */
/* ------------------------------------------------------------------ */
function OverviewTab() {
  return (
    <div className="grid gap-14 md:grid-cols-3">
      <div className="md:col-span-2 space-y-10">
        <div>
          <SectionHeading>Overview</SectionHeading>
          <p className="text-base leading-7 text-muted">{project.summary}</p>
        </div>
        {project.sections.slice(0, 3).map((section) => (
          <div key={section.title}>
            <h2 className="mb-3 text-lg font-semibold tracking-tight">
              {section.title}
            </h2>
            <p className="text-sm leading-7 text-muted">{section.content}</p>
          </div>
        ))}
      </div>
      <div>
        <div className="sticky top-32 rounded-lg border border-border bg-card p-6 shadow-sm">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
            Key Highlights
          </h3>
          <ul className="mt-4 space-y-3">
            {project.highlights.map((h) => (
              <li key={h} className="flex items-start gap-3 text-sm text-muted">
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                {h}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Logic tab                                                           */
/* ------------------------------------------------------------------ */
function LogicTab() {
  return (
    <div className="max-w-3xl space-y-10">
      {project.sections.map((section) => (
        <div key={section.title}>
          <h2 className="mb-3 text-lg font-semibold tracking-tight">
            {section.title}
          </h2>
          <p className="text-sm leading-7 text-muted">{section.content}</p>
        </div>
      ))}

      {/* Factor weight table */}
      <div>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">
          Regime-Dependent Factor Weights
        </h2>
        <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-background">
                <th className="px-4 py-3 font-mono text-[10px] font-medium uppercase tracking-wider text-muted">
                  Factor
                </th>
                {["Bullish", "Bearish", "Mixed"].map((r) => (
                  <th
                    key={r}
                    className="px-4 py-3 text-right font-mono text-[10px] font-medium uppercase tracking-wider text-muted"
                  >
                    {r}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ["Excess Return", "22%", "22%", "12%"],
                ["Trend Quality", "15%", "15%", "15%"],
                ["Price vs VWAP", "15%", "15%", "10%"],
                ["MA Alignment", "15%", "15%", "10%"],
                ["ORB Direction", "10%", "10%", "20%"],
                ["RSI", "10%", "10%", "8%"],
                ["Relative Volume", "8%", "8%", "15%"],
                ["Cross Events", "5%", "5%", "10%"],
              ].map(([factor, ...vals]) => (
                <tr
                  key={factor}
                  className="border-b border-border/50 hover:bg-card-hover transition-colors"
                >
                  <td className="px-4 py-2.5 text-sm">{factor}</td>
                  {vals.map((v, i) => (
                    <td
                      key={i}
                      className="px-4 py-2.5 text-right font-mono text-sm"
                    >
                      {v}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dashboard tab — embeds the full watchlist dashboard                  */
/* ------------------------------------------------------------------ */

const REGIME_DOT: Record<string, string> = {
  bullish: "bg-emerald-500",
  bearish: "bg-red-500",
  mixed: "bg-amber-500",
};

function SessionSelector({
  sessions,
  active,
  onChange,
}: {
  sessions: Session[];
  active: Session;
  onChange: (s: Session) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {sessions.map((s) => {
        const isActive = s.id === active.id;
        return (
          <button
            key={s.id}
            onClick={() => onChange(s)}
            className={`group relative flex items-center gap-2 rounded-lg border px-3 py-2 text-left transition-all duration-200 ${
              isActive
                ? "border-accent bg-accent/5 shadow-sm"
                : "border-border bg-card hover:border-accent/40 hover:bg-card-hover"
            }`}
          >
            <span
              className={`h-2 w-2 flex-shrink-0 rounded-full ${REGIME_DOT[s.regime]}`}
            />
            <div className="min-w-0">
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-xs font-medium ${
                    isActive ? "text-foreground" : "text-muted group-hover:text-foreground"
                  }`}
                >
                  {s.label}
                </span>
                <span className="font-mono text-[10px] text-muted">
                  {s.date}
                </span>
              </div>
              <p className="mt-0.5 text-[11px] leading-tight text-muted/70">
                {s.description}
              </p>
            </div>
            {isActive && (
              <span className="absolute -top-px left-3 right-3 h-0.5 rounded-b bg-accent" />
            )}
          </button>
        );
      })}
    </div>
  );
}

interface DashboardTabProps {
  session: Session;
  sessions: Session[];
  onSessionChange: (s: Session) => void;
  regime: WatchlistData["regime"];
  ranking: WatchlistData["ranking"];
  symbolMap: Record<string, WatchlistData["symbols"][number]>;
  charts: WatchlistData["charts"];
}

function DashboardTab({
  session,
  sessions: allSessions,
  onSessionChange,
  regime,
  ranking,
  symbolMap,
  charts,
}: DashboardTabProps) {
  return (
    <div className="space-y-8">
      {/* Session header + selector */}
      <div>
        <p className="mb-1 font-mono text-[10px] font-medium uppercase tracking-widest text-muted">
          Session Viewer
        </p>
        <p className="mb-4 text-sm text-muted">
          Replay the monitoring dashboard for selected trading sessions.
          Each session shows the regime classification, watchlist ranking,
          and intraday signals as captured at end of day.
        </p>
        <SessionSelector
          sessions={allSessions}
          active={session}
          onChange={onSessionChange}
        />
      </div>

      {/* Active session date */}
      <div className="flex items-center gap-3">
        <span
          className={`h-2.5 w-2.5 rounded-full ${REGIME_DOT[session.regime]}`}
        />
        <div>
          <span className="text-sm font-medium text-foreground">
            {session.label}
          </span>
          <span className="mx-2 text-muted/40">|</span>
          <span className="font-mono text-sm text-muted">{session.date}</span>
        </div>
      </div>

      <RegimeSummary regime={regime} />

      <div>
        <SubLabel>Ranked Watchlist</SubLabel>
        <RankedTable ranked={ranking.ranked} symbolMap={symbolMap} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <SubLabel>Bullish Candidates</SubLabel>
          <CandidatePanel
            items={ranking.topBullish}
            symbolMap={symbolMap}
            kind="bullish"
          />
        </div>
        <div>
          <SubLabel>Bearish Weakness Candidates</SubLabel>
          <CandidatePanel
            items={ranking.topBearish}
            symbolMap={symbolMap}
            kind="bearish"
          />
        </div>
      </div>

      <div>
        <SubLabel>Intraday Price Action</SubLabel>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {WATCHLIST_SYMBOLS.map((sym) => (
            <MiniChart
              key={sym}
              symbol={sym}
              data={charts[sym] ?? []}
              features={symbolMap[sym]}
            />
          ))}
        </div>
      </div>

      {/* Footer note */}
      <p className="border-t border-border/50 pt-4 text-center text-[11px] text-muted/60">
        Replayable session viewer — curated sessions representing different market regimes
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Alerts tab                                                          */
/* ------------------------------------------------------------------ */
function AlertsTab({ alerts, scanDate }: { alerts: WatchlistData["alerts"]; scanDate: string }) {
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <SectionHeading>Alert Feed</SectionHeading>
        <p className="text-sm leading-7 text-muted">
          The system generates severity-prioritized alerts for actionable
          intraday events. Alerts below are from the{" "}
          <span className="font-mono font-medium text-foreground">{scanDate}</span>{" "}
          session, sorted by severity: high (large moves, cross events), medium
          (ORB breakouts, extreme RSI), and low (elevated volume).
        </p>
      </div>
      <AlertFeed alerts={alerts} />
      <div>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">
          Alert Types
        </h2>
        <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-background">
                <th className="px-4 py-3 font-mono text-[10px] font-medium uppercase tracking-wider text-muted">
                  Type
                </th>
                <th className="px-4 py-3 font-mono text-[10px] font-medium uppercase tracking-wider text-muted">
                  Trigger Condition
                </th>
                <th className="px-4 py-3 font-mono text-[10px] font-medium uppercase tracking-wider text-muted">
                  Severity
                </th>
              </tr>
            </thead>
            <tbody>
              {[
                ["MOVE", "DTD return > 2%", "High"],
                ["CROSS", "Golden or death cross (MA10/MA20)", "High"],
                ["ORB", "Price above or below opening range", "Medium"],
                ["RSI", "RSI > 70 (overbought) or < 30 (oversold)", "Medium"],
                ["VOL", "Relative volume > 1.3x average", "Low"],
              ].map(([type, trigger, sev]) => (
                <tr
                  key={type}
                  className="border-b border-border/50 hover:bg-card-hover transition-colors"
                >
                  <td className="px-4 py-2.5 font-mono font-medium">
                    {type}
                  </td>
                  <td className="px-4 py-2.5 text-muted">{trigger}</td>
                  <td className="px-4 py-2.5 text-muted">{sev}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Notes tab                                                           */
/* ------------------------------------------------------------------ */
function NotesTab() {
  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <SectionHeading>Design Decisions</SectionHeading>
        <ul className="mt-4 space-y-3 text-sm leading-7 text-muted">
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            Regime classification uses a weighted scoring approach rather than
            ML classification to maintain interpretability and avoid overfitting
            to limited intraday training data.
          </li>
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            Factor weights shift by regime rather than using a single static
            model. In mixed regimes, breakout potential and volume conviction
            receive higher weight to surface stocks resolving their ranges.
          </li>
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            The system is framed as decision support rather than automated
            execution. Rankings and alerts inform discretionary trading
            decisions rather than generating orders directly.
          </li>
        </ul>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">
          Next Steps
        </h2>
        <ul className="space-y-3 text-sm leading-7 text-muted">
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            Continuous polling mode with scheduled scan intervals during market
            hours for real-time monitoring.
          </li>
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            Historical regime classification backtesting to validate regime
            labels against realized session outcomes.
          </li>
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            Integration of options flow and implied volatility signals into
            the regime and ranking models.
          </li>
          <li className="flex items-start gap-3">
            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
            Alert delivery via webhook or push notification for mobile
            monitoring during trading sessions.
          </li>
        </ul>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold tracking-tight">
          Technical Stack
        </h2>
        <div className="flex flex-wrap gap-2">
          {[
            "Python",
            "pandas",
            "NumPy",
            "Alpaca API",
            "Next.js",
            "TypeScript",
            "Recharts",
            "Tailwind CSS",
          ].map((t) => (
            <span
              key={t}
              className="rounded bg-card border border-border px-2.5 py-1 font-mono text-[11px] text-muted"
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Shared components                                                   */
/* ------------------------------------------------------------------ */
function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <span className="h-5 w-0.5 rounded-full bg-accent" />
      <h2 className="text-xl font-semibold tracking-tight">{children}</h2>
    </div>
  );
}

function SubLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-4 flex items-center gap-3">
      <span className="h-4 w-0.5 rounded-full bg-accent" />
      <h3 className="text-sm font-semibold tracking-tight">{children}</h3>
    </div>
  );
}
