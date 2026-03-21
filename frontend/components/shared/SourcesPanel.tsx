"use client"

import { ExternalLink, Link2, ShieldCheck } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import type { SourceReference } from "@/types"

interface SourcesPanelProps {
  sources: SourceReference[]
  title?: string
  description?: string
}

function getHostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "")
  } catch {
    return url
  }
}

export function SourcesPanel({
  sources,
  title = "Nguồn xác minh",
  description = "Các liên kết này là nguồn tham chiếu để kiểm tra lại thông tin và giữ câu trả lời bám dữ kiện.",
}: SourcesPanelProps) {
  if (!sources.length) {
    return null
  }

  return (
    <Card className="border border-border/70 bg-card/92">
      <CardContent className="space-y-4 p-5">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-primary">
            <ShieldCheck className="size-3.5" />
            {title}
          </div>
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        </div>

        <div className="space-y-3">
          {sources.map((source) => (
            <a
              key={`${source.label}-${source.url}`}
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="block rounded-2xl border border-border/70 bg-background/80 p-4 transition-colors hover:border-primary/30 hover:bg-primary/5"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Link2 className="size-4" />
                </div>
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <p className="line-clamp-2 text-sm font-medium leading-6 text-foreground">
                      {source.label}
                    </p>
                    <ExternalLink className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                  </div>
                  {source.snippet ? (
                    <p className="line-clamp-3 text-sm leading-6 text-muted-foreground">
                      {source.snippet}
                    </p>
                  ) : null}
                  <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    {getHostname(source.url)}
                  </p>
                </div>
              </div>
            </a>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
