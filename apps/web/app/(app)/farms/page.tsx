import { MapPinned, Plus } from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/states";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export default function FarmsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Your farms"
        description="Manage fields and keep each farm’s intelligence in one place."
        actions={
          <Button asChild>
            <Link href="/farms/new">
              <Plus size={18} /> Add farm
            </Link>
          </Button>
        }
      />
      <Card>
        <EmptyState
          icon={MapPinned}
          title="No farms added"
          description="Add your first farm to prepare weather, soil, crop health and water insights."
          action={
            <Button asChild>
              <Link href="/farms/new">Set up a farm</Link>
            </Button>
          }
        />
      </Card>
    </div>
  );
}
