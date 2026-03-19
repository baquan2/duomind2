import { ListChecks, ScrollText } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { extractSummaryBullets } from "@/lib/summary-bullets"

interface SummaryCardProps {
  summary: string
  keyPoints: string[]
}

export function SummaryCard({ summary, keyPoints }: SummaryCardProps) {
  const summaryBullets = extractSummaryBullets(summary, keyPoints, 5)

  return (
    <div className="grid items-start gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="self-start border border-border/70 bg-card/92">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <ScrollText className="size-5 text-primary" />
            Tóm tắt trọng tâm
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {summaryBullets.map((point, index) => (
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
            <ListChecks className="size-5 text-primary" />
            Điều cần nhớ
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {keyPoints.map((point, index) => (
              <li
                key={`${point}-${index}`}
                className="rounded-2xl border border-border/70 bg-background/75 px-4 py-3 text-sm leading-6 text-foreground/85"
              >
                <span className="mr-2 font-semibold text-primary">{index + 1}.</span>
                {point}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
