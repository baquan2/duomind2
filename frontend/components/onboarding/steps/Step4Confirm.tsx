"use client"

import { motion } from "framer-motion"
import { Loader2, Sparkles } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
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

export function Step4Confirm({
  data,
  aiResult,
  loading,
}: Step4ConfirmProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center space-y-4 py-12 text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary"
        >
          <Loader2 className="size-7" />
        </motion.div>
        <div className="space-y-2">
          <p className="font-medium">AI đang phân tích hồ sơ của bạn...</p>
          <p className="text-sm text-muted-foreground">
            Chỉ mất vài giây để tạo persona phù hợp.
          </p>
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
            Persona này sẽ được dùng để cá nhân hóa cách giải thích, độ khó và đề
            xuất học tập.
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
          <SummaryLine
            label="Độ tuổi"
            value={getOptionLabel(data.age_range, AGE_RANGES)}
          />
          <SummaryLine
            label="Trạng thái"
            value={getOptionLabel(data.status, STATUS_OPTIONS)}
          />
          <SummaryLine
            label="Trình độ"
            value={getOptionLabel(data.education_level, EDUCATION_OPTIONS)}
          />
          {data.major ? <SummaryLine label="Chuyên ngành" value={data.major} /> : null}
          {data.school_name ? <SummaryLine label="Trường" value={data.school_name} /> : null}
          {data.industry ? <SummaryLine label="Ngành nghề" value={data.industry} /> : null}
          {data.job_title ? <SummaryLine label="Vị trí" value={data.job_title} /> : null}
          <SummaryLine
            label="Mục tiêu"
            value={getOptionLabels(data.learning_goals, GOAL_OPTIONS)}
          />
          <SummaryLine
            label="Chủ đề"
            value={getOptionLabels(data.topics_of_interest, TOPIC_OPTIONS)}
          />
          <SummaryLine
            label="Thời gian học"
            value={`${data.daily_study_minutes ?? 30} phút/ngày`}
          />
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
