import { BarChart3, Clock3, GitBranch, Layers3, ListChecks } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { InfographicData, InfographicSection } from "@/types"
import { cn } from "@/lib/utils"

interface InfographicProps {
  data: InfographicData
}

const FALLBACK_THEME = "#0f766e"

export function Infographic({ data }: InfographicProps) {
  const themeColor = data.theme_color || FALLBACK_THEME
  const sections = data.sections ?? []

  return (
    <Card className="w-full overflow-hidden border border-border/70 bg-card/95 shadow-lg shadow-primary/5">
      <div
        className="relative overflow-hidden px-6 py-7 text-white"
        style={{
          background: `linear-gradient(135deg, ${themeColor}, ${themeColor}cc)`,
        }}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(255,255,255,0.2),_transparent_35%)]" />
        <div className="relative space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/14 px-3 py-1 text-xs font-medium uppercase tracking-[0.22em]">
            {getTypeLabel(data.type)}
          </div>
          <h3 className="font-display text-2xl font-semibold text-balance">
            {data.title}
          </h3>
          {data.subtitle ? (
            <p className="max-w-3xl text-sm leading-6 text-white/85">{data.subtitle}</p>
          ) : null}
        </div>
      </div>

      <CardContent className="space-y-5 p-5 sm:p-6">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            {sections.length} khối nội dung
          </span>
          <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
            Trình bày theo dạng {getTypeLabel(data.type).toLowerCase()}
          </span>
        </div>

        {sections.length ? (
          <RendererByType data={{ ...data, sections }} />
        ) : (
          <div className="rounded-2xl border border-dashed border-border/70 bg-background/80 px-4 py-6 text-sm text-muted-foreground">
            Chưa có đủ dữ liệu để dựng infographic chi tiết cho chủ đề này.
          </div>
        )}

        {data.footer_note ? (
          <p className="mt-5 text-center text-xs italic text-muted-foreground">
            {data.footer_note}
          </p>
        ) : null}
      </CardContent>
    </Card>
  )
}

function RendererByType({ data }: { data: InfographicData }) {
  switch (data.type) {
    case "comparison":
      return <ComparisonLayout data={data} />
    case "timeline":
      return <TimelineLayout data={data} />
    case "statistics":
      return <StatisticsLayout data={data} />
    case "list":
      return <ListLayout data={data} />
    case "steps":
    default:
      return <StepsLayout data={data} />
  }
}

function StepsLayout({ data }: { data: InfographicData }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {data.sections.map((section, index) => (
        <SectionCard
          key={`${section.heading}-${index}`}
          section={section}
          index={index}
          themeColor={data.theme_color || FALLBACK_THEME}
          icon={<GitBranch className="size-4" />}
        />
      ))}
    </div>
  )
}

function ComparisonLayout({ data }: { data: InfographicData }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {data.sections.map((section, index) => (
        <Card
          key={`${section.heading}-${index}`}
          className="border border-border/70 bg-background/80"
        >
          <CardHeader className="space-y-3">
            <div
              className="inline-flex size-10 items-center justify-center rounded-2xl text-white"
              style={{ backgroundColor: data.theme_color || FALLBACK_THEME }}
            >
              <Layers3 className="size-4" />
            </div>
            <div>
              <CardTitle className="text-lg">{section.heading}</CardTitle>
              {section.highlight ? (
                <CardDescription className="mt-2 font-medium text-primary">
                  {section.highlight}
                </CardDescription>
              ) : null}
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-6 text-muted-foreground">{section.content}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function TimelineLayout({ data }: { data: InfographicData }) {
  return (
    <div className="space-y-4">
      {data.sections.map((section, index) => (
        <div key={`${section.heading}-${index}`} className="grid gap-3 md:grid-cols-[56px_1fr]">
          <div className="flex md:justify-center">
            <div className="flex flex-col items-center">
              <div
                className="flex size-11 items-center justify-center rounded-full text-white shadow-sm"
                style={{ backgroundColor: data.theme_color || FALLBACK_THEME }}
              >
                <Clock3 className="size-4" />
              </div>
              {index < data.sections.length - 1 ? (
                <div
                  className="mt-2 h-full min-h-12 w-px"
                  style={{ backgroundColor: `${data.theme_color || FALLBACK_THEME}55` }}
                />
              ) : null}
            </div>
          </div>
          <div className="rounded-2xl border border-border/70 bg-background/85 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="font-display text-lg font-semibold">{section.heading}</h4>
              {section.highlight ? (
                <span
                  className="rounded-full px-2 py-1 text-xs font-semibold text-white"
                  style={{ backgroundColor: data.theme_color || FALLBACK_THEME }}
                >
                  {section.highlight}
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{section.content}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

function StatisticsLayout({ data }: { data: InfographicData }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {data.sections.map((section, index) => (
        <Card
          key={`${section.heading}-${index}`}
          className="border border-border/70 bg-background/90"
        >
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-muted-foreground">{section.heading}</p>
                <p className="mt-3 font-display text-3xl font-semibold">
                  {section.highlight || section.icon || `${index + 1}`}
                </p>
              </div>
              <div
                className="flex size-10 items-center justify-center rounded-2xl text-white"
                style={{ backgroundColor: data.theme_color || FALLBACK_THEME }}
              >
                <BarChart3 className="size-4" />
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-muted-foreground">{section.content}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function ListLayout({ data }: { data: InfographicData }) {
  return (
    <div className="space-y-3">
      {data.sections.map((section, index) => (
        <SectionCard
          key={`${section.heading}-${index}`}
          section={section}
          index={index}
          themeColor={data.theme_color || FALLBACK_THEME}
          icon={<ListChecks className="size-4" />}
          compact
        />
      ))}
    </div>
  )
}

function SectionCard({
  section,
  index,
  themeColor,
  icon,
  compact = false,
}: {
  section: InfographicSection
  index: number
  themeColor: string
  icon: React.ReactNode
  compact?: boolean
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border/70 bg-background/85 p-4 transition-colors hover:bg-background",
        compact ? "flex items-start gap-4" : "flex gap-4"
      )}
    >
      <div
        className="flex size-11 shrink-0 items-center justify-center rounded-2xl text-sm font-semibold text-white"
        style={{ backgroundColor: themeColor }}
      >
        {section.icon || icon || `${index + 1}`}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h4 className="font-display text-lg font-semibold">{section.heading}</h4>
          {section.highlight ? (
            <span
              className="rounded-full px-2 py-1 text-xs font-semibold text-white"
              style={{ backgroundColor: themeColor }}
            >
              {section.highlight}
            </span>
          ) : null}
        </div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{section.content}</p>
      </div>
    </div>
  )
}

function getTypeLabel(type: InfographicData["type"]) {
  switch (type) {
    case "comparison":
      return "So sánh"
    case "timeline":
      return "Dòng thời gian"
    case "statistics":
      return "Số liệu"
    case "list":
      return "Danh sách"
    case "steps":
    default:
      return "Các bước"
  }
}
