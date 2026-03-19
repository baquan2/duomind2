import { CircleHelp } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import type { QuizQuestion } from "@/types"
import { cn } from "@/lib/utils"

interface MultipleChoiceProps {
  question: QuizQuestion
  selectedAnswer?: string
  onAnswer: (answer: string) => void
}

export function MultipleChoice({
  question,
  selectedAnswer,
  onAnswer,
}: MultipleChoiceProps) {
  return (
    <Card className="border border-border/70 bg-card/92">
      <CardContent className="space-y-4 p-6">
        <div className="flex items-start gap-3">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <CircleHelp className="size-5" />
          </div>
          <div className="space-y-2">
            <span className="inline-flex rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-secondary-foreground">
              {question.difficulty}
            </span>
            <p className="text-base font-medium leading-7 text-foreground">
              {question.question_text}
            </p>
          </div>
        </div>

        <div className="space-y-2">
          {question.options?.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => onAnswer(option.id)}
              className={cn(
                "w-full rounded-2xl border px-4 py-3 text-left text-sm transition-all",
                selectedAnswer === option.id
                  ? "border-primary bg-primary/5 font-medium shadow-sm"
                  : "border-border bg-background hover:border-primary/40 hover:bg-muted/40"
              )}
            >
              <span className="mr-2 font-semibold text-primary">{option.id}.</span>
              {option.text}
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
