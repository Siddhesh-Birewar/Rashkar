import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "green",
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  variant?: "green" | "orange" | "neutral" | "accent" | "destructive" | "outline" | "default" | "secondary";
}) {
  return (
    <span
      className={cn(
        "inline-flex min-h-6 items-center rounded-full px-2.5 text-[11px] font-extrabold",
        (variant === "green" || variant === "default") && "bg-[#e6f3e6] text-forest",
        (variant === "orange" || variant === "accent") && "bg-[#fff0e8] text-accent",
        (variant === "neutral" || variant === "secondary") && "bg-[#eff3ef] text-muted",
        variant === "destructive" && "bg-[#fde8e8] text-[#c62828]",
        variant === "outline" && "border border-line bg-transparent text-ink",
        className,
      )}
      {...props}
    />
  );
}
