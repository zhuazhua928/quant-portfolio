import Link from "next/link";
import Section from "@/components/Section";
import ProjectCard from "@/components/ProjectCard";
import { projects } from "@/data/projects";

export default function Home() {
  return (
    <>
      {/* Hero */}
      <section className="py-28">
        <div className="mx-auto max-w-5xl px-6">
          <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-accent">
            Quantitative Research
          </p>
          <h1 className="max-w-3xl text-3xl font-bold leading-snug tracking-tight sm:text-4xl">
            Quantitative researcher focused on systematic trading,
            market intelligence, and risk-aware portfolio construction
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted">
            I build research-to-execution pipelines across signal generation,
            backtesting, risk control, and monitoring, with experience spanning
            crypto, equities, market microstructure, and NLP-driven trading
            research.
          </p>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-muted">
            I am a Financial Mathematics graduate student at Johns Hopkins
            University with experience in systematic trading, quantitative
            research, and market microstructure. My work combines machine
            learning, reinforcement learning, NLP, and statistical modeling to
            build disciplined trading systems under real-world constraints. I
            have worked across crypto and equity strategies, factor research,
            investor-facing performance reporting, and execution-aware research
            pipelines.
          </p>
          <div className="mt-10 flex gap-4">
            <Link
              href="/projects"
              className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-all duration-200 hover:bg-accent-light hover:shadow-md"
            >
              View Projects
            </Link>
            <Link
              href="/resume"
              className="rounded-md border border-border bg-card px-5 py-2.5 text-sm font-medium text-foreground shadow-sm transition-all duration-200 hover:border-accent/20 hover:shadow-md"
            >
              Resume
            </Link>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Focus Areas */}
      <Section title="Focus Areas">
        <div className="grid gap-6 sm:grid-cols-3">
          {[
            {
              label: "Systematic Trading Systems",
              description:
                "Built research-to-execution workflows covering data, signal design, risk, backtesting, monitoring, and paper/live deployment in crypto trading research.",
            },
            {
              label: "Quant Research & Modeling",
              description:
                "Worked on reinforcement learning, market microstructure features, LASSO, LSTM, PPCA-based arbitrage, and transformer-based behavioral finance research across crypto and equities.",
            },
            {
              label: "Teaching & Communication",
              description:
                "Supported students in empirical finance and crypto trading labs, and translated technical strategy capabilities into investor-facing reporting and diligence-ready materials.",
            },
          ].map((area) => (
            <div
              key={area.label}
              className="rounded-lg border border-border bg-card p-6 shadow-sm"
            >
              <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-accent">
                {area.label}
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-muted">
                {area.description}
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* Divider */}
      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Featured Projects */}
      <Section
        title="Selected Projects"
        subtitle="Research-driven projects in systematic trading and quantitative analysis."
      >
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
        <div className="mt-10">
          <Link
            href="/projects"
            className="text-sm font-medium text-accent transition-colors duration-200 hover:text-accent-light"
          >
            View all projects &rarr;
          </Link>
        </div>
      </Section>

      {/* Divider */}
      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Contact */}
      <Section title="Contact">
        <div className="grid gap-6 sm:grid-cols-3">
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
              Name
            </h3>
            <p className="mt-2 text-sm font-medium">Yuheng (Paul) Yan</p>
          </div>
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
              Email
            </h3>
            <a
              href="mailto:yyan75@jh.edu"
              className="mt-2 block text-sm font-medium text-accent transition-colors duration-200 hover:text-accent-light"
            >
              yyan75@jh.edu
            </a>
          </div>
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
              Phone
            </h3>
            <p className="mt-2 text-sm font-medium">+1 (410) 805-9842</p>
          </div>
        </div>
      </Section>
    </>
  );
}
