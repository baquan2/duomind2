"use client"

import { Save, Sparkles, UserRound } from "lucide-react"
import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { submitOnboarding } from "@/lib/api/onboarding"
import { getApiErrorMessage } from "@/lib/api/errors"
import { createClient } from "@/lib/supabase/client"
import { cn } from "@/lib/utils"
import {
  AGE_RANGES,
  EDUCATION_OPTIONS,
  GOAL_OPTIONS,
  STATUS_OPTIONS,
  TOPIC_OPTIONS,
} from "@/components/onboarding/options"
import type { OnboardingData, OnboardingResponse } from "@/types"

type ProfileEditorState = Partial<OnboardingData> & {
  full_name: string
}

type InitialOnboardingSnapshot = Partial<OnboardingData> & {
  ai_persona?: string | null
  ai_persona_description?: string | null
  ai_recommended_topics?: string[] | null
}

interface ProfileEditorProps {
  userId: string
  email?: string | null
  createdAt?: string | null
  initialFullName?: string | null
  initialOnboarding?: InitialOnboardingSnapshot | null
}

const DAILY_STUDY_PRESETS = [15, 30, 45, 60, 90]
const LOW_SIGNAL_PERSONA_PATTERNS = [
  "gemini tạm thời chưa phân tích",
  "gemini tam thoi chua phan tich",
  "hệ thống đang dùng hồ sơ cơ bản",
  "he thong dang dung ho so co ban",
]
const GENERIC_TOPIC_VALUES = new Set([
  "technology",
  "general",
  "other",
  "misc",
  "learning",
  "study",
])

