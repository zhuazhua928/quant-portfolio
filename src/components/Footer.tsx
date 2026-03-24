export default function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-card">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <div>
            <p className="font-mono text-xs font-bold tracking-widest text-accent uppercase">
              PY
            </p>
            <p className="mt-1 text-xs text-muted">
              &copy; {new Date().getFullYear()} Yuheng (Paul) Yan
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
