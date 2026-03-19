import type { NodeProps } from "@xyflow/react"
import { Handle, Position } from "@xyflow/react"

import type { MindMapNode } from "@/types"
import { cn } from "@/lib/utils"

const nodeStyles = {
  root: "border-primary bg-primary px-6 py-4 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/20",
  main: "border-2 bg-card px-4 py-3 text-sm font-medium text-foreground shadow-sm",
  sub: "border bg-muted/80 px-3 py-2 text-sm text-foreground/80 shadow-sm",
} as const

const nodeWidths = {
  root: "max-w-[260px]",
  main: "max-w-[220px]",
  sub: "max-w-[180px]",
} as const

function normalizeMindMapText(text: string) {
  return text
    .replace(/\b(là gì|la gi)\b/gi, "")
    .replace(/\b(hoạt động như thế nào|hoat dong nhu the nao)\b/gi, "")
    .replace(/\b(vận hành ra sao|van hanh ra sao)\b/gi, "")
    .replace(/\b(vận hành như thế nào|van hanh nhu the nao)\b/gi, "")
    .replace(/\b(ra sao)\b/gi, "")
    .replace(/\b(như thế nào|nhu the nao)\b/gi, "")
    .replace(/\b(thế nào|the nao)\b/gi, "")
    .replace(/[?]+/g, "")
    .replace(/\s{2,}/g, " ")
    .trim()
}

export function CustomNode({ data, type }: NodeProps<MindMapNode>) {
  const nodeType = (type as keyof typeof nodeStyles) || "sub"
  const style = nodeStyles[nodeType]
  const widthClass = nodeWidths[nodeType]
  const displayTitle = normalizeMindMapText((data.label || data.full_label) as string)
  const customStyle =
    nodeType === "main" && data.color
      ? {
          borderColor: data.color,
          boxShadow: `0 10px 25px -18px ${data.color}`,
        }
      : undefined

  return (
    <div
      className={cn(
        widthClass,
        "rounded-2xl text-center transition-shadow hover:shadow-md",
        style
      )}
      style={customStyle}
    >
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <p
        className={cn(
          "break-words whitespace-normal leading-5",
          nodeType === "sub" ? "line-clamp-3 text-sm" : "line-clamp-3"
        )}
      >
        {displayTitle}
      </p>
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
