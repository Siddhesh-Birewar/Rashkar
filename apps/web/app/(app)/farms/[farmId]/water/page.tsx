"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  AlertCircle,
  CheckCircle2,
  Droplets,
  FileUp,
  FlaskConical,
  Loader2,
  Plus,
  RefreshCw,
  Waves,
} from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { waterApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { WaterSource, WaterEvaluation } from "@/lib/api/types";

export default function WaterPage() {
  const params = useParams();
  const { selectedFarmId, farms } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const currentFarm = farms.find((f) => f.id === actualFarmId);

  const [sources, setSources] = useState<WaterSource[]>([]);
  const [evaluation, setEvaluation] = useState<WaterEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [addingSource, setAddingSource] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);

  const [newSourceName, setNewSourceName] = useState("");
  const [newSourceType, setNewSourceType] = useState<"well" | "borewell" | "canal" | "river" | "farm_pond" | "tanker" | "other">("well");
  const [newSourcePerennial, setNewSourcePerennial] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadWaterData = async (farmId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [srcRes, evalRes] = await Promise.allSettled([
        waterApi.listSources(farmId),
        waterApi.getEvaluation(farmId),
      ]);

      if (srcRes.status === "fulfilled") setSources(srcRes.value);
      if (evalRes.status === "fulfilled") setEvaluation(evalRes.value);
    } catch (err: any) {
      setError(err?.message || "Failed to load water data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (actualFarmId) {
      loadWaterData(actualFarmId);
    } else {
      setLoading(false);
    }
  }, [actualFarmId]);

  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actualFarmId || !newSourceName.trim()) return;

    try {
      setAddingSource(true);
      await waterApi.createSource(actualFarmId, {
        name: newSourceName.trim(),
        source_type: newSourceType,
        is_perennial: newSourcePerennial,
      });
      setNewSourceName("");
      setShowAddForm(false);
      await loadWaterData(actualFarmId);
    } catch (err: any) {
      setError(err?.message || "Failed to add water source");
    } finally {
      setAddingSource(false);
    }
  };

  if (!actualFarmId) {
    return (
      <div className="py-16 text-center">
        <Droplets size={40} className="mx-auto text-muted" />
        <h2 className="mt-4 text-xl font-bold">Select a Farm</h2>
        <p className="mt-1 text-sm text-muted">Choose a farm to inspect its water sources and quality evaluations.</p>
        <Button asChild className="mt-4">
          <Link href="/farms">Go to Farms</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-7">
      <PageHeader
        eyebrow="Hydrology & irrigation"
        title={`Water Intelligence · ${currentFarm?.name || "Farm"}`}
        description="Registered irrigation sources and BIS/CSSRI water quality compliance evaluations."
        backHref={`/farms/${actualFarmId}`}
        actions={
          <Button onClick={() => setShowAddForm((v) => !v)} className="bg-forest">
            <Plus size={16} /> {showAddForm ? "Close Form" : "Add Water Source"}
          </Button>
        }
      />

      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
          {error}
        </div>
      )}

      {/* ── Add Water Source Form ── */}
      {showAddForm && (
        <Card className="border-leaf/60 bg-[#f9fbf9]">
          <CardContent className="p-6">
            <h3 className="text-sm font-extrabold text-ink mb-4">Register New Water Source</h3>
            <form onSubmit={handleCreateSource} className="grid gap-4 sm:grid-cols-3">
              <label className="block">
                <span className="text-xs font-bold text-ink block mb-1">Source Name</span>
                <Input
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  placeholder="e.g. Well No. 2, Canal Gate 14"
                  required
                />
              </label>

              <label className="block">
                <span className="text-xs font-bold text-ink block mb-1">Source Type</span>
                <Select
                  value={newSourceType}
                  onValueChange={(val: any) => setNewSourceType(val)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="well">Open Dug Well</SelectItem>
                    <SelectItem value="borewell">Deep Borewell</SelectItem>
                    <SelectItem value="canal">Canal Irrigation</SelectItem>
                    <SelectItem value="farm_pond">Farm Pond (Shet-tale)</SelectItem>
                    <SelectItem value="river">River Lift</SelectItem>
                    <SelectItem value="tanker">Water Tanker</SelectItem>
                  </SelectContent>
                </Select>
              </label>

              <label className="block">
                <span className="text-xs font-bold text-ink block mb-1">Availability</span>
                <Select
                  value={newSourcePerennial ? "perennial" : "seasonal"}
                  onValueChange={(v) => setNewSourcePerennial(v === "perennial")}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="perennial">Perennial (Year-round)</SelectItem>
                    <SelectItem value="seasonal">Seasonal (Dry in Summer)</SelectItem>
                  </SelectContent>
                </Select>
              </label>

              <div className="sm:col-span-3 flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={addingSource} className="bg-forest">
                  {addingSource ? (
                    <>
                      <Loader2 size={15} className="animate-spin" /> Saving...
                    </>
                  ) : (
                    "Save Water Source"
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="py-24 text-center">
          <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
          <p className="mt-4 text-sm text-muted">Retrieving water assets and evaluations...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* ── Registered Water Sources ── */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between pb-4 border-b border-line">
                <div>
                  <h3 className="text-base font-extrabold text-ink">Registered Irrigation Sources</h3>
                  <p className="text-xs text-muted">Infrastructure recorded for this farm boundary</p>
                </div>
                <Badge variant="outline" className="text-[10px]">
                  {sources.length} Sources
                </Badge>
              </div>

              {sources.length === 0 ? (
                <div className="py-10 text-center text-xs text-muted">
                  <Waves size={30} className="mx-auto text-muted/50 mb-2" />
                  No water sources registered yet. Click &ldquo;Add Water Source&rdquo; above.
                </div>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {sources.map((src) => (
                    <div
                      key={src.id}
                      className="rounded-2xl border border-line bg-canvas p-4 flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-extrabold text-ink">{src.name}</span>
                          <Badge variant="outline" className="text-[10px] capitalize">
                            {src.source_type}
                          </Badge>
                        </div>
                        <p className="mt-2 text-xs text-muted">
                          Capacity: {src.is_perennial ? "Perennial (All Seasons)" : "Seasonal"}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── Quality Evaluation ── */}
          {evaluation ? (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between pb-4 border-b border-line">
                  <div>
                    <h3 className="text-base font-extrabold text-ink">BIS & CSSRI Quality Assessment</h3>
                    <p className="text-xs text-muted">Scientific evaluation based on measured EC, SAR, and RSC</p>
                  </div>
                  <Badge
                    className={
                      evaluation.bis_standard_compliance
                        ? "bg-[#edf5ed] text-forest border-0 font-bold"
                        : "bg-red-50 text-red-700 border-0 font-bold"
                    }
                  >
                    {evaluation.bis_standard_compliance ? "BIS Compliant" : "Hazard Detected"}
                  </Badge>
                </div>

                <div className="mt-4 space-y-3 text-xs">
                  <div className="p-3 rounded-xl bg-canvas border border-line">
                    <span className="font-extrabold text-ink text-sm block">
                      {evaluation.suitability}
                    </span>
                    <span className="text-muted block mt-0.5">
                      CSSRI Category: {evaluation.cssri_category || "Standard irrigation water"}
                    </span>
                  </div>

                  {evaluation.actionable_recommendations && evaluation.actionable_recommendations.length > 0 && (
                    <div className="space-y-1 text-muted">
                      <strong className="text-ink block">Agronomic Recommendations:</strong>
                      {evaluation.actionable_recommendations.map((rec, idx) => (
                        <p key={idx}>• {rec}</p>
                      ))}
                    </div>
                  )}

                  <p className="text-[11px] text-muted italic pt-2">
                    {evaluation.disclaimer}
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-8 text-center text-xs text-muted">
                <FlaskConical size={28} className="mx-auto text-muted/60 mb-2" />
                <p className="font-bold text-ink text-sm">No Laboratory Water Test on Record</p>
                <p className="mt-1 max-w-md mx-auto">
                  Water quality parameters (EC, SAR, RSC) require an official laboratory test report before chemical safety can be confirmed.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
