import type { RankedSymbol, SymbolFeatures } from "@/data/watchlist";

function pct(v: number | null, digits = 2): string {
  if (v == null) return "—";
  const s = (v * 100).toFixed(digits);
  return v > 0 ? `+${s}%` : `${s}%`;
}

function colorClass(v: number | null): string {
  if (v == null) return "text-muted";
  if (v > 0.001) return "text-positive";
  if (v < -0.001) return "text-negative";
  return "text-foreground";
}

function scoreBar(score: number) {
  const abs = Math.min(Math.abs(score), 1);
  const widthPct = abs * 100;
  const isPos = score >= 0;
  return (
    <div className="flex items-center gap-2">
      <span className="w-12 text-right font-mono text-[11px]">
        {score > 0 ? "+" : ""}
        {score.toFixed(3)}
      </span>
      <div className="h-1.5 w-16 rounded-full bg-slate-100">
        <div
          className={`h-1.5 rounded-full ${isPos ? "bg-emerald-400" : "bg-red-400"}`}
          style={{ width: `${Math.max(2, widthPct)}%` }}
        />
      </div>
    </div>
  );
}

interface Props {
  ranked: RankedSymbol[];
  symbolMap: Record<string, SymbolFeatures>;
}

export default function RankedTable({ ranked, symbolMap }: Props) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card shadow-sm">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-border bg-background">
            <Th className="w-10">#</Th>
            <Th>Symbol</Th>
            <Th className="text-right">Price</Th>
            <Th className="text-right">DTD</Th>
            <Th className="text-right">xs QQQ</Th>
            <Th className="text-right">RSI</Th>
            <Th className="text-right">RVOL</Th>
            <Th>ORB</Th>
            <Th>Score</Th>
            <Th className="min-w-[200px]">Rationale</Th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((r) => {
            const s = symbolMap[r.symbol];
            return (
              <tr
                key={r.symbol}
                className="border-b border-border/50 transition-colors hover:bg-card-hover"
              >
                <Td className="font-mono text-muted">{r.rank}</Td>
                <Td className="font-mono font-semibold">{r.symbol}</Td>
                <Td className="text-right font-mono">
                  {s?.last_price.toFixed(2)}
                </Td>
                <Td className={`text-right font-mono ${colorClass(s?.ret_dtd ?? null)}`}>
                  {pct(s?.ret_dtd ?? null)}
                </Td>
                <Td
                  className={`text-right font-mono ${colorClass(s?.ret_dtd_xs_qqq ?? null)}`}
                >
                  {pct(s?.ret_dtd_xs_qqq ?? null)}
                </Td>
                <Td className="text-right font-mono">
                  {s?.rsi != null ? s.rsi.toFixed(0) : "—"}
                </Td>
                <Td className="text-right font-mono">
                  {s?.rvol != null ? `${s.rvol.toFixed(2)}x` : "—"}
                </Td>
                <Td>
                  <OrbBadge status={s?.orb_status ?? "undefined"} />
                </Td>
                <Td>{scoreBar(r.score)}</Td>
                <Td className="text-[11px] text-muted">{r.explanation}</Td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Th({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <th
      className={`px-4 py-3 font-mono text-[10px] font-medium uppercase tracking-wider text-muted ${className}`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <td className={`px-4 py-3 ${className}`}>{children}</td>;
}

function OrbBadge({
  status,
}: {
  status: "above" | "below" | "inside" | "undefined";
}) {
  const styles: Record<string, string> = {
    above: "bg-emerald-50 text-emerald-700 border-emerald-200",
    below: "bg-red-50 text-red-700 border-red-200",
    inside: "bg-slate-50 text-slate-600 border-slate-200",
    undefined: "bg-slate-50 text-slate-400 border-slate-200",
  };
  return (
    <span
      className={`inline-block rounded border px-1.5 py-0.5 font-mono text-[10px] ${styles[status]}`}
    >
      {status}
    </span>
  );
}
