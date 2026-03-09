interface SectionProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export default function Section({
  title,
  subtitle,
  children,
  className = "",
}: SectionProps) {
  return (
    <section className={`py-20 ${className}`}>
      <div className="mx-auto max-w-5xl px-6">
        {(title || subtitle) && (
          <div className="mb-12">
            {title && (
              <div className="flex items-center gap-3">
                <span className="h-5 w-0.5 rounded-full bg-accent" />
                <h2 className="text-xl font-semibold tracking-tight">
                  {title}
                </h2>
              </div>
            )}
            {subtitle && (
              <p className="mt-2 pl-5 text-sm text-muted">{subtitle}</p>
            )}
          </div>
        )}
        {children}
      </div>
    </section>
  );
}
