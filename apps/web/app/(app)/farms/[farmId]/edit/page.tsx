import { FarmSetupForm } from "@/components/guided-workflows";
import { DataIntegrityNotice } from "@/components/intelligence-workspace";
import { PageHeader } from "@/components/page-header";

export default function EditFarmPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Farm profile"
        title="Edit farm"
        description="Review the farm name, location and mapped boundary before saving changes."
        backHref="/farms/current"
      />
      <DataIntegrityNotice>
        Existing farm details will load from the farm service. No placeholder location or boundary
        is shown.
      </DataIntegrityNotice>
      <FarmSetupForm />
    </div>
  );
}
