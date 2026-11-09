import { ClipboardCheck, FileClock, FileText, History, Microscope, Search } from "lucide-react";
import { SearchBox } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function HistoryPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Your records"
      title="History"
      description="Find completed reports, assessments and diagnoses with their original source context."
      icon={History}
      steps={[
        "Choose a record type",
        "Open the saved source context",
        "Review the result and limitations",
      ]}
      sections={[
        {
          title: "Soil reports",
          description: "Confirmed laboratory reports and extraction history.",
          icon: FileText,
          href: "/farms/current/soil/reports",
        },
        {
          title: "Crop assessments",
          description: "Completed suitability assessments and explanations.",
          icon: ClipboardCheck,
          status: "No records",
        },
        {
          title: "Crop Doctor",
          description: "Completed diagnoses only; failed attempts are clearly marked.",
          icon: Microscope,
          status: "No records",
        },
        {
          title: "Water reports",
          description: "Reviewed water laboratory reports by source.",
          icon: FileClock,
          status: "No records",
        },
        {
          title: "Search records",
          description: "Search by record type, date or farm.",
          icon: Search,
          status: "Ready",
        },
      ]}
    >
      <SearchBox placeholder="Search your history" />
    </IntelligenceWorkspace>
  );
}
