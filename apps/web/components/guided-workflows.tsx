"use client";

import { useRef, useState } from "react";
import {
  Camera,
  Check,
  FileImage,
  LocateFixed,
  Map,
  RotateCcw,
  Search,
  Upload,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function FarmSetupForm() {
  const [step, setStep] = useState(1);
  return (
    <Card>
      <CardContent className="p-0">
        <div className="border-b border-line p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm font-extrabold">Farm setup</p>
            <Badge>Step {step} of 3</Badge>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#e7eee8]">
            <div
              className="h-full rounded-full bg-leaf transition-all"
              style={{ width: `${step * 33.333}%` }}
            />
          </div>
        </div>
        <div className="p-5 sm:p-6">
          {step === 1 && (
            <div className="space-y-5">
              <label className="block">
                <span className="mb-2 block text-sm font-extrabold">Farm name</span>
                <Input placeholder="For example, North field" />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-extrabold">Village or area</span>
                <Input placeholder="Enter village, taluka or district" />
              </label>
            </div>
          )}
          {step === 2 && (
            <div>
              <div className="grid min-h-64 place-items-center rounded-2xl border border-dashed border-[#a8c2aa] bg-[linear-gradient(45deg,#f1f7f1_25%,transparent_25%),linear-gradient(-45deg,#f1f7f1_25%,transparent_25%)] bg-[size:22px_22px]">
                <div className="max-w-xs text-center">
                  <span className="mx-auto grid size-12 place-items-center rounded-2xl bg-white text-leaf shadow-sm">
                    <Map size={22} />
                  </span>
                  <p className="mt-4 text-sm font-extrabold">Boundary map will load here</p>
                  <p className="mt-2 text-xs leading-5 text-muted">
                    Location access is required before drawing a verified boundary.
                  </p>
                  <Button variant="secondary" className="mt-4">
                    <LocateFixed size={17} /> Use my location
                  </Button>
                </div>
              </div>
            </div>
          )}
          {step === 3 && (
            <div className="rounded-2xl border border-line bg-canvas p-5">
              <div className="flex items-center gap-3">
                <span className="grid size-10 place-items-center rounded-xl bg-[#e8f5e9] text-leaf">
                  <Check size={19} />
                </span>
                <div>
                  <p className="text-sm font-extrabold">Ready to review</p>
                  <p className="text-xs text-muted">
                    No information is saved until the farm service is connected.
                  </p>
                </div>
              </div>
            </div>
          )}
          <div className="mt-6 flex gap-3">
            {step > 1 && (
              <Button variant="secondary" onClick={() => setStep((value) => value - 1)}>
                Back
              </Button>
            )}
            <Button onClick={() => setStep((value) => Math.min(3, value + 1))}>
              {step === 3 ? "Save when connected" : "Continue"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function UploadWorkflow({ kind = "crop image" }: { kind?: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string>();
  return (
    <Card className="overflow-hidden border-0 bg-[#153c2b] text-white">
      <CardContent className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_.75fr]">
        <div>
          <Badge className="bg-white/12 text-white">Guided upload</Badge>
          <h2 className="mt-4 text-2xl font-extrabold tracking-[-0.04em]">
            {fileName ? "Image ready for review" : `Add a clear ${kind}`}
          </h2>
          <p className="mt-3 max-w-lg text-sm leading-6 text-white/70">
            {fileName
              ? `${fileName} is selected. It has not been uploaded or analysed.`
              : "Use a well-lit, close image. CropNet will not show a result unless the backend can process it."}
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event) => setFileName(event.target.files?.[0]?.name)}
          />
          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              className="bg-white text-forest hover:bg-white/90"
              onClick={() => inputRef.current?.click()}
            >
              <Camera size={18} /> Camera or gallery
            </Button>
            {fileName && (
              <Button
                variant="ghost"
                className="text-white hover:bg-white/10"
                onClick={() => setFileName(undefined)}
              >
                <RotateCcw size={17} /> Choose again
              </Button>
            )}
          </div>
        </div>
        <div className="grid min-h-52 place-items-center rounded-2xl border border-white/15 bg-white/6">
          <div className="text-center">
            {fileName ? (
              <FileImage className="mx-auto text-[#a5d6a7]" size={36} />
            ) : (
              <Upload className="mx-auto text-white/45" size={34} />
            )}
            <p className="mt-3 text-xs font-bold text-white/65">
              {fileName ?? "No image selected"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function SearchBox({ placeholder }: { placeholder: string }) {
  const [query, setQuery] = useState("");
  return (
    <div className="relative">
      <Search className="absolute top-1/2 left-4 -translate-y-1/2 text-muted" size={18} />
      <Input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="pl-11"
        placeholder={placeholder}
        aria-label={placeholder}
      />
      {query && (
        <p className="mt-2 text-xs text-muted">No verified records are connected for “{query}”.</p>
      )}
    </div>
  );
}
