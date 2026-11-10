"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AlertCircle, Check, Loader2, Trash2 } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { farmsApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { Farm } from "@/lib/api/types";

export default function EditFarmPage() {
  const params = useParams();
  const router = useRouter();
  const { selectedFarmId, farms, refreshFarms, setSelectedFarmId } = useFarm();

  const paramFarmId = (params?.farmId as string) || "current";
  const actualFarmId =
    paramFarmId === "current"
      ? selectedFarmId || (farms.length > 0 ? farms[0].id : null)
      : paramFarmId;

  const [farm, setFarm] = useState<Farm | null>(null);
  const [name, setName] = useState("");
  const [village, setVillage] = useState("");
  const [taluka, setTaluka] = useState("Baramati");
  const [irrigationType, setIrrigationType] = useState("irrigated");
  const [waterSource, setWaterSource] = useState("canal");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!actualFarmId) {
      setLoading(false);
      return;
    }

    async function fetchFarm() {
      try {
        setLoading(true);
        const data = await farmsApi.get(actualFarmId!);
        setFarm(data);
        setName(data.name);
        setVillage(data.village || "");
        setTaluka(data.taluka || "Baramati");
        setIrrigationType(data.irrigation_type || "irrigated");
        setWaterSource(data.water_source || "canal");
      } catch (err: any) {
        setError(err?.message || "Failed to load farm details");
      } finally {
        setLoading(false);
      }
    }

    fetchFarm();
  }, [actualFarmId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actualFarmId) return;

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      await farmsApi.update(actualFarmId, {
        name: name.trim(),
        village: village.trim() || null,
        taluka,
        irrigation_type: irrigationType,
        water_source: waterSource,
      });

      await refreshFarms();
      setSuccess(true);
      setTimeout(() => {
        router.push(`/farms/${actualFarmId}`);
      }, 800);
    } catch (err: any) {
      setError(err?.message || "Failed to update farm details");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!actualFarmId) return;
    if (!confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`)) {
      return;
    }

    try {
      setDeleting(true);
      await farmsApi.delete(actualFarmId);
      await refreshFarms();
      setSelectedFarmId(null);
      router.push("/farms");
    } catch (err: any) {
      alert(`Delete failed: ${err?.message || "Unknown error"}`);
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center">
        <Loader2 size={32} className="mx-auto animate-spin text-leaf" />
        <p className="mt-4 text-sm text-muted">Loading farm details...</p>
      </div>
    );
  }

  if (!farm) {
    return (
      <div className="py-16 text-center">
        <p className="text-sm text-muted">Farm not found.</p>
        <Button asChild className="mt-4">
          <Link href="/farms">Back to Farms</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        title={`Edit ${farm.name}`}
        description="Update parcel identification, irrigation, and water source parameters."
        backHref={`/farms/${farm.id}`}
      />

      {error && (
        <div className="flex items-start gap-3 rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
          <AlertCircle size={17} className="shrink-0 text-red-600" />
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-3 rounded-xl bg-green-50 p-4 text-xs text-green-800 border border-green-200">
          <Check size={17} className="text-leaf" />
          <p>Farm updated successfully. Redirecting...</p>
        </div>
      )}

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleUpdate} className="space-y-5">
            <label className="block">
              <span className="mb-2 block text-sm font-extrabold text-ink">Farm Name</span>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Farm name"
              />
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-extrabold text-ink">Taluka</span>
                <Select value={taluka} onValueChange={setTaluka}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Baramati">Baramati</SelectItem>
                    <SelectItem value="Indapur">Indapur</SelectItem>
                    <SelectItem value="Maval">Maval</SelectItem>
                    <SelectItem value="Mulshi">Mulshi</SelectItem>
                  </SelectContent>
                </Select>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-extrabold text-ink">Village</span>
                <Input
                  value={village}
                  onChange={(e) => setVillage(e.target.value)}
                  placeholder="Village name"
                />
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-extrabold text-ink">Irrigation Type</span>
                <Select value={irrigationType} onValueChange={setIrrigationType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="irrigated">Irrigated (Perennial)</SelectItem>
                    <SelectItem value="mixed">Mixed (Seasonal)</SelectItem>
                    <SelectItem value="rainfed">Rainfed (Dryland)</SelectItem>
                  </SelectContent>
                </Select>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-extrabold text-ink">Water Source</span>
                <Select value={waterSource} onValueChange={setWaterSource}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="canal">Canal</SelectItem>
                    <SelectItem value="well">Open Well</SelectItem>
                    <SelectItem value="borewell">Borewell</SelectItem>
                    <SelectItem value="river">River</SelectItem>
                    <SelectItem value="farm_pond">Farm Pond</SelectItem>
                    <SelectItem value="rainfall">Rainfall</SelectItem>
                  </SelectContent>
                </Select>
              </label>
            </div>

            <div className="pt-4 border-t border-line flex items-center justify-between">
              <Button
                type="button"
                variant="ghost"
                onClick={handleDelete}
                disabled={deleting || saving}
                className="text-red-600 hover:bg-red-50"
              >
                <Trash2 size={16} /> Delete Farm
              </Button>

              <div className="flex gap-2">
                <Button variant="secondary" asChild>
                  <Link href={`/farms/${farm.id}`}>Cancel</Link>
                </Button>
                <Button type="submit" disabled={saving || deleting} className="bg-forest">
                  {saving ? (
                    <>
                      <Loader2 size={16} className="animate-spin" /> Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
