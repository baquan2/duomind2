"use client"

import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import type { OnboardingData } from "@/types"
import { cn } from "@/lib/utils"

import { GOAL_OPTIONS, TOPIC_OPTIONS } from "../options"

interface Step3GoalsProps {
  data: Partial<OnboardingData>
  onChange: (updates: Partial<OnboardingData>) => void
}

export function Step3Goals({ data, onChange }: Step3GoalsProps) {
  const toggleArray = (
    key: "learning_goals" | "topics_of_interest",
    value: string
  ) => {
    const currentValues = data[key] ?? []
    const nextValues = currentValues.includes(value)
      ? currentValues.filter((item) => item !== value)
      : [...currentValues, value]

    onChange({ [key]: nextValues })
  }

  return (
    <div className="space-y-7">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Bước 3
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">
            Mục tiêu và chủ đề bạn quan tâm
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Chọn nhiều mục nếu cần. DUO MIND sẽ dùng thông tin này để ưu tiên đề xuất.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Mục tiêu học tập</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {GOAL_OPTIONS.map(({ value, label }) => {
            const selected = data.learning_goals?.includes(value)
            return (
              <button
                key={value}
                type="button"
                onClick={() => toggleArray("learning_goals", value)}
                className={cn(
                  "rounded-2xl border bg-card px-4 py-3 text-left text-sm transition-all",
                  selected
                    ? "border-primary bg-primary/5 font-medium"
                    : "border-border hover:border-primary/40"
                )}
              >
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Chủ đề quan tâm</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {TOPIC_OPTIONS.map(({ value, label }) => {
            const selected = data.topics_of_interest?.includes(value)
            return (
              <button
                key={value}
                type="button"
                onClick={() => toggleArray("topics_of_interest", value)}
                className={cn(
                  "rounded-2xl border bg-card px-4 py-3 text-left text-sm transition-all",
                  selected
                    ? "border-primary bg-accent/55 font-medium text-accent-foreground"
                    : "border-border hover:border-primary/40"
                )}
              >
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-4 rounded-3xl border border-border bg-card/70 p-5">
        <Label className="text-base font-medium">
          Thời gian học mỗi ngày:{" "}
          <span className="text-primary">{data.daily_study_minutes ?? 30} phút</span>
        </Label>
        <Slider
          value={[data.daily_study_minutes ?? 30]}
          onValueChange={([value]) => onChange({ daily_study_minutes: value })}
          min={10}
          max={120}
          step={10}
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>10 phút</span>
          <span>120 phút</span>
        </div>
      </div>
    </div>
  )
}
