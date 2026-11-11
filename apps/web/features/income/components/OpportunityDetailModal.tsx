"use client";

import {
  X,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Droplets,
  Coins,
  Scale,
  Zap,
  ShieldAlert,
  BookOpen,
  Calculator,
  GitCompareArrows,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DetailedOpportunity } from "../types";

interface OpportunityDetailModalProps {
  opportunity: DetailedOpportunity | null;
  onClose: () => void;
  onOpenCalculator: (opp: DetailedOpportunity) => void;
  onToggleCompare: (id: string) => void;
  isCompared: boolean;
}

export function OpportunityDetailModal({
  opportunity,
  onClose,
  onOpenCalculator,
  onToggleCompare,
  isCompared,
}: OpportunityDetailModalProps) {
  if (!opportunity) return null;
  const opp = opportunity;

  const minCost = opp.setup_investment_range?.min_inr ?? 0;
  const maxCost = opp.setup_investment_range?.max_inr ?? minCost;
  const minOpex = opp.recurring_operating_cost_range?.min_inr ?? 0;
  const maxOpex = opp.recurring_operating_cost_range?.max_inr ?? minOpex;
  const baseSurplus = opp.estimated_operating_surplus?.base_inr ?? 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="relative max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-3xl border border-line bg-white p-6 shadow-2xl sm:p-8">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-line pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="green" className="font-extrabold uppercase text-[10px]">
                {opp.category_name || opp.category.replace("_", " ")}
              </Badge>
              <span className="text-xs text-muted font-bold">
                {opp.confidence_classification.replace(/_/g, " ")}
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-ink leading-tight sm:text-2xl">
              {opp.name}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-muted hover:bg-canvas hover:text-ink"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div className="mt-5 space-y-6 text-xs text-ink">
          {/* Summary Box */}
          <div className="rounded-2xl bg-canvas p-4 border border-line/80">
            <h4 className="font-bold text-forest uppercase tracking-wider text-[11px]">
              What the Enterprise Involves
            </h4>
            <p className="mt-1.5 leading-relaxed text-ink font-medium">
              {opp.business_model}
            </p>
          </div>

          {/* Feasibility Assessment for Farmer's Plot */}
          <div className="space-y-3 rounded-2xl border border-line bg-white p-4">
            <h4 className="font-extrabold text-ink text-sm">
              Feasibility Diagnosis on Your Farm
            </h4>

            {opp.why_recommended?.length > 0 && (
              <div>
                <span className="font-bold text-forest text-[11px] block">
                  Why this enterprise fits:
                </span>
                <ul className="mt-1 space-y-1">
                  {opp.why_recommended.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-ink">
                      <CheckCircle2 size={13} className="shrink-0 text-leaf mt-0.5" />
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {opp.supporting_resources?.length > 0 && (
              <div>
                <span className="font-bold text-forest text-[11px] block">
                  Supporting farm resources present:
                </span>
                <ul className="mt-1 space-y-1">
                  {opp.supporting_resources.map((s, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-muted">
                      <CheckCircle2 size={13} className="shrink-0 text-leaf mt-0.5" />
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {opp.what_to_arrange?.length > 0 && (
              <div className="rounded-xl border border-accent/20 bg-[#fff8f5] p-3">
                <span className="font-bold text-accent text-[11px] block">
                  Action Checklist: What you need to arrange
                </span>
                <ul className="mt-1 space-y-1">
                  {opp.what_to_arrange.map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5 text-ink">
                      <AlertTriangle size={13} className="shrink-0 text-accent mt-0.5" />
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Financial Breakdown Grid */}
          <div>
            <h4 className="font-extrabold text-ink text-sm mb-3">
              Cost & Return Benchmark Breakdown
            </h4>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-xl border border-line bg-canvas p-3">
                <span className="block text-[10px] text-muted font-bold uppercase">Setup Capital</span>
                <span className="text-base font-extrabold text-ink block mt-0.5">
                  {minCost === 0 ? "₹0" : `₹${minCost.toLocaleString("en-IN")}`}
                </span>
                <span className="text-[10px] text-muted">Up to ₹{maxCost.toLocaleString("en-IN")}</span>
              </div>

              <div className="rounded-xl border border-line bg-canvas p-3">
                <span className="block text-[10px] text-muted font-bold uppercase">Annual Opex</span>
                <span className="text-base font-extrabold text-ink block mt-0.5">
                  ₹{minOpex.toLocaleString("en-IN")}
                </span>
                <span className="text-[10px] text-muted">Recurring outlays</span>
              </div>

              <div className="rounded-xl border border-line bg-canvas p-3">
                <span className="block text-[10px] text-muted font-bold uppercase">First Income</span>
                <span className="text-base font-extrabold text-accent block mt-0.5">
                  {opp.time_to_first_income_months} mo
                </span>
                <span className="text-[10px] text-muted">{opp.production_cycle_days} days cycle</span>
              </div>

              <div className="rounded-xl border border-leaf/40 bg-[#eef7ee] p-3">
                <span className="block text-[10px] text-forest font-bold uppercase">Est. Operating Surplus</span>
                <span className="text-base font-extrabold text-forest block mt-0.5">
                  ₹{baseSurplus.toLocaleString("en-IN")}
                </span>
                <span className="text-[10px] text-forest">Annual benchmark</span>
              </div>
            </div>
          </div>

          {/* Operational Details */}
          <div className="space-y-3 rounded-2xl border border-line p-4">
            <h4 className="font-extrabold text-ink text-sm">Operational Requirements</h4>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 text-xs">
              <div>
                <span className="font-bold text-muted block text-[11px]">Land & Space:</span>
                <span className="font-medium text-ink">{opp.unit_of_operation}</span>
              </div>
              <div>
                <span className="font-bold text-muted block text-[11px]">Water Need:</span>
                <span className="font-medium text-ink capitalize">{opp.water_requirement.replace("_", " ")}</span>
              </div>
              <div>
                <span className="font-bold text-muted block text-[11px]">Daily Labour:</span>
                <span className="font-medium text-ink">
                  {opp.labour_requirements?.daily_hours ?? 1} hours/day ({opp.labour_requirements?.skill_level ?? "basic"} skill)
                </span>
              </div>
              <div>
                <span className="font-bold text-muted block text-[11px]">Electricity:</span>
                <span className="font-medium text-ink capitalize">{opp.electricity_requirements.replace("_", " ")}</span>
              </div>
              <div>
                <span className="font-bold text-muted block text-[11px]">Target Geography:</span>
                <span className="font-medium text-ink">{opp.suitable_geography}</span>
              </div>
              <div>
                <span className="font-bold text-muted block text-[11px]">Market Channel:</span>
                <span className="font-medium text-ink capitalize">{opp.market_access_requirements.replace("_", " ")}</span>
              </div>
            </div>

            {opp.soil_climate_considerations && (
              <div className="mt-2 pt-2 border-t border-line text-[11px]">
                <span className="font-bold text-muted">Soil & Climate Note: </span>
                <span className="text-ink">{opp.soil_climate_considerations}</span>
              </div>
            )}
          </div>

          {/* Risks & Mitigations */}
          {opp.major_risks?.length > 0 && (
            <div className="rounded-2xl border border-[#fed7aa] bg-[#fffaf5] p-4">
              <div className="flex items-center gap-1.5 font-bold text-accent text-xs">
                <ShieldAlert size={15} />
                <span>Major Operational & Market Risks</span>
              </div>
              <ul className="mt-2 space-y-1.5 text-xs text-ink">
                {opp.major_risks.map((risk, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-accent font-bold">•</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Institutional Sources */}
          <div className="border-t border-line pt-3 text-[11px] text-muted space-y-1">
            <div className="flex items-center gap-1 font-bold text-ink">
              <BookOpen size={13} className="text-forest" />
              <span>Evidence & Verified Institutional Sources:</span>
            </div>
            <ul className="list-disc pl-4 space-y-0.5">
              {opp.source_references?.map((ref, i) => (
                <li key={i}>{ref}</li>
              ))}
            </ul>
            <p className="mt-1 text-[10px] text-muted italic">
              Verified against Maharashtra Agricultural University protocols and NABARD unit-cost guidelines (Updated {opp.last_verified_date}).
            </p>
          </div>
        </div>

        {/* Action Footer */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onToggleCompare(opp.opportunity_id)}
          >
            <GitCompareArrows size={14} />
            {isCompared ? "Remove from Compare" : "Compare with another"}
          </Button>

          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={() => {
                onClose();
                onOpenCalculator(opp);
              }}
            >
              <Calculator size={14} />
              Calculate for My Farm
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
