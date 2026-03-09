interface ChartContainerProps {
  title: string;
  children: React.ReactNode;
}

export default function ChartContainer({
  title,
  children,
}: ChartContainerProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
      <h3 className="mb-5 text-xs font-semibold uppercase tracking-wider text-muted">
        {title}
      </h3>
      <div className="h-72">{children}</div>
    </div>
  );
}
