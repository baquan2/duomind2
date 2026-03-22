"use client"

import { Bookmark, Clock3, FlaskConical, ScanSearch, Star } from "lucide-react"
import { useRouter } from "next/navigation"
import type { MouseEvent } from "react"
import { useState } from "react"

import { SessionActions } from "@/components/history/SessionActions"
import { Badge } from "@/components/ui/badge"
import { toggleBookmark } from "@/lib/api/history"
import { getAnalyzeVerdictMeta, normalizeAnalyzeVerdict } from "@/lib/analyze-verdict"
import { cn } from "@/lib/utils"
import type { LearningSession } from "@/types"


interface SessionCardProps {
  session: LearningSession
  onDeleted?: () => void
}


export function SessionCard({ session, onDeleted }: SessionCardProps) {
  const router = useRouter()
  const [bookmarked, setBookmarked] = useState(session.is_bookmarked)
  const [isUpdating, setIsUpdating] = useState(false)

  const isAnalyze = session.session_type === "analyze"
  const Icon = isAnalyze ? ScanSearch : FlaskConical
  const analyzeVerdict = isAnalyze
    ? session.session_subtype === "deep_dive"
      ? "deep_dive"
      : normalizeAnalyzeVerdict(
          session.verdict,
          session.accuracy_assessment,
          session.corrections?.length ?? 0,
          session.sources?.length ?? 0
        )
    : null
  const analyzeVerdictMeta = analyzeVerdict
    ? getAnalyzeVerdictMeta(analyzeVerdict)
    : null

  const handleBookmark = async (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    if (isUpdating) {
      return
    }

    setIsUpdating(true)
    try {
      const response = await toggleBookmark(session.id)
      setBookmarked(response.is_bookmarked)
    } finally {
      setIsUpdating(false)
    }
  }

  return (
    <article className="group rounded-2xl border border-border/70 bg-card/92 p-4 transition-all hover:border-primary/35 hover:shadow-md">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <button
            type="button"
            onClick={() => router.push(`/history/${session.id}`)}
            className="min-w-0 flex-1 space-y-3 text-left"
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge
                className={cn(
                  "border-0",
                  isAnalyze
                    ? "bg-sky-100 text-sky-800"
                    : "bg-emerald-100 text-emerald-800"
                )}
              >
                <Icon className="mr-1 size-3.5" />
                {isAnalyze ? "Phân tích" : "Khám phá"}
              </Badge>

              {isAnalyze && analyzeVerdictMeta ? (
                <Badge
                  variant="outline"
                  className={cn(
                    "bg-background",
                    analyzeVerdict === "correct"
                      ? "text-emerald-700"
                      : analyzeVerdict === "deep_dive"
                        ? "text-sky-700"
                        : "text-rose-700"
                  )}
                >
                  {analyzeVerdictMeta.shortLabel}
                </Badge>
              ) : null}
            </div>

            <div>
              <h3 className="truncate font-display text-xl font-semibold group-hover:text-primary">
                {session.title}
              </h3>
              {session.summary ? (
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">
                  {session.summary}
                </p>
              ) : null}
            </div>

            <div className="flex items-center justify-between gap-3">
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Clock3 className="size-3.5" />
                {new Date(session.created_at).toLocaleDateString("vi-VN")}
              </span>
              {session.session_subtype ? (
                <span className="text-xs text-muted-foreground">
                  Mode: {session.session_subtype}
                </span>
              ) : null}
            </div>
          </button>

          <button
            type="button"
            onClick={handleBookmark}
            disabled={isUpdating}
            className="rounded-full p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
            aria-label={bookmarked ? "Bỏ đánh dấu" : "Thêm đánh dấu"}
          >
            {bookmarked ? (
              <Star className="size-5 fill-current text-amber-500" />
            ) : (
              <Bookmark className="size-5" />
            )}
          </button>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-border/70 pt-3">
          <p className="text-xs text-muted-foreground">
            Bạn có thể xem lại, tải xuống hoặc mở trace của phiên học này.
          </p>
          <SessionActions
            sessionId={session.id}
            sessionTitle={session.title}
            onDeleteSuccess={onDeleted}
            compact
          />
        </div>
      </div>
    </article>
  )
}
