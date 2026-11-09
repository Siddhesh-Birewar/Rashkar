import { FileCheck2, FileClock, FileSearch, FileUp } from "lucide-react";
import { UploadWorkflow } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function SoilReportsPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Measured soil data"
      title="Soil reports"
      description="Upload a laboratory report, verify extracted measurements and keep a traceable history."
      icon={FileClock}
      steps={[
        "Upload a clear report image",
        "Correct OCR extraction",
        "Confirm measurements and source",
      ]}
      sections={[
        {
          title: "Extraction review",
          description: "Every OCR value must be reviewed before confirmation.",
          icon: FileSearch,
          status: "No report",
        },
        {
          title: "Measurement correction",
          description: "Edit units and values while retaining the original image.",
          icon: FileCheck2,
          status: "Not started",
        },
        {
          title: "Report history",
          description: "Confirmed reports will appear here with dates and laboratory source.",
          icon: FileClock,
          status: "No reports",
        },
        {
          title: "Upload guidance",
          description: "Use a sharp, complete image with labels and units visible.",
          icon: FileUp,
          status: "Ready",
        },
      ]}
    >
      <UploadWorkflow kind="soil laboratory report" />
    </IntelligenceWorkspace>
  );
}
