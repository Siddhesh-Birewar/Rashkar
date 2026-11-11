"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  ExternalLink,
  FileCheck2,
  HelpCircle,
  Landmark,
  ListChecks,
  ShieldCheck,
  Tag,
  AlertTriangle,
} from "lucide-react";
import { schemesApi } from "@/lib/api/client";
import type { GovernmentScheme } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { BackButton } from "@/components/back-button";

export default function SchemeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const schemeId = params?.schemeId as string;

  const [scheme, setScheme] = useState<GovernmentScheme | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!schemeId) return;

    async function loadScheme() {
      try {
        setLoading(true);
        setError(null);
        const data = await schemesApi.get(schemeId);
        setScheme(data);
      } catch (err: any) {
        console.error("Failed to load scheme details:", err);
        setError(err.message || "Failed to load scheme details.");
      } finally {
        setLoading(false);
      }
    }

    loadScheme();
  }, [schemeId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="h-6 w-32 animate-pulse rounded-lg bg-gray-200" />
        <div className="h-10 w-3/4 animate-pulse rounded-xl bg-gray-200" />
        <div className="h-48 animate-pulse rounded-2xl bg-gray-100" />
      </div>
    );
  }

  if (error || !scheme) {
    return (
      <div className="mx-auto max-w-2xl rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
        <AlertTriangle size={32} className="mx-auto text-red-600" />
        <h2 className="mt-2 text-base font-bold text-red-800">Scheme not found</h2>
        <p className="mt-1 text-xs text-red-700">{error || "Could not find details for this scheme."}</p>
        <BackButton
          fallbackHref="/schemes"
          variant="pill"
          label="Back to all schemes"
          className="mt-4 bg-[#1b5e20] text-white hover:bg-[#2e7d32]"
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Back button */}
      <div>
        <BackButton
          fallbackHref="/schemes"
          variant="pill"
          label="Back to Government Schemes"
        />
      </div>

      {/* Main Card Header */}
      <div className="rounded-3xl border border-[#dde7df] bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-bold",
              scheme.government_level === "Central"
                ? "bg-[#e0f2fe] text-[#0369a1]"
                : "bg-[#fef3c7] text-[#b45309]",
            )}
          >
            {scheme.government_level === "Central"
              ? "Central Government"
              : `State (${scheme.state || "Maharashtra"})`}
          </span>
          <span className="rounded-md bg-[#f3f4f6] px-2.5 py-1 text-xs font-bold text-[#4b5563]">
            {scheme.category}
          </span>
          <span className="inline-flex items-center gap-1 rounded-md bg-[#e8f5e9] px-2.5 py-1 text-xs font-bold text-[#1b5e20]">
            <CheckCircle2 size={13} />
            Verified Source
          </span>
        </div>

        <h1 className="mt-4 text-2xl font-black text-[#111827] sm:text-3xl">
          {scheme.scheme_name}
        </h1>

        {scheme.department && (
          <p className="mt-2 flex items-center gap-2 text-xs text-[#6b7280]">
            <Building2 size={15} className="shrink-0 text-[#9ca3af]" />
            <span>{scheme.department}</span>
          </p>
        )}

        {scheme.description && (
          <p className="mt-4 text-sm leading-relaxed text-[#374151]">
            {scheme.description}
          </p>
        )}

        {/* Verification Footer */}
        {scheme.last_verified_date && (
          <div className="mt-5 flex items-center gap-2 border-t border-[#f3f4f6] pt-3 text-[11px] text-[#9ca3af]">
            <Calendar size={13} />
            <span>
              Last verified with official gazette:{" "}
              {new Date(scheme.last_verified_date).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </span>
          </div>
        )}
      </div>

      {/* Benefits Section */}
      {scheme.benefits && scheme.benefits.length > 0 && (
        <div className="rounded-2xl border border-[#dde7df] bg-white p-6 shadow-sm">
          <h2 className="flex items-center gap-2 text-base font-black text-[#111827]">
            <ListChecks size={18} className="text-[#2e7d32]" />
            Key Scheme Benefits & Subsidies
          </h2>
          <ul className="mt-4 space-y-2.5 text-sm text-[#374151]">
            {scheme.benefits.map((benefit, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[#2e7d32]" />
                <span className="leading-snug">{benefit}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Eligibility Section */}
      {scheme.eligibility && scheme.eligibility.length > 0 && (
        <div className="rounded-2xl border border-[#dde7df] bg-white p-6 shadow-sm">
          <h2 className="flex items-center gap-2 text-base font-black text-[#111827]">
            <ShieldCheck size={18} className="text-[#0284c7]" />
            Eligibility Criteria
          </h2>
          <ul className="mt-4 space-y-2.5 text-sm text-[#374151]">
            {scheme.eligibility.map((criterion, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <span className="mt-1 size-2 shrink-0 rounded-full bg-[#0284c7]" />
                <span className="leading-snug">{criterion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Required Documents Section */}
      {scheme.required_documents && scheme.required_documents.length > 0 && (
        <div className="rounded-2xl border border-[#dde7df] bg-white p-6 shadow-sm">
          <h2 className="flex items-center gap-2 text-base font-black text-[#111827]">
            <FileCheck2 size={18} className="text-[#d97706]" />
            Required Documents Checklist
          </h2>
          <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
            {scheme.required_documents.map((doc, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 rounded-xl bg-[#fefce8] p-3 text-xs font-bold text-[#854d0e]"
              >
                <FileCheck2 size={15} className="shrink-0 text-[#ca8a04]" />
                <span>{doc}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Application Steps */}
      {scheme.application_steps && scheme.application_steps.length > 0 && (
        <div className="rounded-2xl border border-[#dde7df] bg-white p-6 shadow-sm">
          <h2 className="flex items-center gap-2 text-base font-black text-[#111827]">
            <HelpCircle size={18} className="text-[#7c3aed]" />
            How to Apply
          </h2>
          <ol className="mt-4 space-y-3">
            {scheme.application_steps.map((step, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-[#374151]">
                <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[#f3e8ff] text-xs font-black text-[#7c3aed]">
                  {idx + 1}
                </span>
                <span className="pt-0.5 leading-snug">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Official Links & Actions */}
      <div className="flex flex-col gap-3 rounded-2xl border border-[#bbf7d0] bg-[#f0fdf4] p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-black text-[#166534]">Official Application Portal</p>
          <p className="mt-0.5 text-xs text-[#15803d]">
            Direct link to the verified ministry or state department portal.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {scheme.application_url && (
            <a
              href={scheme.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-[#16a34a] px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[#15803d]"
            >
              Apply on Official Portal
              <ExternalLink size={14} />
            </a>
          )}
          {scheme.source_url && scheme.source_url !== scheme.application_url && (
            <a
              href={scheme.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-[#bbf7d0] bg-white px-3.5 py-2.5 text-xs font-bold text-[#166534] hover:bg-[#f0fdf4]"
            >
              Guidelines Source
              <ExternalLink size={14} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
