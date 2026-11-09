import { Brand } from "@/components/brand";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="relative grid min-h-screen lg:grid-cols-[1.05fr_.95fr]">
      <section className="hidden overflow-hidden bg-forest p-12 text-white lg:flex lg:flex-col">
        <Brand />
        <div className="my-auto max-w-lg">
          <p className="text-sm font-extrabold uppercase tracking-[0.18em] text-[#a5d6a7]">
            Intelligence rooted in your farm
          </p>
          <h1 className="mt-6 text-5xl leading-[1.04] font-extrabold tracking-[-0.055em]">
            Make every field decision with confidence.
          </h1>
          <p className="mt-6 text-lg leading-8 text-white/70">
            One thoughtful workspace for farm health, weather, water, crops and timely agricultural
            guidance.
          </p>
        </div>
        <p className="text-xs text-white/55">CropNet AI · Agricultural intelligence platform</p>
      </section>
      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden">
            <Brand />
          </div>
          {children}
        </div>
      </section>
    </main>
  );
}
