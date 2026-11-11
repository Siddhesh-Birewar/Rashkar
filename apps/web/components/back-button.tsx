"use client";

import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BackButtonProps {
  fallbackHref?: string;
  label?: string;
  variant?: "icon" | "pill" | "outline";
  className?: string;
  confirmDirty?: boolean;
  isDirty?: boolean;
  onNavigate?: () => void;
}

/**
 * Reusable BackButton component conforming to CropNet design tokens.
 * Features 44px minimum touch targets, keyboard accessibility, and variant styling.
 */
export function BackButton({
  fallbackHref = "/",
  label,
  variant = "icon",
  className,
  confirmDirty = false,
  isDirty = false,
  onNavigate,
}: BackButtonProps) {
  const handleClick = () => {
    if (confirmDirty && isDirty && typeof window !== "undefined") {
      const confirmLeave = window.confirm(
        "You have unsaved changes. Are you sure you want to leave this page?"
      );
      if (!confirmLeave) return;
    }

    if (onNavigate) {
      onNavigate();
      return;
    }

    if (typeof window !== "undefined") {
      window.location.href = fallbackHref;
    }
  };

  if (variant === "pill") {
    return (
      <button
        type="button"
        onClick={handleClick}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-xl border border-line bg-white px-3 py-1.5 text-xs font-bold text-forest shadow-sm transition-colors hover:bg-[#f3f8f3] focus-visible:outline-2 focus-visible:outline-forest min-h-[36px]",
          className
        )}
        aria-label={label ? `Go back: ${label}` : "Go back"}
      >
        <ArrowLeft size={15} />
        <span>{label || "Back"}</span>
      </button>
    );
  }

  if (variant === "outline") {
    return (
      <button
        type="button"
        onClick={handleClick}
        className={cn(
          "inline-flex items-center gap-1.5 text-xs font-bold text-muted transition-colors hover:text-forest focus-visible:outline-2 focus-visible:outline-forest min-h-[36px]",
          className
        )}
        aria-label={label ? `Go back: ${label}` : "Go back"}
      >
        <ArrowLeft size={15} />
        <span>{label || "Back"}</span>
      </button>
    );
  }

  // Default "icon" variant matching CropNet PageHeader design token
  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "mt-0.5 grid size-11 shrink-0 place-items-center rounded-xl border border-line bg-white text-forest shadow-sm transition-colors hover:bg-[#f3f8f3] focus-visible:outline-2 focus-visible:outline-forest min-w-[44px] min-h-[44px]",
        className
      )}
      aria-label={label || "Go back"}
    >
      <ArrowLeft size={19} />
    </button>
  );
}
