import { CalendarDays, ChartNoAxesCombined, Clock3, CloudSun, History } from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function WeatherPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Weather & climate"
      title="Farm weather"
      description="Current conditions, short-range forecasts and climate context for the selected farm."
      icon={CloudSun}
      steps={[
        "Select a mapped farm",
        "Load dated weather data",
        "Review forecast source before planning",
      ]}
      sections={[
        {
          title: "Current weather",
          description: "Latest available observation with source and time.",
          icon: CloudSun,
          status: "Unavailable",
        },
        {
          title: "Five-day forecast",
          description: "Daily forecast windows for the farm location.",
          icon: CalendarDays,
          status: "Unavailable",
        },
        {
          title: "Three-hour forecast",
          description: "Short interval forecast with issue time.",
          icon: Clock3,
          status: "Unavailable",
        },
        {
          title: "Weather history",
          description: "Review available historical observations.",
          icon: History,
          status: "Unavailable",
        },
        {
          title: "Climate summary",
          description: "Longer-term context is labelled separately from weather.",
          icon: ChartNoAxesCombined,
          status: "Unavailable",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow label="Temperature" value="Unavailable" kind="observation" />
          <StatusRow label="Rain forecast" value="Unavailable" kind="forecast" />
          <StatusRow label="Last updated" value="Unavailable" kind="source metadata" />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
