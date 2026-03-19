import { AlertTriangle, BadgeCheck, HelpCircle, ShieldX } from "lucide-react"

import { cn } from "@/lib/utils"

interface AccuracyBadgeProps {
  score: number | null | undefined
  assessment: string
}

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

export function AccuracyBadge({ score, assessment }: AccuracyBadgeProps) {
  const config =
    accuracyConfig[assessment as keyof typeof accuracyConfig] ??
    accuracyConfig.unverifiable
  const Icon = config.icon
  const hasNumericScore = typeof score === "number" && Number.isFinite(score)

  return (
    <div
      className={cn(
        "flex min-w-[148px] flex-col items-center rounded-2xl border px-4 py-3 text-center shadow-sm",
        config.className
      )}
    >
      <Icon className="size-6" />
      <div className="mt-2 font-display text-3xl font-semibold leading-none">
        {hasNumericScore ? `${score}%` : "N/A"}
      </div>
      <div className="mt-1 text-xs font-medium">{config.label}</div>
    </div>
  )
}
