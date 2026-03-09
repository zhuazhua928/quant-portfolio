import Link from "next/link";
import type { Project } from "@/data/projects";

export default function ProjectCard({ project }: { project: Project }) {
  return (
    <Link
      href={`/projects/${project.slug}`}
      className="group block rounded-lg border border-border bg-card p-6 shadow-sm transition-all duration-200 hover:border-accent/20 hover:shadow-md"
    >
      <div className="mb-3 flex items-center gap-3">
        <span className="rounded-full bg-accent/8 px-2.5 py-0.5 font-mono text-xs font-medium text-accent">
          {project.category}
        </span>
        <span className="text-xs text-muted">{project.period}</span>
      </div>
      <h3 className="text-base font-semibold tracking-tight text-foreground group-hover:text-accent transition-colors duration-200">
        {project.title}
      </h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">
        {project.subtitle}
      </p>
      <div className="mt-4 flex flex-wrap gap-1.5">
        {project.tags.map((tag) => (
          <span
            key={tag}
            className="rounded bg-background px-2 py-0.5 font-mono text-[11px] text-muted"
          >
            {tag}
          </span>
        ))}
      </div>
      <p className="mt-4 text-xs font-medium text-accent opacity-0 transition-opacity duration-200 group-hover:opacity-100">
        Read case study &rarr;
      </p>
    </Link>
  );
}
