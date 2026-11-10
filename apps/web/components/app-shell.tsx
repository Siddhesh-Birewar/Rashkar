"use client";

import {
  Bell,
  BookOpenText,
  Bot,
  ChevronRight,
  CircleDollarSign,
  CloudSun,
  Droplets,
  Ellipsis,
  FileClock,
  Flame,
  HelpCircle,
  HeartPulse,
  Home,
  Landmark,
  Leaf,
  LogOut,
  Menu,
  Settings,
  Satellite,
  Sprout,
  Stethoscope,
  UserRound,
  Wheat,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "@/components/brand";
import { FarmSelector } from "@/components/farm-selector";
import { CropNetChatbot } from "@/components/chatbot";
import { useAuth } from "@/lib/auth-context";
import { useFarm } from "@/lib/farm-context";
import {
  BottomSheet,
  BottomSheetContent,
  BottomSheetDescription,
  BottomSheetTitle,
  BottomSheetTrigger,
} from "@/components/ui/bottom-sheet";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

function NavLink({ item, compact = false }: { item: NavItem; compact?: boolean }) {
  const pathname = usePathname();
  const active = isActive(pathname, item.href);
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={cn(
        "group flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-bold transition-colors",
        active ? "bg-[#e8f3e8] text-forest" : "text-muted hover:bg-[#f1f6f1] hover:text-ink",
        compact && "justify-center px-0",
      )}
      title={compact ? item.label : undefined}
    >
      <Icon
        size={19}
        strokeWidth={active ? 2.5 : 2}
        className={active ? "text-leaf" : "text-[#718374]"}
      />
      {!compact && <span>{item.label}</span>}
    </Link>
  );
}

function AccountDialog() {
  const { user, signOut, isDevMode } = useAuth();

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          className="flex min-h-11 items-center gap-3 rounded-xl px-2 text-left hover:bg-[#eff5ef]"
          aria-label="Open account menu"
        >
          <span className="grid size-9 place-items-center rounded-xl bg-[#e7f1e7] text-forest">
            <UserRound size={18} />
          </span>
          <span className="hidden xl:block">
            <span className="block text-xs font-extrabold">{user?.email || "Account"}</span>
            <span className="block text-[10px] text-muted">
              {isDevMode ? "Local Dev Mode" : "Farmer Profile"}
            </span>
          </span>
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Account Profile</DialogTitle>
        <DialogDescription>
          {user ? `Signed in as ${user.email} (${user.id.slice(0, 8)}...)` : "Not currently signed in"}
        </DialogDescription>
        <div className="mt-6 grid gap-2">
          <Link
            href="/profile"
            className="flex min-h-12 items-center gap-3 rounded-xl bg-[#f3f7f3] px-4 text-sm font-bold"
          >
            <Settings size={18} className="text-leaf" />
            Account settings & dev bypass
          </Link>
          <Link
            href="/help"
            className="flex min-h-12 items-center gap-3 rounded-xl px-4 text-sm font-bold hover:bg-[#f3f7f3]"
          >
            <HelpCircle size={18} className="text-leaf" />
            Help & agronomic support
          </Link>
          <button
            onClick={() => signOut()}
            className="flex min-h-12 items-center gap-3 rounded-xl px-4 text-sm font-bold text-accent hover:bg-[#fff3ec] text-left w-full"
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function NotificationsDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          className="relative grid size-11 place-items-center rounded-xl border border-line bg-white text-forest shadow-sm hover:bg-[#f3f7f3]"
          aria-label="Open notifications"
        >
          <Bell size={19} />
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Farm Alerts & Advisories</DialogTitle>
        <DialogDescription>
          Important crop alerts, heat warnings, and scheme deadlines.
        </DialogDescription>
        <div className="mt-6 rounded-2xl border border-dashed border-line bg-canvas px-5 py-8 text-center">
          <Bell size={22} className="mx-auto text-[#93a395]" />
          <p className="mt-3 text-sm font-bold">You&apos;re all caught up</p>
          <p className="mt-1 text-xs leading-5 text-muted">No pending critical warnings for your selected farm.</p>
        </div>
        <Link
          href="/notifications"
          className="mt-4 flex min-h-11 items-center justify-center rounded-xl bg-[#edf5ed] text-xs font-extrabold text-forest"
        >
          Notification settings
        </Link>
      </DialogContent>
    </Dialog>
  );
}

