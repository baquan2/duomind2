"use client"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { OnboardingData } from "@/types"

import { EDUCATION_OPTIONS } from "../options"

interface Step2DetailsProps {
  data: Partial<OnboardingData>
  onChange: (updates: Partial<OnboardingData>) => void
}

export function Step2Details({ data, onChange }: Step2DetailsProps) {
  const isStudent = data.status === "student" || data.status === "both"
  const isWorking = data.status === "working" || data.status === "both"

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="inline-flex rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Bước 2
        </div>
        <div>
          <h2 className="font-display text-2xl font-semibold">Thêm thông tin chi tiết</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Độ khó, ví dụ và cách diễn giải sẽ được điều chỉnh dựa trên nền tảng của
            bạn.
          </p>
        </div>
      </div>

      {isStudent ? (
        <div className="space-y-4 rounded-3xl border border-sky-200/70 bg-sky-50/70 p-5">
          <div>
            <p className="text-sm font-medium text-sky-800">Thông tin học tập</p>
            <p className="mt-1 text-sm text-sky-700/80">
              Dùng cho học sinh, sinh viên hoặc người đang vừa học vừa làm.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Trình độ</Label>
            <Select
              value={data.education_level ?? "__empty__"}
              onValueChange={(value) =>
                onChange({
                  education_level:
                    value === "__empty__"
                      ? undefined
                      : (value as OnboardingData["education_level"]),
                })
              }
            >
              <SelectTrigger className="w-full">
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
              placeholder="VD: Công nghệ thông tin, Y khoa, Kinh tế"
              value={data.major ?? ""}
              onChange={(event) => onChange({ major: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>Trường (tùy chọn)</Label>
            <Input
              placeholder="Tên trường của bạn"
              value={data.school_name ?? ""}
              onChange={(event) => onChange({ school_name: event.target.value })}
            />
          </div>
        </div>
      ) : null}

      {isWorking ? (
        <div className="space-y-4 rounded-3xl border border-emerald-200/70 bg-emerald-50/70 p-5">
          <div>
            <p className="text-sm font-medium text-emerald-800">Thông tin công việc</p>
            <p className="mt-1 text-sm text-emerald-700/80">
              AI sẽ ưu tiên tình huống và case study gần với bối cảnh nghề nghiệp.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Ngành nghề</Label>
            <Input
              placeholder="VD: Công nghệ, Y tế, Giáo dục, Marketing"
              value={data.industry ?? ""}
              onChange={(event) => onChange({ industry: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>Chức vụ / vị trí</Label>
            <Input
              placeholder="VD: Developer, Marketing Manager, Giáo viên"
              value={data.job_title ?? ""}
              onChange={(event) => onChange({ job_title: event.target.value })}
            />
          </div>
        </div>
      ) : null}

      {!isStudent && !isWorking ? (
        <div className="rounded-3xl border border-border bg-muted/40 p-5">
          <p className="text-sm text-muted-foreground">
            Bạn đã chọn trạng thái khác. Ở bước tiếp theo, bạn có thể mô tả mục tiêu và
            chủ đề mình muốn học để AI cá nhân hóa trải nghiệm.
          </p>
        </div>
      ) : null}
    </div>
  )
}
