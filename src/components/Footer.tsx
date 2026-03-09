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
          <div className="flex gap-8">
            <a
              href="https://github.com/yourusername"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted transition-colors duration-200 hover:text-foreground"
            >
              GitHub
            </a>
            <a
              href="https://linkedin.com/in/yourusername"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-muted transition-colors duration-200 hover:text-foreground"
            >
              LinkedIn
            </a>
            <a
              href="mailto:yyan75@jh.edu"
              className="text-sm text-muted transition-colors duration-200 hover:text-foreground"
            >
              Email
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
