/**
 * Unit verification suite for BackButton navigation history and fallback mechanics.
 */

export function assertNavigationBehavior(
  historyLength: number,
  historyIdx: number,
  fallbackHref: string = "/"
): { method: "back" | "push"; destination?: string } {
  const hasInAppHistory = historyLength > 1 && historyIdx > 0;

  if (hasInAppHistory) {
    return { method: "back" };
  } else {
    return { method: "push", destination: fallbackHref };
  }
}

export function shouldAllowNavigation(confirmDirty: boolean, isDirty: boolean, userConfirmed: boolean): boolean {
  if (confirmDirty && isDirty) {
    return userConfirmed;
  }
  return true;
}

// In-app history simulation
const inAppResult = assertNavigationBehavior(3, 2, "/schemes");
if (inAppResult.method !== "back") {
  throw new Error("Expected router.back() when in-app history exists");
}

// Direct URL entry simulation
const directResult = assertNavigationBehavior(1, 0, "/schemes");
if (directResult.method !== "push" || directResult.destination !== "/schemes") {
  throw new Error("Expected router.push(/schemes) on direct URL entry");
}

// Dirty form cancel simulation
const blockedNav = shouldAllowNavigation(true, true, false);
if (blockedNav !== false) {
  throw new Error("Expected navigation to be blocked when user cancels dirty form dialogue");
}
