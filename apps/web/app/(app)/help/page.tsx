import { BookOpenText, HelpCircle, LogOut, MessageCircleQuestion, ShieldCheck } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function HelpPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Support"
      title="Help & support"
      description="Learn how CropNet uses data, get workflow help or safely leave your account."
      icon={HelpCircle}
      steps={["Choose a help topic", "Follow the guided steps", "Contact support when connected"]}
      sections={[
        {
          title: "Using CropNet",
          description: "Simple guides for farms, reports and assessments.",
          icon: BookOpenText,
          status: "Available",
        },
        {
          title: "Ask a question",
          description: "Support contact options will appear when the service is connected.",
          icon: MessageCircleQuestion,
          status: "Unavailable",
        },
        {
          title: "Data & limitations",
          description: "Understand sources, forecasts and model limitations.",
          icon: ShieldCheck,
          status: "Available",
        },
        {
          title: "Log out",
          description: "End your session on this device.",
          icon: LogOut,
          status: "Authentication required",
        },
      ]}
    />
  );
}
