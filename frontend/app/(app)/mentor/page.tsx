"use client"

import {
  Bot,
  Lightbulb,
  MessagesSquare,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Send,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import Link from "next/link"
import { useEffect, useMemo, useRef, useState } from "react"
import { useSearchParams } from "next/navigation"

import { MentorResponsePanels } from "@/components/mentor/MentorResponsePanels"
import { GOAL_OPTIONS, getOptionLabel } from "@/components/onboarding/options"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
  createMentorThread,
  getMentorSuggestedQuestions,
  getMentorThreadDetail,
  getMentorThreads,
  sendMentorMessage,
} from "@/lib/api/mentor"
import { getApiErrorMessage } from "@/lib/api/errors"
import { buildProfileReadiness } from "@/lib/learning-roadmap"
import { cn } from "@/lib/utils"
import type { MentorMessageItem, MentorThreadSummary, OnboardingData } from "@/types"

export default function MentorPage() {
  const searchParams = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const [threads, setThreads] = useState<MentorThreadSummary[]>([])
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<MentorMessageItem[]>([])
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([])
  const [onboarding, setOnboarding] = useState<Partial<OnboardingData> | null>(null)
  const [input, setInput] = useState("")
  const [loadingThreads, setLoadingThreads] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [sending, setSending] = useState(false)
  const [pendingOutboundMessage, setPendingOutboundMessage] = useState<string | null>(null)
  const [creatingThread, setCreatingThread] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showThreadPanel, setShowThreadPanel] = useState(false)
  const [showInsightPanel, setShowInsightPanel] = useState(false)

  const selectedThread = useMemo(
    () => threads.find((thread) => thread.id === selectedThreadId) ?? null,
    [selectedThreadId, threads]
  )
  const profileReadiness = useMemo(
    () => buildProfileReadiness(onboarding),
    [onboarding]
  )
  const pendingMessage = useMemo<MentorMessageItem | null>(() => {
    if (!sending || !pendingOutboundMessage?.trim()) {
      return null
    }

    return {
      id: "__pending_user_message__",
      thread_id: selectedThreadId ?? "__pending_thread__",
      role: "user",
      content: pendingOutboundMessage.trim(),
      created_at: new Date().toISOString(),
      sources: [],
    }
  }, [pendingOutboundMessage, selectedThreadId, sending])
  const displayedMessages = useMemo(
    () => (pendingMessage ? [...messages, pendingMessage] : messages),
    [messages, pendingMessage]
  )

  useEffect(() => {
    let mounted = true

    async function bootstrap() {
      try {
        const [threadData, questionData] = await Promise.all([
          getMentorThreads(),
          getMentorSuggestedQuestions(),
        ])

        if (!mounted) {
          return
        }

        setThreads(threadData)
        setSuggestedQuestions(questionData.questions)

        if (threadData.length) {
          const firstThreadId = threadData[0].id
          setSelectedThreadId(firstThreadId)
          await loadThread(firstThreadId, mounted)
        }
      } catch (apiError) {
        if (mounted) {
          setError(
            getApiErrorMessage(apiError, "Không thể tải mentor lúc này. Vui lòng thử lại.")
          )
        }
      } finally {
        if (mounted) {
          setLoadingThreads(false)
        }
      }
    }

    void bootstrap()

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const question = searchParams.get("question")?.trim()
    if (!question) {
      return
    }

    setInput((previous) => previous || question)
  }, [searchParams])

  useEffect(() => {
    if (!onboarding) {
      return
    }
    if (profileReadiness.missingItems.length) {
      setShowInsightPanel(true)
    }
  }, [onboarding, profileReadiness.missingItems.length])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [displayedMessages, sending])

  async function refreshThreads(nextSelectedId?: string | null) {
    const threadData = await getMentorThreads()
    setThreads(threadData)
    if (nextSelectedId) {
      setSelectedThreadId(nextSelectedId)
      return
    }
    if (!selectedThreadId && threadData.length) {
      setSelectedThreadId(threadData[0].id)
    }
  }

  async function loadThread(threadId: string, mountedOverride = true) {
    setLoadingMessages(true)
    setError(null)
    try {
      const detail = await getMentorThreadDetail(threadId)
      if (!mountedOverride) {
        return
      }
      setMessages(detail.messages)
      setSelectedThreadId(threadId)
    } catch (apiError) {
      if (mountedOverride) {
        setError(
          getApiErrorMessage(
            apiError,
            "Không thể tải lịch sử trò chuyện của phiên mentor này."
          )
        )
      }
    } finally {
      if (mountedOverride) {
        setLoadingMessages(false)
      }
    }
  }

  async function handleCreateThread() {
    setCreatingThread(true)
    setError(null)
    try {
      const thread = await createMentorThread("Phiên mentor mới")
      await refreshThreads(thread.id)
      setMessages([])
      setSelectedThreadId(thread.id)
      setShowThreadPanel(true)
    } catch (apiError) {
      setError(getApiErrorMessage(apiError, "Không thể tạo phiên mentor mới lúc này."))
    } finally {
      setCreatingThread(false)
    }
  }

  async function handleSendMessage(nextMessage?: string) {
    const message = (nextMessage ?? input).trim()
    if (!message || sending) {
      return
    }

    setSending(true)
    setPendingOutboundMessage(message)
    setError(null)

    try {
      const response = await sendMentorMessage(message, selectedThreadId)
      setMessages(response.messages)
      setInput("")
      setSelectedThreadId(response.thread_id)
      await refreshThreads(response.thread_id)
    } catch (apiError) {
      setError(
        getApiErrorMessage(
          apiError,
          "Không thể gửi câu hỏi tới mentor lúc này. Vui lòng thử lại."
        )
      )
    } finally {
      setSending(false)
      setPendingOutboundMessage(null)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-none flex-col gap-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.16),_rgba(255,247,221,0.88))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-[-2rem] top-[-2rem] h-44 w-44 rounded-full bg-primary/12 blur-3xl" />
        <div className="relative space-y-4">
          <Badge className="border-0 bg-primary text-primary-foreground">AI Mentor</Badge>
          <div className="max-w-4xl space-y-3">
            <h1 className="font-display text-4xl font-semibold leading-tight text-balance lg:text-5xl">
              Hỏi Mentor AI bất kỳ điều gì, từ kiến thức nền đến định hướng cá nhân
            </h1>
            <p className="max-w-3xl text-base leading-8 text-foreground/78">
              Giao diện này ưu tiên phần chat. Bạn có thể dùng Mentor như một trợ lý tri thức trả lời thẳng câu hỏi, hoặc kéo câu hỏi về hồ sơ, thị trường và lộ trình khi thực sự cần cá nhân hóa.
            </p>
          </div>
        </div>
      </section>

      {onboarding && profileReadiness.missingItems.length ? (
        <Alert>
          <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span>
              Mentor đã có thể trả lời, nhưng hồ sơ của bạn vẫn thiếu{" "}
              {profileReadiness.missingItems.slice(0, 3).join(", ")}. Bổ sung các mục này để
              câu trả lời khóa ưu tiên sát hơn.
            </span>
            <Button asChild size="sm" variant="outline" className="shrink-0">
              <Link href="/profile">Bổ sung hồ sơ</Link>
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card className="min-w-0 border border-border/70 bg-card/92">
        <CardHeader className="gap-4 border-b border-border/70 pb-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="space-y-2">
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Bot className="size-5 text-primary" />
                {selectedThread?.title || "Mentor chat"}
              </CardTitle>
              <p className="text-sm leading-7 text-muted-foreground">
                Có thể hỏi trực tiếp kiến thức nền trước. Khi câu hỏi cần cá nhân hóa, hãy thêm bối cảnh, mục tiêu và quỹ thời gian để mentor khóa ưu tiên sát hơn.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="outline" onClick={handleCreateThread} disabled={creatingThread}>
                <Plus className="mr-2 size-4" />
                Phiên mới
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="/roadmap">
                  <TrendingUp className="mr-2 size-4" />
                  Lộ trình
                </Link>
              </Button>
              <Button
                type="button"
                variant={showThreadPanel ? "secondary" : "outline"}
                size="sm"
                onClick={() => setShowThreadPanel((value) => !value)}
              >
                {showThreadPanel ? (
                  <PanelLeftClose className="mr-2 size-4" />
                ) : (
                  <PanelLeftOpen className="mr-2 size-4" />
                )}
                Phiên mentor
              </Button>
              <Button
                type="button"
                variant={showInsightPanel ? "secondary" : "outline"}
                size="sm"
                onClick={() => setShowInsightPanel((value) => !value)}
              >
                {showInsightPanel ? (
                  <PanelRightClose className="mr-2 size-4" />
                ) : (
                  <PanelRightOpen className="mr-2 size-4" />
                )}
                Tài nguyên phụ
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4 p-0">
          {showThreadPanel || showInsightPanel ? (
            <div className="space-y-3 border-b border-border/70 bg-muted/20 px-6 py-4">
              {showThreadPanel ? (
                <div className="space-y-3 rounded-2xl border border-emerald-200/70 bg-[linear-gradient(180deg,_rgba(240,253,250,0.98),_rgba(255,255,255,0.98))] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                      <MessagesSquare className="size-4 text-primary" />
                      Phiên mentor
                    </div>
                    <Button
                      size="icon-sm"
                      variant="ghost"
                      onClick={() => setShowThreadPanel(false)}
                      className="size-8 rounded-full"
                    >
                      <PanelLeftClose className="size-4" />
                    </Button>
                  </div>

                  <div className="flex gap-3 overflow-x-auto pb-1">
                    {loadingThreads ? (
                      [1, 2, 3].map((item) => (
                        <Skeleton key={item} className="h-24 min-w-[220px] rounded-2xl" />
                      ))
                    ) : threads.length ? (
                      threads.map((thread) => (
                        <button
                          key={thread.id}
                          type="button"
                          onClick={() => void loadThread(thread.id)}
                          className={cn(
                            "min-w-[220px] rounded-2xl border px-4 py-3 text-left transition-colors",
                            selectedThreadId === thread.id
                              ? "border-primary/40 bg-primary/8 shadow-sm"
                              : "border-border/70 bg-white hover:border-primary/25"
                          )}
                        >
                          <div className="line-clamp-2 text-sm font-semibold text-foreground">
                            {thread.title}
                          </div>
                          <div className="mt-2 text-xs text-muted-foreground">
                            {thread.last_message_at
                              ? new Date(thread.last_message_at).toLocaleString("vi-VN")
                              : "Chưa có tin nhắn"}
                          </div>
                        </button>
                      ))
                    ) : (
                      <div className="rounded-2xl border border-dashed border-border/70 bg-white px-4 py-6 text-sm text-muted-foreground">
                        Chưa có phiên mentor nào.
                      </div>
                    )}
                  </div>
                </div>
              ) : null}

              {showInsightPanel ? (
                <div className="space-y-2 rounded-2xl border border-amber-200/70 bg-[linear-gradient(180deg,_rgba(255,251,235,0.98),_rgba(255,255,255,0.98))] p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                      <Lightbulb className="size-4 text-primary" />
                      Tài nguyên phụ
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setShowInsightPanel(false)}
                      className="size-8 rounded-full"
                    >
                      <PanelRightClose className="size-4" />
                    </Button>
                  </div>

                  {onboarding ? (
                    <div className="grid gap-2 rounded-xl border border-border/70 bg-white/90 p-3 sm:grid-cols-2 xl:grid-cols-4">
                      <div>
                        <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                          Mục tiêu
                        </div>
                        <div className="mt-1 text-sm font-medium text-foreground">
                          {onboarding.target_role || "Chưa chốt rõ"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                          Quỹ học
                        </div>
                        <div className="mt-1 text-sm font-medium text-foreground">
                          {onboarding.daily_study_minutes
                            ? `${onboarding.daily_study_minutes} phút/ngày`
                            : "Chưa rõ"}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                          Trọng tâm
                        </div>
                        <div className="mt-1 text-sm font-medium text-foreground">
                          {getOptionLabel(onboarding.learning_goals?.[0], GOAL_OPTIONS)}
                        </div>
                      </div>
                      {onboarding.desired_outcome ? (
                        <div>
                          <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                            Đầu ra
                          </div>
                          <div className="mt-1 text-sm font-medium text-foreground">
                            {onboarding.desired_outcome}
                          </div>
                        </div>
                      ) : null}
                      {onboarding.current_challenges ? (
                        <div className="sm:col-span-2 xl:col-span-2">
                          <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                            Khó khăn hiện tại
                          </div>
                          <div className="mt-1 text-sm font-medium text-foreground">
                            {onboarding.current_challenges}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  <Tabs defaultValue="questions" className="gap-2">
                    <TabsList className="h-9 w-fit rounded-xl bg-background/85 p-1" variant="default">
                      <TabsTrigger value="questions" className="rounded-lg px-3 text-xs sm:text-sm">
                        Câu hỏi mẫu
                      </TabsTrigger>
                      <TabsTrigger value="advisor" className="rounded-lg px-3 text-xs sm:text-sm">
                        Mentor dùng gì
                      </TabsTrigger>
                    </TabsList>

                    <TabsContent value="questions" className="mt-0 space-y-2">
                      {suggestedQuestions.length ? (
                        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                          {suggestedQuestions.slice(0, 4).map((question) => (
                            <button
                              key={question}
                              type="button"
                              onClick={() => void handleSendMessage(question)}
                              className="rounded-xl border border-border/70 bg-white px-3 py-2.5 text-left text-[13px] leading-5 text-foreground/85 transition-colors hover:border-primary/30 hover:bg-primary/5"
                            >
                              <span className="line-clamp-3">{question}</span>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {[1, 2, 3, 4].map((item) => (
                            <Skeleton key={item} className="h-12 rounded-xl" />
                          ))}
                        </div>
                      )}
                    </TabsContent>

                    <TabsContent value="advisor" className="mt-0 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                      <div className="rounded-xl border border-border/70 bg-white px-3 py-2.5">
                        <div className="text-sm font-medium text-foreground">Hồ sơ</div>
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          Đọc profile để biết bối cảnh, ngành, quỹ học và mục tiêu.
                        </p>
                      </div>
                      <div className="rounded-xl border border-border/70 bg-white px-3 py-2.5">
                        <div className="text-sm font-medium text-foreground">Lịch sử & bộ nhớ</div>
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          Dùng các phiên trước để giảm hỏi lại và giảm trả lời chung chung.
                        </p>
                      </div>
                      <div className="rounded-xl border border-border/70 bg-white px-3 py-2.5">
                        <div className="text-sm font-medium text-foreground">Nguồn thực tế</div>
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          Nếu có tín hiệu thị trường hoặc web research, mentor sẽ dùng để trả lời chắc hơn.
                        </p>
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="h-[68vh] space-y-4 overflow-y-auto bg-[linear-gradient(180deg,_rgba(250,250,249,0.7),_rgba(255,255,255,1))] px-6 py-6">
            {loadingMessages ? (
              <div className="space-y-3">
                {[1, 2, 3].map((item) => (
                  <Skeleton key={item} className="h-28 rounded-2xl" />
                ))}
              </div>
            ) : displayedMessages.length ? (
              displayedMessages.map((message) => (
                <MessageCard
                  key={message.id}
                  message={message}
                  onFollowup={(question) => void handleSendMessage(question)}
                />
              ))
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Sparkles className="size-6" />
                </div>
                <div className="space-y-2">
                  <h2 className="font-display text-2xl font-semibold">Mentor đã sẵn sàng</h2>
                  <p className="max-w-2xl text-base leading-8 text-muted-foreground">
                    Hỏi một khái niệm, cơ chế, sự khác nhau giữa hai vai trò, hoặc kéo câu hỏi về hồ sơ của bạn khi cần. Mentor sẽ ưu tiên trả lời thẳng vào điều đang được hỏi trước.
                  </p>
                </div>
              </div>
            )}

            {sending ? <ThinkingBubble /> : null}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-border/70 bg-background/92 px-5 py-4">
            <div className="space-y-2.5">
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ví dụ: Business Analyst khác Product Analyst ở điểm nào? | SQL là gì và dùng khi nào? | Theo hồ sơ hiện tại của tôi, nên ưu tiên học gì trước?"
                className="min-h-[88px] resize-none border-primary/15 bg-background text-[15px] leading-6 shadow-none sm:min-h-[96px]"
                onKeyDown={(event) => {
                  if (event.key === "Enter" && event.ctrlKey) {
                    event.preventDefault()
                    void handleSendMessage()
                  }
                }}
              />
              <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-muted-foreground sm:text-sm">
                  Mẹo: nhấn <span className="font-medium text-foreground">Ctrl + Enter</span> để gửi nhanh.
                </p>
                <Button
                  onClick={() => void handleSendMessage()}
                  disabled={!input.trim() || sending}
                  size="sm"
                  className="h-10 rounded-full bg-primary px-4 hover:bg-primary/90"
                >
                  {sending ? "Mentor đang phân tích..." : "Gửi câu hỏi"}
                  <Send className="ml-2 size-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function MessageCard({
  message,
  onFollowup,
}: {
  message: MentorMessageItem
  onFollowup: (question: string) => void
}) {
  const isUser = message.role === "user"
  const payload = !isUser ? message.response_data : null

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[96%] rounded-3xl border px-5 py-4 shadow-sm",
          isUser
            ? "border-primary/15 bg-primary text-primary-foreground"
            : "border-border/70 bg-white"
        )}
      >
        <div className={cn("text-[15px] leading-8", !isUser && "whitespace-pre-wrap text-foreground/88")}>
          {message.content}
        </div>

        {!isUser && payload ? (
          <MentorResponsePanels
            payload={payload}
            intent={typeof message.intent === "string" ? message.intent : null}
            onFollowup={onFollowup}
          />
        ) : null}
      </div>
    </div>
  )
}

function ThinkingBubble() {
  return (
    <div className="flex justify-start">
      <div className="max-w-[70%] rounded-3xl border border-border/70 bg-white px-5 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Bot className="size-4" />
          </div>
          <div>
            <div className="text-sm font-medium text-foreground">Mentor đang suy nghĩ</div>
            <div className="mt-2 flex items-center gap-1">
              <span className="size-2.5 animate-bounce rounded-full bg-primary/65 [animation-delay:0ms]" />
              <span className="size-2.5 animate-bounce rounded-full bg-primary/65 [animation-delay:150ms]" />
              <span className="size-2.5 animate-bounce rounded-full bg-primary/65 [animation-delay:300ms]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
