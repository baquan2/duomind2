import {
  ArrowRight,
  BookCopy,
  BrainCircuit,
  Compass,
  History,
  MessagesSquare,
  Telescope,
} from "lucide-react"
import Link from "next/link"
import { redirect } from "next/navigation"

import { DashboardIntroGuide } from "@/components/dashboard/DashboardIntroGuide"
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
    href: "/mentor",
    title: "Mentor AI",
    description:
      "Nhận tư vấn hướng nghiệp, kỹ năng còn thiếu và lộ trình học tập dựa trên hồ sơ của bạn.",
    icon: MessagesSquare,
  },
  {
    href: "/explore",
    title: "Khám phá chủ đề",
    description:
      "Học sâu một chủ đề mới với phần kiến thức chi tiết, ví dụ theo persona và mind map tổng quan.",
    icon: Telescope,
  },
  {
    href: "/analyze",
    title: "Phân tích kiến thức",
    description:
      "Tải nội dung của bạn lên để chấm độ chính xác, sửa lỗi và cấu trúc lại thành bản học dễ hiểu.",
    icon: BrainCircuit,
  },
  {
    href: "/history",
    title: "Lịch sử học tập",
    description:
      "Xem lại các phiên gần đây, mở lại kết quả cũ và theo dõi tiến trình học tập của bạn.",
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
    supabase.from("profiles").select("*").eq("id", user.id).maybeSingle(),
    supabase.from("user_onboarding").select("*").eq("user_id", user.id).maybeSingle(),
    supabase
      .from("learning_sessions")
      .select("id, title, session_type, created_at")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(4),
  ])

  const profile = profileResponse.data
  const onboarding = onboardingResponse.data
  const recentSessions = sessionsResponse.data ?? []
  const displayName =
    profile?.full_name || user.user_metadata?.full_name || user.email?.split("@")[0] || "bạn"
  const mentorPath = buildMentorLearningPath(onboarding)

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[radial-gradient(circle_at_top_left,_rgba(255,217,102,0.32),_transparent_30%),linear-gradient(135deg,_rgba(15,118,110,0.14),_rgba(248,250,252,0.94))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-[-2rem] top-[-2rem] h-44 w-44 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative space-y-5">
          <Badge className="border-0 bg-primary text-primary-foreground">Tổng quan</Badge>

          <div className="max-w-4xl space-y-3">
            <h1 className="font-display text-4xl font-semibold leading-tight text-balance">
              Xin chào {displayName}, hôm nay bạn muốn học sâu hơn hay định hướng rõ hơn?
            </h1>
            <p className="text-sm leading-7 text-foreground/76 sm:text-base">
              Từ đây bạn có thể mở Mentor AI để nhận tư vấn cá nhân hóa, khám phá sâu một chủ đề mới
              hoặc quay lại các phiên học gần nhất.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/mentor">
                Mở Mentor AI
                <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
            <DashboardIntroGuide
              userId={user.id}
              displayName={displayName}
              showInitially={profile?.has_seen_intro_tour !== true}
            />
          </div>

        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-4">
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

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)]">
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Compass className="size-5 text-primary" />
              Mentor AI learning path
            </CardTitle>
            <CardDescription>
              Đây là lộ trình khởi động nhanh để mentor, khám phá chủ đề và phần học tập của bạn nối
              với nhau mượt hơn.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-3">
            {mentorPath.map((item, index) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.title}
                  href={item.href}
                  className={`rounded-[1.5rem] border border-border/70 bg-gradient-to-br ${item.accent} p-4 transition-transform hover:-translate-y-0.5`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <Badge variant="secondary">Bước {index + 1}</Badge>
                    <div className="flex size-10 items-center justify-center rounded-2xl bg-background/90 text-primary shadow-sm">
                      <Icon className="size-5" />
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="font-display text-xl font-semibold text-foreground">{item.title}</div>
                    <p className="text-sm leading-7 text-foreground/78">{item.description}</p>
                  </div>
                </Link>
              )
            })}
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle>Phiên học gần đây</CardTitle>
            <CardDescription>
              {recentSessions.length
                ? "Tiếp tục từ các buổi học mới nhất của bạn."
                : "Chưa có phiên nào. Hãy bắt đầu với Mentor AI, Phân tích hoặc Khám phá."}
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
    </div>
  )
}

function buildMentorLearningPath(
  onboarding:
    | {
        ai_recommended_topics?: string[] | null
        learning_goals?: string[] | null
        daily_study_minutes?: number | null
      }
    | null
    | undefined
) {
  const topTopic = onboarding?.ai_recommended_topics?.[0] || "chủ đề quan trọng nhất lúc này"
  const secondTopic = onboarding?.ai_recommended_topics?.[1] || "một kỹ năng ứng dụng gần mục tiêu của bạn"
  const studyWindow = onboarding?.daily_study_minutes ? `${onboarding.daily_study_minutes} phút mỗi ngày` : "quỹ thời gian hiện tại"
  const primaryGoal = onboarding?.learning_goals?.[0] || "mục tiêu học tập hiện tại"

  return [
    {
      title: "Chốt hướng với mentor",
      description: `Bắt đầu bằng một câu hỏi nghề nghiệp hoặc roadmap để mentor bám vào ${primaryGoal} và hồ sơ cá nhân của bạn.`,
      href: "/mentor",
      icon: MessagesSquare,
      accent: "from-emerald-500/18 to-teal-500/8",
    },
    {
      title: "Đi sâu chủ đề ưu tiên",
      description: `Khám phá sâu ${topTopic} trước, sau đó nối sang ${secondTopic} để hiểu rõ phần kiến thức có ích nhất.`,
      href: "/explore",
      icon: Telescope,
      accent: "from-amber-500/18 to-orange-500/8",
    },
    {
      title: "Củng cố và thực hành",
      description: `Dùng Phân tích để rà lại hiểu biết và giữ tiến độ học đều theo ${studyWindow} mà không bị lan man.`,
      href: "/analyze",
      icon: BookCopy,
      accent: "from-violet-500/18 to-fuchsia-500/8",
    },
  ]
}
