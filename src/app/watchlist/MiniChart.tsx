import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import type { ChartPoint, SymbolFeatures } from "@/data/watchlist";

const axisStyle = {
  fontSize: 9,
  fill: "#94a3b8",
  fontFamily: "var(--font-geist-mono)",
};

function pct(v: number | null): string {
  if (v == null) return "—";
  const s = (v * 100).toFixed(2);
  return v > 0 ? `+${s}%` : `${s}%`;
}

interface Props {
  symbol: string;
  data: ChartPoint[];
  features?: SymbolFeatures;
}

export default function MiniChart({ symbol, data, features }: Props) {
  if (!data.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-border bg-card text-xs text-muted shadow-sm">
        No chart data for {symbol}
      </div>
    );
  }

  // Compute Y domain with padding
  const prices = data.map((d) => d.c);
  const allVals = [
    ...prices,
    ...data.map((d) => d.v).filter((v): v is number => v != null),
  ];
  const yMin = Math.min(...allVals);
  const yMax = Math.max(...allVals);
  const padding = (yMax - yMin) * 0.08;

  const dtdReturn = features?.ret_dtd ?? null;
  const dtdColor =
    dtdReturn != null && dtdReturn > 0.001
      ? "text-positive"
      : dtdReturn != null && dtdReturn < -0.001
        ? "text-negative"
        : "text-foreground";

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      {/* Header */}
      <div className="mb-3 flex items-baseline justify-between">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-sm font-semibold">{symbol}</span>
          <span className="font-mono text-xs text-muted">
            {features?.last_price.toFixed(2)}
          </span>
        </div>
        <span className={`font-mono text-xs font-medium ${dtdColor}`}>
          {pct(dtdReturn)}
        </span>
      </div>

      {/* Chart */}
      <div className="h-44">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 4, right: 4, bottom: 2, left: 4 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#f1f5f9"
              vertical={false}
            />
            <XAxis
              dataKey="t"
              tick={axisStyle}
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
              interval={Math.floor(data.length / 4)}
            />
            <YAxis
              tick={axisStyle}
              tickLine={false}
              axisLine={false}
              domain={[yMin - padding, yMax + padding]}
              tickFormatter={(v: number) => v.toFixed(0)}
              width={36}
            />
            <Tooltip
              contentStyle={{
                fontSize: 10,
                fontFamily: "var(--font-geist-mono)",
                background: "#fff",
                border: "1px solid #e2e8f0",
                borderRadius: 6,
                boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
                padding: "6px 10px",
              }}
              formatter={(v, name) => [
                Number(v).toFixed(2),
                String(name),
              ]}
            />

            {/* ORB range */}
            {features?.orb_high != null && (
              <ReferenceLine
                y={features.orb_high}
                stroke="#94a3b8"
                strokeDasharray="2 3"
                strokeWidth={0.75}
              />
            )}
            {features?.orb_low != null && (
              <ReferenceLine
                y={features.orb_low}
                stroke="#94a3b8"
                strokeDasharray="2 3"
                strokeWidth={0.75}
              />
            )}

            {/* VWAP */}
            <Line
              type="monotone"
              dataKey="v"
              stroke="#8b5cf6"
              strokeWidth={1}
              dot={false}
              name="VWAP"
              strokeDasharray="3 2"
            />
            {/* MA 20 */}
            <Line
              type="monotone"
              dataKey="m20"
              stroke="#f59e0b"
              strokeWidth={0.8}
              dot={false}
              name="MA 20"
              strokeDasharray="4 3"
            />
            {/* MA 5 */}
            <Line
              type="monotone"
              dataKey="m5"
              stroke="#3b82f6"
              strokeWidth={0.8}
              dot={false}
              name="MA 5"
            />
            {/* Price */}
            <Line
              type="monotone"
              dataKey="c"
              stroke="#1e3a5f"
              strokeWidth={1.4}
              dot={false}
              name="Price"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 border-t border-border/50 pt-2">
        <LegendItem color="#1e3a5f" label="Price" />
        <LegendItem color="#8b5cf6" label="VWAP" dashed />
        <LegendItem color="#3b82f6" label="MA 5" />
        <LegendItem color="#f59e0b" label="MA 20" dashed />
        <span className="font-mono text-[9px] text-muted/50">
          ── ORB range
        </span>
      </div>

      {/* Mini metrics */}
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-0.5 text-[10px]">
        <MiniMetric label="RSI" value={features?.rsi != null ? features.rsi.toFixed(0) : "—"} />
        <MiniMetric label="RVOL" value={features?.rvol != null ? `${features.rvol.toFixed(2)}x` : "—"} />
        <MiniMetric label="ORB" value={features?.orb_status ?? "—"} />
        <MiniMetric label="xs QQQ" value={pct(features?.ret_dtd_xs_qqq ?? null)} />
      </div>
    </div>
  );
}

function LegendItem({
  color,
  label,
  dashed,
}: {
  color: string;
  label: string;
  dashed?: boolean;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <span
        className="inline-block h-px w-3"
        style={
          dashed
            ? {
                backgroundImage: `repeating-linear-gradient(90deg, ${color} 0 3px, transparent 3px 5px)`,
              }
            : { backgroundColor: color }
        }
      />
      <span className="font-mono text-[9px] text-muted">{label}</span>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <span className="font-mono text-muted">
      <span className="uppercase tracking-wider">{label}</span>{" "}
      <span className="font-medium text-foreground">{value}</span>
    </span>
  );
}
