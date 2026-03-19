"use client"

import type { ReactNode } from "react"
import {
  BookOpenText,
  BriefcaseBusiness,
  Compass,
  Lightbulb,
  Network,
  Route,
  TriangleAlert,
} from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import type { KnowledgeDetailData, KnowledgeDetailSection } from "@/types"

interface KnowledgeDetailProps {
  data: KnowledgeDetailData
}

const SECTION_CONFIG: Array<{
  key: keyof KnowledgeDetailData["detailed_sections"]
  icon: ReactNode
}> = [
  { key: "core_concept", icon: <BookOpenText className="size-4" /> },
  { key: "mechanism", icon: <Network className="size-4" /> },
  { key: "components_and_relationships", icon: <Compass className="size-4" /> },
  { key: "persona_based_example", icon: <Lightbulb className="size-4" /> },
  { key: "real_world_applications", icon: <BriefcaseBusiness className="size-4" /> },
  { key: "common_misconceptions", icon: <TriangleAlert className="size-4" /> },
  { key: "next_step_self_study", icon: <Route className="size-4" /> },
]

export function KnowledgeDetail({ data }: KnowledgeDetailProps) {
  return (
    <Card className="w-full overflow-hidden border border-border/70 bg-card/95 shadow-lg shadow-primary/5">
      <div className="relative overflow-hidden px-6 py-7 text-white">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,_rgba(15,118,110,1),_rgba(22,163,74,0.88))]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(255,255,255,0.18),_transparent_35%)]" />
        <div className="relative space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/14 px-3 py-1 text-xs font-medium uppercase tracking-[0.22em]">
            Chi tiết kiến thức
          </div>
          <h3 className="font-display text-2xl font-semibold text-balance">{data.title}</h3>
          <p className="max-w-3xl whitespace-pre-line text-sm leading-7 text-white/88">
            {data.summary}
          </p>
        </div>
      </div>

      <CardContent className="space-y-5 p-5 sm:p-6">
        <div className="grid gap-4 lg:grid-cols-2">
          {SECTION_CONFIG.map(({ key, icon }, index) => (
            <SectionCard
              key={key}
              section={data.detailed_sections[key]}
              icon={icon}
              index={index}
            />
          ))}
        </div>

        <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
            Gợi ý đọc nhanh phần này
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <AdaptationChip label="Nên đọc trước" value={data.teaching_adaptation.focus_priority} />
            <AdaptationChip label="Cách diễn giải" value={data.teaching_adaptation.tone} />
            <AdaptationChip label="Mức độ" value={data.teaching_adaptation.depth_control} />
            <AdaptationChip label="Cách ghi nhớ" value={data.teaching_adaptation.example_strategy} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function SectionCard({
  section,
  icon,
  index,
}: {
  section: KnowledgeDetailSection
  icon: ReactNode
  index: number
}) {
  return (
    <div className="rounded-2xl border border-border/70 bg-background/85 p-4 transition-colors hover:bg-background">
      <div className="flex items-start gap-3">
        <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground">
              Phần {index + 1}
            </span>
            <h4 className="font-display text-lg font-semibold">{section.title}</h4>
          </div>
          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground/82">
            {section.content}
          </p>
        </div>
      </div>
    </div>
  )
}

function AdaptationChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-card/90 p-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-sm leading-6 text-foreground/85">{value}</p>
    </div>
  )
}
