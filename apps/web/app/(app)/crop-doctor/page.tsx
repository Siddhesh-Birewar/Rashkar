"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  FileUp,
  Gauge,
  HelpCircle,
  Loader2,
  Microscope,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { cropDoctorApi } from "@/lib/api/client";
import type { CropDoctorStatus, CropDoctorPrediction } from "@/lib/api/types";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CropDoctorPage() {
  const [status, setStatus] = useState<CropDoctorStatus | null>(null);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [prediction, setPrediction] = useState<CropDoctorPrediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isServiceUnavailable, setIsServiceUnavailable] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function checkModel() {
      setCheckingStatus(true);
      try {
        const res = await cropDoctorApi.getStatus();
        setStatus(res);
      } catch (err: any) {
        setStatus({
          loaded: false,
          model_id: "PlantVillage MobileNetV2",
          error: err?.message || "Crop Doctor model offline",
        });
      } finally {
        setCheckingStatus(false);
      }
    }
    checkModel();
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
        setError("The Crop Doctor diagnostic model is temporarily unavailable or undergoing inference reloads. Please try again in a few moments.");
      } else if (err.status === 422 || err.status === 400) {
        setError("The submitted image could not be processed. Please ensure you upload a well-lit photograph of a plant leaf or symptom.");
      } else {
        setError(err.message || "Failed to diagnose crop symptom.");
      }
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

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader
        eyebrow="Vision intelligence"
        title="Crop Doctor"
        description="Photograph visible leaf symptoms to diagnose plant diseases using verified PlantVillage MobileNetV2 neural classification."
        backHref="/"
        actions={
          <div className="flex items-center gap-2">
            {checkingStatus ? (
              <Badge variant="neutral" className="gap-1.5 py-1">
                <Loader2 size={12} className="animate-spin" /> Checking Model Status
              </Badge>
            ) : status?.loaded ? (
              <Badge variant="accent" className="gap-1.5 py-1 text-xs">
                <ShieldCheck size={14} /> Diagnostic Model Online
              </Badge>
            ) : (
              <Badge variant="destructive" className="gap-1.5 py-1 text-xs">
                <ShieldAlert size={14} /> Model Unavailable
              </Badge>
            )}
          </div>
        }
      />

      {/* Scientific Integrity Disclaimer */}
      <div className="flex gap-3 rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-sm text-forest">
        <Sparkles className="mt-0.5 shrink-0 text-primary" size={19} />
        <div className="text-xs leading-5 sm:text-sm">
          <strong>Deterministic Agricultural Governance:</strong> Predictions are generated from optical features of crop leaves. Never apply hazardous chemical pesticides without consulting your local Krishi Vigyan Kendra (KVK) officer or state agricultural extension guidelines.
        </div>
      </div>

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
                  className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-line bg-secondary/20 p-8 text-center cursor-pointer hover:border-forest/50 hover:bg-secondary/40 transition-colors"
                >
                  <div className="rounded-full bg-forest/10 p-3 text-forest mb-3">
                    <Microscope size={28} />
                  </div>
                  <p className="text-sm font-semibold">Choose image or drag photo here</p>
                  <p className="mt-1 text-xs text-muted max-w-xs">
                    JPG, PNG or WEBP up to 10MB. Capture high-contrast leaf symptoms.
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
                      disabled={diagnosing || !status?.loaded}
                      className="flex-1 gap-2"
                    >
                      {diagnosing ? (
                        <>
                          <Loader2 size={16} className="animate-spin" /> Diagnosing...
                        </>
                      ) : (
                        <>
                          <Microscope size={16} /> Run Diagnosis
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
              <div className="rounded-xl border border-line/70 bg-card p-3 text-xs text-muted space-y-1.5">
                <p className="font-semibold text-foreground flex items-center gap-1.5">
                  <Camera size={14} className="text-forest" /> Photographing Tips:
                </p>
                <ul className="list-disc pl-4 space-y-1">
                  <li>Focus directly on the infected leaf or discolored lesion.</li>
                  <li>Ensure natural sunlight without harsh reflections or deep shadows.</li>
                  <li>Hold camera steady to avoid motion blur.</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Diagnosis Results or Status */}
        <div className="lg:col-span-7 space-y-4">
          {error && (
            <Card className="border-destructive/30 bg-destructive/5">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-destructive">
                      {isServiceUnavailable ? "Diagnostic Model Offline" : "Assessment Notice"}
                    </h4>
                    <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                      {error}
                    </p>
                    {isServiceUnavailable && (
                      <p className="mt-2 text-xs font-medium text-destructive">
                        The backend ensures honest 503 states rather than hallucinating artificial disease diagnoses.
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {prediction ? (
            <div className="space-y-4">
              <Card className="border-forest/20">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Badge variant={prediction.is_healthy ? "accent" : "destructive"} className="gap-1.5 text-xs py-1">
                      {prediction.is_healthy ? (
                        <>
                          <CheckCircle2 size={14} /> Healthy Plant Tissue
                        </>
                      ) : (
                        <>
                          <AlertTriangle size={14} /> Pathogen / Symptom Detected
                        </>
                      )}
                    </Badge>
                    <span className="text-xs font-semibold text-muted">
                      Confidence: {prediction.confidence_percent.toFixed(1)}%
                    </span>
                  </div>
                  <CardTitle className="mt-2 text-2xl font-bold text-forest">
                    {prediction.crop} — {prediction.diagnosis}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Confidence Progress Bar */}
                  <div>
                    <div className="flex justify-between text-xs font-medium mb-1">
                      <span className="text-muted">Model Confidence</span>
                      <span className="text-forest font-bold">{prediction.confidence_percent.toFixed(1)}%</span>
                    </div>
                    <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 rounded-full ${
                          prediction.is_healthy
                            ? "bg-forest"
                            : prediction.confidence_percent >= 80
                            ? "bg-amber-600"
                            : "bg-destructive"
                        }`}
                        style={{ width: `${Math.min(prediction.confidence_percent, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Actionable Advice */}
                  <div className="rounded-xl border border-line bg-secondary/30 p-4">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-forest mb-1.5 flex items-center gap-1.5">
                      <ShieldCheck size={15} /> Verified Management Protocol
                    </h4>
                    <p className="text-sm leading-relaxed text-foreground">
                      {prediction.actionable_advice}
                    </p>
                  </div>

                  {/* Agronomic Disclaimer */}
                  <div className="rounded-xl border border-line/60 bg-muted/20 p-3 text-xs text-muted leading-relaxed">
                    <strong>Disclaimer:</strong> {prediction.disclaimer}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Diagnostic Capabilities & Scope</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-muted leading-relaxed">
                  CropNet Crop Doctor leverages an optimized MobileNetV2 architecture trained on verified agricultural pathology datasets. No disease label is ever displayed until the neural model returns a verified inference payload.
                </p>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-line p-3">
                    <p className="text-xs font-semibold text-foreground">Multi-Crop Support</p>
                    <p className="mt-0.5 text-xs text-muted">Tomato, Potato, Corn, Apple, Grape, Pepper, Soybean, and Cotton.</p>
                  </div>

                  <div className="rounded-xl border border-line p-3">
                    <p className="text-xs font-semibold text-foreground">Early Detection</p>
                    <p className="mt-0.5 text-xs text-muted">Identifies blights, leaf spots, rusts, bacterial infections, and healthy foliage.</p>
                  </div>

                  <div className="rounded-xl border border-line p-3">
                    <p className="text-xs font-semibold text-foreground">Transparent Confidence</p>
                    <p className="mt-0.5 text-xs text-muted">Clear confidence rating on every assessment to guide verification.</p>
                  </div>

                  <div className="rounded-xl border border-line p-3">
                    <p className="text-xs font-semibold text-foreground">Integrated Advisory</p>
                    <p className="mt-0.5 text-xs text-muted">Direct agronomic recommendations aligned with sustainable IPM protocols.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
