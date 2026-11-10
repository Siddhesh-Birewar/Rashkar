"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  Calendar,
  Check,
  CheckCircle2,
  FileCheck2,
  FileText,
  FlaskConical,
  Loader2,
  PencilLine,
  Scale,
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
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!actualFarmId || !reportId) return;

    async function loadReport() {
      try {
        setLoading(true);
        setError(null);
        const data = await soilApi.getReport(actualFarmId!, reportId);
        setReport(data);
        setMeasurements(data.measurements || []);
      } catch (err: any) {
        setError(err?.message || "Failed to load soil report details");
      } finally {
        setLoading(false);
      }
    }

    loadReport();
  }, [actualFarmId, reportId]);

  const handleValueChange = (index: number, val: string) => {
    const updated = [...measurements];
    const num = parseFloat(val);
    updated[index] = {
      ...updated[index],
      numeric_value: isNaN(num) ? null : num,
    };
    setMeasurements(updated);
  };

  const handleConfirm = async () => {
    if (!actualFarmId || !reportId) return;
    try {
      setConfirming(true);
      setError(null);
      await soilApi.confirmReport(actualFarmId, reportId, {
        measurements: measurements.map((m) => ({
          parameter_name: m.parameter_name,
          numeric_value: m.numeric_value,
          unit: m.unit,
        })),
      });
      setSuccess("Report confirmed successfully! Values integrated into farm soil profile.");
      const refreshed = await soilApi.getReport(actualFarmId, reportId);
      setReport(refreshed);
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

  if (loading) {
    return (
      <div className="py-24 text-center">
        <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
        <p className="mt-4 text-sm text-muted">Loading report measurements...</p>
      </div>
    );
  }

  if (error && !report) {
    return (
      <div className="py-16 text-center">
        <p className="text-sm text-muted">{error}</p>
        <Button asChild className="mt-4">
          <Link href={`/farms/${actualFarmId}/soil/reports`}>Back to Reports</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Soil laboratory certificate"
        title="Review OCR Measurements"
        description="Verify and correct extracted soil parameters before integrating them into the verified profile."
        backHref={`/farms/${actualFarmId}/soil/reports`}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleDelete}
              disabled={deleting || confirming}
              className="text-red-600 hover:bg-red-50"
            >
              <Trash2 size={15} /> Delete
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={confirming || report?.status === "CONFIRMED"}
              className="bg-forest"
            >
              {confirming ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Confirming...
                </>
              ) : report?.status === "CONFIRMED" ? (
                <>
                  <CheckCircle2 size={16} /> Confirmed
                </>
              ) : (
                <>
                  <Check size={16} /> Confirm & Save Profile
                </>
              )}
            </Button>
          </div>
        }
      />

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
          <div className="grid gap-4 sm:grid-cols-3 text-xs">
            <div>
              <span className="text-muted block text-[10px] font-bold uppercase">Laboratory</span>
              <span className="font-extrabold text-ink text-sm">
                {report?.laboratory_name || "Certified Soil Testing Lab"}
              </span>
            </div>
            <div>
              <span className="text-muted block text-[10px] font-bold uppercase">Sample Date</span>
              <span className="font-extrabold text-ink text-sm">
                {report?.sample_date || "Not specified"}
              </span>
            </div>
            <div>
              <span className="text-muted block text-[10px] font-bold uppercase">Verification Status</span>
              <Badge
                className={
                  report?.status === "CONFIRMED"
                    ? "bg-[#edf5ed] text-forest border-0"
                    : "bg-orange-50 text-accent border-0"
                }
              >
                {report?.status || "NEEDS_REVIEW"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Measurements Table ── */}
      <Card>
        <CardContent className="p-0">
          <div className="p-5 border-b border-line flex items-center justify-between">
            <h3 className="text-sm font-extrabold text-ink">Extracted Measurements</h3>
            <span className="text-xs text-muted">
              {measurements.length} parameters identified
            </span>
          </div>

          {measurements.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted">
              No individual parameters extracted yet. Check the original uploaded document.
            </div>
          ) : (
            <div className="divide-y divide-line">
              {measurements.map((m, idx) => (
                <div
                  key={m.id || idx}
                  className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div>
                    <p className="text-sm font-extrabold text-ink">{m.parameter_name}</p>
                    <p className="text-xs text-muted">
                      Unit: {m.unit || "—"}
                      {m.confidence_score != null
                        ? ` · OCR Confidence: ${(m.confidence_score * 100).toFixed(0)}%`
                        : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      step="any"
                      value={m.numeric_value ?? ""}
                      onChange={(e) => handleValueChange(idx, e.target.value)}
                      className="w-32 text-right font-mono font-bold"
                    />
                    <span className="text-xs font-semibold text-muted w-14">{m.unit}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
