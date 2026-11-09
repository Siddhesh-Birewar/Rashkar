import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function MetricCard({
  label,
  value,
  helper,
  icon: Icon,
}: {
  label: string;
  value?: string;
  helper: string;
  icon: LucideIcon;
}) {
  return (
    <Card>
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-muted">{label}</p>
            <p className="mt-2 text-xl font-extrabold">{value ?? "—"}</p>
          </div>
          <span className="grid size-10 place-items-center rounded-xl bg-[#edf5ed] text-leaf">
            <Icon size={19} />
          </span>
        </div>
        <p className="mt-3 text-[11px] leading-4 text-muted">{helper}</p>
      </CardContent>
    </Card>
  );
}
