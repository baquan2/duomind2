"use client"

import { BrainCircuit, ScanSearch } from "lucide-react"
import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"

import { AnalysisResult } from "@/components/analyze/AnalysisResult"
import { ContentInput } from "@/components/analyze/ContentInput"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { analyzeContent, analyzeFile } from "@/lib/api/analyze"
import { getApiErrorMessage } from "@/lib/api/errors"
import type { AnalyzeResult as AnalyzeResultData } from "@/types"

export default function AnalyzePage() {
  const searchParams = useSearchParams()
  const [result, setResult] = useState<AnalyzeResultData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prefilledContent = searchParams.get("content")?.trim() || ""

  useEffect(() => {
    if (!prefilledContent) {
      return
    }

    setResult(null)
    setError(null)
  }, [prefilledContent])

  const runAnalysis = async (runner: () => Promise<AnalyzeResultData>) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await runner()
      setResult(response)
    } catch (nextError) {
      setResult(null)
      setError(
        getApiErrorMessage(
          nextError,
          "Không thể phân tích nội dung lúc này. Vui lòng thử lại."
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeText = async (content: string, analysisGoal?: string) => {
    await runAnalysis(() => analyzeContent(content, "vi", analysisGoal))
  }

  const handleAnalyzeFile = async (file: File, analysisGoal?: string) => {
    await runAnalysis(() => analyzeFile(file, "vi", analysisGoal))
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[radial-gradient(circle_at_top_left,_rgba(255,217,102,0.35),_transparent_28%),linear-gradient(135deg,_rgba(15,118,110,0.12),_rgba(248,250,252,0.92))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative space-y-4">
          <Badge className="border-0 bg-primary text-primary-foreground">
            Milestone 3
          </Badge>
          <div className="max-w-3xl space-y-3">
            <h1 className="font-display text-4xl font-semibold text-balance">
              Phân tích độ chính xác của nội dung học tập theo cách dễ đọc hơn
            </h1>
            <p className="text-sm leading-7 text-foreground/75 sm:text-base">
              Dán nội dung hoặc tải file văn bản, hệ thống sẽ đánh giá độ tin cậy,
              tóm tắt trọng tâm, chỉ ra điểm cần đính chính và sinh mind map ngay
              trong cùng một phiên.
            </p>
          </div>
        </div>
      </section>

      <ContentInput
        onSubmitText={handleAnalyzeText}
        onSubmitFile={handleAnalyzeFile}
        loading={loading}
        initialContent={prefilledContent}
      />

      {prefilledContent ? (
        <Card className="border border-primary/20 bg-primary/5">
          <CardContent className="px-5 py-4 text-sm leading-7 text-foreground/82">
            Nội dung này được đưa từ roadmap hoặc mentor để bạn tự kiểm tra mức độ hiểu bài. Bạn có
            thể sửa lại ghi chú trước khi bấm <span className="font-medium text-foreground">Phân tích</span>.
          </CardContent>
        </Card>
      ) : null}

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {loading ? (
        <Card className="border border-border/70 bg-card/92">
          <CardContent className="space-y-3 px-6 py-12 text-center">
            <div className="mx-auto flex size-14 animate-soft-float items-center justify-center rounded-full bg-primary/10 text-primary">
              <BrainCircuit className="size-6" />
            </div>
            <h2 className="font-display text-2xl font-semibold">
              Đang phân tích nội dung
            </h2>
            <p className="text-sm text-muted-foreground">
              AI đang đọc dữ liệu đầu vào, đối chiếu độ chính xác, gom ý chính và
              chuẩn bị sơ đồ mind map cho phiên này.
            </p>
          </CardContent>
        </Card>
      ) : null}

      {!result && !loading ? (
        <Card className="border border-dashed border-border/70 bg-card/70">
          <CardContent className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
            <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <ScanSearch className="size-6" />
            </div>
            <div className="space-y-2">
              <h2 className="font-display text-2xl font-semibold">
                Sẵn sàng phân tích
              </h2>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Kết quả sẽ được trình bày theo từng khối rõ ràng gồm tổng quan,
                điểm chính, đính chính, mind map và khu vực ôn tập để bạn đọc nhanh
                hơn.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {result ? <AnalysisResult result={result} /> : null}
    </div>
  )
}
