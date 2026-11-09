import { Bell, Languages, MapPin, Settings, ShieldCheck, UserRound } from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function ProfilePage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Account"
      title="Profile & settings"
      description="Manage your personal details, language, notifications and privacy choices."
      icon={UserRound}
      steps={[
        "Review profile information",
        "Choose language and alerts",
        "Save through the connected account service",
      ]}
      sections={[
        {
          title: "Personal details",
          description: "Name and contact details from your authenticated account.",
          icon: UserRound,
          status: "Not connected",
        },
        {
          title: "Language",
          description: "Choose English or Marathi interface layouts.",
          icon: Languages,
          href: "/settings/language",
        },
        {
          title: "Notifications",
          description: "Control advisory and farm alert preferences.",
          icon: Bell,
          href: "/notifications",
        },
        {
          title: "Farm locations",
          description: "Review location permissions and saved farm access.",
          icon: MapPin,
          href: "/farms",
        },
        {
          title: "Privacy & security",
          description: "Account access and data permissions.",
          icon: ShieldCheck,
          status: "Not connected",
        },
        {
          title: "App settings",
          description: "Accessibility and display preferences.",
          icon: Settings,
          href: "/settings",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow label="Authentication" value="Not connected" kind="account service" />
          <StatusRow label="Preferred language" value="English" kind="device preference" />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
