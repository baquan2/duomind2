"use client"

import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import type { OnboardingData } from "@/types"
import { cn } from "@/lib/utils"

import { AGE_RANGES, STATUS_OPTIONS } from "../options"

interface Step1BasicProps {
  data: Partial<OnboardingData>
  onChange: (updates: Partial<OnboardingData>) => void
}

export function Step1Basic({ data, onChange }: Step1BasicProps) {
  return (
    <div className="space-y-7">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Step 1
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">Cho DUO MIND biet ban la ai</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            AI se duoc canh chinh theo boi canh hoc tap va giai doan hien tai cua ban.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Do tuoi cua ban?</Label>
        <RadioGroup
          value={data.age_range}
          onValueChange={(value) => onChange({ age_range: value as OnboardingData["age_range"] })}
          className="grid gap-3 sm:grid-cols-2"
        >
          {AGE_RANGES.map(({ value, label }) => (
            <label
              key={value}
              htmlFor={value}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-2xl border bg-card px-4 py-4 transition-colors",
                data.age_range === value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/40"
              )}
            >
              <RadioGroupItem value={value} id={value} />
              <span className="text-sm font-medium">{label}</span>
            </label>
          ))}
        </RadioGroup>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Hien tai ban dang o trang thai nao?</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {STATUS_OPTIONS.map(({ value, label, desc }) => (
            <button
              key={value}
              type="button"
              onClick={() =>
                onChange({ status: value as OnboardingData["status"] })
              }
              className={cn(
                "rounded-2xl border bg-card px-4 py-4 text-left transition-all",
                data.status === value
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "border-border hover:border-primary/40"
              )}
            >
              <div className="font-medium">{label}</div>
              <div className="mt-1 text-sm text-muted-foreground">{desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
