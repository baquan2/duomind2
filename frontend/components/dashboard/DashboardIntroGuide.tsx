"use client"

import {
  BookCopy,
  Compass,
  History,
  LayoutDashboard,
  MessagesSquare,
  Sparkles,
  UserRound,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Progress } from "@/components/ui/progress"
import { createClient } from "@/lib/supabase/client"

const INTRO_GUIDE_STORAGE_KEY = "duomind_intro_guide_seen"

type IntroStep = {
  title: string
  subtitle: string
  icon: typeof LayoutDashboard
  accent: string
}

const INTRO_STEPS: IntroStep[] = [
  {
    title: "Tổng quan",
    subtitle: "Nhìn nhanh persona AI, phiên học gần đây và các lối tắt quan trọng.",
    icon: LayoutDashboard,
    accent: "from-emerald-500/20 to-teal-500/10",
  },
  {
    title: "Mentor AI",
    subtitle: "Hỏi về hướng nghiệp, kỹ năng còn thiếu và lộ trình học phù hợp với bạn.",
    icon: MessagesSquare,
    accent: "from-sky-500/20 to-cyan-500/10",
  },
  {
    title: "Khám phá",
    subtitle: "Học sâu một chủ đề mới với kiến thức chi tiết, ví dụ và mind map tổng quan.",
    icon: Compass,
    accent: "from-amber-500/20 to-orange-500/10",
  },
  {
    title: "Phân tích",
    subtitle: "Đưa nội dung của bạn vào để kiểm tra độ chính xác và làm sạch kiến thức.",
    icon: BookCopy,
    accent: "from-violet-500/20 to-fuchsia-500/10",
  },
  {
    title: "Lịch sử",
    subtitle: "Xem lại các phiên đã học, kết quả cũ và tiến trình của bạn theo thời gian.",
    icon: History,
    accent: "from-rose-500/20 to-pink-500/10",
  },
  {
    title: "Hồ sơ",
    subtitle: "Cập nhật lại thông tin cá nhân để mentor và hệ thống cá nhân hóa sát hơn.",
    icon: UserRound,
    accent: "from-lime-500/20 to-emerald-500/10",
  },
]

interface DashboardIntroGuideProps {
  userId: string
  displayName: string
  showInitially: boolean
}

export function DashboardIntroGuide({
  userId,
  displayName,
  showInitially,
}: DashboardIntroGuideProps) {
  const [open, setOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [persisting, setPersisting] = useState(false)
  const [hasMarkedSeen, setHasMarkedSeen] = useState(!showInitially)
  const storageKey = `${INTRO_GUIDE_STORAGE_KEY}:${userId}`

  useEffect(() => {
    if (!showInitially) {
      return
    }

    const storedValue = window.localStorage.getItem(storageKey)
    if (storedValue === "true") {
      setHasMarkedSeen(true)
      return
    }

    setOpen(true)
  }, [showInitially, storageKey])

  const step = INTRO_STEPS[currentStep]
  const progressValue = useMemo(
    () => ((currentStep + 1) / INTRO_STEPS.length) * 100,
    [currentStep]
  )

  const persistGuideSeen = async () => {
    window.localStorage.setItem(storageKey, "true")
    if (hasMarkedSeen) {
      return
    }

    setHasMarkedSeen(true)
    const supabase = createClient()
    await supabase.from("profiles").update({ has_seen_intro_tour: true }).eq("id", userId)
  }

  const closeGuide = async () => {
    setPersisting(true)
    try {
      await persistGuideSeen()
      setOpen(false)
      setCurrentStep(0)
    } finally {
      setPersisting(false)
    }
  }

  const handleNext = async () => {
    if (currentStep === INTRO_STEPS.length - 1) {
      await closeGuide()
      return
    }
    setCurrentStep((value) => value + 1)
  }

  const handleOpenGuide = () => {
    setCurrentStep(0)
    setOpen(true)
  }

  const Icon = step.icon

  return (
    <>
      <Button variant="outline" size="sm" onClick={handleOpenGuide}>
        <Sparkles className="mr-2 size-4" />
        Xem hướng dẫn nhanh
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent
          className="flex max-h-[88vh] max-w-xl flex-col overflow-hidden rounded-[1.75rem] border border-border/70 p-0"
          showCloseButton={false}
        >
          <div className="border-b border-border/70 bg-background/95 px-5 py-5 sm:px-6">
            <DialogHeader className="gap-3">
              <div className="flex items-center gap-2">
                <Badge className="border-0 bg-primary text-primary-foreground">Người dùng mới</Badge>
                <Badge variant="secondary">
                  Bước {currentStep + 1}/{INTRO_STEPS.length}
                </Badge>
              </div>
              <DialogTitle className="font-display text-2xl font-semibold leading-tight">
                Chào {displayName}, đây là bản hướng dẫn siêu nhanh của DUO MIND
              </DialogTitle>
              <DialogDescription className="text-sm leading-6 text-foreground/72">
                Mỗi bước chỉ tập trung vào đúng một chức năng để bạn nhìn là hiểu ngay app dùng
                như thế nào.
              </DialogDescription>
            </DialogHeader>
          </div>

          <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
            <div className={`rounded-[1.5rem] border border-border/70 bg-gradient-to-br ${step.accent} p-5`}>
              <div className="flex items-start gap-4">
                <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-background/85 text-primary shadow-sm">
                  <Icon className="size-5" />
                </div>
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                    Chức năng trọng tâm
                  </div>
                  <h2 className="font-display text-2xl font-semibold">{step.title}</h2>
                  <p className="text-sm leading-7 text-foreground/78">{step.subtitle}</p>
                </div>
              </div>
            </div>

            <div className="mt-5 space-y-3">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.18em] text-muted-foreground">
                <span>Tiến trình</span>
                <span>{Math.round(progressValue)}%</span>
              </div>
              <Progress value={progressValue} className="h-2" />
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2 sm:grid-cols-6">
              {INTRO_STEPS.map((item, index) => (
                <button
                  key={item.title}
                  type="button"
                  onClick={() => setCurrentStep(index)}
                  className={`rounded-xl border px-2 py-2 text-left text-xs transition-colors ${
                    index === currentStep
                      ? "border-primary bg-primary/8 text-primary"
                      : "border-border/70 bg-background text-muted-foreground hover:border-primary/30"
                  }`}
                >
                  {item.title}
                </button>
              ))}
            </div>
          </div>

          <DialogFooter className="border-t border-border/70 bg-background/95 px-5 py-4 sm:px-6">
            <Button variant="ghost" onClick={() => void closeGuide()} disabled={persisting}>
              Để sau
            </Button>
            <div className="flex flex-1 items-center justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setCurrentStep((value) => Math.max(0, value - 1))}
                disabled={currentStep === 0 || persisting}
              >
                Quay lại
              </Button>
              <Button onClick={() => void handleNext()} disabled={persisting}>
                {currentStep === INTRO_STEPS.length - 1 ? "Bắt đầu dùng app" : "Tiếp tục"}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
