"use client";

import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";
import type { FarmMapEditorProps } from "./farm-map-editor";

const DynamicFarmMapEditor = dynamic(
  () => import("./farm-map-editor").then((mod) => mod.FarmMapEditor),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[440px] w-full flex-col items-center justify-center rounded-2xl border border-line bg-canvas/60 text-muted">
        <Loader2 size={32} className="animate-spin text-leaf" />
        <p className="mt-3 text-xs font-semibold">Initializing interactive map engine...</p>
      </div>
    ),
  }
);

export function FarmMap(props: FarmMapEditorProps) {
  return <DynamicFarmMapEditor {...props} />;
}
export default FarmMap;
