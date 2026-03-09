import { notFound } from "next/navigation";
import Link from "next/link";
import Section from "@/components/Section";
import { projects } from "@/data/projects";

export function generateStaticParams() {
  return projects.map((p) => ({ slug: p.slug }));
}

export function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  return params.then(({ slug }) => {
    const project = projects.find((p) => p.slug === slug);
    return {
      title: project
        ? `${project.title} – Portfolio`
        : "Project Not Found",
    };
  });
}

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = projects.find((p) => p.slug === slug);

  if (!project) {
    notFound();
  }

  return (
    <>
      {/* Header */}
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <Link
            href="/projects"
            className="mb-8 inline-flex items-center gap-1.5 text-sm text-muted transition-colors duration-200 hover:text-foreground"
          >
            <span>&larr;</span>
            <span>Back to Projects</span>
          </Link>
          <div className="mb-4 flex items-center gap-3">
            <span className="rounded-full bg-accent/8 px-2.5 py-0.5 font-mono text-xs font-medium text-accent">
              {project.category}
            </span>
            <span className="text-sm text-muted">{project.period}</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            {project.title}
          </h1>
          <p className="mt-3 text-lg text-muted">{project.subtitle}</p>
          <div className="mt-5 flex flex-wrap gap-1.5">
            {project.tags.map((tag) => (
              <span
                key={tag}
                className="rounded bg-card px-2 py-0.5 font-mono text-[11px] text-muted"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      {/* Content */}
      <Section>
        <div className="grid gap-14 md:grid-cols-3">
          <div className="md:col-span-2 space-y-10">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="h-5 w-0.5 rounded-full bg-accent" />
                <h2 className="text-xl font-semibold tracking-tight">
                  Overview
                </h2>
              </div>
              <p className="text-base leading-7 text-muted">
                {project.summary}
              </p>
            </div>

            {project.sections.map((section) => (
              <div key={section.title}>
                <h2 className="mb-3 text-lg font-semibold tracking-tight">
                  {section.title}
                </h2>
                <p className="text-sm leading-7 text-muted">
                  {section.content}
                </p>
              </div>
            ))}
          </div>

          {/* Sidebar */}
          <div>
            <div className="sticky top-24 rounded-lg border border-border bg-card p-6 shadow-sm">
              <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted">
                Key Highlights
              </h3>
              <ul className="mt-4 space-y-3">
                {project.highlights.map((highlight) => (
                  <li
                    key={highlight}
                    className="flex items-start gap-3 text-sm text-muted"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent/60" />
                    {highlight}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
