"use client";

import {
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Droplets,
  Coins,
  Scale,
  ArrowRight,
  Calculator,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DetailedOpportunity, FeasibilityStatus } from "../types";

interface OpportunityCardProps {
  opportunity: DetailedOpportunity;
  isCompared: boolean;
  onToggleCompare: (id: string) => void;
  onExplore: (opp: DetailedOpportunity) => void;
  onCalculate: (opp: DetailedOpportunity) => void;
}

export function OpportunityCard({
  opportunity,
  isCompared,
  onToggleCompare,
  onExplore,
  onCalculate,
}: OpportunityCardProps) {
  const opp = opportunity;
  const minCost = opp.setup_investment_range?.min_inr ?? 0;
  const maxCost = opp.setup_investment_range?.max_inr ?? minCost;
  const baseSurplus = opp.estimated_operating_surplus?.base_inr ?? 0;

  const renderFeasibilityBadge = (status: FeasibilityStatus) => {
    switch (status) {
      case "GOOD_POTENTIAL_FIT":
        return (
          <Badge variant="green" className="font-extrabold flex items-center gap-1">
            <CheckCircle2 size={12} /> Good Potential Fit
          </Badge>
        );
      case "POTENTIALLY_SUITABLE":
        return (
          <Badge variant="orange" className="font-extrabold flex items-center gap-1">
            <Info size={12} /> Potentially Suitable
          </Badge>
        );
      case "MORE_INFORMATION_REQUIRED":
        return (
          <Badge variant="neutral" className="font-extrabold">
            More Info Required
          </Badge>
        );
      case "NOT_SUITABLE":
      default:
        return (
          <Badge variant="outline" className="border-line font-bold text-muted">
            Not Currently Suitable
          </Badge>
        );
    }
  };

  return (
    <div className="flex flex-col justify-between rounded-2xl border border-line bg-white p-5 shadow-sm transition-all hover:border-leaf/40 hover:shadow-md">
      <div>
        {/* Category & Feasibility Row */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="rounded-md bg-[#edf5ed] px-2 py-0.5 text-[10px] font-extrabold text-forest uppercase tracking-wider">
            {opp.category_name || opp.category.replace("_", " ")}
          </span>
          {renderFeasibilityBadge(opp.feasibility_status)}
        </div>

        {/* Title & Description */}
        <h3 className="mt-3 text-base font-extrabold text-ink leading-snug line-clamp-2">
          {opp.name}
        </h3>
        <p className="mt-1 text-xs text-muted line-clamp-2 leading-relaxed">
          {opp.farmer_friendly_description}
        </p>

        {/* Key Metrics Grid */}
        <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-canvas p-2.5 text-xs">
          <div className="flex items-center gap-2">
            <Coins size={14} className="text-forest shrink-0" />
            <div className="min-w-0">
              <span className="block text-[10px] text-muted">Setup Capital</span>
              <span className="font-extrabold text-ink truncate block">
                {minCost === 0 ? "₹0 (Zero Cash)" : `₹${(minCost / 1000).toFixed(0)}k – ₹${(maxCost / 1000).toFixed(0)}k`}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Clock size={14} className="text-accent shrink-0" />
            <div className="min-w-0">
              <span className="block text-[10px] text-muted">Time to Income</span>
              <span className="font-extrabold text-ink truncate block">
                {opp.time_to_first_income_months} mo
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Scale size={14} className="text-soil shrink-0" />
            <div className="min-w-0">
              <span className="block text-[10px] text-muted">Typical Scale</span>
              <span className="font-extrabold text-ink truncate block">
                {opp.unit_of_operation}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Droplets size={14} className="text-calm shrink-0" />
            <div className="min-w-0">
              <span className="block text-[10px] text-muted">Water Needed</span>
              <span className="font-extrabold text-ink capitalize truncate block">
                {opp.water_requirement.replace("_", " ")}
              </span>
            </div>
          </div>
        </div>

        {/* Operating Surplus Highlight */}
        {baseSurplus > 0 && (
          <div className="mt-3 flex items-center justify-between rounded-xl border border-leaf/30 bg-[#f4f9f4] px-3 py-2 text-xs">
            <span className="font-bold text-forest text-[11px]">Est. Operating Surplus:</span>
            <span className="font-extrabold text-forest text-sm">
              ₹{baseSurplus.toLocaleString("en-IN")}/yr
            </span>
          </div>
        )}

        {/* Reason / Missing Check */}
        <div className="mt-3 text-[11px] leading-tight">
          {opp.feasibility_status === "GOOD_POTENTIAL_FIT" && opp.why_recommended?.length > 0 && (
            <p className="flex items-start gap-1 text-forest font-medium">
              <CheckCircle2 size={13} className="shrink-0 mt-0.5 text-leaf" />
              <span>{opp.why_recommended[0]}</span>
            </p>
          )}

          {opp.feasibility_status === "POTENTIALLY_SUITABLE" && opp.what_to_arrange?.length > 0 && (
            <p className="flex items-start gap-1 text-accent font-medium">
              <AlertTriangle size={13} className="shrink-0 mt-0.5" />
              <span>{opp.what_to_arrange[0]}</span>
            </p>
          )}

          {opp.feasibility_status === "NOT_SUITABLE" && opp.missing_requirements?.length > 0 && (
            <p className="flex items-start gap-1 text-muted font-medium">
              <Info size={13} className="shrink-0 mt-0.5" />
              <span>{opp.missing_requirements[0]}</span>
            </p>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="mt-5 border-t border-line pt-3 flex items-center justify-between gap-2">
        <label className="flex items-center gap-1.5 cursor-pointer text-xs font-semibold text-muted select-none">
          <input
            type="checkbox"
            checked={isCompared}
            onChange={() => onToggleCompare(opp.opportunity_id)}
            className="rounded border-line text-forest focus:ring-forest"
          />
          <span>Compare</span>
        </label>

        <div className="flex items-center gap-1.5">
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => onExplore(opp)}
            className="text-xs font-bold"
          >
            Explore
          </Button>

          <Button
            type="button"
            size="sm"
            variant="primary"
            onClick={() => onCalculate(opp)}
            className="text-xs font-bold"
          >
            <Calculator size={13} />
            Calculate
          </Button>
        </div>
      </div>
    </div>
  );
}
