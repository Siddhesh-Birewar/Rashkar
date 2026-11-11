"use client";

import { useEffect, useState } from "react";
import {
  Calculator,
  Coins,
  TrendingUp,
  Clock,
  Save,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  RotateCcw,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { incomeApi } from "../lib/api";
import type { DetailedOpportunity, FinancialSimulation } from "../types";

interface ScenarioCalculatorProps {
  opportunity: DetailedOpportunity;
  allOpportunities?: DetailedOpportunity[];
  onSelectOpportunity?: (opp: DetailedOpportunity) => void;
  farmId: string;
  onPlanSaved?: () => void;
}

export function ScenarioCalculator({
  opportunity,
  allOpportunities,
  onSelectOpportunity,
  farmId,
  onPlanSaved,
}: ScenarioCalculatorProps) {
  const opp = opportunity;
  const unitDesc = opp.unit_of_operation || "unit";
  const defaultScale = opp.typical_scale > 0 ? opp.typical_scale : 1.0;

  const [scale, setScale] = useState<number>(defaultScale);
  const [mode, setMode] = useState<"LOW" | "BASE" | "HIGH">("BASE");
  const [customCapex, setCustomCapex] = useState<number | undefined>(undefined);
  const [customOpex, setCustomOpex] = useState<number | undefined>(undefined);
  const [customPrice, setCustomPrice] = useState<number | undefined>(undefined);
  const [customYield, setCustomYield] = useState<number | undefined>(undefined);

  const [simulation, setSimulation] = useState<FinancialSimulation | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [savingPlan, setSavingPlan] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [planNotes, setPlanNotes] = useState<string>("");

  const runSimulation = async () => {
    try {
      setLoading(true);
      const res = await incomeApi.simulateScenario({
        opportunity_id: opp.opportunity_id,
        allocated_scale: scale,
        scenario_mode: mode,
        custom_setup_investment_inr: customCapex,
        custom_annual_opex_inr: customOpex,
        custom_yield: customYield,
        custom_sale_price: customPrice,
      });
      setSimulation(res);
    } catch (e) {
      console.error("Simulation error", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [opp.opportunity_id, scale, mode]);

  const handleReset = () => {
    setCustomCapex(undefined);
    setCustomOpex(undefined);
    setCustomPrice(undefined);
    setCustomYield(undefined);
    setScale(defaultScale);
    setMode("BASE");
  };

  const handleSavePlan = async () => {
    if (!simulation) return;
    setSavingPlan(true);
    try {
      await incomeApi.savePlan(farmId, {
        opportunity_id: opp.opportunity_id,
        allocated_scale: scale,
        scale_unit: unitDesc,
        custom_budget_inr: simulation.initial_setup_investment_inr,
        projected_operating_surplus_inr: simulation.estimated_operating_surplus_inr,
        scenario_mode: mode,
        notes: planNotes || `${opp.name} (${mode} scenario)`,
      });
      setSaveSuccess(true);
      if (onPlanSaved) onPlanSaved();
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (e) {
      alert("Failed to save plan: " + (e as Error).message);
    } finally {
      setSavingPlan(false);
    }
  };

  return (
    <div className="rounded-3xl border border-line bg-white p-5 shadow-sm sm:p-7">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between border-b border-line pb-5">
        <div className="space-y-2 flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="green" className="font-extrabold text-[10px] uppercase">
              Financial Simulator
            </Badge>
            <Badge variant="outline" className="text-[10px] font-bold">
              {opp.category_name || opp.category?.replace(/_/g, " ")}
            </Badge>
            <span className="text-xs text-muted font-bold">
              {opp.confidence_classification?.replace(/_/g, " ")}
            </span>
          </div>

          {allOpportunities && allOpportunities.length > 1 ? (
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 pt-1">
              <label htmlFor="enterprise-selector" className="text-xs font-bold text-muted shrink-0">
                Enterprise:
              </label>
              <select
                id="enterprise-selector"
                value={opp.opportunity_id}
                onChange={(e) => {
                  const selected = allOpportunities.find((o) => o.opportunity_id === e.target.value);
                  if (selected && onSelectOpportunity) onSelectOpportunity(selected);
                }}
                className="w-full sm:w-auto rounded-xl border border-line bg-canvas px-3.5 py-2 text-sm sm:text-base font-extrabold text-forest focus:border-forest focus:outline-none"
              >
                {allOpportunities.map((o) => (
                  <option key={o.opportunity_id} value={o.opportunity_id}>
                    {o.name}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <h2 className="text-xl font-extrabold text-ink mt-1">
              {opp.name}
            </h2>
          )}

          <p className="text-xs text-muted leading-relaxed max-w-2xl">{opp.farmer_friendly_description}</p>
        </div>

        <button
          type="button"
          onClick={handleReset}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-muted hover:text-ink self-start sm:self-auto shrink-0 mt-1"
        >
          <RotateCcw size={13} />
          Reset Defaults
        </button>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Interactive Inputs (5 cols) */}
        <div className="space-y-5 lg:col-span-5 text-xs">
          <div className="rounded-2xl border border-line bg-canvas p-4 space-y-4">
            <h3 className="font-extrabold text-ink text-sm flex items-center gap-1.5">
              <Calculator size={15} className="text-forest" />
              Adjust Farm Scale & Market Assumptions
            </h3>

            {/* Scale Input */}
            <div>
              <div className="flex items-center justify-between">
                <label className="font-bold text-ink">Scale of Operation</label>
                <span className="font-extrabold text-forest">{scale} {unitDesc}</span>
              </div>
              <input
                type="number"
                min={0.1}
                step={0.1}
                value={scale}
                onChange={(e) => setScale(parseFloat(e.target.value) || 0.1)}
                className="mt-1.5 w-full rounded-xl border border-line bg-white p-2.5 font-bold text-ink focus:border-forest focus:outline-none"
              />
              <span className="text-[10px] text-muted block mt-0.5">
                Typical institutional unit: {opp.unit_of_operation}
              </span>
            </div>

            {/* Scenario Mode (LOW, BASE, HIGH) */}
            <div>
              <label className="font-bold text-ink block mb-1.5">Scenario Confidence Range</label>
              <div className="grid grid-cols-3 gap-1.5">
                {(["LOW", "BASE", "HIGH"] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMode(m)}
                    className={`rounded-xl border py-2 text-xs font-extrabold transition-all ${
                      mode === m
                        ? "border-forest bg-forest text-white shadow-sm"
                        : "border-line bg-white text-ink hover:bg-canvas"
                    }`}
                  >
                    {m === "LOW" && "Conservative"}
                    {m === "BASE" && "Standard"}
                    {m === "HIGH" && "Optimistic"}
                  </button>
                ))}
              </div>
            </div>

            {/* Initial Capex Override */}
            <div>
              <label className="font-bold text-ink block">
                Initial Setup Investment (₹)
              </label>
              <input
                type="number"
                placeholder={`Typical: ₹${(simulation?.initial_setup_investment_inr ?? 0).toLocaleString("en-IN")}`}
                value={customCapex ?? ""}
                onChange={(e) =>
                  setCustomCapex(e.target.value === "" ? undefined : parseFloat(e.target.value))
                }
                onBlur={runSimulation}
                className="mt-1 w-full rounded-xl border border-line bg-white p-2.5 font-bold text-ink focus:border-forest focus:outline-none"
              />
            </div>

            {/* Annual Opex Override */}
            <div>
              <label className="font-bold text-ink block">
                Annual Operating Expenses (₹)
              </label>
              <input
                type="number"
                placeholder={`Typical: ₹${(simulation?.recurring_operating_expenses_inr ?? 0).toLocaleString("en-IN")}`}
                value={customOpex ?? ""}
                onChange={(e) =>
                  setCustomOpex(e.target.value === "" ? undefined : parseFloat(e.target.value))
                }
                onBlur={runSimulation}
                className="mt-1 w-full rounded-xl border border-line bg-white p-2.5 font-bold text-ink focus:border-forest focus:outline-none"
              />
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={runSimulation}
              className="w-full font-bold"
            >
              Recalculate Projections
            </Button>
          </div>

          {/* Save Business Plan Box */}
          <div className="rounded-2xl border border-leaf/40 bg-[#f4f9f4] p-4 space-y-3">
            <h4 className="font-extrabold text-forest text-xs flex items-center gap-1.5">
              <Save size={14} />
              Save to Farm Business Plans
            </h4>
            <input
              type="text"
              placeholder="Optional notes (e.g., 'Allocated 0.5 acre near borewell')"
              value={planNotes}
              onChange={(e) => setPlanNotes(e.target.value)}
              className="w-full rounded-xl border border-line bg-white p-2 text-xs font-medium text-ink focus:border-forest focus:outline-none"
            />
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={savingPlan || loading}
              onClick={handleSavePlan}
              className="w-full font-extrabold"
            >
              {savingPlan ? "Saving Plan..." : "Save Business Plan to Farm"}
            </Button>
            {saveSuccess && (
              <p className="flex items-center gap-1 text-[11px] font-bold text-forest">
                <CheckCircle2 size={13} /> Saved successfully to your farm records!
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Live Projected Return KPIs (7 cols) */}
        <div className="space-y-5 lg:col-span-7">
          {loading ? (
            <div className="py-20 text-center text-xs text-muted">Calculating financial simulation...</div>
          ) : simulation ? (
            <div className="space-y-5 text-xs">
              {/* 4 Big KPI Cards */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-line bg-white p-4 shadow-sm">
                  <span className="block text-[10px] text-muted font-bold uppercase tracking-wider">
                    Initial Setup Outlay
                  </span>
                  <span className="text-xl font-extrabold text-ink block mt-1">
                    {simulation.initial_setup_investment_inr === 0
                      ? "₹0 (Zero Cash)"
                      : `₹${simulation.initial_setup_investment_inr.toLocaleString("en-IN")}`}
                  </span>
                  <span className="text-[10px] text-muted mt-1 block">One-time capital expenditure</span>
                </div>

                <div className="rounded-2xl border border-line bg-white p-4 shadow-sm">
                  <span className="block text-[10px] text-muted font-bold uppercase tracking-wider">
                    Annual Recurring Opex
                  </span>
                  <span className="text-xl font-extrabold text-ink block mt-1">
                    ₹{simulation.recurring_operating_expenses_inr.toLocaleString("en-IN")}
                  </span>
                  <span className="text-[10px] text-muted mt-1 block">Seeds, feed, inputs, labour</span>
                </div>

                <div className="rounded-2xl border border-line bg-white p-4 shadow-sm">
                  <span className="block text-[10px] text-muted font-bold uppercase tracking-wider">
                    Expected Gross Sales
                  </span>
                  <span className="text-xl font-extrabold text-accent block mt-1">
                    ₹{simulation.expected_gross_revenue_inr.toLocaleString("en-IN")}
                  </span>
                  <span className="text-[10px] text-muted mt-1 block">Total annual market turnover</span>
                </div>

                <div className="rounded-2xl border border-leaf/60 bg-[#edf5ed] p-4 shadow-sm">
                  <span className="block text-[10px] text-forest font-bold uppercase tracking-wider">
                    Estimated Operating Surplus
                  </span>
                  <span className="text-2xl font-extrabold text-forest block mt-1">
                    ₹{simulation.estimated_operating_surplus_inr.toLocaleString("en-IN")}
                  </span>
                  <span className="text-[10px] text-forest font-medium mt-1 block">
                    Gross sales minus recurring opex
                  </span>
                </div>
              </div>

              {/* Break-even & Payback Card */}
              <div className="rounded-2xl border border-line bg-canvas p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <Clock size={20} className="text-leaf shrink-0" />
                  <div>
                    <span className="font-extrabold text-ink text-sm block">
                      Payback & Capital Recovery
                    </span>
                    <span className="text-xs text-muted">{simulation.break_even_estimate}</span>
                  </div>
                </div>
                {simulation.estimated_payback_months && (
                  <Badge variant="green" className="font-extrabold text-xs px-3 py-1 self-start sm:self-auto">
                    ~{simulation.estimated_payback_months} Months Payback
                  </Badge>
                )}
              </div>

              {/* Assumptions Applied */}
              <div className="rounded-2xl border border-line bg-white p-4 space-y-2">
                <h4 className="font-bold text-ink text-xs uppercase tracking-wider text-muted">
                  Underlying Agricultural Assumptions
                </h4>
                <ul className="space-y-1 text-xs text-ink">
                  {simulation.assumptions_applied.map((a, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-forest font-bold">•</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Honest Agricultural Disclaimers */}
              <div className="rounded-2xl border border-line/60 bg-[#f9faf9] p-4 text-[11px] text-muted space-y-1.5">
                <p className="font-bold text-ink flex items-center gap-1">
                  <HelpCircle size={13} className="text-soil" />
                  Understanding Farm Financial Metrics:
                </p>
                <p className="leading-relaxed">
                  <strong>Operating surplus</strong> is gross sales minus recurring cash operating expenses. It is
                  <strong> not net profit</strong>: it does not deduct unpaid family physical labour, depreciation of
                  sheds/equipment, or debt financing interest.
                </p>
                <p className="leading-relaxed italic">
                  Source: {simulation.source_attribution}. Figures are planning benchmarks and not guaranteed income.
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
