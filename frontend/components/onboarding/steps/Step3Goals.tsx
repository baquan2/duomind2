"use client"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import type { OnboardingData } from "@/types"

import { GOAL_OPTIONS, TARGET_ROLE_OPTIONS, TOPIC_OPTIONS } from "../options"

interface Step3GoalsProps {
  data: Partial<OnboardingData>
  onChange: (updates: Partial<OnboardingData>) => void
}

export function Step3Goals({ data, onChange }: Step3GoalsProps) {
  const toggleArray = (key: "learning_goals" | "topics_of_interest", value: string) => {
    const currentValues = data[key] ?? []
    const nextValues = currentValues.includes(value)
      ? currentValues.filter((item) => item !== value)
      : [...currentValues, value]

    onChange({ [key]: nextValues })
  }

  return (
    <div className="space-y-7">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Bước 3
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">Mục tiêu nghề nghiệp và ưu tiên học tập</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Đây là phần dữ liệu quan trọng nhất để DUO MIND suy ra persona, khoảng trống kỹ năng và bước học
            tiếp theo.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Vai trò bạn đang hướng tới</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {TARGET_ROLE_OPTIONS.map((option) => {
            const selected = data.target_role === option.value
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => onChange({ target_role: option.value })}
                className={cn(
                  "rounded-2xl border bg-card px-4 py-3 text-left transition-all",
                  selected ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
                )}
              >
                <div className="font-medium">{option.label}</div>
                <div className="mt-1 text-sm text-muted-foreground">{option.desc}</div>
              </button>
            )
          })}
        </div>

        <div className="space-y-2 rounded-[1.5rem] border border-dashed border-primary/30 bg-primary/5 p-4">
          <Label htmlFor="custom-target-role">Hoặc tự nhập hướng đi nghề nghiệp của bạn</Label>
          <Input
            id="custom-target-role"
            value={data.target_role ?? ""}
            onChange={(event) => onChange({ target_role: event.target.value })}
            placeholder="Ví dụ: Giáo viên tiếng Anh, Chuyên viên tuyển dụng, QA Engineer, UI/UX Designer..."
            className="h-11 bg-background"
          />
          <p className="text-sm leading-6 text-muted-foreground">
            Nếu mục tiêu của bạn chưa có trong danh sách, hãy nhập trực tiếp. DUO MIND sẽ dùng chính
            vai trò này để phân tích onboarding, mentor và roadmap.
          </p>
        </div>
      </div>

      <div className="space-y-4 rounded-[1.75rem] border border-border/70 bg-background/70 p-5">
        <div className="space-y-2">
          <Label className="text-base font-medium">Bối cảnh thực tế để mentor hiểu đúng bạn</Label>
          <p className="text-sm leading-6 text-muted-foreground">
            Càng cụ thể, AI càng dễ chốt đúng thứ bạn cần học và tránh trả lời lan man.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="desired-outcome">Đầu ra mong muốn trong ngắn hạn</Label>
            <Textarea
              id="desired-outcome"
              value={data.desired_outcome ?? ""}
              onChange={(event) => onChange({ desired_outcome: event.target.value })}
              placeholder="Ví dụ: Trong 3 tháng có thể apply intern Data Analyst với 2 project dashboard rõ ràng."
              className="min-h-[120px] rounded-2xl border-border/70 bg-background"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="current-focus">Bạn đang tập trung vào điều gì</Label>
            <Textarea
              id="current-focus"
              value={data.current_focus ?? ""}
              onChange={(event) => onChange({ current_focus: event.target.value })}
              placeholder="Ví dụ: Đang học SQL, ôn lại Excel và tìm cách làm dashboard đầu tiên."
              className="min-h-[120px] rounded-2xl border-border/70 bg-background"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="current-challenges">Khó khăn lớn nhất hiện tại</Label>
            <Textarea
              id="current-challenges"
              value={data.current_challenges ?? ""}
              onChange={(event) => onChange({ current_challenges: event.target.value })}
              placeholder="Ví dụ: Học dễ lan man, chưa biết nên học gì trước và chưa tự tin với tư duy phân tích."
              className="min-h-[120px] rounded-2xl border-border/70 bg-background"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="learning-constraints">Ràng buộc học tập cần tính tới</Label>
            <Textarea
              id="learning-constraints"
              value={data.learning_constraints ?? ""}
              onChange={(event) => onChange({ learning_constraints: event.target.value })}
              placeholder="Ví dụ: Chỉ có 45 phút mỗi ngày, đang vừa đi học vừa làm, chưa có thiết bị mạnh."
              className="min-h-[120px] rounded-2xl border-border/70 bg-background"
            />
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Mục tiêu học tập</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {GOAL_OPTIONS.map(({ value, label }) => {
            const selected = data.learning_goals?.includes(value)
            return (
              <button
                key={value}
                type="button"
                onClick={() => toggleArray("learning_goals", value)}
                className={cn(
                  "rounded-2xl border bg-card px-4 py-3 text-left text-sm transition-all",
                  selected
                    ? "border-primary bg-primary/5 font-medium"
                    : "border-border hover:border-primary/40"
                )}
              >
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-3">
        <Label className="text-base font-medium">Chủ đề quan tâm</Label>
        <div className="grid gap-3 sm:grid-cols-2">
          {TOPIC_OPTIONS.map(({ value, label }) => {
            const selected = data.topics_of_interest?.includes(value)
            return (
              <button
                key={value}
                type="button"
                onClick={() => toggleArray("topics_of_interest", value)}
                className={cn(
                  "rounded-2xl border bg-card px-4 py-3 text-left text-sm transition-all",
                  selected
                    ? "border-primary bg-accent/55 font-medium text-accent-foreground"
                    : "border-border hover:border-primary/40"
                )}
              >
                {label}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
