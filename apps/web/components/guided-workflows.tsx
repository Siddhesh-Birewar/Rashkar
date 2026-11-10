"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  Camera,
  Check,
  FileImage,
  Loader2,
  LocateFixed,
  Map,
  MapPin,
  RotateCcw,
  Search,
  Upload,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { farmsApi } from "@/lib/api/client";
import { useFarm } from "@/lib/farm-context";
import type { GeoJSONPolygon } from "@/lib/api/types";

const PILOT_COORDINATE_PRESETS: Record<string, [number, number][]> = {
  Baramati: [
    [74.5305, 18.1824],
    [74.5335, 18.1824],
    [74.5319, 18.1800],
    [74.5302, 18.1800],
    [74.5305, 18.1824],
  ],
  Indapur: [
    [75.0200, 18.1150],
    [75.0235, 18.1150],
    [75.0235, 18.1120],
    [75.0200, 18.1120],
    [75.0200, 18.1150],
  ],
  Maval: [
    [73.5350, 18.7520],
    [73.5380, 18.7520],
    [73.5380, 18.7490],
    [73.5350, 18.7490],
    [73.5350, 18.7520],
  ],
  Mulshi: [
    [73.5120, 18.5050],
    [73.5160, 18.5050],
    [73.5160, 18.5020],
    [73.5120, 18.5020],
    [73.5120, 18.5050],
  ],
};

