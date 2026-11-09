import { FileUp, FlaskConical, Layers3, Leaf, Scale, TestTubes } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function SoilPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Soil intelligence"
      title="Understand your soil"
      description="Review profiles, depth, texture and laboratory evidence with every source clearly labelled."
      icon={Leaf}
      steps={[
        "Upload or connect a report",
        "Review OCR measurements",
        "Confirm corrections before analysis",
      ]}
      actionLabel="Upload soil report"
      actionHref="/farms/current/soil/reports/new"
      sections={[
        {
          title: "Profile & depth",
          description: "Review connected soil layers and depth information.",
          icon: Layers3,
          status: "Unavailable",
        },
        {
          title: "Texture & composition",
          description: "See source-labelled sand, silt, clay and composition data.",
          icon: TestTubes,
          status: "Laboratory test required",
        },
        {
          title: "Laboratory reports",
          description: "Upload and review measured soil results.",
          icon: FlaskConical,
          href: "/farms/current/soil/reports",
        },
        {
          title: "OCR review",
          description: "Correct extracted measurements before confirming the report.",
          icon: FileUp,
          status: "No report",
        },
        {
          title: "Lab vs SoilGrids",
          description: "Compare measured and modelled values without merging their sources.",
          icon: Scale,
          status: "Unavailable",
        },
      ]}
    />
  );
}
