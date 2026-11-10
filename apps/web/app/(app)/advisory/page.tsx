"use client";

import React, { useState } from "react";
import {
  BookOpenText,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Loader2,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Languages,
  RotateCcw,
  Layers,
  Sprout,
  Send,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useFarm } from "@/lib/farm-context";
import { advisoryApi } from "@/lib/api/client";
import type {
  FarmEvaluationResponse,
  CropEvaluationOutcome,
  AgriculturalExplanationResponse,
} from "@/lib/api/types";

const AVAILABLE_CROPS = [
  { id: "sugarcane", name: "Sugarcane", marathi: "ऊस", category: "Cash Crop" },
  { id: "soybean", name: "Soybean", marathi: "सोयाबीन", category: "Oilseed" },
  { id: "tomato", name: "Tomato", marathi: "टोमॅटो", category: "Vegetable" },
  { id: "onion", name: "Onion", marathi: "कांदा", category: "Vegetable" },
  { id: "wheat", name: "Wheat", marathi: "गहू", category: "Cereal" },
  { id: "cotton", name: "Cotton", marathi: "कापूस", category: "Cash Crop" },
  { id: "grapes", name: "Grapes", marathi: "द्राक्षे", category: "Horticulture" },
  { id: "pomegranate", name: "Pomegranate", marathi: "डाळिंब", category: "Horticulture" },
  { id: "chickpea", name: "Gram / Chickpea", marathi: "हरभरा", category: "Pulse" },
];

const SEASONS = [
  { id: "Kharif", label: "Kharif (Monsoon: Jun – Oct)" },
  { id: "Rabi", label: "Rabi (Winter: Oct – Feb)" },
  { id: "Summer", label: "Summer / Zaid (Hot: Mar – May)" },
];

