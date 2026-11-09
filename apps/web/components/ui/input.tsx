import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "min-h-12 w-full rounded-xl border border-line bg-white px-4 text-[15px] text-ink shadow-sm placeholder:text-[#91a294] focus:border-leaf",
        className,
      )}
      {...props}
    />
  );
}
