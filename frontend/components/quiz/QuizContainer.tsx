"use client"

import { BrainCircuit, Loader2, RotateCcw } from "lucide-react"
import { useMemo, useState } from "react"

import { OpenQuestion } from "@/components/quiz/OpenQuestion"
import { MultipleChoice } from "@/components/quiz/MultipleChoice"
import { QuizResult } from "@/components/quiz/QuizResult"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { getApiErrorMessage } from "@/lib/api/errors"
import { generateQuiz, submitQuiz } from "@/lib/api/quiz"
import type { QuizQuestion, QuizSubmissionResult } from "@/types"

interface QuizContainerProps {
  sessionId?: string | null
}

type Phase = "idle" | "loading" | "quiz" | "result"

export function QuizContainer({ sessionId }: QuizContainerProps) {
  const [phase, setPhase] = useState<Phase>("idle")
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitResult, setSubmitResult] = useState<QuizSubmissionResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const multipleChoiceQuestions = useMemo(
    () => questions.filter((question) => question.question_type === "multiple_choice"),
    [questions]
  )
  const openQuestions = useMemo(
    () => questions.filter((question) => question.question_type === "open"),
    [questions]
  )
  const currentQuestion = multipleChoiceQuestions[currentIndex]

  if (!sessionId) {
    return (
      <Card className="border border-border/70 bg-card/92">
        <CardContent className="flex flex-col items-center gap-3 px-6 py-12 text-center">
          <div className="flex size-14 items-center justify-center rounded-full bg-amber-100 text-amber-700">
            <BrainCircuit className="size-6" />
          </div>
          <div className="space-y-2">
            <h3 className="font-display text-2xl font-semibold">Chưa thể tạo quiz</h3>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              Kết quả AI đã có, nhưng phiên này chưa lưu được vào database nên quiz chưa khả dụng.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const activeSessionId = sessionId

  const handleStart = async () => {
    setPhase("loading")
    setError(null)
    setSubmitResult(null)
    setAnswers({})
    setCurrentIndex(0)

    try {
      const response = await generateQuiz(activeSessionId, 5)
      setQuestions(response.questions)

      const nextMcq = response.questions.filter(
        (question) => question.question_type === "multiple_choice"
      )

      if (nextMcq.length === 0) {
        setSubmitResult({
          attempt_id: "no-mcq",
          score: 0,
          total: 0,
          percentage: 0,
          results: [],
        })
        setPhase("result")
        return
      }

      setPhase("quiz")
    } catch (submissionError) {
      setError(getApiErrorMessage(submissionError, "Không thể tạo quiz lúc này. Vui lòng thử lại."))
      setPhase("idle")
    }
  }

  const handleAnswer = (questionId: string, answer: string) => {
    setAnswers((previous) => ({ ...previous, [questionId]: answer }))
  }

  const handleNext = async () => {
    if (currentIndex < multipleChoiceQuestions.length - 1) {
      setCurrentIndex((previous) => previous + 1)
      return
    }

    await handleSubmit()
  }

  const handleSubmit = async () => {
    setPhase("loading")
    setError(null)

    try {
      const response = await submitQuiz(
        activeSessionId,
        multipleChoiceQuestions
          .filter((question) => answers[question.id])
          .map((question) => ({
            question_id: question.id,
            user_answer: answers[question.id],
          }))
      )
      setSubmitResult(response)
      setPhase("result")
    } catch (submissionError) {
      setError(getApiErrorMessage(submissionError, "Không thể nộp bài quiz lúc này. Vui lòng thử lại."))
      setPhase("quiz")
    }
  }

  const progress = multipleChoiceQuestions.length
    ? ((currentIndex + 1) / multipleChoiceQuestions.length) * 100
    : 0

  if (phase === "idle") {
    return (
      <Card className="border border-border/70 bg-card/92">
        <CardContent className="flex flex-col items-center gap-4 px-6 py-12 text-center">
          <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
            <BrainCircuit className="size-6" />
          </div>
          <div className="space-y-2">
            <h3 className="font-display text-2xl font-semibold">Sẵn sàng làm quiz?</h3>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              Hệ thống sẽ tạo bộ câu hỏi trắc nghiệm và một vài câu hỏi mở dựa trên phiên học hiện tại.
            </p>
          </div>
          <Button onClick={handleStart}>Bắt đầu quiz</Button>
          {error ? (
            <Alert variant="destructive" className="w-full max-w-xl text-left">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
        </CardContent>
      </Card>
    )
  }

  if (phase === "loading") {
    return (
      <Card className="border border-border/70 bg-card/92">
        <CardContent className="flex flex-col items-center gap-3 px-6 py-12 text-center text-muted-foreground">
          <Loader2 className="size-6 animate-spin text-primary" />
          <p className="text-sm">AI đang tạo và chấm bộ câu hỏi cho phiên học này...</p>
        </CardContent>
      </Card>
    )
  }

  if (phase === "result" && submitResult) {
    return (
      <div className="space-y-6">
        <QuizResult result={submitResult} />

        {openQuestions.length ? (
          <div className="space-y-4">
            <div>
              <h3 className="font-display text-2xl font-semibold">Câu hỏi mở để đào sâu</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Phần này đánh giá cách lập luận và tư duy phản biện thay vì đúng sai tuyệt đối.
              </p>
            </div>
            {openQuestions.map((question) => (
              <OpenQuestion key={question.id} question={question} />
            ))}
          </div>
        ) : null}

        <Button variant="outline" onClick={handleStart}>
          Làm lại quiz
          <RotateCcw className="ml-2 size-4" />
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-2xl border border-border/70 bg-card/92 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium">
            Câu {currentIndex + 1}/{multipleChoiceQuestions.length}
          </p>
          <p className="text-sm text-muted-foreground">
            {multipleChoiceQuestions.length} trắc nghiệm + {openQuestions.length} tự luận
          </p>
        </div>
        <div className="w-full sm:max-w-xs">
          <Progress value={progress} className="h-2" />
        </div>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {currentQuestion ? (
        <MultipleChoice
          question={currentQuestion}
          selectedAnswer={answers[currentQuestion.id]}
          onAnswer={(answer) => handleAnswer(currentQuestion.id, answer)}
        />
      ) : null}

      <Button
        onClick={() => void handleNext()}
        className="w-full"
        disabled={!currentQuestion || !answers[currentQuestion.id]}
      >
        {currentIndex < multipleChoiceQuestions.length - 1 ? "Câu tiếp theo" : "Nộp bài"}
      </Button>
    </div>
  )
}
