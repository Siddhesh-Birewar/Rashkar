import { BookOpenText, CalendarDays, ClipboardCheck, History, Search, Sprout } from "lucide-react";
import { SearchBox } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function CropsPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Crop catalogue"
      title="Crop intelligence"
      description="Explore verified crop profiles, Maharashtra seasons and farm suitability workflows."
      icon={Sprout}
      steps={[
        "Choose a verified crop profile",
        "Confirm farm and season",
        "Request a backend suitability assessment",
      ]}
      sections={[
        {
          title: "Crop catalogue",
          description: "Search crop profiles and their verified source information.",
          icon: Search,
          status: "Source required",
        },
        {
          title: "Maharashtra seasons",
          description: "Review Kharif, Rabi and summer context from connected records.",
          icon: CalendarDays,
          status: "Source required",
        },
        {
          title: "Farm suitability",
          description: "Start an assessment using the selected farm.",
          icon: ClipboardCheck,
          href: "/advisory",
        },
        {
          title: "Decision explanation",
          description: "Understand evidence and limitations behind a completed result.",
          icon: BookOpenText,
          status: "Unavailable",
        },
        {
          title: "Assessment history",
          description: "Revisit earlier assessments without changing their original context.",
          icon: History,
          href: "/history",
        },
      ]}
    >
      <SearchBox placeholder="Search the crop catalogue" />
    </IntelligenceWorkspace>
  );
}
