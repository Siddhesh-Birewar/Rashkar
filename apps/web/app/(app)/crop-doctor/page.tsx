"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  ChevronRight,
  Droplets,
  ExternalLink,
  FileUp,
  FlaskConical,
  HelpCircle,
  Info,
  Leaf,
  Loader2,
  Microscope,
  RotateCcw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Sprout,
  Stethoscope,
  Thermometer,
} from "lucide-react";
import { cropDoctorApi } from "@/lib/api/client";
import type {
  CropDoctorStatus,
  CropDoctorPrediction,
  CropDoctorDiseaseItem,
  ChemicalTreatment,
  BiologicalControl,
} from "@/lib/api/types";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CropDoctorPage() {
  const [status, setStatus] = useState<CropDoctorStatus | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [activeMode, setActiveMode] = useState<"upload" | "symptoms">("upload");

  // Upload mode state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [prediction, setPrediction] = useState<CropDoctorPrediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isServiceUnavailable, setIsServiceUnavailable] = useState(false);

  // Symptom Explorer state
  const [diseasesList, setDiseasesList] = useState<CropDoctorDiseaseItem[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loadingDiseases, setLoadingDiseases] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function initPage() {
      setCheckingStatus(true);
      try {
        const [statusRes, diseasesRes] = await Promise.allSettled([
          cropDoctorApi.getStatus(),
          cropDoctorApi.getDiseases(),
        ]);

        if (statusRes.status === "fulfilled") {
          setStatus(statusRes.value);
        } else {
          setStatus({
            loaded: false,
            model_id: "PlantVillage MobileNetV2",
            error: "Neural vision model standby",
          });
        }

        if (diseasesRes.status === "fulfilled" && diseasesRes.value?.diseases) {
          setDiseasesList(diseasesRes.value.diseases);
        }
      } catch (err: any) {
        console.error("Failed to initialize Crop Doctor", err);
      } finally {
        setCheckingStatus(false);
      }
    }
    initPage();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setPrediction(null);
      setError(null);
      setIsServiceUnavailable(false);
    }
  };

  const handleRunDiagnosis = async () => {
    if (!selectedFile) return;
    setDiagnosing(true);
    setError(null);
    setIsServiceUnavailable(false);
    try {
      const result = await cropDoctorApi.predict(selectedFile);
      setPrediction(result);
    } catch (err: any) {
      if (err.status === 503) {
        setIsServiceUnavailable(true);
        setError("The vision neural stack is currently initialising or undergoing model reload. You can still use the Symptom Explorer below to look up verified pathology treatments.");
      } else if (err.status === 422 || err.status === 400) {
        setError("The submitted image could not be processed. Please ensure you upload a clear photograph of a plant leaf or symptom.");
      } else {
        setError(err.message || "Failed to diagnose crop symptom.");
      }
    } finally {
      setDiagnosing(false);
    }
  };

  const handleDiagnoseDiseaseKey = async (diseaseKey: string, cropName: string) => {
    setDiagnosing(true);
    setError(null);
    try {
      const result = await cropDoctorApi.diagnoseSymptoms({
        crop: cropName,
        disease_key: diseaseKey,
      });
      setPrediction(result);
      window.scrollTo({ top: 380, behavior: "smooth" });
    } catch (err: any) {
      setError(err?.message || "Failed to retrieve pathology details.");
    } finally {
      setDiagnosing(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setPrediction(null);
    setError(null);
    setIsServiceUnavailable(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (cameraInputRef.current) cameraInputRef.current.value = "";
  };

  // Unique crops list for filtering
  const availableCrops = ["All", ...Array.from(new Set(diseasesList.map((d) => d.crop)))];

  const filteredDiseases = diseasesList.filter((d) => {
    const matchesCrop = selectedCrop === "All" || d.crop.toLowerCase() === selectedCrop.toLowerCase();
    const matchesSearch =
      !searchQuery.trim() ||
      d.common_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.crop.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.causal_agent.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCrop && matchesSearch;
  });

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader
        eyebrow="Pathology & damage intelligence"
        title="AI Crop Doctor"
        description="Diagnose crop symptoms, identify causal pathogens, and retrieve ICAR/MPKV aligned chemical and biological treatment protocols."
        backHref="/"
        actions={
          <div className="flex items-center gap-2">
            {checkingStatus ? (
              <Badge variant="neutral" className="gap-1.5 py-1">
                <Loader2 size={12} className="animate-spin" /> Checking Model Status
              </Badge>
            ) : status?.loaded ? (
              <Badge variant="accent" className="gap-1.5 py-1 text-xs">
                <ShieldCheck size={14} /> Diagnostic Vision Online
              </Badge>
            ) : (
              <Badge variant="neutral" className="gap-1.5 py-1 text-xs bg-amber-50 text-soil border-line">
                <Microscope size={14} /> Pathology Engine Ready
              </Badge>
            )}
          </div>
        }
      />

      {/* Mode Switcher Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-line pb-3">
        <button
          type="button"
          onClick={() => setActiveMode("upload")}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-extrabold transition-all sm:text-sm ${
            activeMode === "upload"
              ? "bg-forest text-white shadow-sm"
              : "border border-line bg-white text-ink hover:bg-canvas"
          }`}
        >
          <Camera size={16} /> Leaf Photo Diagnosis
        </button>

        <button
          type="button"
          onClick={() => setActiveMode("symptoms")}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-extrabold transition-all sm:text-sm ${
            activeMode === "symptoms"
              ? "bg-forest text-white shadow-sm"
              : "border border-line bg-white text-ink hover:bg-canvas"
          }`}
        >
          <Stethoscope size={16} /> Symptom & Disease Directory ({diseasesList.length > 0 ? diseasesList.length : "23"})
        </button>
      </div>

      {/* Scientific Integrity Notice */}
      <div className="flex gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-sm text-forest">
        <Sparkles className="mt-0.5 shrink-0 text-primary" size={19} />
        <div className="text-xs leading-5 sm:text-sm">
          <strong>Deterministic Agricultural Governance:</strong> Diagnostic pathology insights cite verified ICAR, MPKV Rahuri, and CIBRC approved crop protection protocols. Chemical dosages specify exact active formulations and Pre-Harvest Intervals (PHI).
        </div>
      </div>

      {activeMode === "upload" ? (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Left Column: Image Upload & Preview */}
          <div className="lg:col-span-5 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Upload Leaf Photograph</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleFileChange}
                />
                <input
                  ref={cameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {!previewUrl ? (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-line bg-canvas p-8 text-center cursor-pointer hover:border-forest/50 hover:bg-secondary/40 transition-colors"
                  >
                    <div className="rounded-full bg-forest/10 p-3 text-forest mb-3">
                      <Microscope size={28} />
                    </div>
                    <p className="text-sm font-semibold text-ink">Choose leaf image or drag photo here</p>
                    <p className="mt-1 text-xs text-muted max-w-xs">
                      JPG, PNG or WEBP up to 10MB. Capture high-contrast leaf lesions or discoloration.
                    </p>
                    <div className="mt-4 flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          fileInputRef.current?.click();
                        }}
                        className="gap-2"
                      >
                        <FileUp size={14} /> Browse Files
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          cameraInputRef.current?.click();
                        }}
                        className="gap-2"
                      >
                        <Camera size={14} /> Open Camera
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="relative aspect-4/3 w-full overflow-hidden rounded-xl border border-line bg-black/5">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={previewUrl}
                        alt="Crop symptom preview"
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted">
                      <span className="truncate max-w-[200px]">{selectedFile?.name}</span>
                      <span>{selectedFile ? (selectedFile.size / 1024 / 1024).toFixed(2) : 0} MB</span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        onClick={handleRunDiagnosis}
                        disabled={diagnosing}
                        className="flex-1 gap-2 bg-forest text-white"
                      >
                        {diagnosing ? (
                          <>
                            <Loader2 size={16} className="animate-spin" /> Diagnosing Pathology...
                          </>
                        ) : (
                          <>
                            <Microscope size={16} /> Run Pathology Diagnosis
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={handleReset}
                        disabled={diagnosing}
                        className="gap-1.5"
                      >
                        <RotateCcw size={14} /> Reset
                      </Button>
                    </div>
                  </div>
                )}

                {/* Best Practice Guidelines */}
                <div className="rounded-xl border border-line/70 bg-card p-3.5 text-xs text-muted space-y-1.5">
                  <p className="font-semibold text-ink flex items-center gap-1.5">
                    <Camera size={14} className="text-forest" /> Photographing Tips:
                  </p>
                  <ul className="list-disc pl-4 space-y-1 text-[11px]">
                    <li>Focus closely on the infected leaf or discolored lesion.</li>
                    <li>Ensure natural diffuse sunlight without heavy shadows or glare.</li>
                    <li>Or use the Symptom & Disease Directory tab to diagnose by observed symptoms.</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Diagnosis Results or Guidelines */}
          <div className="lg:col-span-7 space-y-4">
            {error && (
              <Card className="border-red-200 bg-red-50/70">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-semibold text-red-900">
                        {isServiceUnavailable ? "Diagnostic Vision Standby" : "Assessment Notice"}
                      </h4>
                      <p className="mt-1 text-xs text-red-800 leading-relaxed">
                        {error}
                      </p>
                      {isServiceUnavailable && (
                        <div className="mt-3">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setActiveMode("symptoms")}
                            className="bg-white text-xs border-red-200 text-red-900 font-bold"
                          >
                            Explore Symptom Directory Instead →
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {prediction ? (
              <DetailedPathologyView prediction={prediction} onClear={handleReset} />
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-semibold">Diagnostic Coverage & Pathology Engine</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-xs text-muted leading-relaxed">
                    CropNet Crop Doctor identifies plant pathogens, physiological leaf damage, and nutrient disorders across staple Indian and global commercial crops. Every diagnosis delivers exact chemical active ingredients with ICAR-approved dosages and bio-control alternatives.
                  </p>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-line p-3.5 bg-canvas">
                      <p className="text-xs font-bold text-ink">Supported Major Crops</p>
                      <p className="mt-1 text-xs text-muted">Tomato, Potato, Corn, Wheat, Grape, Apple, Pepper, Soybean, Rice, and Cotton.</p>
                    </div>

                    <div className="rounded-xl border border-line p-3.5 bg-canvas">
                      <p className="text-xs font-bold text-ink">Actionable Dosages</p>
                      <p className="mt-1 text-xs text-muted">Exact ml/liter and g/acre formulations plus mandatory Pre-Harvest Intervals (PHI).</p>
                    </div>

                    <div className="rounded-xl border border-line p-3.5 bg-canvas">
                      <p className="text-xs font-bold text-ink">Integrated Bio-Controls</p>
                      <p className="mt-1 text-xs text-muted">Organic fungal/bacterial antagonists (Trichoderma, Pseudomonas) and botanicals.</p>
                    </div>

                    <div className="rounded-xl border border-line p-3.5 bg-canvas">
                      <p className="text-xs font-bold text-ink">AI Agronomist Integration</p>
                      <p className="mt-1 text-xs text-muted">Direct escalation to the CropNet Agronomist with pre-loaded diagnostic context.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      ) : (
        /* ── Symptom & Disease Directory Mode ── */
        <div className="space-y-6">
          {/* Filters Bar */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="relative flex-1">
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    type="text"
                    placeholder="Search by symptom or disease (e.g., Blight, Concentric rings, Mildew, Rust, Canker)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full rounded-xl border border-line bg-canvas pl-9 pr-3 py-2 text-xs font-medium text-ink focus:border-forest focus:outline-none"
                  />
                </div>

                <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0">
                  <span className="text-xs font-bold text-muted shrink-0">Crop:</span>
                  {availableCrops.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setSelectedCrop(c)}
                      className={`shrink-0 rounded-xl px-3 py-1.5 text-xs font-extrabold transition-all ${
                        selectedCrop === c
                          ? "bg-forest text-white shadow-sm"
                          : "border border-line bg-white text-ink hover:bg-canvas"
                      }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* If an active prediction is open from the directory */}
          {prediction && (
            <DetailedPathologyView prediction={prediction} onClear={() => setPrediction(null)} />
          )}

          {/* Diseases Grid */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filteredDiseases.map((d) => (
              <div
                key={d.key}
                onClick={() => handleDiagnoseDiseaseKey(d.key, d.crop)}
                className="group cursor-pointer rounded-2xl border border-line bg-white p-4 shadow-sm hover:border-forest/50 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <Badge variant="outline" className="text-[10px] font-bold">
                      {d.crop}
                    </Badge>
                    <Badge
                      className={
                        d.severity_level === "High"
                          ? "bg-red-100 text-red-800 border-0 text-[10px]"
                          : d.severity_level === "Moderate"
                            ? "bg-orange-100 text-accent border-0 text-[10px]"
                            : "bg-green-100 text-forest border-0 text-[10px]"
                      }
                    >
                      {d.severity_level} Severity
                    </Badge>
                  </div>

                  <h3 className="mt-2.5 text-base font-extrabold text-ink group-hover:text-forest transition-colors">
                    {d.common_name}
                  </h3>

                  <p className="mt-1 text-xs text-muted italic">
                    {d.causal_agent} · {d.pathogen_type}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-line flex items-center justify-between text-xs font-bold text-forest">
                  <span>View Treatments & Dosages</span>
                  <ChevronRight size={15} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Detailed Pathology and Damage Insights View ──────────────────────────────
function DetailedPathologyView({
  prediction,
  onClear,
}: {
  prediction: CropDoctorPrediction;
  onClear: () => void;
}) {
  const isHealthy = prediction.is_healthy;
  const chemicalControls = prediction.chemical_control || [];
  const organicControls = prediction.organic_control || [];
  const culturalTips = Array.isArray(prediction.actionable_advice)
    ? prediction.actionable_advice
    : [prediction.actionable_advice];

  return (
    <div className="space-y-4">
      {/* ── 1. Header & Severity Summary Card ── */}
      <Card className="border-forest/30 shadow-sm overflow-hidden">
        <div className={`p-4 sm:p-6 ${isHealthy ? "bg-[#edf5ed]" : "bg-white"}`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Badge
                className={
                  isHealthy
                    ? "bg-forest text-white border-0 text-xs font-bold"
                    : "bg-red-600 text-white border-0 text-xs font-bold"
                }
              >
                {isHealthy ? "Healthy Tissue" : `${prediction.severity_level || "Pathogen"} Detected`}
              </Badge>
              {prediction.pathogen_type && (
                <Badge variant="outline" className="text-xs">
                  {prediction.pathogen_type}
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs font-bold text-muted">
                Confidence: {prediction.confidence_percent.toFixed(1)}%
              </span>
              <Button variant="outline" size="sm" onClick={onClear} className="text-xs h-7 px-2">
                Clear
              </Button>
            </div>
          </div>

          <h2 className="mt-3 text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
            {prediction.crop} — {prediction.diagnosis}
          </h2>

          {prediction.causal_agent && (
            <p className="mt-1 text-sm font-semibold text-muted italic">
              Causal Agent: <span className="text-ink not-italic">{prediction.causal_agent}</span>
            </p>
          )}

          {prediction.yield_loss_risk && (
            <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-xs text-amber-900 flex items-start gap-2">
              <AlertTriangle size={15} className="shrink-0 text-amber-700 mt-0.5" />
              <div>
                <strong>Yield Loss Risk:</strong> {prediction.yield_loss_risk}
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* ── 2. Damage Symptoms & Favoring Conditions ── */}
      {prediction.damage_symptoms && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Stethoscope size={16} className="text-leaf" /> Observed Damage Symptoms
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-xs sm:text-sm text-ink leading-relaxed">
              {prediction.damage_symptoms}
            </p>

            {prediction.favorable_conditions && (
              <div className="rounded-xl border border-line bg-canvas p-3 text-xs">
                <span className="font-extrabold text-muted uppercase tracking-wider block text-[10px] mb-1">
                  Environmental Favoring Conditions
                </span>
                <p className="text-ink">{prediction.favorable_conditions}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── 3. Chemical Control Protocols (with ICAR Dosages) ── */}
      {chemicalControls.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold flex items-center gap-2 text-forest">
                <FlaskConical size={16} className="text-forest" /> Chemical Intervention Protocols (ICAR / CIBRC)
              </CardTitle>
              <Badge className="bg-[#edf5ed] text-forest border-0 text-[10px] font-bold">
                Certified Dosages
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-line">
              {chemicalControls.map((chem, idx) => (
                <div key={idx} className="p-4 sm:p-5 space-y-2 hover:bg-canvas/50 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <h4 className="text-sm font-extrabold text-ink">{chem.product}</h4>
                    <span className="text-[11px] font-bold text-accent bg-orange-50 px-2 py-0.5 rounded-md self-start sm:self-auto">
                      PHI: {chem.pre_harvest_interval_days != null ? `${chem.pre_harvest_interval_days} days` : "Not specified"}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    <div className="rounded-xl bg-canvas border border-line/60 p-2.5">
                      <span className="block text-[10px] font-bold uppercase text-muted">Foliar Dosage / Liter</span>
                      <span className="font-extrabold text-forest text-sm">{chem.dosage_per_liter}</span>
                    </div>

                    <div className="rounded-xl bg-canvas border border-line/60 p-2.5">
                      <span className="block text-[10px] font-bold uppercase text-muted">Field Dosage / Acre</span>
                      <span className="font-extrabold text-forest text-sm">{chem.dosage_per_acre}</span>
                    </div>
                  </div>

                  {chem.application_type && (
                    <p className="text-xs text-muted">
                      <strong>Method:</strong> {chem.application_type} · <strong>Interval:</strong> {chem.spray_interval}
                    </p>
                  )}

                  {chem.notes && (
                    <p className="text-[11px] text-soil bg-amber-50/50 rounded p-2 italic">
                      Tip: {chem.notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── 4. Organic & Biological Control ── */}
      {organicControls.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2 text-forest">
              <Leaf size={16} className="text-leaf" /> Organic & Bio-Rational Alternatives
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {organicControls.map((bio, idx) => (
              <div key={idx} className="rounded-xl border border-line bg-canvas p-3.5 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-forest">{bio.agent}</span>
                  <Badge variant="outline" className="text-[10px]">
                    {bio.dosage}
                  </Badge>
                </div>
                <p className="text-muted text-[11px]">
                  <strong>Application:</strong> {bio.application_method}
                </p>
                {bio.benefits && (
                  <p className="text-ink text-[11px] mt-1 font-medium">
                    ✓ {bio.benefits}
                  </p>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* ── 5. Preventive IPM Cultural Practices ── */}
      {culturalTips.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <ShieldCheck size={16} className="text-forest" /> Preventive Field & Cultural Practices
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5 text-xs text-muted list-disc pl-5">
              {culturalTips.map((tip, i) => (
                <li key={i} className="text-ink leading-relaxed">
                  {tip}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* ── 6. Ask Agronomist Deep-Link ── */}
      <div className="rounded-2xl border border-[#c4e3c4] bg-[#edf5ed] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-forest text-white">
            <Sprout size={20} />
          </div>
          <div>
            <h4 className="text-sm font-extrabold text-forest">Need Custom Sprayer Guidance?</h4>
            <p className="text-xs text-forest/80">
              Consult the CropNet AI Agronomist with this diagnosis pre-attached.
            </p>
          </div>
        </div>

        <Button asChild size="sm" className="bg-forest text-white font-bold shrink-0">
          <Link
            href={`/assistant?q=${encodeURIComponent(
              `I have diagnosed ${prediction.diagnosis} on my ${prediction.crop}. What immediate steps, tank mixes, and safety intervals should I follow?`
            )}`}
          >
            Ask AI Agronomist →
          </Link>
        </Button>
      </div>

      {/* Agronomic Disclaimer */}
      <div className="rounded-xl border border-line bg-canvas p-3 text-[11px] text-muted leading-relaxed">
        <strong>Governance Notice:</strong> {prediction.disclaimer} Always perform a small bucket test before mixing two agrochemicals and verify local harvest withholding intervals.
      </div>
    </div>
  );
}
