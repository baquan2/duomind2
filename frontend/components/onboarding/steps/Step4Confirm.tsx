"use client"

import { motion } from "framer-motion"
import { Orbit, Sparkles, Stars } from "lucide-react"
import { useEffect, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { OnboardingData, OnboardingResponse } from "@/types"

import {
  AGE_RANGES,
  EDUCATION_OPTIONS,
  GOAL_OPTIONS,
  STATUS_OPTIONS,
  TOPIC_OPTIONS,
  getOptionLabel,
  getOptionLabels,
} from "../options"

interface Step4ConfirmProps {
  data: Partial<OnboardingData>
  aiResult: OnboardingResponse | null
  loading: boolean
}

const LOADING_STAGES = [
  { label: "AI đang đọc hồ sơ học tập", hint: "Tổng hợp độ tuổi, bối cảnh và quỹ thời gian học." },
  { label: "AI đang xác định learning persona", hint: "Suy luận cách dạy, mức độ khó và kiểu ví dụ phù hợp." },
  { label: "AI đang cá nhân hóa chiến lược dạy", hint: "Điều chỉnh tốc độ, độ sâu kiến thức và lượng nội dung phù hợp." },
  { label: "AI đang hoàn thiện gợi ý mở đầu", hint: "Chuẩn bị persona và các chủ đề nên học trước cho bạn." },
]

export function Step4Confirm({
  data,
  aiResult,
  loading,
}: Step4ConfirmProps) {
  const [activeStage, setActiveStage] = useState(0)

  useEffect(() => {
    if (!loading) {
      setActiveStage(0)
      return
    }

    const intervalId = window.setInterval(() => {
      setActiveStage((current) => (current + 1) % LOADING_STAGES.length)
    }, 1200)

    return () => window.clearInterval(intervalId)
  }, [loading])

  if (loading) {
    const progress = [24, 51, 78, 92][activeStage] ?? 24

    return (
      <div className="space-y-6 py-8 text-center">
        <div className="relative mx-auto flex size-36 items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
            className="absolute inset-0 rounded-full border border-primary/15"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
            className="absolute inset-3 rounded-full border-2 border-dashed border-primary/30"
          />
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 3.2, repeat: Infinity, ease: "linear" }}
            className="absolute inset-0"
          >
            <div className="absolute left-1/2 top-0 h-4 w-4 -translate-x-1/2 rounded-full bg-primary/80 shadow-lg shadow-primary/30" />
          </motion.div>
          <motion.div
            animate={{ scale: [1, 1.06, 1] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
            className="relative flex size-20 items-center justify-center rounded-full bg-primary/10 text-primary"
          >
            <Orbit className="size-8" />
          </motion.div>
        </div>

        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.2em] text-primary">
            <Stars className="size-3.5" />
            AI đang phân tích
          </div>
          <div className="space-y-2">
            <p className="font-display text-2xl font-semibold">{LOADING_STAGES[activeStage]?.label}</p>
            <p className="mx-auto max-w-xl text-sm leading-6 text-muted-foreground">
              {LOADING_STAGES[activeStage]?.hint}
            </p>
          </div>
        </div>

        <div className="mx-auto max-w-xl space-y-3">
          <Progress value={progress} className="h-2.5" />
          <div className="grid gap-2 text-left sm:grid-cols-2">
            {LOADING_STAGES.map((stage, index) => (
              <div
                key={stage.label}
                className={`rounded-2xl border px-3 py-3 text-sm transition-colors ${
                  index <= activeStage
                    ? "border-primary/25 bg-primary/8 text-foreground"
                    : "border-border/70 bg-background/70 text-muted-foreground"
                }`}
              >
                {stage.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (aiResult) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="space-y-5 py-4 text-center"
      >
        <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Sparkles className="size-7" />
        </div>
        <div className="space-y-2">
          <h3 className="font-display text-2xl font-semibold">AI đã hiểu bạn rõ hơn</h3>
          <p className="text-sm text-muted-foreground">
            Persona này sẽ được dùng để cá nhân hóa cách giải thích, độ khó và đề xuất học
            tập.
          </p>
        </div>

        <Card className="border-primary/20 bg-primary/5 text-left">
          <CardContent className="space-y-3 p-5">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-primary/70">AI Persona</p>
              <Badge className="mt-2 border-0 bg-primary text-primary-foreground">
                {aiResult.ai_persona}
              </Badge>
            </div>
            <p className="text-sm leading-6 text-foreground/85">
              {aiResult.ai_persona_description}
            </p>
          </CardContent>
        </Card>

        {aiResult.ai_recommended_topics.length ? (
          <div className="space-y-3">
            <p className="text-sm font-medium">Chủ đề đề xuất cho bạn</p>
            <div className="flex flex-wrap justify-center gap-2">
              {aiResult.ai_recommended_topics.map((topic) => (
                <Badge key={topic} variant="outline" className="bg-card">
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        <p className="text-sm text-muted-foreground">Đang chuyển đến dashboard...</p>
      </motion.div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Bước 4
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">Xác nhận thông tin</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Kiểm tra nhanh trước khi gửi để AI phân loại persona cho bạn.
          </p>
        </div>
      </div>

      <Card className="border border-border/70 bg-card/90">
        <CardContent className="space-y-3 p-5 text-sm">
          <SummaryLine label="Độ tuổi" value={getOptionLabel(data.age_range, AGE_RANGES)} />
          <SummaryLine label="Trạng thái" value={getOptionLabel(data.status, STATUS_OPTIONS)} />
          <SummaryLine label="Trình độ" value={getOptionLabel(data.education_level, EDUCATION_OPTIONS)} />
          {data.major ? <SummaryLine label="Chuyên ngành" value={data.major} /> : null}
          {data.school_name ? <SummaryLine label="Trường" value={data.school_name} /> : null}
          {data.industry ? <SummaryLine label="Ngành nghề" value={data.industry} /> : null}
          {data.job_title ? <SummaryLine label="Vị trí" value={data.job_title} /> : null}
          <SummaryLine label="Mục tiêu" value={getOptionLabels(data.learning_goals, GOAL_OPTIONS)} />
          <SummaryLine label="Chủ đề" value={getOptionLabels(data.topics_of_interest, TOPIC_OPTIONS)} />
          <SummaryLine label="Thời gian học" value={`${data.daily_study_minutes ?? 30} phút/ngày`} />
        </CardContent>
      </Card>
    </div>
  )
}

function SummaryLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 border-b border-border/60 pb-3 last:border-b-0 last:pb-0 sm:grid-cols-[140px_1fr]">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground">{value}</span>
    </div>
  )
}
