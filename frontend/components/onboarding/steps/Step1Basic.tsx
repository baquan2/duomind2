"use client"

import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Slider } from "@/components/ui/slider"
import { cn } from "@/lib/utils"
import type { OnboardingData } from "@/types"

import { AGE_RANGES, STATUS_OPTIONS } from "../options"

interface Step1BasicProps {
  data: Partial<OnboardingData>
  onChange: (updates: Partial<OnboardingData>) => void
}

const DAILY_STUDY_PRESETS = [15, 30, 45, 60, 90]

export function Step1Basic({ data, onChange }: Step1BasicProps) {
  const dailyStudyMinutes = data.daily_study_minutes ?? 30

  return (
    <div className="space-y-7">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Bước 1
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">Cho DUO MIND biết bạn là ai</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            AI sẽ điều chỉnh mentor, tốc độ học và độ sâu nội dung theo đúng bối cảnh hiện tại
            của bạn.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Độ tuổi của bạn</Label>
        <RadioGroup
          value={data.age_range ?? ""}
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
        <Label className="text-base font-medium">Hiện tại bạn đang ở trạng thái nào</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {STATUS_OPTIONS.map(({ value, label, desc }) => (
            <button
              key={value}
              type="button"
              onClick={() => onChange({ status: value as OnboardingData["status"] })}
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

      <div className="space-y-4 rounded-3xl border border-border bg-card/80 p-5">
        <div className="space-y-2">
          <Label className="text-base font-medium">
            Thời gian bạn có thể học mỗi ngày:{" "}
            <span className="text-primary">{dailyStudyMinutes} phút</span>
          </Label>
          <p className="text-sm text-muted-foreground">
            DUO MIND sẽ dùng thông tin này để điều chỉnh độ sâu kiến thức, tốc độ giải thích và
            lượng nội dung phù hợp với bạn.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          {DAILY_STUDY_PRESETS.map((minutes) => (
            <button
              key={minutes}
              type="button"
              onClick={() => onChange({ daily_study_minutes: minutes })}
              className={cn(
                "rounded-full border px-3 py-1.5 text-sm transition-colors",
                dailyStudyMinutes === minutes
                  ? "border-primary bg-primary/10 font-medium text-primary"
                  : "border-border bg-background hover:border-primary/40"
              )}
            >
              {minutes} phút
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-border/70 bg-background/85 px-4 py-4">
          <Slider
            value={[dailyStudyMinutes]}
            onValueChange={([value]) => onChange({ daily_study_minutes: value })}
            min={10}
            max={180}
            step={5}
          />
          <div className="mt-3 flex justify-between text-xs text-muted-foreground">
            <span>10 phút</span>
            <span>180 phút</span>
          </div>
        </div>
      </div>
    </div>
  )
}
