import type { Regime } from "@/data/watchlist";

const LABEL_STYLE: Record<string, string> = {
  bullish: "bg-emerald-50 text-emerald-700 border-emerald-200",
  bearish: "bg-red-50 text-red-700 border-red-200",
  mixed: "bg-amber-50 text-amber-700 border-amber-200",
};

const SIGNAL_NAMES: Record<string, string> = {
  price_vs_vwap: "Price vs VWAP",
  ma_alignment: "MA Alignment",
  early_direction: "Early Direction",
  momentum: "Momentum",
  orb: "Opening Range",
};

export default function RegimeSummary({ regime }: { regime: Regime }) {
  const benchmarks = (["QQQ", "SPY"] as const).filter(
    (b) => regime.details[b]
  );

  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      {/* Top row */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] font-medium uppercase tracking-widest text-muted">
            Market Regime
          </p>
          <div className="mt-2 flex items-center gap-3">
            <span
              className={`rounded-md border px-3 py-1 font-mono text-xs font-semibold uppercase ${LABEL_STYLE[regime.label]}`}
            >
              {regime.label}
            </span>
            <span className="font-mono text-sm text-muted">
              {(regime.confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
        </div>

        {/* Composite score */}
        <div className="text-right">
          <p className="font-mono text-[10px] font-medium uppercase tracking-widest text-muted">
            Composite
          </p>
          <p className="mt-1 font-mono text-lg font-semibold tracking-tight">
            {(regime.details.composite ?? 0) > 0 ? "+" : ""}
            {((regime.details.composite ?? 0) * 100).toFixed(1)}
          </p>
        </div>
      </div>

      {/* Explanation */}
      <p className="mt-4 text-xs leading-relaxed text-muted">
        {regime.explanation}
      </p>

      {/* Benchmark signal breakdown */}
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {benchmarks.map((bench) => {
          const signals = regime.details[bench]!;
          const composite =
            regime.details[
              `${bench}_composite` as keyof typeof regime.details
            ] as number;

          return (
            <div
              key={bench}
              className="rounded-md border border-border bg-background p-4"
            >
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-xs font-semibold">
                  {bench}
                </span>
                <span className="font-mono text-[10px] text-muted">
                  composite{" "}
                  <span className="font-semibold text-foreground">
                    {composite > 0 ? "+" : ""}
                    {(composite * 100).toFixed(1)}
                  </span>
                </span>
              </div>
              <div className="mt-3 space-y-2">
                {Object.entries(signals).map(([key, sig]) => (
                  <SignalRow
                    key={key}
                    name={SIGNAL_NAMES[key] ?? key}
                    score={sig.score}
                    detail={sig.detail}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SignalRow({
  name,
  score,
  detail,
}: {
  name: string;
  score: number;
  detail: string;
}) {
  const pct = ((score + 1) / 2) * 100; // map [-1, 1] → [0, 100]
  const barColor =
    score > 0.1
      ? "bg-emerald-400"
      : score < -0.1
        ? "bg-red-400"
        : "bg-slate-300";

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] text-muted">{name}</span>
        <span className="font-mono text-[10px] font-medium">
          {score > 0 ? "+" : ""}
          {score.toFixed(2)}
        </span>
      </div>
      <div className="mt-1 h-1 w-full rounded-full bg-slate-100">
        <div
          className={`h-1 rounded-full ${barColor} transition-all`}
          style={{ width: `${Math.max(2, pct)}%` }}
        />
      </div>
      <p className="mt-0.5 truncate text-[10px] text-muted/70">{detail}</p>
    </div>
  );
}
