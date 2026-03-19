"use client"

import { Lightbulb, Loader2, MessageCircleMore } from "lucide-react"
import { useState } from "react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { getApiErrorMessage } from "@/lib/api/errors"
import { getOpenFeedback } from "@/lib/api/quiz"
import type { OpenFeedbackResult, QuizQuestion } from "@/types"

interface OpenQuestionProps {
  question: QuizQuestion
}

export function OpenQuestion({ question }: OpenQuestionProps) {
  const [answer, setAnswer] = useState("")
  const [feedback, setFeedback] = useState<OpenFeedbackResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!answer.trim()) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await getOpenFeedback(question.id, answer)
      setFeedback(response)
    } catch (submissionError) {
      setError(getApiErrorMessage(submissionError, "Không thể đánh giá câu trả lời lúc này. Vui lòng thử lại."))
    } finally {
      setLoading(false)
    }
  }

  const score = feedback?.critical_thinking_score ?? 0
  const scoreColor =
    score >= 7 ? "text-emerald-600" : score >= 4 ? "text-amber-600" : "text-rose-600"

  return (
    <Card className="border border-primary/15 bg-card/92">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <MessageCircleMore className="size-5" />
          </div>
          <div className="space-y-2">
            <span className="inline-flex rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground">
              Tư duy phản biện
            </span>
            <p className="text-base font-medium leading-7 text-foreground">
              {question.question_text}
            </p>
          </div>
        </div>

        {question.thinking_hints?.length ? (
          <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-primary">
              <Lightbulb className="size-4" />
              Gợi ý suy nghĩ
            </div>
            <ul className="space-y-1 text-sm text-primary/80">
              {question.thinking_hints.map((hint, index) => (
                <li key={`${hint}-${index}`}>• {hint}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {!feedback ? (
          <>
            <Textarea
              placeholder="Viết cách bạn lập luận, đưa ví dụ hoặc phản biện quan điểm..."
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              className="min-h-[140px] resize-none bg-background"
            />

            {error ? (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            <Button onClick={handleSubmit} disabled={!answer.trim() || loading}>
              {loading ? (
                <>
                  Đang đánh giá
                  <Loader2 className="ml-2 size-4 animate-spin" />
                </>
              ) : (
                "Gửi câu trả lời"
              )}
            </Button>
          </>
        ) : (
          <div className="space-y-4">
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
                Câu trả lời của bạn
              </p>
              <p className="mt-2 text-sm leading-6 text-foreground/85">{answer}</p>
            </div>

            <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <p className="font-medium text-primary">Đánh giá từ AI</p>
                <span className={`text-2xl font-semibold ${scoreColor}`}>{score}/10</span>
              </div>
              <p className="text-sm leading-6 text-foreground/85">{feedback.ai_feedback}</p>

              {feedback.strengths?.length ? (
                <div className="mt-4">
                  <p className="text-sm font-medium text-emerald-700">Điểm mạnh</p>
                  <ul className="mt-2 space-y-1 text-sm text-emerald-700/85">
                    {feedback.strengths.map((item, index) => (
                      <li key={`${item}-${index}`}>• {item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {feedback.improvements?.length ? (
                <div className="mt-4">
                  <p className="text-sm font-medium text-amber-700">Cần cải thiện</p>
                  <ul className="mt-2 space-y-1 text-sm text-amber-700/85">
                    {feedback.improvements.map((item, index) => (
                      <li key={`${item}-${index}`}>• {item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
