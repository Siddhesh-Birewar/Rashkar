import { CloudSun, Droplets, HeartPulse, Leaf, MapPinned, Satellite } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function FarmDetailPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Farm workspace"
      title="Farm overview"
      description="One clear view of location, crops and connected intelligence for this farm."
      icon={MapPinned}
      steps={[
        "Confirm the farm profile",
        "Connect reports and observations",
        "Review verified insights",
      ]}
      actionLabel="Edit farm"
      actionHref="/farms/current/edit"
      sections={[
        {
          title: "Soil intelligence",
          description: "Soil profile, laboratory reports and source comparison.",
          icon: Leaf,
          href: "/farms/current/soil",
        },
        {
          title: "Weather & climate",
          description: "Current conditions, forecasts and climate context.",
          icon: CloudSun,
          href: "/farms/current/weather",
        },
        {
          title: "Farm health",
          description: "Unified soil, water, weather and crop condition view.",
          icon: HeartPulse,
          href: "/farms/current/health",
        },
        {
          title: "Water intelligence",
          description: "Water sources, quality reports and irrigation context.",
          icon: Droplets,
          href: "/farms/current/water",
        },
        {
          title: "Satellite & vegetation",
          description: "Field imagery, NDVI, NDMI and observation history.",
          icon: Satellite,
          href: "/farms/current/vegetation",
        },
        {
          title: "Boundary & location",
          description: "Review the mapped field boundary and location source.",
          icon: MapPinned,
        },
      ]}
    />
  );
}
