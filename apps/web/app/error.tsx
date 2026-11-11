"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Root Error Boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6 text-center bg-[#F9FBF9]">
      <div className="grid size-16 place-items-center rounded-3xl bg-red-100 text-red-700 shadow-sm border border-red-200">
        <AlertCircle size={32} />
      </div>

      <h1 className="mt-5 text-2xl font-extrabold text-ink sm:text-3xl">
        Application Error
      </h1>

      <p className="mt-2 max-w-md text-sm text-muted leading-relaxed">
        {error?.message || "CropNet AI encountered an unexpected issue while rendering."}
      </p>

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button
          onClick={() => reset()}
          className="gap-2 bg-[#1b5e20] text-white"
        >
          <RefreshCw size={15} />
          Reload Screen
        </Button>

        <Button asChild variant="outline" className="gap-2 bg-white">
          <Link href="/">
            <Home size={15} />
            Back to Home
          </Link>
        </Button>
      </div>
    </div>
  );
}
