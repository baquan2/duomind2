"use client"

import {
  ArrowRight,
  BriefcaseBusiness,
  Compass,
  GraduationCap,
  Lightbulb,
  Link2,
  Target,
  TrendingUp,
} from "lucide-react"
import Link from "next/link"
import type { ReactNode } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { buildAnalyzeStarterContent } from "@/lib/learning-roadmap"
import type {
  MentorCareerPath,
  MentorMarketSignal,
  MentorMessagePayload,
  MentorSkillGap,
} from "@/types"


const GAP_BADGE_STYLES: Record<string, string> = {
  high: "border-0 bg-amber-100 text-amber-900",
  medium: "border-0 bg-emerald-100 text-emerald-900",
  low: "border-0 bg-slate-200 text-slate-800",
}

const GAP_BADGE_LABELS: Record<string, string> = {
  high: "Ưu tiên cao",
  medium: "Ưu tiên vừa",
  low: "Ưu tiên thấp",
}


export function MentorResponsePanels({
  payload,
  intent,
  onFollowup,
}: {
  payload: MentorMessagePayload
  intent?: string | null
  onFollowup: (question: string) => void
}) {
  const explorePrompt = buildExplorePrompt(payload)
  const analyzeContent = buildAnalyzeContent(payload)
  const visibility = resolveIntentVisibility(intent)

  return (
    <div className="mt-4 space-y-4 border-t border-border/70 pt-4">
      {payload.decision_summary ? (
        <DecisionSummarySection payload={payload} />
      ) : null}

      <div className="flex flex-wrap gap-2">
        {explorePrompt ? (
          <Button asChild size="sm" variant="outline">
            <Link href={`/explore?prompt=${encodeURIComponent(explorePrompt)}`}>
              Học tiếp trong Khám phá
              <Compass className="ml-2 size-4" />
            </Link>
          </Button>
        ) : null}

        {analyzeContent ? (
          <Button asChild size="sm" variant="outline">
            <Link href={`/analyze?content=${encodeURIComponent(analyzeContent)}`}>
              Tự kiểm tra bằng Phân tích
              <ArrowRight className="ml-2 size-4" />
            </Link>
          </Button>
        ) : null}

        <Button asChild size="sm" variant="outline">
          <Link href="/roadmap">
            Xem lộ trình
            <TrendingUp className="ml-2 size-4" />
          </Link>
        </Button>
      </div>

      {visibility.careerPaths && payload.career_paths?.length ? (
        <CareerPathsSection items={payload.career_paths} />
      ) : null}
      {visibility.skillGaps && payload.skill_gaps?.length ? (
        <SkillGapSection items={payload.skill_gaps} />
      ) : null}
      {visibility.learningSteps && payload.recommended_learning_steps?.length ? (
        <LearningStepsSection items={payload.recommended_learning_steps} />
      ) : null}
      {visibility.marketSignals && payload.market_signals?.length ? (
        <MarketSignalsSection items={payload.market_signals} />
      ) : null}
      {payload.sources?.length ? (
        <SourcesSection title="Nguồn đã dùng" sources={payload.sources} />
      ) : null}
      {payload.related_materials?.length ? (
        <SourcesSection
          title="Tài liệu liên quan"
          sources={payload.related_materials}
          description="Các liên kết này phù hợp để đọc sâu thêm sau khi bạn đã nắm được ý chính."
        />
      ) : null}
      {payload.suggested_followups?.length ? (
        <FollowupSection items={payload.suggested_followups} onFollowup={onFollowup} />
      ) : null}
    </div>
  )
}


