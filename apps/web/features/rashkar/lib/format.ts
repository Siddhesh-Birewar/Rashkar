export type RiskTone = {
  badgeVariant: "green" | "orange" | "destructive" | "neutral";
  surfaceClass: string;
  label: string;
};

const RISK_LEVEL_MAP: Record<string, RiskTone> = {
  LOW: {
    badgeVariant: "green",
    surfaceClass: "border-[#cde0ce] bg-[#f1f8f1] text-forest",
    label: "LOW",
  },
  LOW_RISK: {
    badgeVariant: "green",
    surfaceClass: "border-[#cde0ce] bg-[#f1f8f1] text-forest",
    label: "LOW",
  },
  MODERATE: {
    badgeVariant: "orange",
    surfaceClass: "border-[#f3d6c4] bg-[#fff7f0] text-[#b44300]",
    label: "MODERATE",
  },
  HIGH: {
    badgeVariant: "orange",
    surfaceClass: "border-[#efb89c] bg-[#fff0e6] text-accent",
    label: "HIGH",
  },
  VERY_HIGH: {
    badgeVariant: "destructive",
    surfaceClass: "border-[#f2b8b5] bg-[#fdeeee] text-[#b71c1c]",
    label: "VERY HIGH",
  },
  CRITICAL: {
    badgeVariant: "destructive",
    surfaceClass: "border-[#f2b8b5] bg-[#fdeeee] text-[#b71c1c]",
    label: "CRITICAL",
  },
  SEVERE: {
    badgeVariant: "destructive",
    surfaceClass: "border-[#f2b8b5] bg-[#fdeeee] text-[#b71c1c]",
    label: "SEVERE",
  },
  EXTREME: {
    badgeVariant: "destructive",
    surfaceClass: "border-[#f2b8b5] bg-[#fdeeee] text-[#b71c1c]",
    label: "EXTREME",
  },
  UNAVAILABLE: {
    badgeVariant: "neutral",
    surfaceClass: "border-line bg-[#f4f7f4] text-muted",
    label: "UNAVAILABLE",
  },
};

export function getRiskTone(level?: string | null): RiskTone {
  const key = (level || "UNAVAILABLE").toUpperCase().replace(/\s+/g, "_");
  return (
    RISK_LEVEL_MAP[key] ?? {
      badgeVariant: "neutral",
      surfaceClass: "border-line bg-[#f4f7f4] text-ink",
      label: key.replace(/_/g, " "),
    }
  );
}

export function formatInr(amount?: number | null): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return "—";
  }
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

export function formatNumber(value?: number | null, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Data Not Available";
  }
  return value.toFixed(digits);
}

export function formatCropLabel(cropCode?: string | null): string {
  if (!cropCode) return "Unspecified crop";
  return cropCode
    .split("_")
    .map((part) => (part ? part.charAt(0).toUpperCase() + part.slice(1) : ""))
    .join(" ");
}

export function formatTokenLabel(token?: string | null): string {
  if (!token) return "—";
  return token
    .replace(/^stage_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatIstTimestamp(isoOrStr?: string | null): string {
  if (!isoOrStr) return "—";
  if (isoOrStr.includes("IST")) return isoOrStr;
  const dt = new Date(isoOrStr);
  if (Number.isNaN(dt.getTime())) return isoOrStr;
  return dt.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
