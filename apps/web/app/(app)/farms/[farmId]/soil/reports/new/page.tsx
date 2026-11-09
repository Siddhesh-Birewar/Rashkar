import { FileUp, ScanText, ShieldCheck } from "lucide-react";
import { UploadWorkflow } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function NewSoilReportPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Soil laboratory report"
      title="Upload a soil report"
      description="Add a complete, readable report image. You will review every extracted measurement before confirmation."
      icon={FileUp}
      steps={[
        "Choose a clear report image",
        "Review OCR values and units",
        "Confirm the laboratory source",
      ]}
      sections={[
        {
          title: "Image check",
          description: "Include all pages, labels and units.",
          icon: FileUp,
          status: "Not started",
        },
        {
          title: "OCR extraction",
          description: "Extraction begins only after the report service accepts the image.",
          icon: ScanText,
          status: "Unavailable",
        },
        {
          title: "Human confirmation",
          description: "No measurement becomes verified without your review.",
          icon: ShieldCheck,
          status: "Required",
        },
      ]}
    >
      <UploadWorkflow kind="soil laboratory report" />
    </IntelligenceWorkspace>
  );
}
