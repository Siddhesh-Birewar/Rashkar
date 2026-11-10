"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { FileUp, ScanText, ShieldCheck } from "lucide-react";
import { UploadWorkflow } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";
import { soilApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";

export default function NewSoilReportPage() {
  const params = useParams();
  const router = useRouter();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const [uploadStatus, setUploadStatus] = useState<string>("Ready");

  const handleUpload = async (file: File) => {
    if (!actualFarmId) throw new Error("No active farm parcel selected.");
    setUploadStatus("Uploading & Running OCR...");
    const report = await soilApi.uploadReport(actualFarmId, file);
    setUploadStatus("Extracted successfully");
    if (report && report.id) {
      router.push(`/farms/${actualFarmId}/soil/reports/${report.id}`);
    } else {
      router.push(`/farms/${actualFarmId}/soil/reports`);
    }
  };

  return (
    <IntelligenceWorkspace
      eyebrow="Soil laboratory report"
      title="Upload a soil report"
      description="Add a complete, readable Soil Health Card or laboratory test certificate (PDF, JPG or PNG ≤15 MB)."
      icon={FileUp}
      steps={[
        "Choose a clear report document",
        "Review OCR extractions and units",
        "Confirm measurements into farm profile",
      ]}
      sections={[
        {
          title: "Document check",
          description: "Ensure test laboratory name, date and units (kg/ha, dS/m, %) are clearly visible.",
          icon: FileUp,
          status: uploadStatus,
        },
        {
          title: "OCR extraction",
          description: "Extraction isolates pH, EC, Organic Carbon, and available N/P/K with confidence scores.",
          icon: ScanText,
          status: "Automated",
        },
        {
          title: "Human confirmation",
          description: "No measurement becomes verified without human-in-the-loop review.",
          icon: ShieldCheck,
          status: "Required",
        },
      ]}
    >
      <UploadWorkflow
        kind="soil laboratory report (PDF or Image)"
        accept=".pdf,image/png,image/jpeg"
        onUpload={handleUpload}
      />
    </IntelligenceWorkspace>
  );
}
