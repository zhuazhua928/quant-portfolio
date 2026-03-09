import Section from "@/components/Section";
import { resumeData } from "@/data/resume";

export const metadata = {
  title: "Resume – Quantitative Research Portfolio",
};

export default function ResumePage() {
  return (
    <>
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-accent">
            Resume
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            {resumeData.name}
          </h1>
          <p className="mt-2 text-lg text-muted">{resumeData.title}</p>
          <div className="mt-4 flex flex-wrap gap-4 text-sm text-muted">
            <span>{resumeData.location}</span>
            <span className="hidden sm:inline text-border">&middot;</span>
            <a
              href={`mailto:${resumeData.email}`}
              className="text-accent transition-colors duration-200 hover:text-accent-light"
            >
              {resumeData.email}
            </a>
            <span className="hidden sm:inline text-border">&middot;</span>
            <span>{resumeData.phone}</span>
            <span className="hidden sm:inline text-border">&middot;</span>
            <a
              href={resumeData.links.github}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent transition-colors duration-200 hover:text-accent-light"
            >
              GitHub
            </a>
            <a
              href={resumeData.links.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent transition-colors duration-200 hover:text-accent-light"
            >
              LinkedIn
            </a>
          </div>
          <div className="mt-8">
            <a
              href="/resume.pdf"
              download
              className="inline-flex items-center gap-2 rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-all duration-200 hover:bg-accent-light hover:shadow-md"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M8 2v9M4.5 7.5L8 11l3.5-3.5M3 13h10" />
              </svg>
              Download PDF
            </a>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Education */}
      <Section title="Education">
        <div className="space-y-8">
          {resumeData.education.map((edu) => (
            <div key={edu.degree}>
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold">{edu.degree}</h3>
                  <p className="mt-0.5 text-sm text-muted">
                    {edu.institution}
                  </p>
                  <p className="text-sm text-muted">{edu.detail}</p>
                </div>
                <span className="mt-1 font-mono text-xs text-muted whitespace-nowrap sm:mt-0.5">
                  {edu.period}
                </span>
              </div>
              {edu.bullets && edu.bullets.length > 0 && (
                <ul className="mt-3 space-y-1.5 text-sm text-muted">
                  {edu.bullets.map((bullet, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Experience */}
      <Section title="Experience">
        <div className="space-y-8">
          {resumeData.experience.map((exp) => (
            <div key={exp.role + exp.firm}>
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold">{exp.role}</h3>
                  <p className="mt-0.5 text-sm text-muted">
                    {exp.firm}
                    {exp.location && ` · ${exp.location}`}
                  </p>
                </div>
                <span className="mt-1 font-mono text-xs text-muted whitespace-nowrap sm:mt-0.5">
                  {exp.period}
                </span>
              </div>
              {exp.bullets && exp.bullets.length > 0 && (
                <ul className="mt-3 space-y-1.5 text-sm text-muted">
                  {exp.bullets.map((bullet, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Research */}
      <Section title="Research">
        <div className="space-y-8">
          {resumeData.research.map((item) => (
            <div key={item.title}>
              <h3 className="text-base font-semibold">{item.title}</h3>
              <p className="mt-1 text-sm text-muted">{item.detail}</p>
              {item.bullets && item.bullets.length > 0 && (
                <ul className="mt-3 space-y-1.5 text-sm text-muted">
                  {item.bullets.map((bullet, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Teaching */}
      <Section title="Teaching">
        <div className="space-y-8">
          {resumeData.teaching.map((item) => (
            <div key={item.role}>
              <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="text-base font-semibold">{item.role}</h3>
                  <p className="mt-0.5 text-sm text-muted">
                    {item.institution}
                  </p>
                </div>
                <span className="mt-1 font-mono text-xs text-muted whitespace-nowrap sm:mt-0.5">
                  {item.period}
                </span>
              </div>
              {item.bullets && item.bullets.length > 0 && (
                <ul className="mt-3 space-y-1.5 text-sm text-muted">
                  {item.bullets.map((bullet, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </Section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Skills */}
      <Section title="Technical Skills">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {(
            Object.entries(resumeData.skills) as [string, string[]][]
          ).map(([category, items]) => (
            <div
              key={category}
              className="rounded-lg border border-border bg-card p-5 shadow-sm"
            >
              <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted">
                {category}
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {items.map((item) => (
                  <span
                    key={item}
                    className="rounded bg-background px-2 py-0.5 font-mono text-[11px] text-muted"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
