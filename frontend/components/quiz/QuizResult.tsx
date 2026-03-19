import { CircleCheckBig, ShieldAlert, Sparkles } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { QuizSubmissionResult } from "@/types"

interface QuizResultProps {
  result: QuizSubmissionResult
}

export function QuizResult({ result }: QuizResultProps) {
  const percentage = result.percentage || 0
  const isStrong = percentage >= 80
  const isOkay = percentage >= 60 && percentage < 80

  return (
    <Card className="border border-border/70 bg-card/92">
      <CardHeader className="items-center text-center">
        <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
          {isStrong ? (
            <Sparkles className="size-6" />
          ) : isOkay ? (
            <CircleCheckBig className="size-6" />
          ) : (
            <ShieldAlert className="size-6" />
          )}
        </div>
        <CardTitle className="font-display text-3xl font-semibold">
          {percentage}%
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          {result.score}/{result.total} cau dung
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-center text-sm text-foreground/85">
          {isStrong
            ? "Xuat sac. Ban dang nam kha vung nhung y chinh cua chu de nay."
            : isOkay
              ? "Ket qua kha tot. Ban nen xem lai mot vai diem de lap lai kien thuc."
              : "Ban can on them. Hãy quay lại phần tóm tắt và mind map trước khi làm lại quiz."}
        </p>

        <div className="space-y-2">
          {result.results.map((item, index) => (
            <div
              key={`${item.question_id}-${index}`}
              className={`rounded-2xl border px-4 py-3 text-sm ${
                item.is_correct
                  ? "border-emerald-200 bg-emerald-50/75"
                  : "border-rose-200 bg-rose-50/75"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium">
                  Cau {index + 1} {item.is_correct ? "dung" : "chua dung"}
                </span>
                <span className="text-xs text-muted-foreground">
                  Ban chon: {item.user_answer}
                </span>
              </div>
              <p className="mt-2 leading-6 text-foreground/80">{item.explanation}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
