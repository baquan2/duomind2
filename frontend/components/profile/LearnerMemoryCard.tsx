"use client"

import { BrainCircuit } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { MentorMemoryItem } from "@/types"

interface LearnerMemoryCardProps {
  mentorMemories: MentorMemoryItem[]
}

const MEMORY_TYPE_LABELS: Record<string, string> = {
  goal: "Mục tiêu",
  constraint: "Ràng buộc",
  skill: "Kỹ năng",
  career_interest: "Định hướng nghề nghiệp",
  preference: "Sở thích học",
  fact: "Thông tin đã biết",
  summary: "Tóm tắt bối cảnh",
}

const MEMORY_KEY_LABELS: Record<string, string> = {
  target_role: "Mục tiêu nghề nghiệp",
  desired_outcome: "Đầu ra mong muốn",
  current_focus: "Trọng tâm hiện tại",
  current_challenges: "Khó khăn hiện tại",
  learning_constraints: "Ràng buộc học tập",
  learning_style: "Phong cách học",
}

export function LearnerMemoryCard({ mentorMemories }: LearnerMemoryCardProps) {
  const topMemories = mentorMemories.slice(0, 6)

  return (
    <Card className="border border-border/70 bg-card/92">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <BrainCircuit className="size-5 text-primary" />
          Mentor đang ghi nhớ gì về bạn
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm leading-7 text-foreground/78">
        <div className="rounded-[1.5rem] border border-primary/15 bg-primary/5 p-4 text-muted-foreground">
          Bộ nhớ này được cập nhật từ onboarding, hồ sơ và các cuộc trò chuyện với mentor để giữ
          lại bối cảnh học tập thực tế của bạn.
        </div>

        {topMemories.length ? (
          <div className="grid gap-3">
            {topMemories.map((memory) => (
              <div
                key={memory.id}
                className="rounded-2xl border border-border/70 bg-background/80 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="font-medium text-foreground">
                      {labelForMemoryKey(memory.memory_key)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {labelForMemoryType(memory.memory_type)}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {typeof memory.confidence === "number" ? (
                      <Badge variant="secondary">{Math.round(memory.confidence * 100)}%</Badge>
                    ) : null}
                    {memory.updated_at ? (
                      <span className="text-xs text-muted-foreground">
                        {formatDate(memory.updated_at)}
                      </span>
                    ) : null}
                  </div>
                </div>
                <p className="mt-3 text-sm leading-7 text-foreground/78">
                  {formatMemoryValue(memory.memory_value)}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-border/70 bg-background/70 p-4 text-muted-foreground">
            Chưa có dữ liệu bộ nhớ nào được lưu. Sau khi bạn cập nhật hồ sơ hoặc trò chuyện với
            mentor, các mốc bối cảnh quan trọng sẽ hiện tại đây.
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function labelForMemoryType(memoryType: string) {
  return MEMORY_TYPE_LABELS[memoryType] ?? "Bối cảnh đã lưu"
}

function labelForMemoryKey(memoryKey: string) {
  return MEMORY_KEY_LABELS[memoryKey] ?? humanize(memoryKey)
}

function humanize(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function formatDate(value: string) {
  try {
    return new Date(value).toLocaleDateString("vi-VN")
  } catch {
    return value
  }
}

function formatMemoryValue(value: unknown): string {
  if (typeof value === "string") {
    return trimText(value)
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value)
  }

  if (Array.isArray(value)) {
    return trimText(
      value
        .map((item) => formatMemoryValue(item))
        .filter(Boolean)
        .join(", ")
    )
  }

  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>
    const preferredKeys = ["label", "value", "summary", "content", "text", "role", "goal", "name"]
    for (const key of preferredKeys) {
      const candidate = record[key]
      if (typeof candidate === "string" && candidate.trim()) {
        return trimText(candidate)
      }
    }

    return trimText(JSON.stringify(record))
  }

  return "Chưa có nội dung cụ thể"
}

function trimText(value: string, maxLength = 180) {
  const normalized = value.trim()
  if (normalized.length <= maxLength) {
    return normalized
  }

  return `${normalized.slice(0, maxLength - 3)}...`
}