export function FarmSetupForm() {
  const router = useRouter();
  const { refreshFarms, setSelectedFarmId } = useFarm();

  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [taluka, setTaluka] = useState("Baramati");
  const [village, setVillage] = useState("");
  const [irrigationType, setIrrigationType] = useState("irrigated");
  const [waterSource, setWaterSource] = useState("canal");

  const [coordinates, setCoordinates] = useState<[number, number][]>(
    PILOT_COORDINATE_PRESETS["Baramati"]
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTalukaChange = (newTaluka: string) => {
    setTaluka(newTaluka);
    if (PILOT_COORDINATE_PRESETS[newTaluka]) {
      setCoordinates(PILOT_COORDINATE_PRESETS[newTaluka]);
    }
  };

  const handleSaveFarm = async () => {
    if (!name.trim()) {
      setError("Please provide a name for this farm parcel.");
      setStep(1);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const geometry: GeoJSONPolygon = {
        type: "Polygon",
        coordinates: [coordinates],
      };

      const newFarm = await farmsApi.create({
        name: name.trim(),
        taluka,
        village: village.trim() || undefined,
        district: "Pune",
        state: "Maharashtra",
        irrigation_type: irrigationType,
        water_source: waterSource,
        geometry,
      });

      await refreshFarms();
      setSelectedFarmId(newFarm.id);
      router.push(`/farms/${newFarm.id}`);
    } catch (err: any) {
      setError(err?.message || "Failed to create farm. Please verify polygon boundary.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-0">
        <div className="border-b border-line p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-extrabold text-ink">Farm registration wizard</p>
            <Badge>Step {step} of 3</Badge>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#e7eee8]">
            <div
              className="h-full rounded-full bg-leaf transition-all duration-300"
              style={{ width: `${step * 33.333}%` }}
            />
          </div>
        </div>

        {error && (
          <div className="m-5 sm:m-6 flex items-start gap-3 rounded-xl bg-red-50 p-4 text-xs text-red-800 border border-red-200">
            <AlertCircle size={17} className="shrink-0 text-red-600" />
            <div>
              <p className="font-bold">Error saving farm</p>
              <p className="mt-0.5">{error}</p>
            </div>
          </div>
        )}

        <div className="p-5 sm:p-6">
          {/* ── STEP 1: General Details ── */}
          {step === 1 && (
            <div className="space-y-5">
              <label className="block">
                <span className="mb-2 block text-sm font-extrabold text-ink">
                  Farm Name <span className="text-red-500">*</span>
                </span>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. North Orchard, Gat No 142"
                  required
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm font-extrabold text-ink">
                    Taluka (Pune District) <span className="text-red-500">*</span>
                  </span>
                  <Select value={taluka} onValueChange={handleTalukaChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Baramati">Baramati (Rain-shadow / Vertisols)</SelectItem>
                      <SelectItem value="Indapur">Indapur (Lower Nira canal basin)</SelectItem>
                      <SelectItem value="Maval">Maval (Western Ghats / Heavy rain)</SelectItem>
                      <SelectItem value="Mulshi">Mulshi (Heavy rainfall hilly zone)</SelectItem>
                    </SelectContent>
                  </Select>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-extrabold text-ink">
                    Village / Locality (Optional)
                  </span>
                  <Input
                    value={village}
                    onChange={(e) => setVillage(e.target.value)}
                    placeholder="e.g. Malegaon, Shirasne, Paud"
                  />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm font-extrabold text-ink">
                    Irrigation Type
                  </span>
                  <Select value={irrigationType} onValueChange={setIrrigationType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="irrigated">Perennial Irrigated (Drip / Furrow)</SelectItem>
                      <SelectItem value="mixed">Mixed (Protective / Seasonal)</SelectItem>
                      <SelectItem value="rainfed">Pure Rainfed (Dryland Kharif)</SelectItem>
                    </SelectContent>
                  </Select>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-extrabold text-ink">
                    Primary Water Source
                  </span>
                  <Select value={waterSource} onValueChange={setWaterSource}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="canal">Canal (Nira / Mutha)</SelectItem>
                      <SelectItem value="well">Open Dug Well</SelectItem>
                      <SelectItem value="borewell">Deep Borewell</SelectItem>
                      <SelectItem value="river">River Lift Irrigation</SelectItem>
                      <SelectItem value="farm_pond">Farm Pond (Shet-tale)</SelectItem>
                      <SelectItem value="rainfall">Direct Rainfall only</SelectItem>
                    </SelectContent>
                  </Select>
                </label>
              </div>
            </div>
          )}

          {/* ── STEP 2: Field Boundary ── */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-line bg-canvas p-4 text-xs">
                <div className="flex items-center gap-2 font-bold text-ink">
                  <MapPin size={16} className="text-leaf" />
                  Boundary coordinates for {taluka}
                </div>
                <p className="mt-1 text-muted">
                  GeoJSON EPSG:4326 polygon (min 4 coordinates, closed ring).
                </p>
                <div className="mt-3 font-mono text-[11px] bg-white p-3 rounded-xl border border-line overflow-x-auto">
                  {JSON.stringify(coordinates)}
                </div>
              </div>

              <div className="grid min-h-48 place-items-center rounded-2xl border border-dashed border-[#a8c2aa] bg-[linear-gradient(45deg,#f1f7f1_25%,transparent_25%),linear-gradient(-45deg,#f1f7f1_25%,transparent_25%)] bg-[size:22px_22px] p-6 text-center">
                <div className="max-w-md">
                  <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-white text-leaf shadow-sm">
                    <Map size={22} />
                  </span>
                  <p className="mt-3 text-sm font-extrabold text-ink">Verified Polygon Coordinates</p>
                  <p className="mt-1 text-xs leading-5 text-muted">
                    Boundary is preset for the {taluka} pilot agro-climatic region. The backend computes exact acreage, centroid latitude, and intersects ISRIC soil rasters upon registration.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="mt-4"
                    onClick={() => {
                      if (PILOT_COORDINATE_PRESETS[taluka]) {
                        setCoordinates(PILOT_COORDINATE_PRESETS[taluka]);
                      }
                    }}
                  >
                    <LocateFixed size={15} /> Reset to {taluka} Pilot Center
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* ── STEP 3: Review & Confirmation ── */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-line bg-canvas p-5">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 place-items-center rounded-xl bg-[#e8f5e9] text-leaf">
                    <Check size={19} />
                  </span>
                  <div>
                    <p className="text-sm font-extrabold text-ink">Ready to save {name || "your farm"}</p>
                    <p className="text-xs text-muted">
                      Your parcel will be verified against Maharashtra pilot boundaries and assigned to your account.
                    </p>
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3 text-xs pt-4 border-t border-line">
                  <div>
                    <span className="text-muted block text-[10px]">Taluka / District</span>
                    <span className="font-bold text-ink">{taluka}, Pune</span>
                  </div>
                  <div>
                    <span className="text-muted block text-[10px]">Village</span>
                    <span className="font-bold text-ink">{village || "Not specified"}</span>
                  </div>
                  <div>
                    <span className="text-muted block text-[10px]">Irrigation Type</span>
                    <span className="font-bold text-ink capitalize">{irrigationType}</span>
                  </div>
                  <div>
                    <span className="text-muted block text-[10px]">Water Source</span>
                    <span className="font-bold text-ink capitalize">{waterSource}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Action Buttons ── */}
          <div className="mt-6 flex gap-3">
            {step > 1 && (
              <Button
                variant="secondary"
                onClick={() => setStep((value) => value - 1)}
                disabled={isSubmitting}
              >
                Back
              </Button>
            )}
            {step < 3 ? (
              <Button
                onClick={() => {
                  if (step === 1 && !name.trim()) {
                    setError("Farm name is required.");
                    return;
                  }
                  setError(null);
                  setStep((v) => v + 1);
                }}
              >
                Continue to Boundary
              </Button>
            ) : (
              <Button
                onClick={handleSaveFarm}
                disabled={isSubmitting}
                className="bg-forest hover:bg-forest/90"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" /> Registering Farm...
                  </>
                ) : (
                  "Confirm & Save Farm"
                )}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function UploadWorkflow({
  kind = "crop image",
  accept = "image/*",
  onUpload,
}: {
  kind?: string;
  accept?: string;
  onUpload?: (file: File) => Promise<void>;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (selected) {
      setFile(selected);
      setUploadSuccess(false);
      setUploadError(null);
    }
  };

  const handleUploadClick = async () => {
    if (!file || !onUpload) return;
    try {
      setUploading(true);
      setUploadError(null);
      await onUpload(file);
      setUploadSuccess(true);
    } catch (err: any) {
      setUploadError(err?.message || "Failed to process uploaded file.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card className="overflow-hidden border-0 bg-[#153c2b] text-white">
      <CardContent className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_.75fr]">
        <div>
          <Badge className="bg-white/12 text-white">Guided upload</Badge>
          <h2 className="mt-4 text-2xl font-extrabold tracking-[-0.04em]">
            {file ? "File ready for analysis" : `Add a clear ${kind}`}
          </h2>
          <p className="mt-3 max-w-lg text-sm leading-6 text-white/70">
            {file
              ? `${file.name} (${(file.size / 1024).toFixed(0)} KB) selected.`
              : `Use a clear, high-resolution document or photograph. CropNet will process it against verified agronomic rules.`}
          </p>

          {uploadError && (
            <div className="mt-3 rounded-lg bg-red-900/50 p-3 text-xs text-red-200 border border-red-700/60">
              {uploadError}
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            accept={accept}
            className="hidden"
            onChange={handleFileChange}
          />

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              className="bg-white text-forest hover:bg-white/90"
              onClick={() => inputRef.current?.click()}
              disabled={uploading}
            >
              <Camera size={18} /> {file ? "Change file" : "Select file / Camera"}
            </Button>

            {file && onUpload && (
              <Button
                className="bg-leaf hover:bg-leaf/90 text-white"
                onClick={handleUploadClick}
                disabled={uploading}
              >
                {uploading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" /> Processing...
                  </>
                ) : (
                  <>
                    <Upload size={16} /> Run Analysis
                  </>
                )}
              </Button>
            )}

            {file && !uploading && (
              <Button
                variant="ghost"
                className="text-white hover:bg-white/10"
                onClick={() => setFile(null)}
              >
                <RotateCcw size={17} /> Clear
              </Button>
            )}
          </div>
        </div>

        <div className="grid min-h-52 place-items-center rounded-2xl border border-white/15 bg-white/6 p-4">
          <div className="text-center">
            {uploadSuccess ? (
              <Check className="mx-auto text-[#a5d6a7]" size={36} />
            ) : file ? (
              <FileImage className="mx-auto text-[#a5d6a7]" size={36} />
            ) : (
              <Upload className="mx-auto text-white/45" size={34} />
            )}
            <p className="mt-3 text-xs font-bold text-white/80">
              {uploadSuccess ? "Processing completed" : file ? file.name : "No file selected"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function SearchBox({
  placeholder,
  value,
  onChange,
}: {
  placeholder: string;
  value?: string;
  onChange?: (val: string) => void;
}) {
  const [internalQuery, setInternalQuery] = useState("");
  const query = value !== undefined ? value : internalQuery;

  const handleChange = (newVal: string) => {
    if (onChange) {
      onChange(newVal);
    } else {
      setInternalQuery(newVal);
    }
  };

  return (
    <div className="relative">
      <Search className="absolute top-1/2 left-4 -translate-y-1/2 text-muted" size={18} />
      <Input
        value={query}
        onChange={(event) => handleChange(event.target.value)}
        className="pl-11"
        placeholder={placeholder}
        aria-label={placeholder}
      />
    </div>
  );
}
