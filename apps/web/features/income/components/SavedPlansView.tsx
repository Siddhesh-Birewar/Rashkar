"use client";

import { useState } from "react";
import {
  FileCheck2,
  Trash2,
  Calculator,
  Calendar,
  Coins,
  TrendingUp,
  Sprout,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/states";
import type { SavedPlan } from "../types";

interface SavedPlansViewProps {
  plans: SavedPlan[];
  onDeletePlan: (planId: string) => Promise<void>;
  onSelectPlanToRecalculate: (oppId: string) => void;
  onExploreCatalogue: () => void;
}

export function SavedPlansView({
  plans,
  onDeletePlan,
  onSelectPlanToRecalculate,
  onExploreCatalogue,
}: SavedPlansViewProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (planId: string) => {
    if (!confirm("Are you sure you want to delete this saved business plan?")) return;
    setDeletingId(planId);
    try {
      await onDeletePlan(planId);
    } finally {
      setDeletingId(null);
    }
  };

  if (plans.length === 0) {
    return (
      <EmptyState
        icon={Sprout}
        title="No Saved Business Plans Yet"
        description="Explore the diversification catalogue, run the scenario calculator for your farm, and save tailored business plans to track your progress."
        action={
          <Button type="button" variant="primary" onClick={onExploreCatalogue}>
            Browse Opportunity Catalogue
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-extrabold text-ink">
            Saved Farm Business Plans ({plans.length})
          </h3>
          <p className="text-xs text-muted">
            Personalized financial scenarios and diversification plans recorded for this farm
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {plans.map((plan) => (
          <div
            key={plan.plan_id}
            className="flex flex-col justify-between rounded-2xl border border-line bg-white p-5 shadow-sm transition-all hover:border-leaf/40 hover:shadow-md text-xs"
          >
            <div>
              <div className="flex items-center justify-between">
                <Badge variant="green" className="font-extrabold text-[10px] uppercase">
                  {plan.category.replace("_", " ")}
                </Badge>
                <span className="flex items-center gap-1 text-[10px] text-muted font-bold">
                  <Calendar size={11} />
                  {plan.created_at_utc ? new Date(plan.created_at_utc).toLocaleDateString("en-IN") : "Saved"}
                </span>
              </div>

              <h4 className="mt-3 text-sm font-extrabold text-ink leading-snug">
                {plan.opportunity_title}
              </h4>

              {plan.notes && (
                <p className="mt-1 text-[11px] text-muted italic line-clamp-2">
                  "{plan.notes}"
                </p>
              )}

              <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-canvas p-2.5">
                <div>
                  <span className="block text-[10px] text-muted">Budget Outlay</span>
                  <span className="font-extrabold text-ink block truncate">
                    {plan.chosen_budget_inr === 0
                      ? "₹0 (Zero Cash)"
                      : `₹${plan.chosen_budget_inr.toLocaleString("en-IN")}`}
                  </span>
                </div>

                <div>
                  <span className="block text-[10px] text-forest font-bold">Est. Surplus</span>
                  <span className="font-extrabold text-forest block truncate">
                    ₹{plan.projected_operating_surplus_inr.toLocaleString("en-IN")}/yr
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-4 border-t border-line pt-3 flex items-center justify-between gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onSelectPlanToRecalculate(plan.opportunity_id)}
                className="text-xs font-bold"
              >
                <Calculator size={13} /> Recalculate
              </Button>

              <button
                type="button"
                disabled={deletingId === plan.plan_id}
                onClick={() => handleDelete(plan.plan_id)}
                className="rounded-lg p-2 text-muted hover:bg-red-50 hover:text-red-600 transition"
                title="Delete Plan"
              >
                <Trash2 size={15} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
