import { Droplets, FileClock, FileUp, FlaskConical, Waves } from "lucide-react";
import { UploadWorkflow } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function WaterPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Water intelligence"
      title="Water sources & quality"
      description="Manage farm water sources and review measured quality results without guessing irrigation advice."
      icon={Droplets}
      steps={[
        "Add a water source",
        "Upload and review a laboratory report",
        "Request a backend quality evaluation",
      ]}
      sections={[
        {
          title: "Water sources",
          description: "Record source type and farmer-reported availability.",
          icon: Waves,
          status: "Information required",
        },
        {
          title: "Quality evaluation",
          description: "Evaluation requires reviewed laboratory measurements.",
          icon: FlaskConical,
          status: "Laboratory test required",
        },
        {
          title: "Measurement review",
          description: "Check extracted values and units against the original report.",
          icon: FileUp,
          status: "No report",
        },
        {
          title: "Report history",
          description: "Keep reviewed quality reports by source and sample date.",
          icon: FileClock,
          status: "No reports",
        },
      ]}
    >
      <UploadWorkflow kind="water laboratory report" />
    </IntelligenceWorkspace>
  );
}
