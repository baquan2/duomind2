"use client"

import { motion } from "framer-motion"
import { Compass, Sparkles, Wand2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"

import { ExploreResultView } from "@/components/explore/ExploreResultView"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { exploreTopicApi } from "@/lib/api/analyze"
import { getApiErrorMessage } from "@/lib/api/errors"
import type { ExploreResult } from "@/types"

const EXAMPLE_PROMPTS = [
  "Trí tuệ nhân tạo là gì và hoạt động như thế nào?",
  "Blockchain và tiền mã hóa khác nhau ở đâu?",
  "Biến đổi khí hậu ảnh hưởng đến kinh tế như thế nào?",
  "Thị trường chứng khoán vận hành ra sao?",
]

const OUTPUT_GUIDE = [
  {
    title: "Tổng quan chủ đề",
    description: "AI gom ý chính để bạn nắm được bức tranh tổng thể trước.",
  },
  {
    title: "Chi tiết kiến thức",
    description: "Chủ đề được giải thích theo đúng trọng tâm: khái niệm, cơ chế, ví dụ và ứng dụng.",
  },
  {
    title: "Mind map toàn cảnh",
    description: "Sơ đồ khái niệm được dựng ngay sau khi có kết quả để bạn học có cấu trúc hơn.",
  },
]

export default function ExplorePage() {
  const searchParams = useSearchParams()
  const [prompt, setPrompt] = useState("")
  const [result, setResult] = useState<ExploreResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prefilledPrompt = searchParams.get("prompt")?.trim() || ""

  useEffect(() => {
    if (!prefilledPrompt) {
      return
    }

    setPrompt(prefilledPrompt)
    setResult(null)
    setError(null)
  }, [prefilledPrompt])

  const handleExplore = async (nextPrompt?: string) => {
    const query = (nextPrompt ?? prompt).trim()
    if (!query) {
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await exploreTopicApi(query)
      setResult(response)
      setPrompt(query)
    } catch (apiError) {
      setError(getApiErrorMessage(apiError, "Không thể khám phá chủ đề lúc này. Vui lòng thử lại."))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.12),_rgba(255,247,221,0.82))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-0 top-0 h-44 w-44 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative space-y-4">
          <Badge className="border-0 bg-primary text-primary-foreground">Milestone 2</Badge>
          <div className="max-w-3xl space-y-3">
            <h1 className="font-display text-4xl font-semibold text-balance">
              Explore để nắm nền tảng và tổng quan của một chủ đề
            </h1>
            <p className="text-sm leading-7 text-foreground/75 sm:text-base">
              Explore ưu tiên breadth-first: giúp bạn nắm định nghĩa, ranh giới, cơ chế, ví dụ và
              nhầm lẫn phổ biến trước khi chuyển sang đào sâu.
            </p>
          </div>
        </div>
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Compass className="size-5 text-primary" />
              Nhập chủ đề cần khám phá
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <Textarea
              placeholder="Ví dụ: AI là gì? | Lạm phát vận hành như thế nào? | SQL khác NoSQL ở đâu?"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              className="min-h-[180px] resize-none bg-background"
              onKeyDown={(event) => {
                if (event.key === "Enter" && event.ctrlKey) {
                  event.preventDefault()
                  void handleExplore()
                }
              }}
            />

            {prefilledPrompt ? (
              <div className="rounded-2xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm leading-6 text-foreground/82">
                Prompt này được đưa từ roadmap hoặc mentor. Bạn có thể chỉnh lại trước khi bấm{" "}
                <span className="font-medium text-foreground">Khám phá</span>.
              </div>
            ) : null}

            <div className="space-y-3">
              <p className="text-sm font-medium">Prompt mẫu</p>
              <div className="grid gap-2 sm:grid-cols-2">
                {EXAMPLE_PROMPTS.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => void handleExplore(example)}
                    className="rounded-2xl border border-border/70 bg-background px-4 py-3 text-left text-sm transition-colors hover:border-primary/40 hover:bg-primary/5"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-3 border-t border-border/70 pt-4 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-muted-foreground">
                Mẹo: nhấn <span className="font-medium text-foreground">Ctrl + Enter</span> để gửi nhanh.
              </p>
              <Button
                onClick={() => void handleExplore()}
                disabled={!prompt.trim() || loading}
                className="min-w-40"
              >
                {loading ? "Đang khám phá..." : "Khám phá"}
                <Wand2 className="ml-2 size-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl">
              <Sparkles className="size-5 text-primary" />
              Kết quả bạn sẽ nhận
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {OUTPUT_GUIDE.map((item, index) => (
              <div key={item.title} className="rounded-2xl border border-border/70 bg-background/80 p-4">
                <div className="mb-2 inline-flex size-8 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                  {index + 1}
                </div>
                <h3 className="font-medium">{item.title}</h3>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.description}</p>
              </div>
            ))}
            <div className="rounded-2xl border border-dashed border-primary/25 bg-primary/5 p-4 text-sm leading-6 text-foreground/80">
              Explore tập trung vào <span className="font-medium">tổng quan + nền tảng + mind map</span>.
              Khi cần đi hẹp và chặt hơn, hãy chuyển sang Analyze ở chế độ{" "}
              <span className="font-medium">Đào sâu</span>.
            </div>
          </CardContent>
        </Card>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {!result && !loading ? (
        <Card className="border border-dashed border-border/70 bg-card/70">
          <CardContent className="flex flex-col items-center justify-center gap-3 px-6 py-14 text-center">
            <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Sparkles className="size-6" />
            </div>
            <div className="space-y-2">
              <h2 className="font-display text-2xl font-semibold">Chưa có chủ đề nào được mở ra</h2>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
                Chọn một prompt mẫu hoặc nhập câu hỏi riêng của bạn. Kết quả sẽ được chia theo
                từng phần rõ ràng để dễ đọc, dễ hiểu và dễ quay lại.
              </p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {loading ? (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid gap-4 lg:grid-cols-3"
        >
          {[
            "Đọc và hiểu prompt",
            "Giải thích đúng trọng tâm",
            "Dựng mind map cho cùng phiên học",
          ].map((label, index) => (
            <Card key={label} className="border border-border/70 bg-card/92">
              <CardContent className="space-y-3 p-5">
                <div className="inline-flex size-10 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary">
                  {index + 1}
                </div>
                <p className="font-medium">{label}</p>
                <p className="text-sm leading-6 text-muted-foreground">
                  Hệ thống đang xử lý bước này bằng Gemini và ghép thêm nguồn nếu chủ đề cần tra cứu.
                </p>
              </CardContent>
            </Card>
          ))}
        </motion.div>
      ) : null}

      {result ? <ExploreResultView result={result} /> : null}
    </div>
  )
}
