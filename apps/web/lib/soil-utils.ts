/**
 * CropNet AI — Soil Utilities & Data Normalizers
 * Safely extracts numerical values, units, sources, and display interpretations
 * from UnifiedSoilProfile observations (ISRIC SoilGrids 2.0 / Certified Lab Reports).
 */

import type { SoilProfile, SoilParameterObservation } from "./api/types";

/**
 * Safely extracts a numeric value from either a SoilParameterObservation object or a primitive number.
 */
export function getSoilParamValue(param: any): number | null {
  if (param === null || param === undefined) return null;
  if (typeof param === "number") return isNaN(param) ? null : param;
  if (typeof param === "object" && "value" in param) {
    if (param.value === null || param.value === undefined) return null;
    const num = Number(param.value);
    return isNaN(num) ? null : num;
  }
  return null;
}

/**
 * Safely extracts measurement unit.
 */
export function getSoilParamUnit(param: any, defaultUnit = ""): string {
  if (param && typeof param === "object" && param.unit) {
    return param.unit;
  }
  return defaultUnit;
}

/**
 * Safely extracts source provider (e.g. ISRIC SoilGrids 2.0 or Certified Laboratory).
 */
export function getSoilParamSource(param: any, defaultSource = "ISRIC"): string {
  if (param && typeof param === "object" && param.source) {
    return param.source;
  }
  return defaultSource;
}

/**
 * Safely extracts verification status string.
 */
export function getSoilParamStatus(param: any, defaultStatus = "map_derived_estimate"): string {
  if (param && typeof param === "object" && param.verification_status) {
    return param.verification_status;
  }
  return defaultStatus;
}

/**
 * Safely extracts scientific explanatory note.
 */
export function getSoilParamNote(param: any, defaultNote = ""): string {
  if (param && typeof param === "object" && param.scientific_note) {
    return param.scientific_note;
  }
  return defaultNote;
}

/**
 * Categorizes soil pH based on MPKV agronomic ranges.
 */
export function interpretSoilPh(ph: number | null): string {
  if (ph === null) return "Unmeasured";
  if (ph < 5.5) return "Strongly Acidic";
  if (ph < 6.5) return "Moderately Acidic";
  if (ph <= 7.5) return "Neutral / Optimal";
  if (ph <= 8.2) return "Mildly Alkaline";
  return "Calcareous / Highly Alkaline";
}

/**
 * Categorizes Soil Organic Carbon (SOC %) for Deccan Vertisols.
 */
export function interpretSoc(soc: number | null, unit = "%"): string {
  if (soc === null) return "Unmeasured";
  // If unit is g/kg, convert to % (divide by 10)
  const socPct = unit.toLowerCase().includes("g/kg") ? soc / 10.0 : soc;
  if (socPct < 0.5) return "Low SOC (< 0.5%)";
  if (socPct <= 0.75) return "Medium SOC (0.5–0.75%)";
  return "High SOC (> 0.75%)";
}

/**
 * Categorizes Electrical Conductivity (salinity hazard).
 */
export function interpretEc(ec: number | null): string {
  if (ec === null) return "Lab test required";
  if (ec < 1.0) return "Normal / Non-saline (< 1.0 dS/m)";
  if (ec <= 2.0) return "Mild Salinity (1.0–2.0 dS/m)";
  return "Critical Salinity Risk (> 2.0 dS/m)";
}
