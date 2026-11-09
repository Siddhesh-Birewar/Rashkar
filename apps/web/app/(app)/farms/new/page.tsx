import { FarmSetupForm } from "@/components/guided-workflows";
import { DataIntegrityNotice } from "@/components/intelligence-workspace";
import { PageHeader } from "@/components/page-header";

export default function NewFarmPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Add a farm"
        description="Name your field, confirm its location and review the boundary before saving."
        backHref="/farms"
      />
      <DataIntegrityNotice>
        Your location and farm boundary are not stored until the farm API confirms the save.
      </DataIntegrityNotice>
      <FarmSetupForm />
    </div>
  );
}
