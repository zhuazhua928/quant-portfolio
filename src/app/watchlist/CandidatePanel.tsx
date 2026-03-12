import type { RankedSymbol, SymbolFeatures } from "@/data/watchlist";

function pct(v: number | null): string {
  if (v == null) return "—";
  const s = (v * 100).toFixed(2);
  return v > 0 ? `+${s}%` : `${s}%`;
}

const FACTOR_LABELS: Record<string, string> = {
  excess_return: "Excess Ret",
  rsi: "RSI",
  price_vs_vwap: "vs VWAP",
  ma_alignment: "MA Align",
  relative_volume: "RVOL",
  cross_events: "Cross",
  trend_quality: "Trend",
  orb: "ORB",
};

interface Props {
  items: RankedSymbol[];
  symbolMap: Record<string, SymbolFeatures>;
  kind: "bullish" | "bearish";
}

export default function CandidatePanel({ items, symbolMap, kind }: Props) {
  const accent =
    kind === "bullish"
      ? { border: "border-emerald-200", bg: "bg-emerald-50", text: "text-emerald-700" }
      : { border: "border-red-200", bg: "bg-red-50", text: "text-red-700" };

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const s = symbolMap[item.symbol];
        const topFactors = Object.entries(item.factors)
          .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
          .slice(0, 4);

        return (
          <div
            key={item.symbol}
            className={`rounded-lg border ${accent.border} bg-card p-4 shadow-sm`}
          >
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-md ${accent.bg} font-mono text-[10px] font-bold ${accent.text}`}
                >
                  {item.rank}
                </span>
                <div>
                  <span className="font-mono text-sm font-semibold">
                    {item.symbol}
                  </span>
                  <span className="ml-2 font-mono text-xs text-muted">
                    {s?.last_price.toFixed(2)}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="font-mono text-xs font-semibold">
                  {item.score > 0 ? "+" : ""}
                  {item.score.toFixed(3)}
                </p>
                <p className="font-mono text-[10px] text-muted">score</p>
              </div>
            </div>

            {/* Metrics row */}
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 border-t border-border/50 pt-3">
              <Metric label="DTD" value={pct(s?.ret_dtd ?? null)} positive={(s?.ret_dtd ?? 0) > 0} />
              <Metric label="xs QQQ" value={pct(s?.ret_dtd_xs_qqq ?? null)} positive={(s?.ret_dtd_xs_qqq ?? 0) > 0} />
              <Metric label="RSI" value={s?.rsi != null ? s.rsi.toFixed(0) : "—"} />
              <Metric label="RVOL" value={s?.rvol != null ? `${s.rvol.toFixed(2)}x` : "—"} />
              <Metric label="ORB" value={s?.orb_status ?? "—"} />
            </div>

            {/* Factor bars */}
            <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
              {topFactors.map(([key, val]) => (
                <FactorBar
                  key={key}
                  label={FACTOR_LABELS[key] ?? key}
                  value={val}
                />
              ))}
            </div>

            {/* Explanation */}
            <p className="mt-3 text-[11px] leading-relaxed text-muted">
              {item.explanation}
            </p>
          </div>
        );
      })}
    </div>
  );
}

function Metric({
  label,
  value,
  positive,
}: {
  label: string;
  value: string;
  positive?: boolean;
}) {
  const color =
    positive === undefined
      ? "text-foreground"
      : positive
        ? "text-positive"
        : "text-negative";
  return (
    <div>
      <span className="font-mono text-[9px] uppercase tracking-wider text-muted">
        {label}
      </span>
      <p className={`font-mono text-[11px] font-medium ${color}`}>{value}</p>
    </div>
  );
}

function FactorBar({ label, value }: { label: string; value: number }) {
  const abs = Math.min(Math.abs(value), 1);
  const isPos = value >= 0;
  return (
    <div className="flex items-center gap-2">
      <span className="w-14 truncate text-[10px] text-muted">{label}</span>
      <div className="h-1 flex-1 rounded-full bg-slate-100">
        <div
          className={`h-1 rounded-full ${isPos ? "bg-emerald-400" : "bg-red-400"}`}
          style={{ width: `${Math.max(2, abs * 100)}%` }}
        />
      </div>
      <span className="w-8 text-right font-mono text-[9px] text-muted">
        {value > 0 ? "+" : ""}
        {value.toFixed(2)}
      </span>
    </div>
  );
}
