import {
  ArrowRight,
  BookOpenText,
  CloudSun,
  Droplets,
  Flame,
  Leaf,
  MapPinned,
  Plus,
  ScanSearch,
  Sprout,
  Stethoscope,
} from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/states";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionHeader } from "@/components/section-header";

const quickActions = [
  {
    label: "Add farm",
    helper: "Map a new field",
    href: "/farms/new",
    icon: Plus,
    tone: "green",
  },
  {
    label: "Crop Doctor",
    helper: "Check crop symptoms",
    href: "/crop-doctor",
    icon: Stethoscope,
    tone: "orange",
  },
  {
    label: "Heat Risk",
    helper: "Plan for hot days",
    href: "/heat-risk",
    icon: Flame,
    tone: "brown",
  },
] as const;

const intelligenceLinks = [
  {
    label: "Soil insights",
    href: "/farms/current/soil",
    icon: Leaf,
    description: "Reports and soil health",
  },
  {
    label: "Water planning",
    href: "/farms/current/water",
    icon: Droplets,
    description: "Irrigation guidance",
  },
  {
    label: "Farm health",
    href: "/farms/current/health",
    icon: ScanSearch,
    description: "Field condition overview",
  },
  {
    label: "Advisory",
    href: "/advisory",
    icon: BookOpenText,
    description: "Timely recommendations",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-7 sm:space-y-9">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Badge>Farm workspace</Badge>
          <h1 className="mt-3 text-[30px] leading-[1.08] font-extrabold tracking-[-0.05em] sm:text-[38px]">
            Welcome to CropNet
          </h1>
          <p className="mt-2 text-sm leading-6 text-muted sm:text-[15px]">
            Your farm intelligence will come together here.
          </p>
        </div>
        <Button asChild className="w-full sm:w-auto">
          <Link href="/farms/new">
            <Plus size={18} /> Add your first farm
          </Link>
        </Button>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.4fr_.6fr]">
        <Card
          className="relative overflow-hidden border-0 bg-forest bg-cover bg-center text-white shadow-[0_20px_45px_rgba(27,94,32,.18)]"
          style={{
            backgroundImage:
              "linear-gradient(90deg, rgba(21,60,43,.98) 0%, rgba(21,60,43,.9) 52%, rgba(21,60,43,.32) 100%), url('https://images.unsplash.com/photo-1694153491575-1eb69655e4f0?auto=format&fit=crop&w=1400&q=80')",
          }}
        >
          <div className="absolute -top-14 -right-16 size-60 rounded-full border-[38px] border-white/5" />
          <div className="absolute -right-6 -bottom-16 size-40 rounded-full bg-[#4d9c52]/25 blur-sm" />
          <CardContent className="relative p-6 sm:p-8">
            <div className="flex items-start justify-between gap-4">
              <span className="grid size-11 place-items-center rounded-2xl bg-white/12">
                <MapPinned size={21} className="text-[#b7dfb9]" />
              </span>
              <Badge className="bg-white/12 text-white">No farm selected</Badge>
            </div>
            <div className="mt-10 max-w-md">
              <h2 className="text-2xl font-extrabold tracking-[-0.04em] sm:text-3xl">
                Start with your farm
              </h2>
              <p className="mt-3 text-sm leading-6 text-white/70">
                Add a farm to unlock location-aware weather, soil information, crop health and
                practical recommendations.
              </p>
              <Link
                href="/farms/new"
                className="mt-6 inline-flex min-h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-extrabold text-forest transition-transform active:scale-[.98]"
              >
                Set up a farm <ArrowRight size={17} />
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex h-full min-h-64 flex-col">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-muted">
                  Weather
                </p>
                <h2 className="mt-1 font-extrabold">Today&apos;s outlook</h2>
              </div>
              <span className="grid size-11 place-items-center rounded-2xl bg-[#edf5ed] text-leaf">
                <CloudSun size={22} />
              </span>
            </div>
            <div className="my-auto py-6 text-center">
              <p className="text-4xl font-extrabold text-[#c3cec4]">—</p>
              <p className="mt-3 text-sm font-bold">Location needed</p>
              <p className="mt-1 text-xs leading-5 text-muted">
                Select a farm to see local conditions.
              </p>
            </div>
            <Link
              href="/farms"
              className="flex min-h-11 items-center justify-center rounded-xl bg-[#f0f5f0] text-xs font-extrabold text-forest"
            >
              Choose a farm
            </Link>
          </CardContent>
        </Card>
      </section>

      <section>
        <SectionHeader title="Quick actions" description="Common tasks, always within reach" />
        <div className="grid grid-cols-1 gap-3 min-[390px]:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.label}
                href={action.href}
                className="group rounded-card border border-line bg-white p-4 shadow-[0_8px_24px_rgba(27,65,32,.045)] transition-transform hover:-translate-y-0.5"
              >
                <span
                  className={
                    action.tone === "green"
                      ? "grid size-10 place-items-center rounded-xl bg-[#e9f4e9] text-leaf"
                      : action.tone === "orange"
                        ? "grid size-10 place-items-center rounded-xl bg-[#fff0e8] text-accent"
                        : "grid size-10 place-items-center rounded-xl bg-[#f3ece9] text-soil"
                  }
                >
                  <Icon size={19} />
                </span>
                <p className="mt-4 text-sm font-extrabold">{action.label}</p>
                <p className="mt-1 text-[11px] leading-4 text-muted">{action.helper}</p>
              </Link>
            );
          })}
        </div>
      </section>

      <section>
        <SectionHeader title="Crop intelligence" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {intelligenceLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                href={item.href}
                key={item.label}
                className="flex min-h-20 items-center gap-4 rounded-2xl border border-line bg-white p-4 shadow-[0_8px_24px_rgba(27,65,32,.04)] hover:border-[#b9d2ba]"
              >
                <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-[#edf5ed] text-forest">
                  <Icon size={20} />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-extrabold">{item.label}</span>
                  <span className="mt-1 block text-[11px] text-muted">{item.description}</span>
                </span>
                <ArrowRight size={16} className="ml-auto shrink-0 text-[#9aab9c]" />
              </Link>
            );
          })}
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <div>
          <SectionHeader title="Important advisories" />
          <Card>
            <EmptyState
              icon={Sprout}
              title="No advisories yet"
              description="Important recommendations will appear once a farm and crop profile are connected."
            />
          </Card>
        </div>
        <div>
          <SectionHeader title="Recent activity" />
          <Card>
            <EmptyState
              icon={BookOpenText}
              title="No recent activity"
              description="Reports, diagnoses and farm updates will be collected here as you use CropNet."
            />
          </Card>
        </div>
      </section>
    </div>
  );
}
