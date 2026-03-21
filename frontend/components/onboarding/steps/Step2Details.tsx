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
          <h2 className="font-display text-2xl font-semibold">Thêm bối cảnh hiện tại</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            DUO MIND cần biết bạn đang học hay làm trong môi trường nào để gợi ý ví dụ và roadmap
            sát thực tế hơn.
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
            <Label>Trình độ học tập</Label>
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
            <Label>Chuyên ngành hoặc môn học chính</Label>
            <Input
              placeholder="Ví dụ: Công nghệ thông tin, Y khoa, Kinh tế"
              value={data.major ?? ""}
              onChange={(event) => onChange({ major: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>Trường học</Label>
            <Input
              placeholder="Tên trường hoặc nơi bạn đang học"
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
              AI sẽ ưu tiên case study và ví dụ gần với bối cảnh nghề nghiệp hiện tại của bạn.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Ngành nghề</Label>
            <Input
              placeholder="Ví dụ: Công nghệ, Giáo dục, Marketing, Tài chính"
              value={data.industry ?? ""}
              onChange={(event) => onChange({ industry: event.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label>Chức danh hoặc vị trí hiện tại</Label>
            <Input
              placeholder="Ví dụ: Data Analyst, Giáo viên, QA Engineer"
              value={data.job_title ?? ""}
              onChange={(event) => onChange({ job_title: event.target.value })}
            />
          </div>
        </div>
      ) : null}

      {!isStudent && !isWorking ? (
        <div className="rounded-3xl border border-border bg-muted/40 p-5">
          <p className="text-sm text-muted-foreground">
            Bạn đang ở trạng thái linh hoạt. Ở bước tiếp theo, hãy mô tả rõ mục tiêu nghề nghiệp và
            đầu ra mong muốn để AI cá nhân hóa tốt hơn.
          </p>
        </div>
      ) : null}
    </div>
  )
}
