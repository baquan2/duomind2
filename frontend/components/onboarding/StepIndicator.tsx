import { Check } from "lucide-react"

import { cn } from "@/lib/utils"

interface StepIndicatorProps {
  current: number
  total: number
}

const labels = ["Cơ bản", "Bối cảnh", "Mục tiêu", "Xác nhận"]

export function StepIndicator({ current, total }: StepIndicatorProps) {
  return (
    <div className="mt-4 grid grid-cols-4 gap-2">
      {Array.from({ length: total }, (_, index) => {
        const step = index + 1
        const isDone = step < current
        const isActive = step === current

        return (
          <div key={step} className="flex flex-col items-center gap-2">
            <div
              className={cn(
                "flex size-9 items-center justify-center rounded-full border text-sm font-semibold transition-all",
                isDone && "border-primary bg-primary text-primary-foreground",
                isActive &&
                  "border-primary bg-primary text-primary-foreground shadow-[0_0_0_6px_hsl(var(--primary)/0.15)]",
                !isDone && !isActive && "border-border bg-card text-muted-foreground"
              )}
            >
              {isDone ? <Check className="size-4" /> : step}
            </div>
            <span
              className={cn(
                "text-center text-xs",
                isActive ? "font-medium text-foreground" : "text-muted-foreground"
              )}
            >
              {labels[index]}
            </span>
          </div>
        )
      })}
    </div>
  )
}
