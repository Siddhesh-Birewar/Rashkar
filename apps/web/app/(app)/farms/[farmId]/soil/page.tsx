"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  FileUp,
  FlaskConical,
  Layers3,
  Leaf,
  Loader2,
  RefreshCw,
  Scale,
  Sparkles,
  TestTubes,
  Info,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soilApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { SoilProfile } from "@/lib/api/types";
import {
  getSoilParamValue,
  getSoilParamUnit,
  getSoilParamSource,
  interpretSoilPh,
  interpretSoc,
  interpretEc,
} from "@/lib/soil-utils";

export default function SoilPage() {
  const params = useParams();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const currentFarm = farms.find((f) => f.id === actualFarmId);

  const [profile, setProfile] = useState<SoilProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedDepth, setSelectedDepth] = useState("0-5cm");
  const [error, setError] = useState<string | null>(null);

  const loadProfile = async (farmId: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await soilApi.getProfile(farmId);
      setProfile(data);
    } catch (err: any) {
      if (err.status === 404) {
        setProfile(null);
      } else {
        setError(err?.message || "Failed to load soil profile");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (actualFarmId) {
      loadProfile(actualFarmId);
    } else {
      setLoading(false);
    }
  }, [actualFarmId]);

  const handleRunSpatialAnalysis = async () => {
    if (!actualFarmId) return;
    try {
      setAnalyzing(true);
      setError(null);
      const updated = await soilApi.analyse(actualFarmId, selectedDepth);
      setProfile(updated);
    } catch (err: any) {
      setError(err?.message || "Spatial soil analysis failed. Please verify parcel boundary.");
    } finally {
      setAnalyzing(false);
    }
  };

  if (!actualFarmId) {
    return (
      <div className="py-16 text-center">
        <Leaf size={40} className="mx-auto text-muted" />
        <h2 className="mt-4 text-xl font-bold">Select a Farm</h2>
        <p className="mt-1 text-sm text-muted">Choose a farm from the header to view its soil profile.</p>
        <Button asChild className="mt-4">
          <Link href="/farms">Go to Farms</Link>
        </Button>
      </div>
    );
  }

  // Safe numerical extractions
  const phVal = profile ? getSoilParamValue(profile.ph) : null;
  const rawSocVal = profile
    ? getSoilParamValue(profile.organic_carbon ?? profile.organic_carbon_percentage)
    : null;
  const socUnit = profile
    ? getSoilParamUnit(profile.organic_carbon ?? profile.organic_carbon_percentage, "%")
    : "%";
  // Convert g/kg to % if applicable
  const socPct =
    rawSocVal !== null
      ? socUnit.toLowerCase().includes("g/kg")
        ? rawSocVal / 10.0
        : rawSocVal
      : null;

  const ecVal = profile
    ? getSoilParamValue(
        profile.electrical_conductivity ?? profile.additional_parameters?.["electrical_conductivity"]
      )
    : null;
  const texture =
    profile?.soil_texture_class || profile?.texture_class || "Clay Vertisol";

  const sandVal = profile
    ? getSoilParamValue(profile.sand_percent ?? profile.sand_percentage)
    : null;
  const siltVal = profile
    ? getSoilParamValue(profile.silt_percent ?? profile.silt_percentage)
    : null;
  const clayVal = profile
    ? getSoilParamValue(profile.clay_percent ?? profile.clay_percentage)
    : null;
  const cecVal = profile
    ? getSoilParamValue(profile.cation_exchange_capacity)
    : null;

  const availN = profile
    ? getSoilParamValue(profile.available_nitrogen ?? profile.nitrogen_available_kg_ha)
    : null;
  const availP = profile
    ? getSoilParamValue(profile.available_phosphorus ?? profile.phosphorus_available_kg_ha)
    : null;
  const availK = profile
    ? getSoilParamValue(profile.available_potassium ?? profile.potassium_available_kg_ha)
    : null;

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Soil intelligence"
        title={`Soil Profile · ${currentFarm?.name || "Farm Parcel"}`}
        description="ISRIC SoilGrids 2.0 spatial extraction and certified laboratory soil test reports."
        backHref={`/farms/${actualFarmId}`}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleRunSpatialAnalysis}
              disabled={analyzing || loading}
            >
              {analyzing ? (
                <>
                  <Loader2 size={15} className="animate-spin" /> Analysing SoilGrids...
                </>
              ) : (
                <>
                  <Sparkles size={15} className="text-leaf" /> Extract SoilGrids
                </>
              )}
            </Button>
            <Button asChild>
              <Link href={`/farms/${actualFarmId}/soil/reports/new`}>
                <FileUp size={16} /> Upload Lab Report
              </Link>
            </Button>
          </div>
        }
      />

      {error && (
        <div className="flex items-start gap-3 rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
          <AlertTriangle size={17} className="shrink-0 text-red-600" />
          <p>{error}</p>
        </div>
      )}

      {loading ? (
        <div className="py-24 text-center">
          <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
          <p className="mt-4 text-sm text-muted">Loading unified soil profile...</p>
        </div>
      ) : profile ? (
        <div className="space-y-6">
          {/* Transparency Disclaimer Notice */}
          <div className="rounded-2xl border border-[#cde0ce] bg-[#f1f8f1] p-4 text-xs text-forest flex items-start gap-3">
            <Info size={18} className="shrink-0 text-leaf mt-0.5" />
            <div>
              <p className="font-bold">
                {profile.source_dataset || "ISRIC SoilGrids 2.0"} Spatial Soil Model ({profile.depth_interval || "0-5cm"})
              </p>
              <p className="mt-0.5 leading-relaxed text-[#2d5032]">
                {profile.disclaimer ||
                  "These results are spatial estimates derived from geospatial soil datasets. They are not direct laboratory test results. Physical laboratory tests take precedence."}
              </p>
            </div>
          </div>

          {/* ── Key Parameters Grid ── */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="bg-white">
              <CardContent className="p-5">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted">
                  Soil pH (1:2.5)
                </span>
                <p className="mt-2 text-3xl font-extrabold text-ink">
                  {phVal !== null ? phVal.toFixed(2) : "—"}
                </p>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-muted">{interpretSoilPh(phVal)}</span>
                  <Badge variant="outline" className="text-[10px]">
                    {getSoilParamSource(profile.ph)}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white">
              <CardContent className="p-5">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted">
                  Organic Carbon (SOC %)
                </span>
                <p className="mt-2 text-3xl font-extrabold text-ink">
                  {socPct !== null ? `${socPct.toFixed(2)}%` : "—"}
                </p>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-muted">{interpretSoc(socPct)}</span>
                  <Badge variant="outline" className="text-[10px]">
                    {getSoilParamSource(profile.organic_carbon)}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white">
              <CardContent className="p-5">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted">
                  Electrical Conductivity (EC)
                </span>
                <p className="mt-2 text-3xl font-extrabold text-ink">
                  {ecVal !== null ? `${ecVal.toFixed(2)} dS/m` : "—"}
                </p>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-muted">{interpretEc(ecVal)}</span>
                  <Badge variant="outline" className="text-[10px]">
                    {ecVal !== null ? "Measured" : "Pending Lab"}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white">
              <CardContent className="p-5">
                <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted">
                  Soil Texture Class
                </span>
                <p className="mt-2 text-2xl font-extrabold text-ink truncate">
                  {texture}
                </p>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className="text-muted">
                    Clay: {clayVal !== null ? `${clayVal.toFixed(0)}%` : "—"} · Sand:{" "}
                    {sandVal !== null ? `${sandVal.toFixed(0)}%` : "—"} · Silt:{" "}
                    {siltVal !== null ? `${siltVal.toFixed(0)}%` : "—"}
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {cecVal !== null ? `CEC: ${cecVal.toFixed(1)}` : "USDA"}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ── Strict Evidence Gating: Available Macronutrients (NPK) ── */}
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-line">
                <div>
                  <h3 className="text-base font-extrabold text-ink">
                    Available Macronutrients (NPK)
                  </h3>
                  <p className="text-xs text-muted mt-0.5">
                    Deterministic Principle: Available mineral NPK is never fabricated or modeled from global satellite rasters.
                  </p>
                </div>
                <Badge className="bg-[#edf5ed] text-forest border-0">Evidence Gated</Badge>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-line bg-canvas p-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted block">
                    Available Nitrogen (N)
                  </span>
                  <p className="mt-2 text-xl font-extrabold text-ink">
                    {availN !== null ? `${availN} kg/ha` : "Not verified"}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {availN !== null
                      ? "Lab alkaline permanganate extraction"
                      : "Requires certified soil lab test report"}
                  </p>
                </div>

                <div className="rounded-2xl border border-line bg-canvas p-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted block">
                    Available Phosphorus (P)
                  </span>
                  <p className="mt-2 text-xl font-extrabold text-ink">
                    {availP !== null ? `${availP} kg/ha` : "Not verified"}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {availP !== null
                      ? "Olsen extraction method"
                      : "Requires certified soil lab test report"}
                  </p>
                </div>

                <div className="rounded-2xl border border-line bg-canvas p-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted block">
                    Available Potassium (K)
                  </span>
                  <p className="mt-2 text-xl font-extrabold text-ink">
                    {availK !== null ? `${availK} kg/ha` : "Not verified"}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {availK !== null
                      ? "Neutral ammonium acetate extraction"
                      : "Requires certified soil lab test report"}
                  </p>
                </div>
              </div>

              <div className="mt-5 rounded-xl bg-[#fffbf5] border border-[#f5e6d0] p-4 flex items-start gap-3">
                <FlaskConical size={18} className="text-soil shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-extrabold text-soil">
                    Have a Physical Soil Health Card or Lab Report?
                  </p>
                  <p className="mt-0.5 text-muted">
                    Upload your Government Soil Health Card (SHC) or private lab report. CropNet extracts NPK, EC, and micronutrients with automated OCR and asks you to confirm.
                  </p>
                  <Link
                    href={`/farms/${actualFarmId}/soil/reports/new`}
                    className="inline-block mt-2 font-bold text-forest hover:underline"
                  >
                    Upload Laboratory Report →
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ── Secondary Links ── */}
          <div className="grid gap-4 sm:grid-cols-2">
            <Link
              href={`/farms/${actualFarmId}/soil/reports`}
              className="flex items-center justify-between p-5 rounded-2xl border border-line bg-white hover:border-leaf transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-[#eef7ee] text-leaf">
                  <FlaskConical size={18} />
                </span>
                <div>
                  <p className="text-sm font-extrabold text-ink">Laboratory Reports</p>
                  <p className="text-xs text-muted">Manage uploaded reports and OCR extractions</p>
                </div>
              </div>
              <span className="text-xs font-bold text-forest">View Reports →</span>
            </Link>

            <Link
              href={`/farms/${actualFarmId}/health`}
              className="flex items-center justify-between p-5 rounded-2xl border border-line bg-white hover:border-leaf transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-[#edf5ed] text-forest">
                  <Scale size={18} />
                </span>
                <div>
                  <p className="text-sm font-extrabold text-ink">Farm Health Gating</p>
                  <p className="text-xs text-muted">Review how soil evidence gates crop suitability</p>
                </div>
              </div>
              <span className="text-xs font-bold text-forest">Health View →</span>
            </Link>
          </div>
        </div>
      ) : (
        <Card>
          <CardContent className="p-10 text-center">
            <Layers3 size={40} className="mx-auto text-leaf/60" />
            <h3 className="mt-4 text-xl font-extrabold text-ink">No Soil Profile Generated</h3>
            <p className="mt-2 max-w-md mx-auto text-xs leading-5 text-muted">
              We haven&apos;t run spatial soil extraction for this boundary yet. Extract 250m SoilGrids data or upload a lab test report to unlock soil intelligence.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <Button onClick={handleRunSpatialAnalysis} disabled={analyzing} className="bg-forest">
                {analyzing ? (
                  <>
                    <Loader2 size={16} className="animate-spin" /> Extracting SoilGrids...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Run SoilGrids Analysis
                  </>
                )}
              </Button>
              <Button variant="outline" asChild>
                <Link href={`/farms/${actualFarmId}/soil/reports/new`}>Upload Lab Report</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
