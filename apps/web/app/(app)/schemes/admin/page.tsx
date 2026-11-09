import { FilePenLine, Landmark, ListChecks, ShieldCheck, Users } from "lucide-react";
import { IntelligenceWorkspace } from "@/components/intelligence-workspace";

export default function SchemeAdminPage() {
  return (
    <IntelligenceWorkspace
      eyebrow="Restricted workspace"
      title="Scheme administration"
      description="Create and review source-backed scheme records. Access control will be enforced by the connected backend."
      icon={Landmark}
      steps={[
        "Verify administrator access",
        "Add official source information",
        "Review and publish the record",
      ]}
      sections={[
        {
          title: "Draft schemes",
          description: "Prepare scheme records before publication.",
          icon: FilePenLine,
          status: "Authentication required",
        },
        {
          title: "Review queue",
          description: "Check eligibility, benefits and official links.",
          icon: ListChecks,
          status: "Authentication required",
        },
        {
          title: "Source verification",
          description: "Every published record requires an official source.",
          icon: ShieldCheck,
          status: "Required",
        },
        {
          title: "Admin access",
          description: "Role assignment remains controlled by the backend.",
          icon: Users,
          status: "Restricted",
        },
      ]}
    />
  );
}
