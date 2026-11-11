import { Badge } from "@/components/ui/badge";
import { BackButton } from "@/components/back-button";

export function PageHeader({
  title,
  description,
  eyebrow,
  backHref,
  actions,
  confirmDirty,
  isDirty,
}: {
  title: string;
  description?: string;
  eyebrow?: string;
  backHref?: string;
  actions?: React.ReactNode;
  confirmDirty?: boolean;
  isDirty?: boolean;
}) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        {backHref && (
          <BackButton
            fallbackHref={backHref}
            confirmDirty={confirmDirty}
            isDirty={isDirty}
          />
        )}
        <div>
          {eyebrow && <Badge className="mb-3">{eyebrow}</Badge>}
          <h1 className="text-balance text-[28px] leading-[1.1] font-extrabold tracking-[-0.045em] text-ink sm:text-[34px]">
            {title}
          </h1>
          {description && (
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
              {description}
            </p>
          )}
        </div>
      </div>
      {actions && <div className="flex shrink-0 gap-2">{actions}</div>}
    </header>
  );
}
