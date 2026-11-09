import { CalendarRange, ChartNoAxesCombined, Image, Satellite, ScanSearch } from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function VegetationPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Satellite & vegetation"
      title="Field observations from space"
      description="View dated satellite imagery and vegetation indicators with cloud and source context."
      icon={Satellite}
      steps={[
        "Confirm the mapped boundary",
        "Request available imagery",
        "Review indicator history and limitations",
      ]}
      sections={[
        {
          title: "Satellite map",
          description: "Field imagery appears only for a verified farm boundary.",
          icon: Image,
          status: "Unavailable",
        },
        {
          title: "NDVI",
          description: "Vegetation index observations are shown with capture date and source.",
          icon: ScanSearch,
          status: "Unavailable",
        },
        {
          title: "NDMI",
          description: "Moisture index observations are not treated as soil measurements.",
          icon: ScanSearch,
          status: "Unavailable",
        },
        {
          title: "Time-series charts",
          description: "Compare available observations across dates.",
          icon: ChartNoAxesCombined,
          status: "Unavailable",
        },
        {
          title: "Observation history",
          description: "Review image dates, cloud context and processing status.",
          icon: CalendarRange,
          status: "No observations",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow label="Latest satellite observation" value="Unavailable" kind="observation" />
          <StatusRow label="Cloud context" value="Unavailable" kind="observation metadata" />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
