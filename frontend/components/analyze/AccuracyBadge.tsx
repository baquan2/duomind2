import { BadgeCheck, ShieldX } from "lucide-react"

import { getAnalyzeVerdictMeta } from "@/lib/analyze-verdict"
import { cn } from "@/lib/utils"
import type { AnalyzeVerdict } from "@/types"

interface AnalysisVerdictBadgeProps {
  verdict: AnalyzeVerdict
  compact?: boolean
}

const verdictConfig = {
  correct: {
    icon: BadgeCheck,
    className:
      "border-emerald-200 bg-emerald-50 text-emerald-800 shadow-emerald-100/50",
  },
  incorrect: {
    icon: ShieldX,
    className: "border-rose-200 bg-rose-50 text-rose-800 shadow-rose-100/50",
  },
} as const

export function AnalysisVerdictBadge({
  verdict,
  compact = false,
}: AnalysisVerdictBadgeProps) {
  const config = verdictConfig[verdict] ?? verdictConfig.incorrect
  const meta = getAnalyzeVerdictMeta(verdict)
  const Icon = config.icon

  return (
    <div
      className={cn(
        compact
          ? "inline-flex min-w-[220px] flex-row items-center gap-3 rounded-full border px-4 py-2 text-left shadow-sm"
          : "flex min-w-[168px] flex-col items-center rounded-2xl border px-4 py-3 text-center shadow-sm",
        config.className
      )}
    >
      <Icon className={compact ? "size-5 shrink-0" : "size-6"} />
      <div className={compact ? "min-w-0" : "mt-2"}>
        <div className={cn("font-display font-semibold leading-none", compact ? "text-base" : "text-2xl")}>
          {compact ? meta.shortLabel : meta.label}
        </div>
        <div className={cn("font-medium", compact ? "mt-1 text-xs" : "mt-2 text-xs")}>
          {meta.description}
        </div>
      </div>
    </div>
  )
}
