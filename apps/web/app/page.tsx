export default function HomePage() {
  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "not configured (see .env.example)";

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <section className="w-full max-w-2xl rounded-card border border-border bg-white p-8 shadow-card">
        <span className="inline-flex items-center rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
          Web foundation
        </span>
        <h1 className="mt-4 text-2xl font-semibold text-brand">
          CropNet AI — Next.js foundation
        </h1>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This is the Vercel-ready App Router foundation for the redesigned,
          mobile-first frontend. Product screens will be built in Vercel v0
          against the existing FastAPI backend.
        </p>

        <dl className="mt-6 grid gap-3 text-sm">
          <div className="rounded-button border border-border p-3">
            <dt className="font-medium text-slate-700">API base URL</dt>
            <dd className="mt-1 font-mono text-xs text-slate-500">{apiBase}</dd>
          </div>
          <div className="rounded-button border border-border p-3">
            <dt className="font-medium text-slate-700">Handoff docs</dt>
            <dd className="mt-1 font-mono text-xs text-slate-500">
              apps/web/docs/handoff/
            </dd>
          </div>
        </dl>

        <p className="mt-6 text-xs text-slate-500">
          Source of truth: the FastAPI backend. Authentication: Supabase. The
          frontend never computes agronomic decisions, thresholds or NPK values.
        </p>
      </section>
    </main>
  );
}
