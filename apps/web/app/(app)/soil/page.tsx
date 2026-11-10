"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useFarm } from "@/lib/farm-context";
import { Loader2 } from "lucide-react";

export default function SoilRedirectPage() {
  const router = useRouter();
  const { selectedFarmId, farms } = useFarm();

  useEffect(() => {
    const targetFarmId = selectedFarmId || (farms.length > 0 ? farms[0].id : "current");
    router.replace(`/farms/${targetFarmId}/soil`);
  }, [router, selectedFarmId, farms]);

  return (
    <div className="flex h-64 items-center justify-center">
      <Loader2 className="animate-spin text-forest" size={32} />
    </div>
  );
}
