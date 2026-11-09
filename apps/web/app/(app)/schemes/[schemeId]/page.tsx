import { ExternalLink, FileCheck2, Landmark, ListChecks, ShieldCheck } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function SchemeDetailPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Scheme detail"
      title="Scheme details"
      description="Verified benefits, eligibility, documents and instructions will appear after a scheme source is connected."
      icon={Landmark}
      steps={[
        "Read the verified eligibility",
        "Prepare required documents",
        "Continue on the official portal",
      ]}
      sections={[
        {
          title: "Benefits",
          description: "Benefit details must match the official scheme source.",
          icon: ListChecks,
          status: "Source required",
        },
        {
          title: "Eligibility",
          description: "Check location, applicant and farm criteria.",
          icon: ShieldCheck,
          status: "Source required",
        },
        {
          title: "Documents",
          description: "Prepare every document listed by the official source.",
          icon: FileCheck2,
          status: "Source required",
        },
        {
          title: "How to apply",
          description: "Follow verified instructions and deadlines.",
          icon: ListChecks,
          status: "Source required",
        },
        {
          title: "Official portal",
          description: "Continue only through a verified government link.",
          icon: ExternalLink,
          status: "Unavailable",
        },
      ]}
    />
  );
}
