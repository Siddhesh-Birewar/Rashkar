"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck2,
  FileClock,
  FileSearch,
  FileText,
  FileUp,
  FlaskConical,
  Loader2,
  Plus,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/states";
import { soilApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { SoilTestReport } from "@/lib/api/types";

export default function SoilReportsPage() {
  const params = useParams();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const [reports, setReports] = useState<SoilTestReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!actualFarmId) {
      setLoading(false);
      return;
    }

    async function loadReports() {
      try {
        setLoading(true);
        setError(null);
        const data = await soilApi.listReports(actualFarmId!);
        setReports(data);
      } catch (err: any) {
        setError(err?.message || "Failed to load soil reports");
      } finally {
        setLoading(false);
      }
    }

    loadReports();
  }, [actualFarmId]);

  if (!actualFarmId) {
    return (
      <div className="py-16 text-center">
        <p className="text-sm text-muted">Please select a farm first.</p>
        <Button asChild className="mt-4">
          <Link href="/farms">Select Farm</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Soil laboratory testing"
        title="Soil Test Reports"
        description="Physical laboratory certificates and automated OCR extractions with human-in-the-loop review."
        backHref={`/farms/${actualFarmId}/soil`}
        actions={
          <Button asChild>
            <Link href={`/farms/${actualFarmId}/soil/reports/new`}>
              <Plus size={16} /> Upload New Report
            </Link>
          </Button>
        }
      />

      {error && (
        <div className="flex items-start gap-3 rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
          <AlertCircle size={17} className="shrink-0 text-red-600" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center">
          <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
          <p className="mt-4 text-sm text-muted">Retrieving laboratory records...</p>
        </div>
      ) : reports.length === 0 ? (
        <Card>
          <EmptyState
            icon={FlaskConical}
            title="No soil reports uploaded"
            description="Upload a photo or PDF of your Soil Health Card or laboratory test to verify available NPK."
            action={
              <Button asChild>
                <Link href={`/farms/${actualFarmId}/soil/reports/new`}>
                  <FileUp size={16} /> Upload Soil Report
                </Link>
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid gap-4">
          {reports.map((report) => (
            <Card key={report.id} className="border-line hover:border-leaf/60 transition-colors">
              <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-start gap-4">
                  <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-[#edf5ed] text-forest">
                    <FileText size={22} />
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-extrabold text-ink">
                        {report.laboratory_name || "Soil Test Certificate"}
                      </h3>
                      <Badge
                        variant="outline"
                        className={
                          report.status === "CONFIRMED"
                            ? "border-leaf text-forest bg-green-50"
                            : report.status === "NEEDS_REVIEW"
                              ? "border-accent text-accent bg-orange-50"
                              : "border-line text-muted"
                        }
                      >
                        {report.status}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted flex items-center gap-2">
                      <span className="flex items-center gap-1">
                        <Calendar size={13} /> Sample Date: {report.sample_date || "Not recorded"}
                      </span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <Clock size={13} /> Uploaded:{" "}
                        {new Date(report.upload_timestamp || report.created_at || Date.now()).toLocaleDateString()}
                      </span>
                    </p>
                    {report.file_name && (
                      <p className="mt-1 text-[11px] text-muted font-mono">{report.file_name}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/farms/${actualFarmId}/soil/reports/${report.id}`}>
                      <FileSearch size={15} /> Review Extractions
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
