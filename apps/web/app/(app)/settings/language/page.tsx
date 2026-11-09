"use client";

import { useState } from "react";
import { Check, Languages } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function LanguagePage() {
  const [language, setLanguage] = useState("en");
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        eyebrow="Preferences"
        title="Choose language"
        description="Select the interface language that is easiest for you to read."
        backHref="/profile"
      />
      <Card>
        <CardContent className="space-y-3">
          {[
            { value: "en", label: "English", helper: "English interface" },
            { value: "mr", label: "मराठी", helper: "मराठी इंटरफेस" },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setLanguage(option.value)}
              className={cn(
                "flex min-h-20 w-full items-center gap-4 rounded-2xl border p-4 text-left",
                language === option.value ? "border-leaf bg-[#f1f8f1]" : "border-line",
              )}
            >
              <span className="grid size-11 place-items-center rounded-xl bg-white text-leaf">
                <Languages size={20} />
              </span>
              <span>
                <strong className="block">{option.label}</strong>
                <span className="text-xs text-muted">{option.helper}</span>
              </span>
              {language === option.value && <Check className="ml-auto text-leaf" size={20} />}
            </button>
          ))}
          <Button className="mt-3 w-full">Use selected language</Button>
        </CardContent>
      </Card>
    </div>
  );
}