function DecisionSummarySection({
  payload,
}: {
  payload: MentorMessagePayload
}) {
  const summary = payload.decision_summary || buildDecisionSummaryFallback(payload)
  if (!summary) {
    return null
  }

  return (
    <section className="rounded-[1.6rem] border border-primary/15 bg-[linear-gradient(135deg,_rgba(240,253,250,0.96),_rgba(255,251,235,0.94))] p-4">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-primary">
        <Target className="size-4" />
        Tóm tắt quyết định
      </div>

      <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <div className="space-y-3 rounded-[1.3rem] border border-white/60 bg-white/90 p-4">
          <div className="font-display text-xl font-semibold text-foreground">{summary.headline}</div>
          <p className="text-sm leading-7 text-foreground/78">{summary.reason}</p>
          <div className="rounded-2xl border border-emerald-200/70 bg-emerald-50/80 p-3">
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-emerald-900">
              Hành động nên làm ngay
            </div>
            <div className="mt-1 text-sm leading-6 text-emerald-950">{summary.next_action}</div>
          </div>
        </div>

        <div className="grid gap-3">
          <div className="rounded-[1.3rem] border border-white/60 bg-white/90 p-4">
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              {summary.priority_label}
            </div>
            <div className="mt-2 font-display text-xl font-semibold text-foreground">
              {summary.priority_value}
            </div>
          </div>
          <div className="rounded-[1.3rem] border border-white/60 bg-white/90 p-4">
            <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Độ tin cậy bối cảnh
            </div>
            <div className="mt-2 text-sm leading-7 text-foreground/78">{summary.confidence_note}</div>
          </div>
        </div>
      </div>
    </section>
  )
}


function CareerPathsSection({ items }: { items: MentorCareerPath[] }) {
  return (
    <StructuredSection
      title="Hướng nghề gợi ý"
      icon={<BriefcaseBusiness className="size-4" />}
      description="Mentor đang đối chiếu hồ sơ hiện tại của bạn với các hướng đi phù hợp nhất."
    >
      <div className="grid gap-3 lg:grid-cols-2">
        {items.map((item) => (
          <div
            key={`${item.role}-${item.next_step}`}
            className="rounded-[1.5rem] border border-border/70 bg-[linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.92))] p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-display text-lg font-semibold text-foreground">{item.role}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                  {item.entry_level}
                </div>
              </div>
              <Badge variant="secondary">Phù hợp với hồ sơ</Badge>
            </div>

            <p className="mt-3 text-sm leading-7 text-foreground/80">{item.fit_reason}</p>

            {item.required_skills?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {item.required_skills.slice(0, 4).map((skill) => (
                  <Badge key={skill} variant="outline" className="rounded-full">
                    {skill}
                  </Badge>
                ))}
              </div>
            ) : null}

            <div className="mt-4 rounded-2xl border border-emerald-200/70 bg-emerald-50/80 p-3">
              <div className="text-xs font-medium uppercase tracking-[0.16em] text-emerald-800">
                Bước tiếp theo
              </div>
              <div className="mt-1 text-sm leading-6 text-emerald-950">{item.next_step}</div>
            </div>
          </div>
        ))}
      </div>
    </StructuredSection>
  )
}


function SkillGapSection({ items }: { items: MentorSkillGap[] }) {
  return (
    <StructuredSection
      title="Kỹ năng nên ưu tiên"
      icon={<GraduationCap className="size-4" />}
      description="Đây là các khoảng trống nên xử lý trước để tăng tốc đúng hướng."
    >
      <div className="grid gap-3 lg:grid-cols-2">
        {items.map((item) => {
          const toneKey = normalizeGapLevel(item.gap_level)
          return (
            <div
              key={`${item.skill}-${item.suggested_action}`}
              className="rounded-[1.5rem] border border-border/70 bg-white p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="font-display text-lg font-semibold text-foreground">{item.skill}</div>
                <Badge className={GAP_BADGE_STYLES[toneKey]}>{GAP_BADGE_LABELS[toneKey]}</Badge>
              </div>

              <p className="mt-3 text-sm leading-7 text-foreground/78">{item.why_it_matters}</p>

              <div className="mt-4 rounded-2xl border border-amber-200/70 bg-amber-50/80 p-3">
                <div className="text-xs font-medium uppercase tracking-[0.16em] text-amber-900">
                  Hành động gợi ý
                </div>
                <div className="mt-1 text-sm leading-6 text-amber-950">{item.suggested_action}</div>
              </div>
            </div>
          )
        })}
      </div>
    </StructuredSection>
  )
}


