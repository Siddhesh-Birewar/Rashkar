"use client";

import { MapPin } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function FarmSelector() {
  return (
    <div className="relative">
      <MapPin
        size={16}
        className="pointer-events-none absolute top-1/2 left-3.5 z-10 -translate-y-1/2 text-leaf"
      />
      <Select defaultValue="none">
        <SelectTrigger className="min-w-0 pl-10 md:w-[220px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="none">No farm selected</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
