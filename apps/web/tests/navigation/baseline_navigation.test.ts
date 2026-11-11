/**
 * Baseline navigation registry test suite.
 * Defines expected fallback routes and back navigation contracts across CropNet AI modules.
 */

export interface RouteNavigationContract {
  path: string;
  category: "root" | "auth" | "redirect" | "standard";
  requiresBackButton: boolean;
  expectedFallbackHref?: string;
  confirmDirtyGuarded?: boolean;
}

export const ROUTE_NAVIGATION_REGISTRY: RouteNavigationContract[] = [
  // Root and Entry (Explicitly No Back Button)
  { path: "/", category: "root", requiresBackButton: false },
  { path: "/login", category: "auth", requiresBackButton: false },
  { path: "/register", category: "auth", requiresBackButton: false },

  // Farm Management
  { path: "/farms", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/farms/new", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms" },
  { path: "/farms/[farmId]", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms" },
  { path: "/farms/[farmId]/edit", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]", confirmDirtyGuarded: true },

  // Farm Health & Environmental Intelligence
  { path: "/farms/[farmId]/health", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]" },
  { path: "/farms/[farmId]/soil", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]" },
  { path: "/farms/[farmId]/soil/reports", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]/soil" },
  { path: "/farms/[farmId]/soil/reports/[reportId]", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]/soil/reports" },
  { path: "/farms/[farmId]/soil/reports/new", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]/soil/reports" },
  { path: "/farms/[farmId]/vegetation", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]" },
  { path: "/farms/[farmId]/water", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]" },
  { path: "/farms/[farmId]/weather", category: "standard", requiresBackButton: true, expectedFallbackHref: "/farms/[farmId]" },

  // Crop Intelligence
  { path: "/advisory", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/assistant", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/crop-doctor", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/crops", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },

  // Climate Resilience & RASHKAR
  { path: "/heat-risk", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/rashkar", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/rashkar/crop-heat", category: "standard", requiresBackButton: true, expectedFallbackHref: "/rashkar" },
  { path: "/rashkar/earn-more", category: "standard", requiresBackButton: true, expectedFallbackHref: "/rashkar" },
  { path: "/rashkar/worker-heat", category: "standard", requiresBackButton: true, expectedFallbackHref: "/rashkar" },
  { path: "/rashkar/yield", category: "standard", requiresBackButton: true, expectedFallbackHref: "/rashkar" },

  // Farm Income Diversification
  { path: "/income", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },

  // Government Support
  { path: "/schemes", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/schemes/[schemeId]", category: "standard", requiresBackButton: true, expectedFallbackHref: "/schemes" },
  { path: "/schemes/admin", category: "standard", requiresBackButton: true, expectedFallbackHref: "/schemes" },

  // Profile & System
  { path: "/profile", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/history", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/notifications", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/help", category: "standard", requiresBackButton: true, expectedFallbackHref: "/" },
  { path: "/settings", category: "standard", requiresBackButton: true, expectedFallbackHref: "/profile" },
  { path: "/settings/language", category: "standard", requiresBackButton: true, expectedFallbackHref: "/profile" },

  // Redirect Endpoints
  { path: "/health", category: "redirect", requiresBackButton: false },
  { path: "/soil", category: "redirect", requiresBackButton: false },
  { path: "/vegetation", category: "redirect", requiresBackButton: false },
  { path: "/water", category: "redirect", requiresBackButton: false },
  { path: "/weather", category: "redirect", requiresBackButton: false },
];

export function validateRouteContract(path: string): RouteNavigationContract | undefined {
  return ROUTE_NAVIGATION_REGISTRY.find((r) => r.path === path);
}