export default function AdvisoryPage() {
  const { selectedFarm, farms, selectedFarmId, setSelectedFarmId } = useFarm();
  const activeFarm = farms.find((f) => f.id === selectedFarmId) || selectedFarm || farms[0];

  const [selectedSeason, setSelectedSeason] = useState("Kharif");
  const [selectedCropIds, setSelectedCropIds] = useState<string[]>([
    "sugarcane",
    "soybean",
    "tomato",
  ]);
  const [language, setLanguage] = useState<"en" | "mr">("en");

  // Advisory execution state
  const [evaluating, setEvaluating] = useState(false);
  const [decision, setDecision] = useState<FarmEvaluationResponse | null>(null);
  const [explanation, setExplanation] = useState<AgriculturalExplanationResponse | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Follow-up diagnostic answers state: { target_parameter: selected_value }
  const [followupAnswers, setFollowupAnswers] = useState<Record<string, any>>({});
  const [submittingFollowup, setSubmittingFollowup] = useState(false);

  const toggleCrop = (cropId: string) => {
    setSelectedCropIds((prev) =>
      prev.includes(cropId)
        ? prev.length > 1
          ? prev.filter((id) => id !== cropId)
          : prev
        : [...prev, cropId]
    );
  };

  const handleRunEvaluation = async () => {
    if (!activeFarm) {
      setError("Please select or register a farm parcel first.");
      return;
    }

    try {
      setEvaluating(true);
      setError(null);
      setExplanation(null);
      setFollowupAnswers({});

      const resp = await advisoryApi.evaluateFarm({
        farm_id: activeFarm.id,
        taluka: activeFarm.taluka || "Baramati",
        district: activeFarm.district || "Pune",
        candidate_crops: selectedCropIds,
        target_season: selectedSeason,
        language,
      });

      setDecision(resp);
    } catch (err: any) {
      setError(err?.message || "Agricultural feasibility evaluation failed.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleFetchExplanation = async () => {
    if (!decision) return;
    try {
      setLoadingExplanation(true);
      const res = await advisoryApi.explainDecision({
        decision_id: decision.decision_id,
        language,
      });
      setExplanation(res);
    } catch (err: any) {
      setError(err?.message || "Failed to generate natural language explanation.");
    } finally {
      setLoadingExplanation(false);
    }
  };

  const handleAnswerFollowup = (targetParam: string, value: string) => {
    setFollowupAnswers((prev) => ({
      ...prev,
      [targetParam]: value,
    }));
  };

  const handleSubmitFollowup = async () => {
    if (!decision || Object.keys(followupAnswers).length === 0) return;
    try {
      setSubmittingFollowup(true);
      setError(null);
      const updated = await advisoryApi.processFollowup({
        decision_id: decision.decision_id,
        answers: followupAnswers,
      });
      setDecision(updated);
      setExplanation(null); // reset explanation so farmer can regenerate with new outcome
    } catch (err: any) {
      setError(err?.message || "Failed to process diagnostic follow-up answers.");
    } finally {
      setSubmittingFollowup(false);
    }
  };

  const getDecisionBadge = (state: string) => {
    switch (state) {
      case "RECOMMENDED":
        return <Badge className="bg-leaf text-white border-0">Recommended</Badge>;
      case "CONDITIONALLY_SUITABLE":
        return <Badge className="bg-calm text-white border-0">Conditionally Suitable</Badge>;
      case "REGIONAL_SCREENING_ONLY":
        return (
          <Badge className="bg-amber-100 text-amber-900 border-amber-300">
            Regional Screening (Verification Needed)
          </Badge>
        );
      case "DISQUALIFIED":
        return <Badge variant="destructive">Disqualified (Constraint Violated)</Badge>;
      default:
        return <Badge variant="outline">{state.replace(/_/g, " ")}</Badge>;
    }
  };

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Crop intelligence"
        title="Crop Advisory & Feasibility Assessment"
        description="Deterministic agronomic suitability engine grounded in MPKV Rahuri rules, SoilGrids, and local water tables."
        backHref="/"
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const nextLang = language === "en" ? "mr" : "en";
                setLanguage(nextLang);
                if (decision) {
                  // Re-fetch explanation in selected language if already generated
                  advisoryApi
                    .explainDecision({ decision_id: decision.decision_id, language: nextLang })
                    .then((res) => setExplanation(res))
                    .catch(() => {});
                }
              }}
              className="gap-1.5 text-xs font-bold"
            >
              <Languages size={15} className="text-leaf" />
              <span>{language === "en" ? "मराठी (MR)" : "English (EN)"}</span>
            </Button>
          </div>
        }
      />

      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200 flex items-start gap-3">
          <AlertCircle size={17} className="shrink-0 text-red-600 mt-0.5" />
          <p>{error}</p>
        </div>
      )}

      {/* ── Active Farm & Context Card ── */}
      <Card className="border-line shadow-sm">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-line">
            <div>
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted">
                Target Farm Parcel
              </span>
              <div className="mt-1 flex items-center gap-3">
                <h3 className="text-xl font-extrabold text-ink">
                  {activeFarm ? activeFarm.name : "No Farm Selected"}
                </h3>
                {activeFarm?.taluka && (
                  <Badge variant="outline" className="text-xs">
                    {activeFarm.taluka}, Pune
                  </Badge>
                )}
              </div>
            </div>

            {farms.length > 1 && (
              <div className="w-56">
                <Select
                  value={activeFarm?.id}
                  onValueChange={(val) => {
                    setSelectedFarmId(val);
                    setDecision(null);
                    setExplanation(null);
                  }}
                >
                  <SelectTrigger className="h-9 text-xs">
                    <SelectValue placeholder="Switch farm parcel" />
                  </SelectTrigger>
                  <SelectContent>
                    {farms.map((f) => (
                      <SelectItem key={f.id} value={f.id} className="text-xs">
                        {f.name} ({f.taluka})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-muted">
            <div>
              <span className="block text-[10px] uppercase font-bold text-muted/70">Area</span>
              <strong className="text-ink">
                {activeFarm?.calculated_area_acres
                  ? `${activeFarm.calculated_area_acres.toFixed(2)} acres`
                  : activeFarm?.calculated_area_hectares
                    ? `${activeFarm.calculated_area_hectares.toFixed(2)} ha`
                    : "Boundary mapped"}
              </strong>
            </div>
            <div>
              <span className="block text-[10px] uppercase font-bold text-muted/70">Irrigation</span>
              <strong className="text-ink capitalize">
                {activeFarm?.irrigation_type || "Irrigated"}
              </strong>
            </div>
            <div>
              <span className="block text-[10px] uppercase font-bold text-muted/70">Water Source</span>
              <strong className="text-ink capitalize">
                {activeFarm?.water_source || "Canal"}
              </strong>
            </div>
            <div>
              <span className="block text-[10px] uppercase font-bold text-muted/70">Soil Zone</span>
              <strong className="text-ink">Deccan Plain Vertisol</strong>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Assessment Configuration Form ── */}
      <Card className="border-line shadow-sm">
        <CardContent className="p-6 space-y-6">
          <div>
            <h3 className="text-base font-extrabold text-ink">1. Select Target Cropping Season</h3>
            <p className="text-xs text-muted mt-0.5">
              CropNet matches water budgets, temperature windows, and monsoon characteristics to the season.
            </p>
            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              {SEASONS.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setSelectedSeason(s.id)}
                  className={`rounded-2xl border p-4 text-left transition-all ${
                    selectedSeason === s.id
                      ? "border-forest bg-[#f4f9f4] shadow-sm ring-1 ring-forest/20"
                      : "border-line bg-canvas hover:border-leaf/40"
                  }`}
                >
                  <span className="text-xs font-bold text-ink block">{s.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-extrabold text-ink">2. Choose Candidate Crops to Evaluate</h3>
                <p className="text-xs text-muted mt-0.5">
                  Select one or multiple crops to test against soil, salinity, water tables, and climate limits.
                </p>
              </div>
              <Badge variant="outline" className="text-xs">
                {selectedCropIds.length} selected
              </Badge>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {AVAILABLE_CROPS.map((crop) => {
                const isSelected = selectedCropIds.includes(crop.id);
                return (
                  <button
                    key={crop.id}
                    type="button"
                    onClick={() => toggleCrop(crop.id)}
                    className={`rounded-xl border px-3.5 py-2 text-xs font-bold transition-all flex items-center gap-2 ${
                      isSelected
                        ? "border-forest bg-forest text-white shadow-sm"
                        : "border-line bg-canvas text-ink hover:border-leaf/40 hover:bg-white"
                    }`}
                  >
                    <Sprout size={14} className={isSelected ? "text-white" : "text-leaf"} />
                    <span>{crop.name}</span>
                    <span className="text-[10px] opacity-75 font-normal">({crop.marathi})</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-2">
            <Button
              onClick={handleRunEvaluation}
              disabled={evaluating || !activeFarm || selectedCropIds.length === 0}
              className="bg-forest hover:bg-forest/90 w-full sm:w-auto px-6"
            >
              {evaluating ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Evaluating Agronomic Feasibility...
                </>
              ) : (
                <>
                  <Sparkles size={16} /> Run Agricultural Evaluation
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Evaluation Results ── */}
      {decision && (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-extrabold text-ink">Evaluation Results</h2>
                <Badge className="bg-[#edf5ed] text-forest border-0 text-[10px] font-bold">
                  ID: {decision.decision_id}
                </Badge>
              </div>
              <p className="text-xs text-muted mt-0.5">
                Deterministic output calculated for {decision.taluka_resolved || activeFarm?.taluka} ({decision.target_season} Season).
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleFetchExplanation}
              disabled={loadingExplanation}
              className="gap-2 text-xs font-bold border-forest text-forest hover:bg-[#edf5ed]"
            >
              {loadingExplanation ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Sparkles size={14} />
              )}
              {explanation ? "Refresh Explanation" : "Explain Assessment with AI"}
            </Button>
          </div>

          {/* Evaluated Crops Grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {decision.crop_outcomes.map((crop) => (
              <Card
                key={crop.crop_id}
                className={`overflow-hidden border transition-all ${
                  crop.is_disqualified
                    ? "border-red-200 bg-red-50/20"
                    : crop.decision_state === "RECOMMENDED"
                      ? "border-green-300 bg-[#f8fcf8]"
                      : "border-line bg-white"
                }`}
              >
                <CardContent className="p-5 flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-start justify-between gap-2 pb-3 border-b border-line">
                      <div>
                        <h4 className="text-base font-extrabold text-ink flex items-center gap-2">
                          {crop.common_name}
                          {crop.marathi_name && (
                            <span className="text-xs font-medium text-muted">
                              ({crop.marathi_name})
                            </span>
                          )}
                        </h4>
                        <span className="text-[10px] text-muted italic">
                          {crop.scientific_name}
                        </span>
                      </div>
                    </div>

                    <div className="mt-3">
                      {getDecisionBadge(crop.decision_state)}
                    </div>

                    {crop.limiting_factors.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-red-700 block">
                          Limiting Agronomic Factors:
                        </span>
                        <ul className="text-xs text-red-800 list-disc pl-4 space-y-0.5">
                          {crop.limiting_factors.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {crop.reproductive_risk_warnings.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 block">
                          Reproductive Heat/Moisture Risks:
                        </span>
                        <ul className="text-xs text-amber-900 list-disc pl-4 space-y-0.5">
                          {crop.reproductive_risk_warnings.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <p className="mt-3 text-xs leading-relaxed text-ink/80">
                      {crop.explanation}
                    </p>
                  </div>

                  {crop.citations && crop.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-line/60 text-[10px] text-muted">
                      <span className="font-semibold block text-muted/80">Agronomic Authority:</span>
                      <p className="truncate">{crop.citations[0].organization} ({crop.citations[0].publication_year})</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* ── Follow-Up Diagnostic Questions (Deterministic Re-evaluation) ── */}
          {decision.follow_up_questions && decision.follow_up_questions.length > 0 && (
            <Card className="border-line bg-canvas shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 pb-3 border-b border-line">
                  <span className="grid size-8 place-items-center rounded-xl bg-amber-100 text-amber-800 font-bold text-xs">
                    ?
                  </span>
                  <div>
                    <h3 className="text-base font-extrabold text-ink">
                      Resolve Decision Uncertainty (Follow-Up Questions)
                    </h3>
                    <p className="text-xs text-muted">
                      Answering field drainage or soil depth questions allows the decision engine to confirm exact parcel suitability.
                    </p>
                  </div>
                </div>

                <div className="mt-5 space-y-5">
                  {decision.follow_up_questions.map((q) => {
                    const qText = language === "mr" ? q.question_text_mr : q.question_text_en;
                    const selectedAns = followupAnswers[q.target_parameter];
                    return (
                      <div key={q.question_id} className="rounded-xl border border-line bg-white p-4">
                        <p className="text-xs font-bold text-ink">{qText}</p>
                        {q.agronomic_rationale && (
                          <p className="text-[11px] text-muted mt-0.5">{q.agronomic_rationale}</p>
                        )}

                        {q.options && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {q.options.map((opt) => {
                              const isChecked = selectedAns === opt;
                              return (
                                <button
                                  key={opt}
                                  type="button"
                                  onClick={() => handleAnswerFollowup(q.target_parameter, opt)}
                                  className={`rounded-xl border px-3 py-1.5 text-xs font-semibold transition-all ${
                                    isChecked
                                      ? "border-forest bg-forest text-white"
                                      : "border-line bg-canvas hover:border-leaf/40 hover:bg-white text-ink"
                                  }`}
                                >
                                  {opt}
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="mt-5 flex justify-end">
                  <Button
                    onClick={handleSubmitFollowup}
                    disabled={submittingFollowup || Object.keys(followupAnswers).length === 0}
                    className="bg-forest gap-2"
                  >
                    {submittingFollowup ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <CheckCircle2 size={16} />
                    )}
                    Submit Answers & Re-evaluate Suitability
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Grounded AI Explanation (Structured Card) ── */}
          {explanation && (
            <Card className="border-line shadow-md bg-gradient-to-br from-white via-white to-[#f6faf6]">
              <CardContent className="p-6 sm:p-8 space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-line">
                  <div className="flex items-center gap-2">
                    <Sparkles size={20} className="text-leaf" />
                    <h3 className="text-base font-extrabold text-ink">
                      {explanation.structured_card?.title || "Crop Feasibility Explanation"}
                    </h3>
                  </div>
                  <Badge className="bg-[#edf5ed] text-forest border-0 text-[10px] font-bold">
                    Grounded AI Analysis ({explanation.language.toUpperCase()})
                  </Badge>
                </div>

                {explanation.structured_card && (
                  <div className="space-y-4">
                    <div className="rounded-xl border border-leaf/30 bg-[#f2f8f2] p-4 text-xs font-medium text-ink leading-relaxed">
                      <strong className="block text-forest text-sm font-bold mb-1">
                        Agronomic Verdict:
                      </strong>
                      {explanation.structured_card.direct_answer}
                    </div>

                    {explanation.structured_card.what_this_means && (
                      <div className="text-xs text-muted leading-relaxed">
                        <strong className="text-ink block mb-0.5">What this means for your farm:</strong>
                        {explanation.structured_card.what_this_means}
                      </div>
                    )}

                    {explanation.structured_card.what_needs_attention &&
                      explanation.structured_card.what_needs_attention.length > 0 && (
                        <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-xs">
                          <strong className="text-amber-900 block font-bold mb-1">
                            Requires Your Attention:
                          </strong>
                          <ul className="list-disc pl-4 space-y-1 text-amber-800">
                            {explanation.structured_card.what_needs_attention.map((item, i) => (
                              <li key={i}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                    {explanation.structured_card.next_steps &&
                      explanation.structured_card.next_steps.length > 0 && (
                        <div className="text-xs space-y-1">
                          <strong className="text-ink block">Recommended Action Steps:</strong>
                          <ol className="list-decimal pl-4 space-y-1 text-muted">
                            {explanation.structured_card.next_steps.map((step, i) => (
                              <li key={i}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      )}

                    {explanation.structured_card.evidence_references && (
                      <div className="pt-3 border-t border-line/60 text-[11px] text-muted">
                        <strong className="text-ink block mb-1">Scientific Citations:</strong>
                        <ul className="list-disc pl-4 space-y-0.5">
                          {explanation.structured_card.evidence_references.map((ref, i) => (
                            <li key={i}>{ref}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Raw Full Explanation Text */}
                {!explanation.structured_card && (
                  <div className="whitespace-pre-line text-xs text-ink/90 leading-relaxed font-sans bg-canvas p-4 rounded-xl border border-line">
                    {explanation.explanation_text}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Governance Notice */}
          <div className="rounded-xl bg-[#fffbf5] border border-[#f5e6d0] p-4 text-xs text-soil">
            <strong>Decision Integrity Notice:</strong> {decision.governance_notice}
          </div>
        </div>
      )}
    </div>
  );
}
