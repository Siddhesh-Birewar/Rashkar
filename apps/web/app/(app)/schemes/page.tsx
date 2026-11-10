"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import {
  Building2,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  FileCheck2,
  Filter,
  Landmark,
  Search,
  ShieldCheck,
  Sparkles,
  Tag,
  X,
} from "lucide-react";
import { schemesApi } from "@/lib/api/client";
import type { GovernmentScheme, SchemeFilters } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export default function SchemesPage() {
  const [schemes, setSchemes] = useState<GovernmentScheme[]>([]);
  const [filters, setFilters] = useState<SchemeFilters | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedLevel, setSelectedLevel] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const [schemesData, filtersData] = await Promise.all([
          schemesApi.list(),
          schemesApi.getFilters(),
        ]);
        setSchemes(schemesData);
        setFilters(filtersData);
      } catch (err: any) {
        console.error("Failed to load government schemes:", err);
        setError(err.message || "Failed to load government schemes. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredSchemes = useMemo(() => {
    return schemes.filter((s) => {
      if (selectedCategory !== "All" && s.category !== selectedCategory) {
        return false;
      }
      if (selectedLevel !== "All" && s.government_level !== selectedLevel) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const inName = s.scheme_name.toLowerCase().includes(q);
        const inDesc = s.description?.toLowerCase().includes(q) || false;
        const inDept = s.department?.toLowerCase().includes(q) || false;
        const inCat = s.category.toLowerCase().includes(q);
        return inName || inDesc || inDept || inCat;
      }
      return true;
    });
  }, [schemes, selectedCategory, selectedLevel, searchQuery]);

  const categories = useMemo(() => {
    if (!filters?.categories) return ["All"];
    return ["All", ...filters.categories];
  }, [filters]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-1.5 rounded-full bg-[#e8f5e9] px-3 py-1 text-xs font-bold text-[#1b5e20]">
          <Landmark size={14} />
          Government Support
        </div>
        <h1 className="mt-2 text-2xl font-black tracking-tight text-[#111827] sm:text-3xl">
          Government Schemes
        </h1>
        <p className="mt-1 text-sm text-[#4b5563]">
          Find verified central and state welfare schemes, eligibility criteria, required documents, and official application portals.
        </p>
      </div>

      {/* Verified Banner */}
      <div className="flex items-start gap-3 rounded-2xl border border-[#c8e6c9] bg-[#f1f8e9] p-4 text-xs text-[#2e7d32]">
        <ShieldCheck size={20} className="shrink-0 text-[#2e7d32]" />
        <div>
          <p className="font-bold text-[#1b5e20]">Verified official sources only</p>
          <p className="mt-0.5 leading-relaxed text-[#388e3c]">
            All scheme details, subsidy calculations, and guidelines are indexed from official Ministry and Maharashtra State gazette notifications.
          </p>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="space-y-3 rounded-2xl border border-[#dde7df] bg-white p-4 shadow-sm">
        <div className="relative flex items-center">
          <Search size={18} className="absolute left-3.5 text-[#9ca3af]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by scheme name, subsidy, or department..."
            className="w-full rounded-xl border border-[#e5e7eb] bg-[#f9fafb] py-2.5 pr-10 pl-10 text-sm text-[#111827] placeholder:text-[#9ca3af] focus:border-[#2e7d32] focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#2e7d32]"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 text-[#9ca3af] hover:text-[#4b5563]"
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Level Filters */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-bold text-[#6b7280]">Level:</span>
          {["All", "Central", "State"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSelectedLevel(lvl)}
              className={cn(
                "rounded-lg px-3 py-1 text-xs font-bold transition-all",
                selectedLevel === lvl
                  ? "bg-[#1b5e20] text-white shadow-sm"
                  : "bg-[#f3f4f6] text-[#4b5563] hover:bg-[#e5e7eb]",
              )}
            >
              {lvl === "State" ? "Maharashtra State" : lvl === "All" ? "All Levels" : "Central Gov"}
            </button>
          ))}
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={cn(
                "shrink-0 rounded-full px-3.5 py-1.5 font-bold transition-all",
                selectedCategory === cat
                  ? "bg-[#2e7d32] text-white shadow-sm"
                  : "bg-[#f1f6f1] text-[#374151] hover:bg-[#e5efe5]",
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs font-bold text-[#6b7280]">
        <span>
          Showing {filteredSchemes.length} of {schemes.length} verified schemes
        </span>
        {selectedCategory !== "All" || selectedLevel !== "All" || searchQuery ? (
          <button
            onClick={() => {
              setSelectedCategory("All");
              setSelectedLevel("All");
              setSearchQuery("");
            }}
            className="text-[#2e7d32] hover:underline"
          >
            Reset all filters
          </button>
        ) : null}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-44 animate-pulse rounded-2xl border border-[#dde7df] bg-white p-5"
            />
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm font-bold text-red-800">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-3 rounded-xl bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-700"
          >
            Reload Schemes
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredSchemes.length === 0 && (
        <div className="rounded-2xl border border-dashed border-[#dde7df] bg-white py-12 text-center">
          <Landmark size={36} className="mx-auto text-[#9ca3af]" />
          <h3 className="mt-3 text-base font-bold text-[#111827]">No schemes found</h3>
          <p className="mt-1 text-xs text-[#6b7280]">
            No government schemes match the selected category or search query.
          </p>
          <button
            onClick={() => {
              setSelectedCategory("All");
              setSelectedLevel("All");
              setSearchQuery("");
            }}
            className="mt-4 rounded-xl bg-[#e8f5e9] px-4 py-2 text-xs font-bold text-[#1b5e20] hover:bg-[#c8e6c9]"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Scheme Cards */}
      {!loading && !error && filteredSchemes.length > 0 && (
        <div className="space-y-4">
          {filteredSchemes.map((scheme) => (
            <div
              key={scheme.id}
              className="group relative flex flex-col justify-between rounded-2xl border border-[#dde7df] bg-white p-5 shadow-sm transition-all hover:border-[#81c784] hover:shadow-md"
            >
              <div>
                {/* Badges */}
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      "rounded-md px-2 py-0.5 text-[11px] font-bold",
                      scheme.government_level === "Central"
                        ? "bg-[#e0f2fe] text-[#0369a1]"
                        : "bg-[#fef3c7] text-[#b45309]",
                    )}
                  >
                    {scheme.government_level === "Central"
                      ? "Central Government"
                      : `State (${scheme.state || "Maharashtra"})`}
                  </span>
                  <span className="rounded-md bg-[#f3f4f6] px-2 py-0.5 text-[11px] font-bold text-[#4b5563]">
                    {scheme.category}
                  </span>
                  <span className="inline-flex items-center gap-1 rounded-md bg-[#e8f5e9] px-2 py-0.5 text-[11px] font-bold text-[#1b5e20]">
                    <CheckCircle2 size={12} />
                    Verified
                  </span>
                </div>

                {/* Title */}
                <h2 className="mt-3 text-lg font-black text-[#111827] group-hover:text-[#1b5e20]">
                  <Link href={`/schemes/${scheme.id}`} className="hover:underline">
                    {scheme.scheme_name}
                  </Link>
                </h2>

                {/* Department */}
                {scheme.department && (
                  <p className="mt-1 flex items-center gap-1.5 text-xs text-[#6b7280]">
                    <Building2 size={13} className="shrink-0 text-[#9ca3af]" />
                    <span className="truncate">{scheme.department}</span>
                  </p>
                )}

                {/* Description */}
                {scheme.description && (
                  <p className="mt-2 text-xs leading-relaxed text-[#4b5563]">
                    {scheme.description}
                  </p>
                )}

                {/* Benefits bullets if available */}
                {scheme.benefits && scheme.benefits.length > 0 && (
                  <div className="mt-3 rounded-xl bg-[#f9fafb] p-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-[#6b7280]">
                      Key Benefits
                    </p>
                    <ul className="mt-1.5 space-y-1 text-xs text-[#374151]">
                      {scheme.benefits.slice(0, 2).map((b, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="mt-1 size-1.5 shrink-0 rounded-full bg-[#2e7d32]" />
                          <span>{b}</span>
                        </li>
                      ))}
                      {scheme.benefits.length > 2 && (
                        <li className="text-[11px] font-medium text-[#6b7280]">
                          +{scheme.benefits.length - 2} more verified benefits...
                        </li>
                      )}
                    </ul>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#f3f4f6] pt-3">
                <Link
                  href={`/schemes/${scheme.id}`}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-[#e8f5e9] px-3.5 py-2 text-xs font-bold text-[#1b5e20] transition-colors hover:bg-[#c8e6c9]"
                >
                  View Eligibility & Documents
                  <ChevronRight size={14} />
                </Link>

                {scheme.application_url && (
                  <a
                    href={scheme.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2e7d32] hover:text-[#1b5e20] hover:underline"
                  >
                    Official Portal
                    <ExternalLink size={13} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