function MoreSheet({ intelligenceNav }: { intelligenceNav: NavItem[] }) {
  const pathname = usePathname();

  return (
    <BottomSheet>
      <BottomSheetTrigger asChild>
        <button
          className="flex min-h-12 flex-1 flex-col items-center justify-center gap-1 rounded-xl text-[10px] font-bold text-muted"
          aria-label="Open more menu"
        >
          <Ellipsis size={21} />
          More
        </button>
      </BottomSheetTrigger>
      <BottomSheetContent>
        <BottomSheetTitle>Farm Intelligence</BottomSheetTitle>
        <BottomSheetDescription>
          All diagnostic modules and decision tools.
        </BottomSheetDescription>
        <div className="mt-6 grid grid-cols-2 gap-2.5">
          {intelligenceNav.map((item) => {
            const Icon = item.icon;
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                className={cn(
                  "flex min-h-14 items-center gap-3 rounded-2xl border border-line bg-white p-3 text-xs font-bold shadow-sm",
                  active && "border-leaf bg-[#eef7ee] text-forest",
                )}
              >
                <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-[#edf5ed] text-leaf">
                  <Icon size={18} />
                </span>
                <span className="min-w-0 truncate">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </BottomSheetContent>
    </BottomSheet>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { selectedFarmId } = useFarm();
  const farmIdParam = selectedFarmId || "current";

  const primaryNav: NavItem[] = [
    { label: "Home", href: "/", icon: Home },
    { label: "Farms", href: "/farms", icon: Sprout },
    { label: "Advisory", href: "/advisory", icon: BookOpenText },
    { label: "Assistant", href: "/assistant", icon: Bot },
  ];

  const intelligenceNav: NavItem[] = [
    { label: "AI Assistant", href: "/assistant", icon: Bot },
    { label: "Soil", href: `/farms/${farmIdParam}/soil`, icon: Leaf },
    { label: "Weather", href: `/farms/${farmIdParam}/weather`, icon: CloudSun },
    { label: "Farm health", href: `/farms/${farmIdParam}/health`, icon: HeartPulse },
    { label: "Water", href: `/farms/${farmIdParam}/water`, icon: Droplets },
    { label: "Satellite", href: `/farms/${farmIdParam}/vegetation`, icon: Satellite },
    { label: "Crop catalogue", href: "/crops", icon: Wheat },
    { label: "Crop Doctor", href: "/crop-doctor", icon: Stethoscope },
    { label: "Heat Risk", href: "/heat-risk", icon: Flame },
    { label: "Schemes", href: "/schemes", icon: Landmark },
    { label: "Income", href: "/income", icon: CircleDollarSign },
    { label: "History", href: "/history", icon: FileClock },
    { label: "Profile & settings", href: "/profile", icon: Settings },
  ];

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[272px] overflow-y-auto border-r border-line bg-white/95 px-5 py-6 backdrop-blur lg:flex lg:flex-col">
        <Brand />
        <nav className="mt-9 space-y-1">
          <p className="mb-3 px-3 text-[10px] font-extrabold uppercase tracking-[0.18em] text-[#8a9b8d]">
            Workspace
          </p>
          {primaryNav.map((item) => (
            <NavLink key={item.label} item={item} />
          ))}
        </nav>
        <nav className="mt-7 space-y-1">
          <p className="mb-3 px-3 text-[10px] font-extrabold uppercase tracking-[0.18em] text-[#8a9b8d]">
            Farm intelligence
          </p>
          {intelligenceNav.map((item) => (
            <NavLink key={item.label} item={item} />
          ))}
        </nav>
        <div className="mt-auto rounded-2xl bg-forest p-4 text-white">
          <Bot size={21} className="text-[#a5d6a7]" />
          <p className="mt-3 text-sm font-extrabold">Need crop help?</p>
          <p className="mt-1 text-[11px] leading-5 text-white/70">Photograph a symptom for rapid diagnosis.</p>
          <Link
            href="/crop-doctor"
            className="mt-3 flex min-h-9 items-center justify-between rounded-lg bg-white/12 px-3 text-xs font-bold hover:bg-white/18"
          >
            Open Crop Doctor <ChevronRight size={15} />
          </Link>
        </div>
      </aside>

      <aside className="fixed inset-y-0 left-0 z-40 hidden w-20 border-r border-line bg-white px-3 py-5 md:flex md:flex-col lg:hidden">
        <Brand compact />
        <nav className="mt-8 space-y-2">
          {[...primaryNav, ...intelligenceNav.slice(0, 5)].map((item) => (
            <NavLink key={item.label} item={item} compact />
          ))}
        </nav>
      </aside>

      <div className="md:pl-20 lg:pl-[272px]">
        <header className="sticky top-0 z-30 border-b border-line/80 bg-canvas/90 backdrop-blur-xl">
          <div className="mx-auto flex h-[72px] max-w-[1440px] items-center gap-3 px-4 sm:px-6 lg:px-8">
            <div className="mr-auto md:hidden">
              <Brand />
            </div>
            <div className="hidden md:block">
              <FarmSelector />
            </div>
            <div className="ml-auto flex items-center gap-2">
              <Link
                href="/assistant"
                className="hidden min-h-11 items-center gap-2 rounded-xl border border-[#c8e6c9] bg-[#e8f5e9] px-3 text-xs font-extrabold text-[#1b5e20] sm:flex"
              >
                <Bot size={17} />
                AI Assistant
              </Link>
              <Link
                href="/crop-doctor"
                className="hidden min-h-11 items-center gap-2 rounded-xl border border-[#f3d6c4] bg-[#fff7f2] px-3 text-xs font-extrabold text-accent sm:flex"
              >
                <Stethoscope size={17} />
                Crop Doctor
              </Link>
              <Link
                href="/heat-risk"
                className="hidden size-11 place-items-center rounded-xl border border-line bg-white text-accent shadow-sm sm:grid"
                aria-label="Open heat risk"
              >
                <Flame size={19} />
              </Link>
              <NotificationsDialog />
              <AccountDialog />
            </div>
          </div>
          <div className="px-4 pb-3 md:hidden">
            <FarmSelector />
          </div>
        </header>

        <main className="mx-auto min-h-[calc(100vh-72px)] max-w-[1440px] px-4 pt-6 pb-28 sm:px-6 sm:pt-8 md:pb-10 lg:px-8">
          {children}
        </main>
      </div>

      <nav className="safe-bottom fixed right-0 bottom-0 left-0 z-40 flex min-h-[68px] items-start border-t border-line bg-white/96 px-2 pt-1.5 shadow-[0_-10px_30px_rgba(24,60,29,.08)] backdrop-blur-xl md:hidden">
        {primaryNav.map((item) => {
          const Icon = item.icon;
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "flex min-h-12 flex-1 flex-col items-center justify-center gap-1 rounded-xl text-[10px] font-bold",
                active ? "text-forest" : "text-muted",
              )}
            >
              <Icon size={21} strokeWidth={active ? 2.6 : 2} />
              {item.label}
            </Link>
          );
        })}
        <MoreSheet intelligenceNav={intelligenceNav} />
      </nav>

      {/* Floating Global Agricultural AI Assistant */}
      <CropNetChatbot />
    </div>
  );
}
