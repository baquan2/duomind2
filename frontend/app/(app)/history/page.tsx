"use client"

import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Brain, Filter, HistoryIcon } from "lucide-react"

import { KnowledgeReport } from "@/components/history/KnowledgeReport"
import { SessionCard } from "@/components/history/SessionCard"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { getKnowledgeReport, getSessions } from "@/lib/api/history"
import { cn } from "@/lib/utils"
import type { KnowledgeReport as KnowledgeReportData, LearningSession } from "@/types"

type SessionFilter = "all" | "analyze" | "explore"

const filterOptions: Array<{
  value: SessionFilter
  label: string
}> = [
  { value: "all", label: "Tất cả" },
  { value: "analyze", label: "Phân tích" },
  { value: "explore", label: "Khám phá" },
]

export default function HistoryPage() {
  const [activeFilter, setActiveFilter] = useState<SessionFilter>("all")
  const [reportLoading, setReportLoading] = useState(false)
  const [report, setReport] = useState<KnowledgeReportData | null>(null)
  const [reportError, setReportError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ["history-sessions"],
    queryFn: () => getSessions(),
  })

  const handleGenerateReport = async () => {
    setReportLoading(true)
    setReportError(null)
    try {
      const response = await getKnowledgeReport()
      setReport(response)
    } catch {
      setReportError("Không thể tạo báo cáo AI lúc này. Vui lòng thử lại.")
    } finally {
      setReportLoading(false)
    }
  }

  const handleSessionDeleted = () => {
    setReport(null)
    setReportError(null)
    void queryClient.invalidateQueries({ queryKey: ["history-sessions"] })
  }

  const sessions = data?.sessions ?? []
  const visibleSessions = sessions.filter((session) => {
    return activeFilter === "all" || session.session_type === activeFilter
  })

  const counts = {
    all: sessions.length,
    analyze: sessions.filter((session) => session.session_type === "analyze").length,
    explore: sessions.filter((session) => session.session_type === "explore").length,
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.08),_rgba(255,247,221,0.8))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative flex flex-col gap-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-3">
              <Badge className="border-0 bg-primary text-primary-foreground">
                Milestone 4
              </Badge>
              <h1 className="font-display text-4xl font-semibold text-balance">
                Lịch sử học tập và kho phiên học của bạn
              </h1>
              <p className="text-sm leading-7 text-foreground/75 sm:text-base">
                Xem lại các phiên phân tích, khám phá, đánh dấu những nội dung quan
                trọng và tải kết quả về máy khi cần lưu trữ.
              </p>
            </div>

            <Button onClick={handleGenerateReport} disabled={reportLoading}>
              {reportLoading ? "Đang phân tích..." : "Báo cáo AI"}
              <Brain className="ml-2 size-4" />
            </Button>
          </div>

          <div className="rounded-2xl border border-border/70 bg-background/80 p-2 shadow-sm backdrop-blur">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-2 px-2 text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                <Filter className="size-3.5" />
                Phân loại phiên
              </div>
              <div className="flex flex-wrap gap-2">
                {filterOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setActiveFilter(option.value)}
                    className={cn(
                      "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium transition-all",
                      activeFilter === option.value
                        ? "border-primary bg-primary text-primary-foreground shadow-sm"
                        : "border-border/70 bg-card text-foreground/75 hover:border-primary/30 hover:text-foreground"
                    )}
                  >
                    <span>{option.label}</span>
                    <span
                      className={cn(
                        "rounded-full px-1.5 py-0.5 text-xs",
                        activeFilter === option.value
                          ? "bg-primary-foreground/15 text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      {counts[option.value]}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {reportError ? (
        <Alert variant="destructive">
          <AlertDescription>{reportError}</AlertDescription>
        </Alert>
      ) : null}

      {report ? <KnowledgeReport report={report} /> : null}

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>
            Không thể tải lịch sử học tập lúc này. Vui lòng thử lại.
          </AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((item) => (
            <Skeleton key={item} className="h-32 rounded-2xl" />
          ))}
        </div>
      ) : visibleSessions.length ? (
        <div className="space-y-3">
          {visibleSessions.map((session: LearningSession) => (
            <SessionCard
              key={session.id}
              session={session}
              onDeleted={handleSessionDeleted}
            />
          ))}
        </div>
      ) : (
        <Card className="border border-dashed border-border/70 bg-card/70">
          <CardContent className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
            <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <HistoryIcon className="size-6" />
            </div>
            <div className="space-y-2">
              <h2 className="font-display text-2xl font-semibold">
                Chưa có phiên phù hợp
              </h2>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Sau khi bạn dùng Phân tích hoặc Khám phá, phiên học sẽ được lưu ở đây
                để xem lại, tải xuống hoặc xóa khi không còn cần thiết.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
