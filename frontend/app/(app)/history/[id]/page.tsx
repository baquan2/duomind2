"use client"

import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, CalendarDays } from "lucide-react"
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
                <Badge variant="outline" className="bg-background">
                  <CalendarDays className="mr-1 size-3.5" />
                  {new Date(session.created_at).toLocaleString("vi-VN")}
                </Badge>
              </div>

              <div className="space-y-3">
                <h1 className="font-display text-3xl font-semibold text-balance">
                  {session.title}
                </h1>
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

      {session.session_type === "analyze" ? (
        <AnalysisResult result={mapSessionToAnalyzeResult(session)} />
      ) : (
        <ExploreResultView result={mapSessionToExploreResult(session)} showHeader={false} />
      )}
    </div>
  )
}
