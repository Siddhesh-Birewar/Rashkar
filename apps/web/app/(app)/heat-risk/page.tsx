import { CalendarClock, CloudSun, Flame, HeartPulse, ShieldAlert, Wheat } from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function HeatRiskPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Heat safety"
      title="Heat Risk"
      description="Check crop heat outlook and agricultural worker WBGT assessment from verified forecast inputs."
      icon={Flame}
      steps={[
        "Choose assessment type",
        "Confirm farm, crop or work context",
        "Review forecast-linked interventions",
      ]}
      sections={[
        {
          title: "Crop assessment",
          description: "Select a supported crop and growth stage for the chosen farm.",
          icon: Wheat,
          status: "Information required",
        },
        {
          title: "Farm heat outlook",
          description: "Forecast-linked risk appears only when farm weather is available.",
          icon: CloudSun,
          status: "Unavailable",
        },
        {
          title: "Risk interventions",
          description: "Backend-approved actions are shown with their forecast window.",
          icon: ShieldAlert,
          status: "Unavailable",
        },
        {
          title: "Worker WBGT",
          description: "Assess field-work exposure separately from crop heat risk.",
          icon: HeartPulse,
          status: "Information required",
        },
        {
          title: "Forecast context",
          description: "Review the date, source and age of the weather forecast.",
          icon: CalendarClock,
          status: "Unavailable",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow label="Farm-specific forecast" value="Unavailable" kind="forecast" />
          <StatusRow
            label="Crop heat risk"
            value="Additional information required"
            kind="backend assessment"
          />
          <StatusRow
            label="Worker WBGT risk"
            value="Additional information required"
            kind="backend assessment"
          />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
