import { CloudSun, Droplets, HeartPulse, Leaf, Satellite, TriangleAlert } from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function FarmHealthPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Unified farm view"
      title="Farm health"
      description="Bring soil, water, weather and satellite context together without hiding source or uncertainty."
      icon={HeartPulse}
      steps={[
        "Connect farm data sources",
        "Review source-specific status",
        "Open evidence before taking action",
      ]}
      sections={[
        {
          title: "Soil context",
          description: "Measured and modelled soil information remain clearly separated.",
          icon: Leaf,
          href: "/farms/current/soil",
        },
        {
          title: "Water context",
          description: "Sources, quality and report status for this farm.",
          icon: Droplets,
          href: "/farms/current/water",
        },
        {
          title: "Weather context",
          description: "Current observations and forecast windows.",
          icon: CloudSun,
          href: "/farms/current/weather",
        },
        {
          title: "Satellite context",
          description: "NDVI and NDMI observations with image dates.",
          icon: Satellite,
          href: "/farms/current/vegetation",
        },
        {
          title: "Attention areas",
          description: "Only backend-confirmed issues appear as alerts.",
          icon: TriangleAlert,
          status: "None verified",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow label="Overall farm status" value="Not verified" kind="combined assessment" />
          <StatusRow
            label="Latest connected observation"
            value="Unavailable"
            kind="data freshness"
          />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
