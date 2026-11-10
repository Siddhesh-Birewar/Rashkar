"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  Calendar,
  Check,
  CheckCircle2,
  Clock,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  FileCheck2,
  FileText,
  FileWarning,
  FlaskConical,
  HelpCircle,
  Info,
  Loader2,
  PencilLine,
  RefreshCw,
  Scale,
  Sparkles,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { soilApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { SoilTestReport, SoilReportMeasurement } from "@/lib/api/types";

// Plausibility boundaries for client-side feedback
const CLIENT_BOUNDARIES: Record<string, [number, number]> = {
  soil_ph: [3.0, 11.0],
  electrical_conductivity: [0.0, 30.0],
  organic_carbon: [0.0, 10.0],
  organic_matter: [0.0, 20.0],
  available_nitrogen: [0.0, 1500.0],
  total_nitrogen: [0.0, 5.0],
  available_phosphorus: [0.0, 300.0],
  available_potassium: [0.0, 2500.0],
  sulphur: [0.0, 500.0],
  zinc: [0.0, 100.0],
  iron: [0.0, 250.0],
  manganese: [0.0, 250.0],
  copper: [0.0, 50.0],
  boron: [0.0, 30.0],
};

export default function SoilReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;
  const reportId = params?.reportId as string;

  const [report, setReport] = useState<SoilTestReport | null>(null);
  const [measurements, setMeasurements] = useState<SoilReportMeasurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [savingIdx, setSavingIdx] = useState<number | null>(null);
  const [showDocument, setShowDocument] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Poll timer reference
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

  const loadReport = useCallback(
    async (showSpinner = true) => {
      if (!actualFarmId || !reportId) return;
      try {
        if (showSpinner) setLoading(true);
        setError(null);
        const data = await soilApi.getReport(actualFarmId, reportId);
        setReport(data);

        // Normalize measurement items with robust fallback keys
        const rawMeasurements = (data.measurements || []).map((m) => {
          const effectiveVal =
            m.farmer_corrected_value != null
              ? m.farmer_corrected_value
              : m.normalized_value != null
                ? m.normalized_value
                : m.original_value != null
                  ? m.original_value
                  : m.numeric_value != null
                    ? m.numeric_value
                    : null;

          const effectiveUnit = m.normalized_unit || m.original_unit || m.unit || "";
          const effectiveName = m.display_name || m.parameter_name || m.original_parameter_name || m.parameter_key || "Parameter";

          return {
            ...m,
            parameter_name: effectiveName,
            numeric_value: effectiveVal,
            unit: effectiveUnit,
          };
        });

        setMeasurements(rawMeasurements);

        // Check if report is still processing in background
        const status = data.extraction_status || data.status;
        if (status === "PROCESSING" || status === "UPLOADED") {
          setIsProcessing(true);
        } else {
          setIsProcessing(false);
        }
      } catch (err: any) {
        setError(err?.message || "Failed to load soil report details");
      } finally {
        if (showSpinner) setLoading(false);
      }
    },
    [actualFarmId, reportId]
  );

  useEffect(() => {
    loadReport(true);

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [loadReport]);

  // Polling loop when extraction is in progress
  useEffect(() => {
    if (isProcessing) {
      pollTimerRef.current = setInterval(() => {
        loadReport(false);
      }, 1500);
    } else {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    }
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [isProcessing, loadReport]);

  const handleValueChange = (index: number, val: string) => {
    const updated = [...measurements];
    const num = parseFloat(val);
    updated[index] = {
      ...updated[index],
      numeric_value: isNaN(num) ? null : num,
      farmer_corrected_value: isNaN(num) ? null : num,
    };
    setMeasurements(updated);
  };

  const handleSaveIndividualCorrection = async (index: number) => {
    if (!actualFarmId || !reportId) return;
    const m = measurements[index];
    if (m.numeric_value == null) return;

    try {
      setSavingIdx(index);
      setError(null);
      await soilApi.correctMeasurement(actualFarmId, reportId, m.id, {
        corrected_value: m.numeric_value,
        corrected_unit: m.unit,
        farmer_notes: "Updated via web portal review",
      });
      setSuccess(`Updated ${m.parameter_name} to ${m.numeric_value} ${m.unit}`);
      await loadReport(false);
    } catch (err: any) {
      setError(err?.message || `Failed to update ${m.parameter_name}`);
    } finally {
      setSavingIdx(null);
    }
  };

  const handleReprocess = async () => {
    if (!actualFarmId || !reportId) return;
    try {
      setReprocessing(true);
      setError(null);
      setSuccess(null);
      await soilApi.reprocessReport(actualFarmId, reportId);
      setIsProcessing(true);
      await loadReport(true);
    } catch (err: any) {
      setError(err?.message || "Failed to trigger document re-extraction");
    } finally {
      setReprocessing(false);
    }
  };

  const handleConfirm = async () => {
    if (!actualFarmId || !reportId) return;
    try {
      setConfirming(true);
      setError(null);

      // Verify each corrected value is saved before confirmation
      for (const m of measurements) {
        if (m.farmer_corrected_value != null && m.verification_status !== "FARMER_CORRECTED") {
          await soilApi.correctMeasurement(actualFarmId, reportId, m.id, {
            corrected_value: m.farmer_corrected_value,
            corrected_unit: m.unit,
          });
        }
      }

      await soilApi.confirmReport(actualFarmId, reportId, {
        confirmation_notes: "Confirmed by farmer through web portal",
      });
      setSuccess("Report confirmed successfully! Extracted values are now integrated into your authoritative farm soil profile.");
      await loadReport(false);
    } catch (err: any) {
      setError(err?.message || "Failed to confirm report");
    } finally {
      setConfirming(false);
    }
  };

  const handleDelete = async () => {
    if (!actualFarmId || !reportId) return;
    if (!confirm("Are you sure you want to delete this soil report?")) return;

    try {
      setDeleting(true);
      await soilApi.deleteReport(actualFarmId, reportId);
      router.push(`/farms/${actualFarmId}/soil/reports`);
    } catch (err: any) {
      alert(`Delete failed: ${err?.message || "Unknown error"}`);
      setDeleting(false);
    }
  };

  if (loading && !report) {
    return (
      <div className="py-24 text-center">
        <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
        <p className="mt-4 text-sm font-semibold text-ink">Loading soil report details...</p>
        <p className="mt-1 text-xs text-muted">Retrieving document and OCR parameter state</p>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="py-16 text-center">
        <AlertCircle size={36} className="mx-auto text-red-600" />
        <h3 className="mt-3 text-base font-bold text-ink">Unable to Load Report</h3>
        <p className="mt-1 text-sm text-muted">{error}</p>
        <Button asChild className="mt-5">
          <Link href={`/farms/${actualFarmId}/soil/reports`}>Back to Reports</Link>
        </Button>
      </div>
    );
  }

  const documentUrl = actualFarmId && reportId ? soilApi.getDocumentUrl(actualFarmId, reportId) : null;
  const isPdf = report?.mime_type === "application/pdf" || report?.original_filename?.toLowerCase().endsWith(".pdf");
  const isConfirmed = report?.review_status === "CONFIRMED" || report?.status === "CONFIRMED";
  const isFailed = report?.extraction_status === "FAILED";

  // Agronomic validation checks
  const boundaryWarnings: string[] = [];
  measurements.forEach((m) => {
    if (m.numeric_value != null && m.parameter_key && CLIENT_BOUNDARIES[m.parameter_key]) {
      const [minB, maxB] = CLIENT_BOUNDARIES[m.parameter_key];
      if (m.numeric_value < minB || m.numeric_value > maxB) {
        boundaryWarnings.push(
          `${m.parameter_name} value ${m.numeric_value} ${m.unit} is outside standard agronomic range (${minB}–${maxB} ${m.unit}).`
        );
      }
    }
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Soil laboratory certificate"
        title="Review OCR Measurements"
        description="Verify and correct extracted soil parameters before integrating them into the verified farm profile."
        backHref={`/farms/${actualFarmId}/soil/reports`}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReprocess}
              disabled={reprocessing || isProcessing || confirming}
              className="gap-1.5"
            >
              <RefreshCw size={14} className={reprocessing || isProcessing ? "animate-spin" : ""} />
              {reprocessing || isProcessing ? "Extracting..." : "Reprocess OCR"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              disabled={deleting || confirming}
              className="text-red-600 hover:bg-red-50 gap-1.5"
            >
              <Trash2 size={14} /> Delete
            </Button>
            <Button
              size="sm"
              onClick={handleConfirm}
              disabled={confirming || isConfirmed || isProcessing || isFailed || measurements.length === 0}
              className="bg-forest gap-1.5"
            >
              {confirming ? (
                <>
                  <Loader2 size={15} className="animate-spin" /> Confirming...
                </>
              ) : isConfirmed ? (
                <>
                  <CheckCircle2 size={15} /> Confirmed
                </>
              ) : (
                <>
                  <Check size={15} /> Confirm & Save Profile
                </>
              )}
            </Button>
          </div>
        }
      />

      {/* ── Processing State Banner ── */}
      {isProcessing && (
        <Card className="border-leaf/50 bg-[#f4f9f4] shadow-sm animate-pulse">
          <CardContent className="p-5 flex items-center gap-4">
            <div className="grid size-10 shrink-0 place-items-center rounded-2xl bg-leaf text-white shadow-sm">
              <Loader2 size={20} className="animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-extrabold text-forest">OCR Analysis in Progress</h4>
              <p className="mt-0.5 text-xs text-muted">
                Extracting soil chemical and nutrient parameters from {report?.original_filename || "document"}. This usually takes a few seconds...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Failed State Banner ── */}
      {isFailed && (
        <Card className="border-red-200 bg-red-50/70 shadow-sm">
          <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-red-100 text-red-700">
                <FileWarning size={18} />
              </div>
              <div>
                <h4 className="text-sm font-extrabold text-red-900">Document Extraction Incomplete</h4>
                <p className="mt-0.5 text-xs text-red-800 leading-relaxed">
                  {report?.extraction_error || "Zero soil parameters were identified in this document. Please ensure the document is a readable laboratory soil test report or Soil Health Card."}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReprocess}
                disabled={reprocessing}
                className="bg-white hover:bg-red-100 border-red-200 text-red-900 text-xs"
              >
                <RefreshCw size={13} className={reprocessing ? "animate-spin" : ""} /> Retry Extraction
              </Button>
              <Button size="sm" asChild className="bg-forest text-xs">
                <Link href={`/farms/${actualFarmId}/soil/reports/new`}>Upload Different File</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Boundary Warnings ── */}
      {boundaryWarnings.length > 0 && !isConfirmed && (
        <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-xs text-amber-900 space-y-1">
          <div className="flex items-center gap-2 font-bold text-amber-950">
            <AlertCircle size={15} />
            <span>Agronomic Boundary Advisories</span>
          </div>
          <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
            {boundaryWarnings.map((warn, i) => (
              <li key={i}>{warn}</li>
            ))}
          </ul>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
          <AlertCircle size={17} className="shrink-0 text-red-600" />
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-3 rounded-xl bg-green-50 p-4 text-xs text-green-800 border border-green-200">
          <CheckCircle2 size={17} className="text-leaf shrink-0" />
          <p>{success}</p>
        </div>
      )}

      {/* ── Metadata Card ── */}
      <Card>
        <CardContent className="p-6">
          <div className="grid gap-4 sm:grid-cols-4 text-xs">
            <div>
              <span className="text-muted block text-[10px] font-bold uppercase tracking-wider">Laboratory</span>
              <span className="font-extrabold text-ink text-sm">
                {report?.laboratory_name || "Certified Soil Testing Lab"}
              </span>
              {report?.lab_number && (
                <span className="text-[10px] text-muted block mt-0.5 font-mono">
                  Ref: {report.lab_number}
                </span>
              )}
            </div>

            <div>
              <span className="text-muted block text-[10px] font-bold uppercase tracking-wider">Sample Date</span>
              <span className="font-extrabold text-ink text-sm">
                {report?.sample_collection_date
                  ? new Date(report.sample_collection_date).toLocaleDateString()
                  : report?.sample_date || report?.report_date
                    ? new Date(report.report_date || report.sample_date!).toLocaleDateString()
                    : "Not specified"}
              </span>
              {report?.date_received && (
                <span className="text-[10px] text-muted block mt-0.5">
                  Received: {new Date(report.date_received).toLocaleDateString()}
                </span>
              )}
            </div>

            <div>
              <span className="text-muted block text-[10px] font-bold uppercase tracking-wider">Sample Depth</span>
              <span className="font-extrabold text-ink text-sm">
                {report?.sample_depth_interval || "0–15 cm"}
              </span>
              <span className="text-[10px] text-muted block mt-0.5">
                Provenance: {report?.depth_provenance || "LAB_REPORT"}
              </span>
            </div>

            <div>
              <span className="text-muted block text-[10px] font-bold uppercase tracking-wider">Verification Status</span>
              <div className="mt-1 flex items-center gap-2">
                <Badge
                  className={
                    isConfirmed
                      ? "bg-[#edf5ed] text-forest border-0"
                      : isFailed
                        ? "bg-red-100 text-red-800 border-0"
                        : isProcessing
                          ? "bg-blue-50 text-blue-800 border-0"
                          : "bg-orange-50 text-accent border-0"
                  }
                >
                  {isConfirmed ? "CONFIRMED" : isFailed ? "EXTRACTION_FAILED" : isProcessing ? "PROCESSING" : "NEEDS_REVIEW"}
                </Badge>
              </div>
            </div>
          </div>

          {/* Document Preview Toggle Bar */}
          <div className="mt-5 pt-4 border-t border-line flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-muted">
              <FileText size={15} className="text-leaf" />
              <span className="font-medium text-ink">{report?.original_filename || "Document"}</span>
              {report?.file_size_bytes && (
                <span>({(report.file_size_bytes / 1024).toFixed(1)} KB)</span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {documentUrl && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowDocument(!showDocument)}
                  className="gap-1.5 text-xs text-forest hover:bg-forest/10"
                >
                  {showDocument ? <EyeOff size={14} /> : <Eye size={14} />}
                  {showDocument ? "Hide Document" : "View Original Certificate"}
                </Button>
              )}
              {documentUrl && (
                <Button variant="outline" size="sm" asChild className="gap-1 text-xs">
                  <a href={documentUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink size={13} /> Open
                  </a>
                </Button>
              )}
            </div>
          </div>

          {/* Embedded Document Viewer Panel */}
          {showDocument && documentUrl && (
            <div className="mt-4 rounded-2xl border border-line bg-canvas p-3 overflow-hidden">
              <div className="flex items-center justify-between pb-2 border-b border-line mb-3 px-1 text-xs font-semibold text-muted">
                <span>Certificate Document Preview</span>
                <a
                  href={documentUrl}
                  download={report?.original_filename || "soil_report"}
                  className="flex items-center gap-1 text-forest hover:underline text-[11px]"
                >
                  <Download size={13} /> Download File
                </a>
              </div>

              {isPdf ? (
                <iframe
                  src={documentUrl}
                  className="w-full h-[520px] rounded-xl border border-line bg-white"
                  title="Soil Laboratory PDF Report"
                />
              ) : (
                <div className="max-h-[520px] overflow-auto flex justify-center bg-black/5 rounded-xl p-2">
                  <img
                    src={documentUrl}
                    alt="Soil Laboratory Test Document"
                    className="max-w-full h-auto object-contain rounded-lg shadow-sm"
                  />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Measurements Table ── */}
      <Card>
        <CardContent className="p-0">
          <div className="p-5 border-b border-line flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-extrabold text-ink">Extracted Soil Parameters</h3>
              <p className="text-xs text-muted">
                Edit individual values below if laboratory scan requires correction before confirmation.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-forest bg-[#edf5ed] px-2.5 py-1 rounded-full">
                {measurements.length} parameters identified
              </span>
            </div>
          </div>

          {isProcessing ? (
            <div className="py-16 text-center">
              <Loader2 size={28} className="mx-auto animate-spin text-leaf" />
              <p className="mt-3 text-xs font-semibold text-ink">Reading tabular data & parameters...</p>
              <p className="mt-1 text-[11px] text-muted">Extracting nutrients, chemical properties, and laboratory methods</p>
            </div>
          ) : measurements.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted">
              <FileWarning size={32} className="mx-auto text-amber-500 mb-2 opacity-80" />
              <p className="font-semibold text-ink">No individual parameters extracted yet.</p>
              <p className="mt-1 text-muted max-w-sm mx-auto">
                Check the original uploaded document using the preview button above, or click "Reprocess OCR" to re-evaluate with the vision pipeline.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReprocess}
                disabled={reprocessing}
                className="mt-4 gap-1.5"
              >
                <RefreshCw size={13} className={reprocessing ? "animate-spin" : ""} /> Reprocess Document
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-line">
              {measurements.map((m, idx) => {
                const isCorrected = m.verification_status === "FARMER_CORRECTED" || m.farmer_corrected_value != null;
                const isFlagged = m.is_ambiguous;
                const rating = m.lab_rating;

                return (
                  <div
                    key={m.id || idx}
                    className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-canvas/50 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-extrabold text-ink">
                          {m.display_name || m.parameter_name || m.original_parameter_name}
                        </p>
                        {m.parameter_category && (
                          <Badge variant="outline" className="text-[10px] capitalize">
                            {m.parameter_category}
                          </Badge>
                        )}
                        {m.sample_designation && (
                          <Badge className="bg-leaf/10 text-forest border-0 text-[10px]">
                            {m.sample_designation} {m.sample_id ? `(#${m.sample_id})` : ""}
                          </Badge>
                        )}
                        {isCorrected && (
                          <Badge className="bg-amber-100 text-amber-900 border-0 text-[10px] font-bold">
                            Farmer Corrected
                          </Badge>
                        )}
                        {isFlagged && (
                          <Badge className="bg-red-100 text-red-800 border-0 text-[10px]">
                            Needs Review
                          </Badge>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted">
                        <span>Unit: <strong className="text-ink">{m.unit || "—"}</strong></span>
                        {m.extraction_confidence != null && (
                          <span>· OCR Confidence: {(m.extraction_confidence * 100).toFixed(0)}%</span>
                        )}
                        {rating && (
                          <span>· Rating: <span className="font-semibold text-ink">{rating}</span></span>
                        )}
                        {m.analytical_method && (
                          <span>· Method: <em>{m.analytical_method}</em></span>
                        )}
                      </div>

                      {m.original_parameter_name && m.original_parameter_name !== (m.display_name || m.parameter_name) && (
                        <p className="text-[10px] text-muted italic">
                          Report text: "{m.original_parameter_name}"
                        </p>
                      )}

                      {m.farmer_notes && (
                        <p className="text-[11px] text-amber-800 bg-amber-50 rounded px-2 py-0.5 inline-block">
                          Note: {m.farmer_notes}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                      <div className="flex items-center gap-1.5">
                        <Input
                          type="number"
                          step="any"
                          value={m.numeric_value ?? ""}
                          onChange={(e) => handleValueChange(idx, e.target.value)}
                          disabled={isConfirmed}
                          className="w-28 text-right font-mono font-bold text-sm bg-white border-line"
                        />
                        <span className="text-xs font-semibold text-muted w-14 truncate">
                          {m.unit}
                        </span>
                      </div>

                      {!isConfirmed && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSaveIndividualCorrection(idx)}
                          disabled={savingIdx === idx}
                          className="h-9 px-2 text-xs text-forest hover:bg-[#edf5ed]"
                          title="Save this measurement correction"
                        >
                          {savingIdx === idx ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <PencilLine size={14} />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
