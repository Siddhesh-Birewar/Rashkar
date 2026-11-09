export function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex items-end justify-between gap-3">
      <div>
        <h2 className="text-[17px] font-extrabold tracking-[-0.025em] sm:text-lg">{title}</h2>
        {description && <p className="mt-1 text-xs leading-5 text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}
