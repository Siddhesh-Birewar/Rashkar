import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-bold transition-all disabled:pointer-events-none disabled:opacity-50 active:scale-[.98]",
  {
    variants: {
      variant: {
        primary: "bg-forest text-white shadow-[0_8px_20px_rgba(27,94,32,.18)] hover:bg-[#154c19]",
        default: "bg-forest text-white shadow-[0_8px_20px_rgba(27,94,32,.18)] hover:bg-[#154c19]",
        secondary: "border border-line bg-white text-ink hover:bg-[#f3f8f3]",
        outline: "border border-line bg-white text-ink hover:bg-[#f3f8f3]",
        ghost: "text-forest hover:bg-[#edf5ed]",
        accent: "bg-accent text-white hover:bg-[#c94700]",
        destructive: "bg-[#c62828] text-white hover:bg-[#a51d1d]",
      },
      size: {
        default: "h-11",
        sm: "min-h-9 rounded-lg px-3 text-xs",
        lg: "min-h-13 rounded-[15px] px-5",
        icon: "size-11 p-0",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, size, asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
