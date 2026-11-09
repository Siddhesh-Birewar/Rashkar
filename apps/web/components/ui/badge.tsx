import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "green",
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  variant?: "green" | "orange" | "neutral";
}) {
  return (
    <span
      className={cn(
        "inline-flex min-h-6 items-center rounded-full px-2.5 text-[11px] font-extrabold",
        variant === "green" && "bg-[#e6f3e6] text-forest",
        variant === "orange" && "bg-[#fff0e8] text-accent",
        variant === "neutral" && "bg-[#eff3ef] text-muted",
        className,
      )}
      {...props}
    />
  );
}
