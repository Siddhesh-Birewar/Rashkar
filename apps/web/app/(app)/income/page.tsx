import {
  Calculator,
  CircleDollarSign,
  GitCompareArrows,
  Lightbulb,
  ListFilter,
  Scale,
} from "lucide-react";
import { IntelligenceWorkspace, StatusRow } from "@/components/intelligence-workspace";
import { Card, CardContent } from "@/components/ui/card";

export default function IncomePage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Income diversification"
      title="Income opportunities"
      description="Explore possibilities, compare assumptions and build financial scenarios without invented returns."
      icon={CircleDollarSign}
      steps={[
        "Review opportunity requirements",
        "Enter your own cost assumptions",
        "Compare scenarios and limitations",
      ]}
      sections={[
        {
          title: "Opportunity catalogue",
          description: "Browse opportunities after trusted sources are connected.",
          icon: Lightbulb,
          status: "Unavailable",
        },
        {
          title: "Opportunity matching",
          description: "Match against verified farm context and your preferences.",
          icon: ListFilter,
          status: "Information required",
        },
        {
          title: "Scenario calculator",
          description: "Enter costs, capacity and selling assumptions yourself.",
          icon: Calculator,
          status: "Ready",
        },
        {
          title: "Compare options",
          description: "Compare your scenarios side by side using the same assumptions.",
          icon: GitCompareArrows,
          status: "Ready",
        },
        {
          title: "Risk and effort",
          description: "Review dependencies and uncertainty before making a decision.",
          icon: Scale,
          status: "Source required",
        },
      ]}
    >
      <Card>
        <CardContent>
          <StatusRow label="Expected income" value="Not verified" kind="user scenario" />
          <StatusRow label="Setup cost" value="Additional information required" kind="user input" />
          <StatusRow label="Opportunity match" value="Unavailable" kind="backend assessment" />
        </CardContent>
      </Card>
    </IntelligenceWorkspace>
  );
}
