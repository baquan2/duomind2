import { Lightbulb, Sparkles } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { extractSummaryBullets } from "@/lib/summary-bullets"

interface ExploreSummaryProps {
  summary: string
  keyPoints: string[]
  topicTags: string[]
}

export function ExploreSummary({
  summary,
  keyPoints,
  topicTags: _topicTags,
}: ExploreSummaryProps) {
  const overviewBullets = extractSummaryBullets(summary, [], 5)
  const theoryBullets = keyPoints.slice(0, 5)

  return (
    <div className="grid items-start gap-4 lg:grid-cols-[1fr_1fr]">
      <Card className="self-start border border-border/70 bg-card/92">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Sparkles className="size-5 text-primary" />
            Tổng quan chủ đề
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {overviewBullets.map((point, index) => (
              <li
                key={`${point}-${index}`}
                className="flex gap-3 rounded-2xl border border-border/70 bg-background/80 px-4 py-3 text-sm leading-7 text-foreground/85"
              >
                <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {index + 1}
                </span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="self-start border border-border/70 bg-card/92">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Lightbulb className="size-5 text-primary" />
            Tóm tắt lý thuyết cốt lõi
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {theoryBullets.map((point, index) => (
              <li
                key={`${point}-${index}`}
                className="rounded-2xl border border-border/70 bg-background/70 px-4 py-3 text-sm leading-7 text-foreground/85"
              >
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                    {index + 1}
                  </span>
                  <span>{point}</span>
                </div>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