function LearningStepsSection({ items }: { items: string[] }) {
  return (
    <StructuredSection
      title="Các bước học tiếp theo"
      icon={<Lightbulb className="size-4" />}
      description="Mentor đã sắp lại thứ tự để bạn không phải tự đoán nên học gì trước."
    >
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item, index) => (
          <div key={item} className="rounded-[1.5rem] border border-border/70 bg-muted/20 p-4">
            <div className="flex items-center gap-3">
              <div className="flex size-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                {index + 1}
              </div>
              <div className="text-sm leading-7 text-foreground/82">{item}</div>
            </div>
          </div>
        ))}
      </div>
    </StructuredSection>
  )
}


function MarketSignalsSection({ items }: { items: MentorMarketSignal[] }) {
  return (
    <StructuredSection
      title="Tín hiệu thị trường"
      icon={<TrendingUp className="size-4" />}
      description="Các tín hiệu này giúp mentor bám sát nhu cầu thực tế thay vì chỉ tư vấn theo cảm tính."
    >
      <div className="space-y-3">
        {items.map((item) => (
          <div
            key={`${item.role_name}-${item.source_url}`}
            className="rounded-[1.5rem] border border-border/70 bg-white p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="font-display text-lg font-semibold text-foreground">{item.role_name}</div>
              {item.source_url ? (
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                >
                  {item.source_name || "Nguồn tham khảo"}
                  <ArrowRight className="size-3.5" />
                </a>
              ) : null}
            </div>

            <p className="mt-3 text-sm leading-7 text-foreground/80">{item.demand_summary}</p>

            {item.top_skills?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {item.top_skills.slice(0, 5).map((skill) => (
                  <Badge key={skill} variant="outline" className="rounded-full">
                    {skill}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </StructuredSection>
  )
}


function SourcesSection({
  title,
  sources,
  description = "Các đường dẫn này dùng để kiểm tra thêm hoặc mở rộng góc nhìn khi cần.",
}: {
  title: string
  sources: NonNullable<MentorMessagePayload["sources"]>
  description?: string
}) {
  return (
    <StructuredSection
      title={title}
      icon={<Link2 className="size-4" />}
      description={description}
    >
      <div className="space-y-2">
        {sources.map((source) => (
          <a
            key={`${source.label}-${source.url}`}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 rounded-2xl border border-border/70 bg-muted/20 px-3 py-2.5 text-sm leading-6 text-foreground/80 transition-colors hover:border-primary/30 hover:bg-primary/5"
          >
            <Link2 className="size-4 text-primary" />
            <span className="line-clamp-2">{source.label}</span>
          </a>
        ))}
      </div>
    </StructuredSection>
  )
}


function FollowupSection({
  items,
  onFollowup,
}: {
  items: string[]
  onFollowup: (question: string) => void
}) {
  return (
    <StructuredSection
      title="Gợi ý hỏi tiếp"
      icon={<ArrowRight className="size-4" />}
      description="Bấm một câu hỏi để mentor đi sâu thêm mà không cần gõ lại từ đầu."
    >
      <div className="flex flex-wrap gap-2">
        {items.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onFollowup(question)}
            className="rounded-full border border-border/70 bg-background px-3 py-1.5 text-xs text-foreground/80 transition-colors hover:border-primary/30 hover:bg-primary/5"
          >
            {question}
          </button>
        ))}
      </div>
    </StructuredSection>
  )
}


function StructuredSection({
  title,
  icon,
  description,
  children,
}: {
  title: string
  icon: ReactNode
  description: string
  children: ReactNode
}) {
  return (
    <section className="space-y-2">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-primary">
        {icon}
        {title}
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      <div className="space-y-3">{children}</div>
    </section>
  )
}


function resolveIntentVisibility(intent?: string | null) {
  switch ((intent || "").trim()) {
    case "market_outlook":
      return {
        careerPaths: false,
        skillGaps: false,
        learningSteps: true,
        marketSignals: true,
      }
    case "skill_gap":
      return {
        careerPaths: false,
        skillGaps: true,
        learningSteps: true,
        marketSignals: false,
      }
    case "learning_roadmap":
      return {
        careerPaths: false,
        skillGaps: false,
        learningSteps: true,
        marketSignals: false,
      }
    case "career_fit":
    case "career_roles":
      return {
        careerPaths: true,
        skillGaps: true,
        learningSteps: true,
        marketSignals: false,
      }
    default:
      return {
        careerPaths: false,
        skillGaps: false,
        learningSteps: false,
        marketSignals: false,
      }
  }
}


function buildExplorePrompt(payload: MentorMessagePayload) {
  const topSkill = payload.skill_gaps?.[0]?.skill?.trim()
  if (topSkill) {
    return `Giải thích ${topSkill} theo cách dễ học và dễ áp dụng thực tế`
  }

  const topRole = payload.career_paths?.[0]?.role?.trim()
  if (topRole) {
    return `Những kỹ năng cốt lõi để bắt đầu với vai trò ${topRole}`
  }

  return payload.suggested_followups?.[0] || ""
}


function buildAnalyzeContent(payload: MentorMessagePayload) {
  const topSkill = payload.skill_gaps?.[0]?.skill?.trim()
  if (topSkill) {
    return buildAnalyzeStarterContent(topSkill, payload.career_paths?.[0]?.role)
  }

  const topRole = payload.career_paths?.[0]?.role?.trim()
  if (topRole) {
    return buildAnalyzeStarterContent(`nhóm kỹ năng cốt lõi cho ${topRole}`, topRole)
  }

  return ""
}


function normalizeGapLevel(level: string) {
  const normalized = level?.toLowerCase().trim()
  if (normalized === "high" || normalized === "medium" || normalized === "low") {
    return normalized
  }
  return "medium"
}


function buildDecisionSummaryFallback(payload: MentorMessagePayload) {
  const topRole = payload.career_paths?.[0]?.role?.trim()
  const topGap = payload.skill_gaps?.[0]?.skill?.trim()
  const topGapAction = payload.skill_gaps?.[0]?.suggested_action?.trim()
  const topStep = payload.recommended_learning_steps?.[0]?.trim()
  const gapReason = payload.skill_gaps?.[0]?.why_it_matters?.trim()

  if (!topRole && !topGap && !topStep) {
    return null
  }

  const priorityValue = topGap || topStep || "Ưu tiên hiện tại"
  const headline = topRole
    ? `Ưu tiên ${priorityValue} để tiến gần vai trò ${topRole}.`
    : `Ưu tiên ${priorityValue} để mentor chốt lại thứ tự học rõ hơn.`

  return {
    headline,
    priority_label: topRole ? `Khoảng trống ưu tiên cho ${topRole}` : "Khoảng trống ưu tiên hiện tại",
    priority_value: priorityValue,
    reason:
      gapReason ||
      payload.career_paths?.[0]?.fit_reason?.trim() ||
      "Mentor đang dựa vào vai trò mục tiêu, khoảng trống kỹ năng và bước học tiếp theo để chốt ưu tiên gần nhất.",
    next_action:
      topGapAction || topStep || "Mở lộ trình hoặc Khám phá để thực hiện bước học tiếp theo.",
    confidence_note:
      payload.skill_gaps?.length || payload.career_paths?.length
        ? "Tóm tắt này được suy ra từ vai trò mục tiêu, khoảng trống kỹ năng và lộ trình học hiện có."
        : "Bạn nên hỏi mentor thêm một câu để khóa ưu tiên sát hơn.",
  }
}
