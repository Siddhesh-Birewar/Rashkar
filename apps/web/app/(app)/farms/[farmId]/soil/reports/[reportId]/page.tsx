import { FileCheck2, FlaskConical, PencilLine, Scale } from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function SoilReportDetailPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Laboratory report"
      title="Review soil measurements"
      description="Confirm extracted values, units and laboratory context before using this report."
      icon={FlaskConical}
      steps={[
        "Compare with the source image",
        "Correct extraction errors",
        "Confirm the reviewed report",
      ]}
      sections={[
        {
          title: "Source image",
          description: "The original uploaded report remains available for checking.",
          icon: FileCheck2,
          status: "Unavailable",
        },
        {
          title: "Extracted measurements",
          description: "No value is accepted until it has been reviewed.",
          icon: PencilLine,
          status: "Not verified",
        },
        {
          title: "Source comparison",
          description: "Compare with modelled SoilGrids values after confirmation.",
          icon: Scale,
          status: "Unavailable",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow
            label="Laboratory name"
            value="Additional information required"
            kind="report metadata"
          />
          <StatusRow
            label="Sample date"
            value="Additional information required"
            kind="report metadata"
          />
          <StatusRow label="Measurement review" value="Not verified" kind="measured" />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
