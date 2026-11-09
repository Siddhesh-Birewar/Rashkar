import type { LucideIcon } from "lucide-react";
import { ArrowRight, CheckCircle2, CircleDashed, Info, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export type WorkspaceSection = {
  title: string;
  description: string;
  icon: LucideIcon;
  href?: string;
  status?: string;
};

export function DataIntegrityNotice({
  children = "Live values and recommendations appear only after they are returned by CropNet services.",
}: {
  children?: React.ReactNode;
}) {
  return (
    <div className="flex gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-sm text-forest">
      <ShieldCheck className="mt-0.5 shrink-0" size={19} />
      <p className="leading-6">
        <strong>Verified data only.</strong> {children}
      </p>
    </div>
  );
}

export function StatusRow({
  label,
  value = "Not verified",
  kind = "modelled",
}: {
  label: string;
  value?: string;
  kind?: string;
}) {
  return (
    <div className="flex min-h-14 items-center justify-between gap-4 border-b border-line/70 py-3 last:border-0">
      <div>
        <p className="text-sm font-bold">{label}</p>
        <p className="mt-0.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
          {kind}
        </p>
      </div>
      <Badge variant="neutral">{value}</Badge>
    </div>
  );
}

export function IntelligenceWorkspace({
  eyebrow,
  title,
  description,
  icon: Icon,
  sections,
  steps,
  actionLabel,
  actionHref,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon: LucideIcon;
  sections: WorkspaceSection[];
  steps: string[];
  actionLabel?: string;
  actionHref?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader
        eyebrow={eyebrow}
        title={title}
        description={description}
        actions={
          actionLabel && actionHref ? (
            <Button asChild>
              <Link href={actionHref}>
                {actionLabel} <ArrowRight size={17} />
              </Link>
            </Button>
          ) : undefined
        }
      />

      <DataIntegrityNotice />

      {children}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {sections.map((section) => {
          const SectionIcon = section.icon;
          const content = (
            <>
              <div className="flex items-start justify-between gap-3">
                <span className="grid size-11 place-items-center rounded-2xl bg-[#e8f5e9] text-leaf">
                  <SectionIcon size={21} />
                </span>
                <Badge variant="neutral">{section.status ?? "Unavailable"}</Badge>
              </div>
              <h2 className="mt-5 text-base font-extrabold tracking-[-0.02em]">{section.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted">{section.description}</p>
              {section.href && (
                <span className="mt-5 flex items-center gap-2 text-xs font-extrabold text-forest">
                  Open workspace <ArrowRight size={15} />
                </span>
              )}
            </>
          );
          return section.href ? (
            <Link
              key={section.title}
              href={section.href}
              className="rounded-card border border-line bg-white p-5 shadow-[0_12px_35px_rgba(27,65,32,.055)] transition hover:-translate-y-0.5 hover:border-[#b8d0ba]"
            >
              {content}
            </Link>
          ) : (
            <Card key={section.title}>
              <CardContent>{content}</CardContent>
            </Card>
          );
        })}
      </section>

      <Card>
        <CardContent className="grid gap-6 lg:grid-cols-[.8fr_1.2fr] lg:p-7">
          <div>
            <span className="grid size-11 place-items-center rounded-2xl bg-[#edf3f8] text-[#3977a8]">
              <Info size={21} />
            </span>
            <h2 className="mt-4 text-lg font-extrabold">How this works</h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              CropNet clearly separates information you provide from laboratory, model and forecast
              sources.
            </p>
          </div>
          <ol className="grid gap-3 sm:grid-cols-3">
            {steps.map((step, index) => (
              <li key={step} className="rounded-2xl bg-canvas p-4">
                <span className="flex items-center gap-2 text-xs font-extrabold text-leaf">
                  {index === 0 ? <CheckCircle2 size={16} /> : <CircleDashed size={16} />}
                  Step {index + 1}
                </span>
                <p className="mt-3 text-sm font-bold leading-5">{step}</p>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    </div>
  );
}
