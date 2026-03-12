import Image from "next/image";
import Link from "next/link";
import Section from "@/components/Section";
import ProjectCard from "@/components/ProjectCard";
import { projects } from "@/data/projects";

export default function Home() {
  return (
    <>
      {/* Hero with photo + contact */}
      <section className="py-28">
        <div className="mx-auto max-w-5xl px-6">
          <div className="flex flex-col gap-10 md:flex-row md:items-start md:gap-14">
            {/* Photo + contact card */}
            <div className="flex-shrink-0">
              <div className="w-40 md:w-48">
                <Image
                  src="/zhaopian.jpg"
                  alt="Yuheng (Paul) Yan"
                  width={192}
                  height={192}
                  className="rounded-xl border border-border object-cover shadow-sm"
                  priority
                />
                <div className="mt-5 space-y-2.5">
                  <div>
                    <p className="font-mono text-[9px] font-medium uppercase tracking-widest text-muted">
                      Name
                    </p>
                    <p className="mt-0.5 text-sm font-semibold">
                      Yuheng (Paul) Yan
                    </p>
                  </div>
                  <div>
                    <p className="font-mono text-[9px] font-medium uppercase tracking-widest text-muted">
                      Email
                    </p>
                    <a
                      href="mailto:yyan75@jh.edu"
                      className="mt-0.5 block text-sm font-medium text-accent transition-colors hover:text-accent-light"
                    >
                      yyan75@jh.edu
                    </a>
                  </div>
                  <div>
                    <p className="font-mono text-[9px] font-medium uppercase tracking-widest text-muted">
                      Phone
                    </p>
                    <p className="mt-0.5 text-sm font-medium">
                      +1 (410) 805-9842
                    </p>
                  </div>
                  <div>
                    <p className="font-mono text-[9px] font-medium uppercase tracking-widest text-muted">
                      Location
                    </p>
                    <p className="mt-0.5 text-sm font-medium">
                      Baltimore, MD
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Intro text */}
            <div className="flex-1">
              <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-accent">
                Quantitative Research
              </p>
              <h1 className="max-w-3xl text-3xl font-bold leading-snug tracking-tight sm:text-4xl">
                Quantitative researcher focused on systematic trading, market
                intelligence, and applied financial research
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-relaxed text-muted">
                I build research-to-execution pipelines across signal
                generation, backtesting, risk management, and monitoring —
                with experience spanning crypto, U.S. equities, derivatives,
                and NLP-driven trading research.
              </p>
              <p className="mt-4 max-w-2xl text-sm leading-relaxed text-muted">
                MSE in Financial Mathematics at Johns Hopkins University.
                Background in systematic trading system design, alternative
                data, Monte Carlo methods, and behavioral finance. I have
                worked across crypto and equity strategies, factor research,
                structured derivatives, and research-grade execution
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
              label: "Systematic Trading",
              description:
                "End-to-end research pipelines from signal design through risk management to live monitoring, across crypto and equity markets.",
            },
            {
              label: "Quantitative Research",
              description:
                "Applied work in behavioral finance, Monte Carlo methods, NLP sentiment, reinforcement learning, and factor-based modeling.",
            },
            {
              label: "Derivatives & Risk",
              description:
                "Exotic option pricing, structured product analysis, and systematic risk frameworks for multi-asset portfolios.",
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

      {/* Selected Projects */}
      <Section
        title="Selected Projects"
        subtitle="Four projects spanning systematic trading, derivatives, alternative data, and quantitative research."
      >
        <div className="grid gap-6 md:grid-cols-2">
          {projects.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </Section>

      {/* Competitive distinction */}
      <div className="mx-auto max-w-5xl px-6 pb-20">
        <div className="rounded-lg border border-border/60 bg-card px-6 py-5 shadow-sm">
          <div className="flex items-start gap-4">
            <span className="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md bg-accent/8">
              <span className="font-mono text-[10px] font-bold text-accent">
                #1
              </span>
            </span>
            <div>
              <h3 className="text-sm font-semibold tracking-tight">
                Competitive Distinction
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">
                Outside of trading and research, I have competed at a high
                level in Teamfight Tactics, reaching Rank 1 on the North
                American server and previously participating in professional
                competition. The experience reinforced skills that also matter
                in markets: decision-making under uncertainty, rapid
                adaptation, disciplined review, and strategic resource
                allocation.
              </p>
              <p className="mt-2 text-xs text-muted/70">
                This competitive background is also reflected in a public{" "}
                <span className="font-medium text-muted">
                  Liquipedia profile
                </span>
                .
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
