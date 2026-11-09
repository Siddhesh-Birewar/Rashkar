import { Sprout } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link
      href="/"
      className="inline-flex items-center gap-3 rounded-xl"
      aria-label="CropNet AI home"
    >
      <span className="grid size-10 shrink-0 place-items-center rounded-[14px] bg-forest text-white shadow-[0_8px_18px_rgba(27,94,32,.2)]">
        <Sprout size={22} strokeWidth={2.3} />
      </span>
      <span className={cn("leading-none", compact && "lg:hidden")}>
        <span className="block text-[17px] font-extrabold tracking-[-0.03em]">
          CropNet <span className="text-leaf">AI</span>
        </span>
        <span className="mt-1 block text-[9px] font-bold uppercase tracking-[0.19em] text-muted">
          Grow with insight
        </span>
      </span>
    </Link>
  );
}
