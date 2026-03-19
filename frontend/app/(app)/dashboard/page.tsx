import { ArrowRight, BrainCircuit, History, Sparkles, Telescope } from "lucide-react"
import Link from "next/link"
import { redirect } from "next/navigation"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { createClient } from "@/lib/supabase/server"

const quickActions = [
  {
    href: "/analyze",
    title: "Phân tích kiến thức",
    description: "Chấm độ chính xác, tóm tắt và tạo mind map từ nội dung của bạn.",
    icon: BrainCircuit,
  },
  {
    href: "/explore",
    title: "Khám phá chủ đề",
    description: "Hỏi AI bất kỳ chủ đề nào để nhận infographic, mind map và quiz.",
    icon: Telescope,
  },
  {
    href: "/history",
    title: "Xem lịch sử học",
    description: "Theo dõi phiên học, đánh dấu bookmark và xin báo cáo AI.",
    icon: History,
  },
]

export default async function DashboardPage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const [profileResponse, onboardingResponse, sessionsResponse] = await Promise.all([
    supabase
      .from("profiles")
      .select("full_name, created_at")
      .eq("id", user.id)
      .maybeSingle(),
    supabase
      .from("user_onboarding")
      .select("ai_persona, ai_persona_description")
      .eq("user_id", user.id)
      .maybeSingle(),
    supabase
      .from("learning_sessions")
      .select("id, title, session_type, created_at")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(3),
  ])

  const profile = profileResponse.data
  const onboarding = onboardingResponse.data
  const recentSessions = sessionsResponse.data ?? []
  const displayName =
    profile?.full_name || user.user_metadata?.full_name || user.email?.split("@")[0] || "bạn"

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[radial-gradient(circle_at_top_left,_rgba(255,217,102,0.36),_transparent_30%),linear-gradient(135deg,_rgba(15,118,110,0.16),_rgba(248,250,252,0.94))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-[-2rem] top-[-2rem] h-44 w-44 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative space-y-4">
          <Badge className="border-0 bg-primary text-primary-foreground">Tổng quan</Badge>
          <div className="max-w-3xl space-y-3">
            <h1 className="font-display text-4xl font-semibold text-balance">
              Xin chào, {displayName}
            </h1>
            <p className="text-sm leading-7 text-foreground/75 sm:text-base">
              Bạn đã hoàn thành onboarding và sẵn sàng cho các flow phân tích, khám phá
              và quiz.
            </p>
          </div>

          {onboarding?.ai_persona ? (
            <div className="inline-flex max-w-3xl flex-col gap-2 rounded-2xl border border-white/20 bg-white/50 px-4 py-3 backdrop-blur">
              <span className="inline-flex items-center gap-2 text-sm font-medium text-primary">
                <Sparkles className="size-4" />
                Chân dung AI: {onboarding.ai_persona}
              </span>
              {onboarding.ai_persona_description ? (
                <p className="text-sm text-foreground/75">
                  {onboarding.ai_persona_description}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        {quickActions.map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.href} className="border border-border/70 bg-card/92">
              <CardHeader>
                <div className="mb-2 inline-flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </div>
                <CardTitle>{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild>
                  <Link href={item.href}>
                    Mở tính năng
                    <ArrowRight className="ml-2 size-4" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <Card className="border border-border/70 bg-card/92">
        <CardHeader>
          <CardTitle>Phiên học gần đây</CardTitle>
          <CardDescription>
            {recentSessions.length
              ? "Tiếp tục từ các buổi học mới nhất của bạn."
              : "Chưa có phiên nào. Hãy bắt đầu với Phân tích hoặc Khám phá."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {recentSessions.length ? (
            recentSessions.map((session) => (
              <Link
                key={session.id}
                href={`/history/${session.id}`}
                className="flex items-center justify-between rounded-2xl border border-border/70 bg-background/75 px-4 py-3 transition-colors hover:border-primary/35"
              >
                <div>
                  <div className="font-medium">{session.title}</div>
                  <div className="mt-1 text-sm text-muted-foreground">
                    {session.session_type === "analyze" ? "Phân tích" : "Khám phá"} |{" "}
                    {new Date(session.created_at).toLocaleDateString("vi-VN")}
                  </div>
                </div>
                <ArrowRight className="size-4 text-muted-foreground" />
              </Link>
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-border/70 bg-muted/30 px-5 py-10 text-center text-sm text-muted-foreground">
              Chưa có dữ liệu lịch sử để hiển thị.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
