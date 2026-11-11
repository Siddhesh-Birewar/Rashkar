"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCw, Home, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App Error Boundary caught error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <div className="grid size-14 place-items-center rounded-2xl bg-red-50 text-red-700 shadow-sm border border-red-200">
        <AlertCircle size={28} />
      </div>

      <h2 className="mt-4 text-xl font-extrabold text-ink sm:text-2xl">
        Something Went Wrong
      </h2>

      <p className="mt-2 max-w-md text-xs sm:text-sm text-muted leading-relaxed">
        {error?.message || "An unexpected error occurred while loading this agricultural intelligence screen."}
      </p>

      {error?.digest && (
        <span className="mt-2 rounded-lg bg-canvas px-2.5 py-1 text-[11px] font-mono text-muted">
          Digest: {error.digest}
        </span>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button
          onClick={() => reset()}
          className="gap-2 bg-forest text-white"
        >
          <RefreshCw size={15} />
          Try Again
        </Button>

        <Button asChild variant="outline" className="gap-2">
          <Link href="/">
            <Home size={15} />
            Farm Dashboard
          </Link>
        </Button>
      </div>
    </div>
  );
}
