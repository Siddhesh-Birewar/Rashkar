"use client";

import { useEffect, useState } from "react";
import { X, GitCompareArrows, CheckCircle2, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { incomeApi } from "../lib/api";
import type { OpportunityComparison } from "../types";

interface OpportunityCompareModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedIds: string[];
  allocatedAcres?: number;
  availableBudget?: number;
  onSelectForCalculate: (oppId: string) => void;
}

export function OpportunityCompareModal({
  isOpen,
  onClose,
  selectedIds,
  allocatedAcres = 0.5,
  availableBudget = 50000,
  onSelectForCalculate,
}: OpportunityCompareModalProps) {
  const [comparisons, setComparisons] = useState<OpportunityComparison[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!isOpen || selectedIds.length === 0) return;
    setLoading(true);
    incomeApi
      .compareOpportunities({
        opportunity_ids: selectedIds,
        allocated_acres: allocatedAcres,
        available_budget_inr: availableBudget,
      })
      .then((res) => setComparisons(res))
      .catch((e) => console.error("Compare error", e))
      .finally(() => setLoading(false));
  }, [isOpen, selectedIds, allocatedAcres, availableBudget]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="relative max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-3xl border border-line bg-white p-6 shadow-2xl sm:p-8">
        <div className="flex items-center justify-between border-b border-line pb-4">
          <div className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-lg bg-[#edf5ed] text-forest">
              <GitCompareArrows size={18} />
            </span>
            <div>
              <h2 className="text-xl font-extrabold text-ink">
                Side-by-Side Enterprise Comparison
              </h2>
              <p className="text-xs text-muted">
                Compare capital, recurring outlays, resource needs, and projected surplus across {comparisons.length} options
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-muted hover:bg-canvas hover:text-ink"
          >
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div className="py-24 text-center text-xs text-muted">
            Evaluating comparative enterprise metrics...
          </div>
        ) : comparisons.length === 0 ? (
          <div className="py-16 text-center text-xs text-muted">
            Please select at least 2 opportunities from the catalogue to compare.
          </div>
        ) : (
          <div className="mt-6 overflow-x-auto text-xs">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-line bg-canvas">
                  <th className="p-3 font-extrabold text-muted uppercase text-[10px] w-40">
                    Enterprise Criteria
                  </th>
                  {comparisons.map((c) => (
                    <th key={c.opportunity_id} className="p-3 font-extrabold text-ink min-w-[200px]">
                      <span className="block text-[10px] text-forest uppercase tracking-wider">
                        {c.category.replace("_", " ")}
                      </span>
                      <span className="text-sm font-extrabold block mt-0.5">{c.name}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {/* 1. Setup Investment */}
                <tr>
                  <td className="p-3 font-bold text-muted">Initial Setup Outlay</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-extrabold text-ink">
                      {c.setup_investment_min_inr === 0 ? (
                        <Badge variant="green">₹0 (Zero Cash)</Badge>
                      ) : (
                        `₹${c.setup_investment_min_inr.toLocaleString("en-IN")} – ₹${c.setup_investment_max_inr.toLocaleString("en-IN")}`
                      )}
                    </td>
                  ))}
                </tr>

                {/* 2. Annual Operating Opex */}
                <tr>
                  <td className="p-3 font-bold text-muted">Recurring Annual Opex</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-medium text-ink">
                      ₹{c.recurring_opex_typical_inr.toLocaleString("en-IN")}
                    </td>
                  ))}
                </tr>

                {/* 3. Est. Operating Surplus */}
                <tr className="bg-[#f4f9f4]">
                  <td className="p-3 font-bold text-forest">Est. Operating Surplus</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-extrabold text-forest text-sm">
                      ₹{c.estimated_operating_surplus_base_inr.toLocaleString("en-IN")}/yr
                    </td>
                  ))}
                </tr>

                {/* 4. Time to First Income */}
                <tr>
                  <td className="p-3 font-bold text-muted">Time to First Cash</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-bold text-accent">
                      {c.time_to_first_income_months} months
                    </td>
                  ))}
                </tr>

                {/* 5. Production Cycle */}
                <tr>
                  <td className="p-3 font-bold text-muted">Production Cycle</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-medium text-ink">
                      {c.production_cycle_days} days
                    </td>
                  ))}
                </tr>

                {/* 6. Scale & Unit */}
                <tr>
                  <td className="p-3 font-bold text-muted">Unit of Operation</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-medium text-ink">
                      {c.unit_of_operation}
                    </td>
                  ))}
                </tr>

                {/* 7. Water Needs */}
                <tr>
                  <td className="p-3 font-bold text-muted">Water Requirement</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-medium capitalize text-ink">
                      {c.water_requirement.replace("_", " ")}
                    </td>
                  ))}
                </tr>

                {/* 8. Daily Labour */}
                <tr>
                  <td className="p-3 font-bold text-muted">Daily Labour Needed</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-medium text-ink">
                      {c.labour_daily_hours} hrs/day
                    </td>
                  ))}
                </tr>

                {/* 9. Electricity */}
                <tr>
                  <td className="p-3 font-bold text-muted">Electricity Needed</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 font-medium capitalize text-ink">
                      {c.electricity_requirements.replace("_", " ")}
                    </td>
                  ))}
                </tr>

                {/* 10. Major Risk */}
                <tr>
                  <td className="p-3 font-bold text-muted">Major Operational Risk</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3 text-[11px] text-muted">
                      {c.major_risk}
                    </td>
                  ))}
                </tr>

                {/* 11. Actions */}
                <tr>
                  <td className="p-3 font-bold text-muted">Action</td>
                  {comparisons.map((c) => (
                    <td key={c.opportunity_id} className="p-3">
                      <Button
                        type="button"
                        size="sm"
                        variant="primary"
                        onClick={() => {
                          onClose();
                          onSelectForCalculate(c.opportunity_id);
                        }}
                        className="text-xs font-bold"
                      >
                        Calculate for Farm
                      </Button>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-6 flex justify-end border-t border-line pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            Close Comparison
          </Button>
        </div>
      </div>
    </div>
  );
}
