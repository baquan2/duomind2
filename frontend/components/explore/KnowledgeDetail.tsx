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
import type {
  KnowledgeDetailData,
  KnowledgeDetailSection,
  KnowledgeSectionKey,
} from "@/types"

interface KnowledgeDetailProps {
  data: KnowledgeDetailData
}

const LEGACY_SECTION_TITLE_MAP: Record<string, string> = {
  "Khai niem cot loi": "Khái niệm cốt lõi",
  "Ban chat / co che hoat dong": "Bản chất / cơ chế hoạt động",
  "Cac thanh phan chinh va quan he giua chung": "Các thành phần chính và quan hệ giữa chúng",
  "Vi du truc quan": "Ví dụ trực quan",
  "Ung dung thuc te": "Ứng dụng thực tế",
  "Nham lan pho bien": "Nhầm lẫn phổ biến",
  "Diem can nam tiep": "Điểm cần nắm tiếp",
}

function extractSummaryBullets(summary: string) {
  return summary
    .split(/\n+/)
    .map((line) => line.replace(/^[-*]\s*/, "").trim())
    .filter((line) => line && !line.endsWith("..."))
}

function normalizeLegacySectionTitle(title: string) {
  return LEGACY_SECTION_TITLE_MAP[title] || title
}

const SECTION_CONFIG: Array<{
  key: KnowledgeSectionKey
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
  const detailSummaryBullets = extractSummaryBullets(data.summary)
  const summaryBullets = detailSummaryBullets.length
    ? detailSummaryBullets.slice(0, 4)
    : data.section_briefs?.detail_focus?.length
      ? data.section_briefs.detail_focus.slice(0, 4)
      : []
  const activeKeys = data.active_section_keys?.length
    ? data.active_section_keys
    : SECTION_CONFIG.map((section) => section.key)
  const visibleSections = SECTION_CONFIG.filter(({ key }) => activeKeys.includes(key))
  const explorationBullets = data.section_briefs?.exploration?.slice(0, 4) ?? []

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
          <ul className="max-w-3xl space-y-2 text-sm leading-7 text-white/88">
            {summaryBullets.map((bullet, index) => (
              <li key={`${bullet}-${index}`} className="flex gap-3">
                <span className="mt-1 inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-white/16 text-xs font-semibold text-white">
                  {index + 1}
                </span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <CardContent className="space-y-5 p-5 sm:p-6">
        <div className="grid gap-4 lg:grid-cols-2">
          {visibleSections.map(({ key, icon }, index) => (
            <SectionCard
              key={key}
              section={data.detailed_sections[key]}
              icon={icon}
              index={index}
            />
          ))}
        </div>

        {explorationBullets.length > 0 ? (
          <div className="rounded-2xl border border-dashed border-border/80 bg-background/70 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-primary/85">
              <TriangleAlert className="size-4" />
              Khám phá sâu hơn
            </div>
            <ul className="mt-3 space-y-3 text-sm leading-7 text-foreground/82">
              {explorationBullets.map((bullet, index) => (
                <li key={`${bullet}-${index}`} className="flex gap-3">
                  <span className="mt-0.5 font-semibold text-primary">{index + 1}.</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
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
            <h4 className="font-display text-lg font-semibold">
              {normalizeLegacySectionTitle(section.title)}
            </h4>
          </div>
          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-foreground/82">
            {section.content}
          </p>
        </div>
      </div>
    </div>
  )
}
