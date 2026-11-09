import { Skeleton } from "@/components/ui/skeleton";

export default function AppLoading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-2/3 max-w-sm" />
      <Skeleton className="h-64 w-full rounded-[24px]" />
      <div className="grid grid-cols-3 gap-3">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
    </div>
  );
}
