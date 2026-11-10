"use client";

import { MapPin, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useFarm } from "@/lib/farm-context";

export function FarmSelector() {
  const router = useRouter();
  const { farms, selectedFarmId, setSelectedFarmId, loading } = useFarm();

  const handleValueChange = (value: string) => {
    if (value === "add_new") {
      router.push("/farms/new");
      return;
    }
    if (value === "none") {
      setSelectedFarmId(null);
      return;
    }
    setSelectedFarmId(value);
  };

  return (
    <div className="relative">
      <MapPin
        size={16}
        className="pointer-events-none absolute top-1/2 left-3.5 z-10 -translate-y-1/2 text-leaf"
      />
      <Select
        value={selectedFarmId || "none"}
        onValueChange={handleValueChange}
        disabled={loading}
      >
        <SelectTrigger className="min-w-0 pl-10 md:w-[240px]">
          <SelectValue placeholder={loading ? "Loading farms..." : "Select a farm"} />
        </SelectTrigger>
        <SelectContent>
          {farms.length === 0 ? (
            <SelectItem value="none">No farms registered</SelectItem>
          ) : (
            farms.map((farm) => (
              <SelectItem key={farm.id} value={farm.id}>
                {farm.name} {farm.taluka ? `(${farm.taluka})` : ""}
              </SelectItem>
            ))
          )}
          <SelectItem value="add_new" className="text-leaf font-bold">
            <span className="flex items-center gap-1.5">
              <Plus size={14} /> Add new farm
            </span>
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
