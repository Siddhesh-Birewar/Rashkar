"use client";

import React from "react";
import { AuthProvider } from "@/lib/auth-context";
import { FarmProvider } from "@/lib/farm-context";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <FarmProvider>{children}</FarmProvider>
    </AuthProvider>
  );
}