export function ProfileEditor({
  userId,
  email,
  createdAt,
  initialFullName,
  initialOnboarding,
}: ProfileEditorProps) {
  const router = useRouter()
  const initialState = useMemo<ProfileEditorState>(
    () => ({
      full_name: initialFullName ?? "",
      age_range: initialOnboarding?.age_range ?? "18_24",
      status: initialOnboarding?.status ?? "student",
      education_level: initialOnboarding?.education_level,
      major: initialOnboarding?.major ?? "",
      school_name: initialOnboarding?.school_name ?? "",
      industry: initialOnboarding?.industry ?? "",
      job_title: initialOnboarding?.job_title ?? "",
      years_experience: initialOnboarding?.years_experience ?? undefined,
      learning_goals: initialOnboarding?.learning_goals ?? [],
      topics_of_interest: initialOnboarding?.topics_of_interest ?? [],
      learning_style: initialOnboarding?.learning_style ?? "mixed",
      daily_study_minutes: initialOnboarding?.daily_study_minutes ?? 30,
    }),
    [initialFullName, initialOnboarding]
  )

  const [form, setForm] = useState<ProfileEditorState>(initialState)
  const [aiResult, setAiResult] = useState<OnboardingResponse | null>(
    initialOnboarding?.ai_persona
      ? {
          success: true,
          ai_persona: initialOnboarding.ai_persona,
          ai_persona_description: initialOnboarding.ai_persona_description ?? "",
          ai_recommended_topics: initialOnboarding.ai_recommended_topics ?? [],
        }
      : null
  )
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const isStudent = form.status === "student" || form.status === "both"
  const isWorking = form.status === "working" || form.status === "both"
  const dailyStudyMinutes = form.daily_study_minutes ?? 30
  const personaDescription = sanitizePersonaDescription(aiResult?.ai_persona_description)
  const recommendedTopics = sanitizeRecommendedTopics(aiResult?.ai_recommended_topics ?? [])
  const hasMeaningfulPersona = Boolean(aiResult?.ai_persona && (personaDescription || recommendedTopics.length))

  const updateField = <K extends keyof ProfileEditorState>(key: K, value: ProfileEditorState[K]) => {
    setForm((previous) => ({ ...previous, [key]: value }))
  }

  const toggleArrayValue = (key: "learning_goals" | "topics_of_interest", value: string) => {
    const currentValues = form[key] ?? []
    const nextValues = currentValues.includes(value)
      ? currentValues.filter((item) => item !== value)
      : [...currentValues, value]

    updateField(key, nextValues)
  }

  const resetForm = () => {
    setForm(initialState)
    setError(null)
    setSuccess(null)
  }

  const handleSubmit = async () => {
    const payload = buildPayload(form)
    if (!payload) {
      setError("Hồ sơ hiện chưa đủ thông tin tối thiểu. Hãy kiểm tra lại các mục bắt buộc.")
      setSuccess(null)
      return
    }

    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const supabase = createClient()
      await supabase.from("profiles").update({ full_name: form.full_name.trim() || null }).eq("id", userId)

      const response = await submitOnboarding(payload)
      setAiResult(response)
      setSuccess("Hồ sơ đã được cập nhật. Mentor và các gợi ý học tập sẽ dùng dữ liệu mới của bạn.")
      router.refresh()
    } catch (saveError) {
      setError(
        getApiErrorMessage(saveError, "Không thể cập nhật hồ sơ lúc này. Vui lòng thử lại sau.")
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.12),_rgba(255,247,221,0.9))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-[-2rem] top-[-2rem] h-44 w-44 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-3xl space-y-3">
            <Badge className="border-0 bg-primary text-primary-foreground">Hồ sơ học tập</Badge>
            <h1 className="font-display text-4xl font-semibold leading-tight text-balance">
              Cập nhật thông tin để AI hiểu đúng bối cảnh của bạn
            </h1>
            <p className="text-sm leading-7 text-foreground/75 sm:text-base">
              Các thay đổi ở đây sẽ tác động trực tiếp đến Mentor AI, lộ trình học và độ sâu nội dung khi bạn khám phá chủ đề.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={resetForm} disabled={saving}>
              Khôi phục
            </Button>
            <Button onClick={handleSubmit} disabled={saving}>
              <Save className="mr-2 size-4" />
              {saving ? "Đang cập nhật..." : "Lưu hồ sơ"}
            </Button>
          </div>
        </div>
      </section>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {success ? (
        <Alert>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_360px]">
        <div className="space-y-6">
          <Card className="border border-border/70 bg-card/92">
            <CardHeader>
              <CardTitle className="text-2xl">Thông tin cơ bản</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-5 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Họ và tên</Label>
                <Input
                  value={form.full_name}
                  onChange={(event) => updateField("full_name", event.target.value)}
                  placeholder="Tên hiển thị trong DUO MIND"
                  className="h-11"
                />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input value={email ?? ""} readOnly className="h-11 bg-muted/35" />
              </div>

              <div className="space-y-3 md:col-span-2">
                <Label className="text-base font-medium">Độ tuổi</Label>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {AGE_RANGES.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => updateField("age_range", option.value)}
                      className={cn(
                        "rounded-2xl border px-4 py-3 text-left transition-colors",
                        form.age_range === option.value
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/35"
                      )}
                    >
                      <div className="font-medium">{option.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3 md:col-span-2">
                <Label className="text-base font-medium">Trạng thái hiện tại</Label>
                <div className="grid gap-3 sm:grid-cols-2">
                  {STATUS_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => updateField("status", option.value)}
                      className={cn(
                        "rounded-2xl border px-4 py-3 text-left transition-colors",
                        form.status === option.value
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/35"
                      )}
                    >
                      <div className="font-medium">{option.label}</div>
                      <div className="mt-1 text-sm text-muted-foreground">{option.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border border-border/70 bg-card/92">
            <CardHeader>
              <CardTitle className="text-2xl">Bối cảnh học tập và nghề nghiệp</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {isStudent ? (
                <div className="grid gap-5 rounded-[1.5rem] border border-sky-200/70 bg-sky-50/75 p-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Trình độ học tập</Label>
                    <Select
                      value={form.education_level ?? "__empty__"}
                      onValueChange={(value) =>
                        updateField(
                          "education_level",
                          value === "__empty__" ? undefined : (value as OnboardingData["education_level"])
                        )
                      }
                    >
                      <SelectTrigger className="h-11 w-full">
                        <SelectValue placeholder="Chọn trình độ học tập" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__empty__">Chưa chọn</SelectItem>
                        {EDUCATION_OPTIONS.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Chuyên ngành / môn học chính</Label>
                    <Input
                      value={form.major ?? ""}
                      onChange={(event) => updateField("major", event.target.value)}
                      placeholder="Ví dụ: Công nghệ thông tin, Kinh tế"
                      className="h-11"
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label>Trường học</Label>
                    <Input
                      value={form.school_name ?? ""}
                      onChange={(event) => updateField("school_name", event.target.value)}
                      placeholder="Tên trường hoặc nơi bạn đang học"
                      className="h-11"
                    />
                  </div>
                </div>
              ) : null}

              {isWorking ? (
                <div className="grid gap-5 rounded-[1.5rem] border border-emerald-200/70 bg-emerald-50/75 p-5 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Ngành nghề</Label>
                    <Input
                      value={form.industry ?? ""}
                      onChange={(event) => updateField("industry", event.target.value)}
                      placeholder="Ví dụ: Tài chính, Công nghệ, Marketing"
                      className="h-11"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Vị trí / chức danh</Label>
                    <Input
                      value={form.job_title ?? ""}
                      onChange={(event) => updateField("job_title", event.target.value)}
                      placeholder="Ví dụ: Data Analyst, Giáo viên"
                      className="h-11"
                    />
                  </div>

                  <div className="space-y-2 md:col-span-2">
                    <Label>Số năm kinh nghiệm</Label>
                    <Input
                      type="number"
                      min={0}
                      value={form.years_experience ?? ""}
                      onChange={(event) =>
                        updateField(
                          "years_experience",
                          event.target.value ? Number(event.target.value) : undefined
                        )
                      }
                      placeholder="Ví dụ: 2"
                      className="h-11"
                    />
                  </div>
                </div>
              ) : null}

              {!isStudent && !isWorking ? (
                <div className="rounded-[1.5rem] border border-border/70 bg-muted/30 p-5 text-sm leading-7 text-muted-foreground">
                  Bạn đang ở trạng thái linh hoạt. Hãy điền rõ mục tiêu, chủ đề quan tâm và phong cách học để AI cá nhân hóa tốt hơn.
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card className="border border-border/70 bg-card/92">
            <CardHeader>
              <CardTitle className="text-2xl">Mục tiêu và cách học</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-3">
                <Label className="text-base font-medium">Mục tiêu học tập</Label>
                <div className="grid gap-3 sm:grid-cols-2">
                  {GOAL_OPTIONS.map((option) => {
                    const selected = form.learning_goals?.includes(option.value)
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => toggleArrayValue("learning_goals", option.value)}
                        className={cn(
                          "rounded-2xl border px-4 py-3 text-left text-sm transition-colors",
                          selected
                            ? "border-primary bg-primary/5 font-medium"
                            : "border-border hover:border-primary/35"
                        )}
                      >
                        {option.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-base font-medium">Chủ đề bạn quan tâm</Label>
                <div className="grid gap-3 sm:grid-cols-2">
                  {TOPIC_OPTIONS.map((option) => {
                    const selected = form.topics_of_interest?.includes(option.value)
                    return (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => toggleArrayValue("topics_of_interest", option.value)}
                        className={cn(
                          "rounded-2xl border px-4 py-3 text-left text-sm transition-colors",
                          selected
                            ? "border-primary bg-primary/5 font-medium"
                            : "border-border hover:border-primary/35"
                        )}
                      >
                        {option.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-base font-medium">Phong cách học phù hợp nhất</Label>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {[
                    { value: "visual", label: "Trực quan" },
                    { value: "reading", label: "Đọc và ghi chú" },
                    { value: "practice", label: "Thực hành" },
                    { value: "mixed", label: "Kết hợp" },
                  ].map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() =>
                        updateField("learning_style", option.value as OnboardingData["learning_style"])
                      }
                      className={cn(
                        "rounded-2xl border px-4 py-3 text-left transition-colors",
                        form.learning_style === option.value
                          ? "border-primary bg-primary/5 font-medium"
                          : "border-border hover:border-primary/35"
                      )}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4 rounded-[1.5rem] border border-border/70 bg-background/70 p-5">
                <div className="space-y-2">
                  <Label className="text-base font-medium">
                    Thời gian học mỗi ngày: <span className="text-primary">{dailyStudyMinutes} phút</span>
                  </Label>
                  <p className="text-sm leading-7 text-muted-foreground">
                    Giá trị này ảnh hưởng trực tiếp đến độ sâu nội dung và tốc độ mentor xây lộ trình cho bạn.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  {DAILY_STUDY_PRESETS.map((minutes) => (
                    <button
                      key={minutes}
                      type="button"
                      onClick={() => updateField("daily_study_minutes", minutes)}
                      className={cn(
                        "rounded-full border px-3 py-1.5 text-sm transition-colors",
                        dailyStudyMinutes === minutes
                          ? "border-primary bg-primary/10 font-medium text-primary"
                          : "border-border hover:border-primary/35"
                      )}
                    >
                      {minutes} phút
                    </button>
                  ))}
                </div>

                <div className="rounded-2xl border border-border/70 bg-background px-4 py-4">
                  <Slider
                    value={[dailyStudyMinutes]}
                    onValueChange={([value]) => updateField("daily_study_minutes", value)}
                    min={10}
                    max={180}
                    step={5}
                  />
                  <div className="mt-3 flex justify-between text-xs text-muted-foreground">
                    <span>10 phút</span>
                    <span>180 phút</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {hasMeaningfulPersona ? (
            <Card className="border border-border/70 bg-card/92">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-2xl">
                  <Sparkles className="size-5 text-primary" />
                  Persona AI hiện tại
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm leading-7">
                <div className="rounded-[1.5rem] border border-primary/15 bg-primary/5 p-4">
                  <div className="font-medium text-primary">{aiResult?.ai_persona}</div>
                  {personaDescription ? (
                    <p className="mt-2 text-muted-foreground">{personaDescription}</p>
                  ) : null}
                </div>

                {recommendedTopics.length ? (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Chủ đề AI ưu tiên</div>
                    <div className="flex flex-wrap gap-2">
                      {recommendedTopics.map((topic) => (
                        <Badge key={topic} variant="secondary">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          <Card className="border border-border/70 bg-card/92">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <UserRound className="size-5 text-primary" />
                Tóm tắt hồ sơ
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm leading-7 text-foreground/78">
              <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
                <div className="font-medium text-foreground">Tài khoản</div>
                <p className="mt-1">{email || "Chưa có email"}</p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
                <div className="font-medium text-foreground">Ngày tham gia</div>
                <p className="mt-1">
                  {createdAt ? new Date(createdAt).toLocaleDateString("vi-VN") : "Chưa rõ"}
                </p>
              </div>
              <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
                <div className="font-medium text-foreground">Gợi ý sử dụng</div>
                <p className="mt-1 text-muted-foreground">
                  Sau khi cập nhật hồ sơ, hãy mở Mentor AI để hỏi về hướng nghề nghiệp hoặc sang Khám phá để xem nội dung học đã đổi theo hồ sơ mới như thế nào.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function buildPayload(form: ProfileEditorState): OnboardingData | null {
  if (!form.age_range || !form.status) {
    return null
  }

  if ((form.status === "student" || form.status === "both") && !form.education_level) {
    return null
  }

  if ((form.status === "student" || form.status === "both") && !form.major?.trim() && !form.school_name?.trim()) {
    return null
  }

  if ((form.status === "working" || form.status === "both") && !form.industry?.trim() && !form.job_title?.trim()) {
    return null
  }

  if (!form.learning_goals?.length || !form.topics_of_interest?.length) {
    return null
  }

  return {
    age_range: form.age_range,
    status: form.status,
    education_level: form.education_level,
    major: form.major?.trim() || undefined,
    school_name: form.school_name?.trim() || undefined,
    industry: form.industry?.trim() || undefined,
    job_title: form.job_title?.trim() || undefined,
    years_experience: form.years_experience ?? undefined,
    learning_goals: form.learning_goals ?? [],
    topics_of_interest: form.topics_of_interest ?? [],
    learning_style: form.learning_style ?? "mixed",
    daily_study_minutes: form.daily_study_minutes ?? 30,
  }
}

function sanitizePersonaDescription(description?: string | null) {
  if (!description) {
    return ""
  }

  const normalized = description.trim()
  const lower = normalized.toLowerCase()
  if (!normalized) {
    return ""
  }

  if (LOW_SIGNAL_PERSONA_PATTERNS.some((pattern) => lower.includes(pattern))) {
    return ""
  }

  return normalized
}

function sanitizeRecommendedTopics(topics: string[]) {
  return topics
    .map((topic) => topic.trim())
    .filter(Boolean)
    .filter((topic) => !GENERIC_TOPIC_VALUES.has(topic.toLowerCase()))
}
