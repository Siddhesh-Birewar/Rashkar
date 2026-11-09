import {
  BookOpenText,
  CircleHelp,
  ClipboardCheck,
  History,
  MessageCircleQuestion,
  Sparkles,
} from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function AdvisoryPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Crop intelligence"
      title="Crop advisory"
      description="A guided, explainable assessment based on your selected farm and crop context."
      icon={BookOpenText}
      steps={[
        "Choose a farm and crop",
        "Answer follow-up questions",
        "Review the decision explanation",
      ]}
      sections={[
        {
          title: "Start an assessment",
          description: "Select the farm, crop and season before requesting an assessment.",
          icon: ClipboardCheck,
          status: "Information required",
        },
        {
          title: "Follow-up questions",
          description: "Provide only the missing context requested by the backend.",
          icon: MessageCircleQuestion,
          status: "Not started",
        },
        {
          title: "Decision explanation",
          description: "See the evidence, limitations and reason behind a result.",
          icon: Sparkles,
          status: "Unavailable",
        },
        {
          title: "Assessment history",
          description: "Revisit completed assessments and their recorded source context.",
          icon: History,
          href: "/history",
        },
        {
          title: "Ask for help",
          description: "Get simple clarification without replacing verified agronomic advice.",
          icon: CircleHelp,
          status: "Unavailable",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow
            label="Selected farm"
            value="Additional information required"
            kind="farmer-reported"
          />
          <StatusRow
            label="Crop and growth stage"
            value="Additional information required"
            kind="farmer-reported"
          />
          <StatusRow label="Suitability result" value="Unavailable" kind="backend assessment" />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
