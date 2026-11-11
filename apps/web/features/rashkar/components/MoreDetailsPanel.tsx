"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Microscope } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface MoreDetailsPanelProps {
  title?: string;
  subtitle?: string;
  badgeText?: string;
  defaultOpen?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function MoreDetailsPanel({
  title = "More Scientific & Technical Details",
  subtitle = "Underlying physical indices, provenance, model thresholds, and academic citations.",
  badgeText,
  defaultOpen = false,
  className,
  children,
}: MoreDetailsPanelProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section
      className={cn(
        "rounded-card border border-line bg-white shadow-[0_10px_28px_rgba(27,65,32,.045)]",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left transition-colors hover:bg-[#f6faf6] sm:px-6"
      >
        <div className="flex min-w-0 items-start gap-3">
          <span className="mt-0.5 grid size-9 shrink-0 place-items-center rounded-xl bg-[#edf5ed] text-forest">
            <Microscope size={17} />
          </span>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-extrabold text-ink">{title}</span>
              {badgeText && (
                <Badge variant="neutral" className="text-[10px]">
                  {badgeText}
                </Badge>
              )}
            </div>
            <p className="mt-0.5 text-xs leading-5 text-muted">{subtitle}</p>
          </div>
        </div>
        <span className="grid size-8 shrink-0 place-items-center rounded-lg border border-line bg-white text-muted">
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {open && (
        <div className="border-t border-line/80 bg-[#fbfdfb] px-5 py-5 sm:px-6">{children}</div>
      )}
    </section>
  );
}
