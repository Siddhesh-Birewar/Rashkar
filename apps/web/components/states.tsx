import { AlertCircle, CloudOff, LoaderCircle, type LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type StateProps = {
  title: string;
  description: string;
  icon?: LucideIcon;
  className?: string;
  action?: React.ReactNode;
};

export function EmptyState({
  title,
  description,
  icon: Icon = CloudOff,
  className,
  action,
}: StateProps) {
  return (
    <div className={cn("grid place-items-center px-5 py-9 text-center", className)}>
      <span className="mb-4 grid size-12 place-items-center rounded-2xl bg-[#edf5ed] text-leaf">
        <Icon size={22} />
      </span>
      <h3 className="font-extrabold tracking-[-0.02em]">{title}</h3>
      <p className="mt-2 max-w-sm text-sm leading-6 text-muted">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description = "We could not load this information. Please try again.",
  action,
  className,
}: Partial<StateProps>) {
  return (
    <EmptyState
      title={title}
      description={description}
      icon={AlertCircle}
      action={action ?? <Button variant="secondary">Try again</Button>}
      className={className}
    />
  );
}

export function LoadingState({ label = "Loading information" }: { label?: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center gap-3 text-sm font-semibold text-muted">
      <LoaderCircle className="animate-spin text-leaf" size={19} />
      {label}
    </div>
  );
}
