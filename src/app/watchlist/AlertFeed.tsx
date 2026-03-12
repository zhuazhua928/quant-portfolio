import type { Alert } from "@/data/watchlist";

const SEVERITY_STYLE: Record<string, { dot: string; bg: string }> = {
  high: { dot: "bg-red-500", bg: "bg-red-50 border-red-100" },
  medium: { dot: "bg-amber-500", bg: "bg-amber-50 border-amber-100" },
  low: { dot: "bg-slate-400", bg: "bg-slate-50 border-slate-100" },
};

const TYPE_LABEL: Record<string, string> = {
  cross: "CROSS",
  orb: "ORB",
  volume: "VOL",
  rsi: "RSI",
  move: "MOVE",
};

export default function AlertFeed({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-5 text-center text-xs text-muted shadow-sm">
        No alerts for this session.
      </div>
    );
  }

  // Sort by severity: high → medium → low
  const order = { high: 0, medium: 1, low: 2 };
  const sorted = [...alerts].sort(
    (a, b) => order[a.severity] - order[b.severity]
  );

  return (
    <div className="rounded-lg border border-border bg-card shadow-sm">
      <div className="divide-y divide-border/50">
        {sorted.map((alert, i) => {
          const style = SEVERITY_STYLE[alert.severity];
          return (
            <div
              key={i}
              className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-card-hover"
            >
              {/* Severity dot */}
              <span
                className={`mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full ${style.dot}`}
              />

              {/* Type badge */}
              <span
                className={`flex-shrink-0 rounded border px-1.5 py-0.5 font-mono text-[9px] font-medium uppercase ${style.bg}`}
              >
                {TYPE_LABEL[alert.type] ?? alert.type}
              </span>

              {/* Symbol */}
              <span className="flex-shrink-0 font-mono text-xs font-semibold">
                {alert.symbol}
              </span>

              {/* Message */}
              <span className="text-xs text-muted">{alert.message}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
