"use client"

import {
  Bot,
  BriefcaseBusiness,
  GraduationCap,
  Lightbulb,
  Link2,
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
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { useSearchParams } from "next/navigation"

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
import { cn } from "@/lib/utils"
import type { MentorMessageItem, MentorThreadSummary } from "@/types"

export default function MentorPage() {
  const searchParams = useSearchParams()
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const [threads, setThreads] = useState<MentorThreadSummary[]>([])
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<MentorMessageItem[]>([])
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([])
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
              Hỏi mentor về nghề nghiệp, kỹ năng và lộ trình học theo đúng bối cảnh của bạn
            </h1>
            <p className="max-w-3xl text-base leading-8 text-foreground/78">
              Giao diện này ưu tiên phần chat. Phiên mentor và tài nguyên phụ chỉ mở khi bạn cần, để trải nghiệm trò chuyện thoáng và dễ tập trung hơn.
            </p>
          </div>
        </div>
      </section>

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
                Hỏi rõ bối cảnh, mục tiêu và quỹ thời gian của bạn để mentor trả lời sát hơn.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="outline" onClick={handleCreateThread} disabled={creatingThread}>
                <Plus className="mr-2 size-4" />
                Phiên mới
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
                    Hỏi về vị trí nghề nghiệp, cơ hội phát triển, kỹ năng còn thiếu hoặc lộ trình học phù hợp với hồ sơ của bạn.
                  </p>
                </div>
              </div>
            )}

            {sending ? <ThinkingBubble /> : null}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-border/70 p-6">
            <div className="space-y-3">
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ví dụ: Tôi đang học ngành Tài chính, muốn theo Data Analyst thì nên học gì trước và thị trường đang yêu cầu những kỹ năng nào?"
                className="min-h-[150px] resize-none border-primary/15 bg-background text-base leading-7"
                onKeyDown={(event) => {
                  if (event.key === "Enter" && event.ctrlKey) {
                    event.preventDefault()
                    void handleSendMessage()
                  }
                }}
              />
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Mẹo: nhấn <span className="font-medium text-foreground">Ctrl + Enter</span> để gửi nhanh.
                </p>
                <Button
                  onClick={() => void handleSendMessage()}
                  disabled={!input.trim() || sending}
                  className="bg-primary hover:bg-primary/90"
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
          <div className="mt-4 space-y-4 border-t border-border/70 pt-4">
            {payload.career_paths?.length ? (
              <InsightSection
                title="Hướng nghề gợi ý"
                icon={<BriefcaseBusiness className="size-4" />}
                items={payload.career_paths.map(
                  (item) => `${item.role}: ${item.fit_reason} | Bước tiếp: ${item.next_step}`
                )}
              />
            ) : null}

            {payload.skill_gaps?.length ? (
              <InsightSection
                title="Kỹ năng nên ưu tiên"
                icon={<GraduationCap className="size-4" />}
                items={payload.skill_gaps.map((item) => `${item.skill}: ${item.suggested_action}`)}
              />
            ) : null}

            {payload.recommended_learning_steps?.length ? (
              <InsightSection
                title="Bước học tiếp"
                icon={<Lightbulb className="size-4" />}
                items={payload.recommended_learning_steps}
              />
            ) : null}

            {payload.market_signals?.length ? (
              <InsightSection
                title="Tín hiệu thị trường"
                icon={<TrendingUp className="size-4" />}
                items={payload.market_signals.map(
                  (item) => `${item.role_name}: ${item.demand_summary}`
                )}
              />
            ) : null}

            {payload.sources?.length ? (
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
                  Nguồn tham khảo
                </p>
                <div className="space-y-2">
                  {payload.sources.map((source) => (
                    <a
                      key={`${source.label}-${source.url}`}
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-2 rounded-2xl border border-border/70 bg-muted/20 px-3 py-2.5 text-sm leading-6 text-foreground/80 transition-colors hover:border-primary/30 hover:bg-primary/5"
                    >
                      <Link2 className="size-4 text-primary" />
                      <span className="line-clamp-2">{source.label}</span>
                    </a>
                  ))}
                </div>
              </div>
            ) : null}

            {payload.suggested_followups?.length ? (
              <div className="space-y-2">
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-primary">
                  Gợi ý hỏi tiếp
                </p>
                <div className="flex flex-wrap gap-2">
                  {payload.suggested_followups.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => onFollowup(question)}
                      className="rounded-full border border-border/70 bg-background px-3 py-1.5 text-xs text-foreground/80 transition-colors hover:border-primary/30 hover:bg-primary/5"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}

function InsightSection({
  title,
  icon,
  items,
}: {
  title: string
  icon: ReactNode
  items: string[]
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-primary">
        {icon}
        {title}
      </div>
      <div className="space-y-2">
        {items.map((item) => (
          <div
            key={item}
            className="rounded-2xl border border-border/70 bg-muted/20 px-3 py-2.5 text-[15px] leading-7 text-foreground/82"
          >
            {item}
          </div>
        ))}
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
