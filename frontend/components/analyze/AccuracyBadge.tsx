import { AlertTriangle, BadgeCheck, HelpCircle, ShieldX } from "lucide-react"

import { cn } from "@/lib/utils"

interface AccuracyBadgeProps {
  score: number | null | undefined
  assessment: string
  compact?: boolean
}

const fallbackAccuracyScores = {
  high: 90,
  medium: 75,
  low: 45,
  unverifiable: 60,
} as const

const accuracyConfig = {
  high: {
    icon: BadgeCheck,
    label: "Chính xác cao",
    className:
      "border-emerald-200 bg-emerald-50 text-emerald-800 shadow-emerald-100/50",
  },
  medium: {
    icon: AlertTriangle,
    label: "Cần kiểm tra thêm",
    className:
      "border-amber-200 bg-amber-50 text-amber-800 shadow-amber-100/50",
  },
  low: {
    icon: ShieldX,
    label: "Nhiều sai sót",
    className: "border-rose-200 bg-rose-50 text-rose-800 shadow-rose-100/50",
  },
  unverifiable: {
    icon: HelpCircle,
    label: "Khó xác minh",
    className: "border-slate-200 bg-slate-50 text-slate-700 shadow-slate-100/50",
  },
} as const

export function AccuracyBadge({
  score,
  assessment,
  compact = false,
}: AccuracyBadgeProps) {
  const config =
    accuracyConfig[assessment as keyof typeof accuracyConfig] ??
    accuracyConfig.unverifiable
  const Icon = config.icon
  const hasNumericScore = typeof score === "number" && Number.isFinite(score)
  const displayScore = hasNumericScore
    ? Math.max(0, Math.min(100, Math.round(score)))
    : fallbackAccuracyScores[
        (assessment as keyof typeof fallbackAccuracyScores) ?? "unverifiable"
      ] ?? fallbackAccuracyScores.unverifiable

  return (
    <div
      className={cn(
        compact
          ? "inline-flex min-w-[220px] flex-row items-center gap-3 rounded-full border px-4 py-2 text-left shadow-sm"
          : "flex min-w-[148px] flex-col items-center rounded-2xl border px-4 py-3 text-center shadow-sm",
        config.className
      )}
    >
      <Icon className={compact ? "size-5 shrink-0" : "size-6"} />
      <div className={compact ? "min-w-0" : "mt-2"}>
        <div className={cn("font-display font-semibold leading-none", compact ? "text-xl" : "text-3xl")}>
          {displayScore}%
        </div>
        <div className={cn("font-medium", compact ? "mt-1 text-xs" : "mt-1 text-xs")}>
          {config.label}
        </div>
      </div>
    </div>
  )
}
