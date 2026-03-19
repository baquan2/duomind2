"use client"

import axios from "axios"
import { AnimatePresence, motion } from "framer-motion"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { StepIndicator } from "@/components/onboarding/StepIndicator"
import { Step1Basic } from "@/components/onboarding/steps/Step1Basic"
import { Step2Details } from "@/components/onboarding/steps/Step2Details"
import { Step3Goals } from "@/components/onboarding/steps/Step3Goals"
import { Step4Confirm } from "@/components/onboarding/steps/Step4Confirm"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import apiClient from "@/lib/api/client"
import type { OnboardingData, OnboardingResponse } from "@/types"

const TOTAL_STEPS = 4

type OnboardingFormState = Partial<OnboardingData>

const INITIAL_FORM_STATE: OnboardingFormState = {
  learning_goals: [],
  topics_of_interest: [],
  learning_style: "mixed",
  daily_study_minutes: 30,
}

export function OnboardingWizard() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aiResult, setAiResult] = useState<OnboardingResponse | null>(null)
  const [data, setData] = useState<OnboardingFormState>(INITIAL_FORM_STATE)

  const updateData = (updates: Partial<OnboardingData>) => {
    setData((previous) => ({ ...previous, ...updates }))
  }

  const stepComponents = [
    <Step1Basic key="step-1" data={data} onChange={updateData} />,
    <Step2Details key="step-2" data={data} onChange={updateData} />,
    <Step3Goals key="step-3" data={data} onChange={updateData} />,
    <Step4Confirm key="step-4" data={data} aiResult={aiResult} loading={loading} />,
  ]

  useEffect(() => {
    if (!aiResult) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      router.push("/dashboard")
      router.refresh()
    }, 2600)

    return () => window.clearTimeout(timeoutId)
  }, [aiResult, router])

  const handleNext = () => {
    const validationMessage = validateStep(step, data)
    if (validationMessage) {
      setError(validationMessage)
      return
    }

    setError(null)
    setStep((current) => Math.min(current + 1, TOTAL_STEPS))
  }

  const handlePrevious = () => {
    setError(null)
    setStep((current) => Math.max(current - 1, 1))
  }

  const handleSubmit = async () => {
    const payload = buildPayload(data)
    if (!payload) {
      setError("Thông tin onboarding chưa đầy đủ. Vui lòng kiểm tra lại.")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.post<OnboardingResponse>(
        "/api/onboarding/submit",
        payload
      )
      setAiResult(response.data)
    } catch (submissionError) {
      setError(getErrorMessage(submissionError))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-3xl animate-fade-up">
      <div className="mb-8 text-center">
        <div className="inline-flex rounded-full border border-primary/15 bg-primary/8 px-4 py-1.5 text-xs font-medium uppercase tracking-[0.24em] text-primary">
          Milestone 1
        </div>
        <h1 className="mt-4 font-display text-4xl font-semibold text-balance">
          Cá nhân hóa trải nghiệm học tập của bạn
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
          Wizard 4 bước này giúp DUO MIND xác định persona, độ khó và cách trình bày
          phù hợp trước khi bạn bắt đầu dashboard.
        </p>
      </div>

      <div className="mb-6">
        <Progress value={(step / TOTAL_STEPS) * 100} className="h-2" />
        <StepIndicator current={step} total={TOTAL_STEPS} />
      </div>

      <Card className="overflow-hidden border border-border/70 bg-card/92 shadow-xl shadow-primary/5 backdrop-blur">
        <CardContent className="p-6 sm:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${step}-${Boolean(aiResult)}-${loading}`}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.98 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
            >
              {stepComponents[step - 1]}
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      {error && !loading && !aiResult ? (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {!aiResult ? (
        <div className="mt-6 flex items-center justify-between gap-4">
          <Button variant="outline" onClick={handlePrevious} disabled={step === 1 || loading}>
            Quay lại
          </Button>
          {step < TOTAL_STEPS ? (
            <Button onClick={handleNext}>Tiếp theo</Button>
          ) : (
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? "AI đang phân tích..." : "Hoàn thành"}
            </Button>
          )}
        </div>
      ) : null}
    </div>
  )
}

function validateStep(step: number, data: OnboardingFormState) {
  if (step === 1) {
    if (!data.age_range || !data.status) {
      return "Hãy chọn độ tuổi và trạng thái hiện tại trước khi tiếp tục."
    }
  }

  if (step === 2) {
    const needsStudentInfo = data.status === "student" || data.status === "both"
    const needsWorkingInfo = data.status === "working" || data.status === "both"

    if (needsStudentInfo && !data.education_level) {
      return "Hãy chọn trình độ học tập của bạn."
    }

    if (needsStudentInfo && !data.major?.trim() && !data.school_name?.trim()) {
      return "Hãy thêm chuyên ngành hoặc tên trường để AI hiểu bối cảnh học tập."
    }

    if (needsWorkingInfo && !data.industry?.trim() && !data.job_title?.trim()) {
      return "Hãy thêm ngành nghề hoặc vị trí công việc của bạn."
    }
  }

  if (step === 3) {
    if (!data.learning_goals?.length) {
      return "Hãy chọn ít nhất một mục tiêu học tập."
    }

    if (!data.topics_of_interest?.length) {
      return "Hãy chọn ít nhất một chủ đề quan tâm."
    }
  }

  return null
}

function buildPayload(data: OnboardingFormState): OnboardingData | null {
  if (!data.age_range || !data.status) {
    return null
  }

  return {
    age_range: data.age_range,
    status: data.status,
    education_level: data.education_level,
    major: data.major?.trim() || undefined,
    school_name: data.school_name?.trim() || undefined,
    industry: data.industry?.trim() || undefined,
    job_title: data.job_title?.trim() || undefined,
    years_experience: data.years_experience,
    learning_goals: data.learning_goals ?? [],
    topics_of_interest: data.topics_of_interest ?? [],
    learning_style: data.learning_style ?? "mixed",
    daily_study_minutes: data.daily_study_minutes ?? 30,
  }
}

function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === "string" && detail.trim()) {
      return detail
    }
  }

  return "Không thể hoàn thành onboarding lúc này. Vui lòng thử lại."
}
