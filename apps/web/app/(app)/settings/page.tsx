import { Contrast, Languages, Settings, Smartphone, Type } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function SettingsPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Preferences"
      title="App settings"
      description="Keep CropNet readable, comfortable and easy to use outdoors."
      icon={Settings}
      backHref="/profile"
      steps={[
        "Choose a preference",
        "Preview the change",
        "Save it to your account when connected",
      ]}
      sections={[
        {
          title: "Language",
          description: "Switch between English and Marathi layouts.",
          icon: Languages,
          href: "/settings/language",
        },
        {
          title: "Text size",
          description: "Use comfortable text and large touch targets.",
          icon: Type,
          status: "Device default",
        },
        {
          title: "High contrast",
          description: "Improve visibility in bright outdoor conditions.",
          icon: Contrast,
          status: "System default",
        },
        {
          title: "Device permissions",
          description: "Review camera, gallery and location access.",
          icon: Smartphone,
          status: "Device managed",
        },
      ]}
    />
  );
}
