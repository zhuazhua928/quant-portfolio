import Section from "@/components/Section";
import ProjectCard from "@/components/ProjectCard";
import { projects } from "@/data/projects";

export const metadata = {
  title: "Projects – Quantitative Research Portfolio",
};

export default function ProjectsPage() {
  return (
    <>
      <section className="py-24">
        <div className="mx-auto max-w-5xl px-6">
          <p className="mb-5 font-mono text-xs font-medium uppercase tracking-widest text-accent">
            Projects
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Research & Development
          </h1>
          <p className="mt-4 max-w-2xl text-base text-muted">
            Six projects spanning energy commodities, ML-based intraday
            forecasting, systematic trading, exotic derivatives research,
            crypto market intelligence, and behavioral finance.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-5xl px-6">
        <hr className="border-border" />
      </div>

      <Section>
        <div className="grid gap-6 md:grid-cols-2">
          {projects.map((project) => (
            <ProjectCard key={project.slug} project={project} />
          ))}
        </div>
      </Section>
    </>
  );
}
