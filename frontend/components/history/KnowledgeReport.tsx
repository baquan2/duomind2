import { Activity, Brain, GraduationCap, Target } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { KnowledgeReport as KnowledgeReportData } from "@/types"

interface KnowledgeReportProps {
  report: KnowledgeReportData
}

const patternLabels: Record<string, string> = {
  consistent: "Học đều đặn",
  sporadic: "Học không thường xuyên",
  intensive: "Học chuyên sâu",
  new: "Mới bắt đầu",
}

const depthLabels: Record<string, string> = {
  surface: "Nền tảng bề mặt",
  intermediate: "Độ sâu trung cấp",
  deep: "Độ sâu tốt",
}

export function KnowledgeReport({ report }: KnowledgeReportProps) {
  return (
    <Card className="overflow-hidden border border-primary/15 bg-[linear-gradient(135deg,_rgba(15,118,110,0.08),_rgba(255,247,221,0.82))]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <Brain className="size-6 text-primary" />
          Báo cáo kiến thức từ AI
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <p className="text-sm leading-7 text-foreground/85">{report.ai_summary}</p>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            icon={<GraduationCap className="size-4" />}
            label="Tổng phiên"
            value={String(report.total_sessions)}
          />
          <StatCard
            icon={<Target className="size-4" />}
            label="Tổng quiz"
            value={String(report.total_quizzes)}
          />
          <StatCard
            icon={<Activity className="size-4" />}
            label="Nhịp học"
            value={patternLabels[report.learning_pattern] || report.learning_pattern || "-"}
          />
          <StatCard
            icon={<Brain className="size-4" />}
            label="Độ sâu"
            value={depthLabels[report.knowledge_depth] || report.knowledge_depth || "-"}
          />
        </div>

        {report.strongest_topics?.length ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-emerald-700">Chủ đề bạn đang mạnh</p>
            <div className="flex flex-wrap gap-2">
              {report.strongest_topics.map((topic) => (
                <Badge key={topic} className="border-0 bg-emerald-100 text-emerald-800">
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {report.weakest_topics?.length ? (
          <div className="space-y-2">
            <p className="text-sm font-medium text-amber-700">Chủ đề nên ôn tiếp</p>
            <div className="flex flex-wrap gap-2">
              {report.weakest_topics.map((topic) => (
                <Badge key={topic} className="border-0 bg-amber-100 text-amber-800">
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {report.ai_recommendations?.length ? (
          <div className="rounded-2xl border border-border/70 bg-card/90 p-4">
            <p className="text-sm font-medium text-primary">AI gợi ý bước tiếp theo</p>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-foreground/85">
              {report.ai_recommendations.map((item, index) => (
                <li key={`${item}-${index}`}>→ {item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card/92 p-4">
      <div className="mb-2 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className="font-display text-xl font-semibold">{value}</div>
    </div>
  )
}
