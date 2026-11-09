import { Bell, CloudSun, Flame, Sprout } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function NotificationsPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Alert preferences"
      title="Notifications"
      description="Choose which verified farm updates you want to receive."
      icon={Bell}
      steps={[
        "Choose alert categories",
        "Confirm notification permission",
        "Receive source-linked alerts",
      ]}
      sections={[
        {
          title: "Farm advisories",
          description: "Important connected-farm updates.",
          icon: Sprout,
          status: "Off",
        },
        {
          title: "Weather alerts",
          description: "Forecast-based notices for the selected farm.",
          icon: CloudSun,
          status: "Off",
        },
        {
          title: "Heat risk alerts",
          description: "Crop and worker heat assessment updates.",
          icon: Flame,
          status: "Off",
        },
        {
          title: "App notifications",
          description: "Report processing and account messages.",
          icon: Bell,
          status: "Off",
        },
      ]}
    />
  );
}
