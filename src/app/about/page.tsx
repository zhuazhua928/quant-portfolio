import Section from "@/components/Section";

export const metadata = {
  title: "About – Quantitative Research Portfolio",
};

export default function AboutPage() {
  return (
    <>
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-accent">
            About
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Background & Philosophy
          </h1>
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      <Section>
        <div className="grid gap-14 md:grid-cols-3">
          <div className="md:col-span-2 space-y-6">
            <p className="text-base leading-7 text-muted">
              I am currently pursuing an MSE in Financial Mathematics at Johns
              Hopkins University, where my coursework and research focus on
              stochastic processes, machine learning in finance, derivatives,
              time series, and systematic trading. My practical experience spans
              end-to-end trading system development, from data engineering and
              signal design to portfolio construction, backtesting, monitoring,
              and communication of results to both technical and non-technical
              stakeholders.
            </p>
            <p className="text-base leading-7 text-muted">
              At SNTIMNT.AI, I have worked on crypto trading research and system
              design with CTO-level ownership, managing a five-person quant team
              and helping build a full research-to-execution pipeline. My work
              there includes reinforcement learning-based strategy development,
              sentiment integration from news and social media, performance
              dashboard design, and translating system capabilities into
              diligence-ready narratives for fundraising.
            </p>
            <p className="text-base leading-7 text-muted">
              In parallel, my academic and research work includes systematic
              arbitrage, factor structure analysis, high-frequency feature
              engineering, and behavioral-finance-driven bubble detection. I am
              especially interested in building trading systems that are not only
              predictive, but also interpretable, robust, and useful under real
              market constraints.
            </p>

            <div className="mt-10 border-t border-border pt-10">
              <div className="flex items-center gap-3">
                <span className="h-5 w-0.5 rounded-full bg-accent" />
                <h2 className="text-lg font-semibold tracking-tight">
                  Research Interests
                </h2>
              </div>
              <ul className="mt-5 space-y-3">
                {[
                  "Systematic trading and portfolio construction",
                  "Market microstructure and high-frequency signals",
                  "NLP and sentiment-aware trading systems",
                  "Reinforcement learning for dynamic exposure control",
                  "Factor modeling and statistical arbitrage",
                  "Event-driven market monitoring and decision systems",
                ].map((interest) => (
                  <li
                    key={interest}
                    className="flex items-start gap-3 text-sm text-muted"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                    {interest}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
              <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                Core Competencies
              </h3>
              <ul className="mt-4 space-y-2.5">
                {[
                  "Systematic Strategy Design",
                  "Time-Series Analysis",
                  "Portfolio Construction",
                  "Risk Modeling & VaR",
                  "NLP & Text Analytics",
                  "Data Engineering",
                  "Statistical Testing",
                  "Execution Algorithms",
                ].map((skill) => (
                  <li key={skill} className="text-sm text-muted">
                    {skill}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
              <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                Technical Stack
              </h3>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {[
                  "Python",
                  "C++",
                  "SQL",
                  "pandas",
                  "NumPy",
                  "scikit-learn",
                  "PyTorch",
                  "AWS",
                  "Docker",
                  "PostgreSQL",
                ].map((tech) => (
                  <span
                    key={tech}
                    className="rounded bg-background px-2 py-0.5 font-mono text-[11px] text-muted"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
