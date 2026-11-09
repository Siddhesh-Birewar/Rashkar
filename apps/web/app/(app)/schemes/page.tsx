import {
  ExternalLink,
  FileCheck2,
  Filter,
  Landmark,
  Search,
  ShieldCheck,
  Tags,
} from "lucide-react";
import { SearchBox } from "@/components/guided-workflows";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function SchemesPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Government support"
      title="Government schemes"
      description="Find verified scheme information, eligibility, documents and official application links."
      icon={Landmark}
      steps={[
        "Search or choose a category",
        "Check eligibility and documents",
        "Continue on the official portal",
      ]}
      actionLabel="Admin interface"
      actionHref="/schemes/admin"
      sections={[
        {
          title: "Browse categories",
          description: "Explore scheme categories once verified records are connected.",
          icon: Tags,
          status: "Unavailable",
        },
        {
          title: "Filter schemes",
          description: "Narrow by benefit, applicant type and location.",
          icon: Filter,
          status: "Ready",
        },
        {
          title: "Eligibility",
          description: "Read exact criteria from the scheme's verified source.",
          icon: ShieldCheck,
          status: "Source required",
        },
        {
          title: "Documents",
          description: "Prepare the required documents before beginning an application.",
          icon: FileCheck2,
          status: "Source required",
        },
        {
          title: "Official portal",
          description: "External links are clearly labelled and open the official service.",
          icon: ExternalLink,
          status: "Source required",
        },
        {
          title: "Scheme search",
          description: "Search titles and verified summaries in one place.",
          icon: Search,
          status: "Ready",
        },
      ]}
    >
      <SearchBox placeholder="Search government schemes" />
    </IntelligenceWorkspace>
  );
}
