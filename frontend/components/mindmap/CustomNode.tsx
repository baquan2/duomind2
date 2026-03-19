import type { NodeProps } from "@xyflow/react"
import { Handle, Position } from "@xyflow/react"

import type { MindMapNode } from "@/types"
import { cn } from "@/lib/utils"

const nodeStyles = {
  root: "border-primary bg-primary px-6 py-4 text-base font-semibold text-primary-foreground shadow-lg shadow-primary/20",
  main: "border-2 bg-card px-4 py-3 text-sm font-medium text-foreground shadow-sm",
  sub: "border bg-muted/80 px-3 py-2 text-sm text-foreground/80 shadow-sm",
} as const

export function CustomNode({ data, type }: NodeProps<MindMapNode>) {
  const style = nodeStyles[(type as keyof typeof nodeStyles) || "sub"]
  const customStyle =
    type === "main" && data.color
      ? {
          borderColor: data.color,
          boxShadow: `0 10px 25px -18px ${data.color}`,
        }
      : undefined

  return (
    <div
      className={cn(
        "max-w-[260px] rounded-2xl text-center transition-shadow hover:shadow-md",
        style
      )}
      style={customStyle}
    >
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <p className="break-words whitespace-normal leading-5">
        {data.label}
      </p>
      {data.description && type !== "root" ? (
        <p className="mt-1 line-clamp-2 break-words text-xs leading-5 opacity-70">
          {data.description}
        </p>
      ) : null}
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
