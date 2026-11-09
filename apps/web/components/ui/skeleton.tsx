import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-xl bg-gradient-to-r from-[#edf2ed] via-[#f6f8f6] to-[#edf2ed] bg-[length:200%_100%]",
        className,
      )}
    />
  );
}
