"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, CalendarDays, ChevronDown, ChevronUp } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"

import { AnalysisResult } from "@/components/analyze/AnalysisResult"
import { ExploreResultView } from "@/components/explore/ExploreResultView"
import { SessionActions } from "@/components/history/SessionActions"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { getSessionDetail } from "@/lib/api/history"
import {
  mapSessionToAnalyzeResult,
  mapSessionToExploreResult,
} from "@/lib/session-mappers"


export default function HistoryDetailPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const sessionId = params.id
  const [showTrace, setShowTrace] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ["history-session", sessionId],
    queryFn: () => getSessionDetail(sessionId),
    enabled: Boolean(sessionId),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-36 rounded-xl" />
        <Skeleton className="h-40 rounded-3xl" />
        <Skeleton className="h-96 rounded-3xl" />
      </div>
    )
  }

  if (error || !data?.session) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Không thể tải chi tiết phiên này. Vui lòng thử lại.
        </AlertDescription>
      </Alert>
    )
  }

  const session = data.session
  const traceBlocks = [
    {
      title: "Raw input",
      content: session.user_input || "Không có dữ liệu đầu vào.",
    },
    {
      title: "Request payload",
      content: prettyJson(session.request_payload),
    },
    {
      title: "Context snapshot",
      content: prettyJson(session.context_snapshot),
    },
    {
      title: "Generation trace",
      content: prettyJson(session.generation_trace),
    },
  ]

  return (
    <div className="space-y-6">
      <Button asChild variant="outline">
        <Link href="/history">
          <ArrowLeft className="mr-2 size-4" />
          Quay lại lịch sử
        </Link>
      </Button>

      <Card className="border border-border/70 bg-card/92">
        <CardContent className="space-y-5 p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge className="border-0 bg-primary text-primary-foreground">
                  {session.session_type === "analyze"
                    ? "Phiên phân tích"
                    : "Phiên khám phá"}
                </Badge>
                {session.session_subtype ? (
                  <Badge variant="outline" className="bg-background">
                    Mode: {session.session_subtype}
                  </Badge>
                ) : null}
                <Badge variant="outline" className="bg-background">
                  <CalendarDays className="mr-1 size-3.5" />
                  {new Date(session.created_at).toLocaleString("vi-VN")}
                </Badge>
              </div>

              <div className="space-y-3">
                <h1 className="font-display text-3xl font-semibold text-balance">
                  {session.title}
                </h1>
                {session.topic_tags?.length ? (
                  <div className="flex flex-wrap gap-2">
                    {session.topic_tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>

            <SessionActions
              sessionId={session.id}
              sessionTitle={session.title}
              showViewButton={false}
              onDeleteSuccess={() => router.push("/history")}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="border border-border/70 bg-card/92">
        <CardContent className="space-y-4 p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-xl font-semibold">Trace và dữ liệu đã lưu</h2>
              <p className="text-sm leading-6 text-muted-foreground">
                Mở phần này để xem raw input, context đã dùng, nguồn và các cờ rewrite/fallback.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowTrace((value) => !value)}
            >
              {showTrace ? (
                <>
                  Ẩn trace
                  <ChevronUp className="ml-2 size-4" />
                </>
              ) : (
                <>
                  Hiện trace
                  <ChevronDown className="ml-2 size-4" />
                </>
              )}
            </Button>
          </div>

          {showTrace ? (
            <div className="grid gap-4">
              {traceBlocks.map((block) => (
                <div
                  key={block.title}
                  className="rounded-2xl border border-border/70 bg-background/80 p-4"
                >
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                    {block.title}
                  </p>
                  <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words rounded-xl bg-muted/35 p-3 text-xs leading-6 text-foreground/88">
                    {block.content}
                  </pre>
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      {session.session_type === "analyze" ? (
        <AnalysisResult result={mapSessionToAnalyzeResult(session)} />
      ) : (
        <ExploreResultView result={mapSessionToExploreResult(session)} showHeader={false} />
      )}
    </div>
  )
}


function prettyJson(value: unknown) {
  if (!value) {
    return "Không có dữ liệu."
  }

  if (typeof value === "string") {
    return value
  }

  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}
