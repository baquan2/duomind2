import {
  ArrowRight,
  BookCopy,
  BrainCircuit,
  Compass,
  History,
  MessagesSquare,
  Route,
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
import {
  buildCareerFocus,
  buildContextSnapshot,
  buildMentorLearningPath,
  buildMiniRoadmap,
  buildProfileReadiness,
  buildReadinessSnapshot,
  type DashboardAnalytics,
  type DashboardOnboarding,
} from "@/lib/learning-roadmap"
import { mergeOnboardingWithMemories } from "@/lib/onboarding-context"
import { createClient } from "@/lib/supabase/server"

const quickActions = [
  {
    href: "/mentor",
    title: "Mentor AI",
    description:
      "Xác định khoảng trống kỹ năng, hỏi lộ trình học và chốt bước tiếp theo theo đúng mục tiêu nghề nghiệp của bạn.",
    icon: MessagesSquare,
  },
  {
    href: "/roadmap",
    title: "Lộ trình",
    description:
      "Xem lộ trình 14 ngày, khoảng trống kỹ năng hiện tại và các bước cần làm để tiến gần hơn tới vai trò mục tiêu.",
    icon: Route,
  },
  {
    href: "/explore",
    title: "Khám phá chủ đề",
    description:
      "Học sâu một chủ đề ưu tiên để bổ sung đúng phần kiến thức bạn đang cần cho mục tiêu hiện tại.",
    icon: Telescope,
  },
  {
    href: "/analyze",
    title: "Phân tích kiến thức",
    description:
      "Dùng với note, bài học hoặc tài liệu của bạn để chốt lại phần đúng, phần sai và phần cần bổ sung.",
    icon: BrainCircuit,
  },
  {
    href: "/history",
    title: "Lịch sử học tập",
    description:
      "Xem lại các phiên học, nhận ra mình đã học đến đâu và những chủ đề nào nên quay lại tiếp tục.",
    icon: History,
  },
] as const

export default async function DashboardPage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const [profileResponse, onboardingResponse, sessionsResponse, analyticsResponse, mentorMemoryResponse] =
    await Promise.all([
      supabase.from("profiles").select("*").eq("id", user.id).maybeSingle(),
      supabase.from("user_onboarding").select("*").eq("user_id", user.id).maybeSingle(),
      supabase
        .from("learning_sessions")
        .select("id, title, session_type, created_at")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .limit(4),
      supabase
        .from("knowledge_analytics")
        .select("*")
        .eq("user_id", user.id)
        .order("generated_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase
        .from("mentor_memory")
        .select("memory_key,memory_value")
        .eq("user_id", user.id)
        .order("updated_at", { ascending: false })
        .limit(8),
    ])

  const profile = profileResponse.data
  const onboarding = mergeOnboardingWithMemories(
    onboardingResponse.data as DashboardOnboarding | null,
    mentorMemoryResponse.data ?? []
  ) as DashboardOnboarding | null
  const analytics = analyticsResponse.data as DashboardAnalytics | null
  const recentSessions = sessionsResponse.data ?? []
  const displayName =
    profile?.full_name || user.user_metadata?.full_name || user.email?.split("@")[0] || "bạn"
  const careerFocus = buildCareerFocus(onboarding)
  const mentorPath = buildMentorLearningPath(onboarding)
  const miniRoadmap = buildMiniRoadmap(onboarding)
  const readiness = buildReadinessSnapshot(onboarding, analytics, recentSessions.length)
  const contextSnapshot = buildContextSnapshot(onboarding)
  const profileReadiness = buildProfileReadiness(onboarding)

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[radial-gradient(circle_at_top_left,_rgba(255,217,102,0.32),_transparent_30%),linear-gradient(135deg,_rgba(15,118,110,0.14),_rgba(248,250,252,0.94))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute right-[-2rem] top-[-2rem] h-44 w-44 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative space-y-5">
          <Badge className="border-0 bg-primary text-primary-foreground">Tổng quan</Badge>

          <div className="max-w-4xl space-y-3">
            <h1 className="font-display text-4xl font-semibold leading-tight text-balance">
              Xin chào {displayName}, mục tiêu hiện tại của bạn là {careerFocus.targetRole}.
            </h1>
            <p className="text-sm leading-7 text-foreground/76 sm:text-base">
              Hôm nay bạn nên ưu tiên {careerFocus.primaryTopic}. Mentor, Khám phá, Phân tích và lộ
              trình bên dưới đã được neo theo hướng đi này để bạn học đúng trọng tâm hơn.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link href={careerFocus.nextActionHref}>
                {careerFocus.nextActionLabel}
                <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/roadmap">
                Xem lộ trình
                <Route className="ml-2 size-4" />
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

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Compass className="size-5 text-primary" />
              Hướng tập trung hiện tại
            </CardTitle>
            <CardDescription>{careerFocus.focusSummary}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4 text-sm leading-7 text-foreground/78">
              {careerFocus.focusDetail}
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookCopy className="size-5 text-primary" />
              Hành động nên làm ngay
            </CardTitle>
            <CardDescription>{careerFocus.nextActionSummary}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center justify-between gap-4">
            <p className="max-w-xl text-sm leading-7 text-foreground/78">
              {careerFocus.nextActionDetail}
            </p>
            <Button asChild>
              <Link href={careerFocus.nextActionHref}>
                Thực hiện ngay
                <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {contextSnapshot.length ? (
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Compass className="size-5 text-primary" />
              Bối cảnh hiện tại
            </CardTitle>
            <CardDescription>
              Đây là lớp dữ liệu giúp DUO MIND hiểu đúng hoàn cảnh thật của bạn, thay vì chỉ bám vào
              vai trò mục tiêu.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {contextSnapshot.map((item) => (
              <div
                key={item.label}
                className="rounded-[1.5rem] border border-border/70 bg-background/80 p-4"
              >
                <div className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  {item.label}
                </div>
                <div className="mt-3 font-medium leading-7 text-foreground">{item.value}</div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <Card className="border border-border/70 bg-card/92">
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <CardTitle>Độ đầy hồ sơ học tập</CardTitle>
            <CardDescription>{profileReadiness.label}</CardDescription>
          </div>
          <Button asChild variant="outline">
            <Link href="/profile">
              Cập nhật hồ sơ
              <ArrowRight className="ml-2 size-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-foreground">Mức sẵn sàng dữ liệu</div>
              <Badge variant="secondary">{profileReadiness.score}/100</Badge>
            </div>
            <p className="mt-3 text-sm leading-7 text-foreground/78">{profileReadiness.summary}</p>
          </div>

          {profileReadiness.missingItems.length ? (
            <div className="flex flex-wrap gap-2">
              {profileReadiness.missingItems.map((item) => (
                <Badge key={item} variant="outline" className="rounded-full">
                  Thiếu: {item}
                </Badge>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-emerald-200/70 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-950">
              Hồ sơ hiện tại đã đủ rõ để mentor đi thẳng vào khoảng trống kỹ năng và hành động tiếp theo.
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="text-lg">Mức sẵn sàng hiện tại</CardTitle>
            <CardDescription>{readiness.level}</CardDescription>
          </CardHeader>
          <CardContent className="text-sm leading-7 text-foreground/78">
            {readiness.summary}
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="text-lg">Điểm mạnh hiện có</CardTitle>
            <CardDescription>{readiness.strongestLabel}</CardDescription>
          </CardHeader>
          <CardContent className="text-sm leading-7 text-foreground/78">
            {readiness.strongestDetail}
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="text-lg">Khoảng trống ưu tiên</CardTitle>
            <CardDescription>{readiness.gapLabel}</CardDescription>
          </CardHeader>
          <CardContent className="text-sm leading-7 text-foreground/78">
            {readiness.gapDetail}
          </CardContent>
        </Card>
      </div>

      <Card className="border border-border/70 bg-card/92">
        <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-1">
            <CardTitle>Lộ trình mini 14 ngày</CardTitle>
            <CardDescription>
              Khối này giúp bạn thấy ngay thứ tự hành động trước khi mở sang lộ trình đầy đủ.
            </CardDescription>
          </div>
          <Button asChild variant="outline">
            <Link href="/roadmap">
              Mở lộ trình chi tiết
              <ArrowRight className="ml-2 size-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-3">
          {miniRoadmap.map((item, index) => (
            <div
              key={item.title}
              className="rounded-[1.5rem] border border-border/70 bg-background/80 p-4"
            >
              <Badge variant="secondary">Chặng {index + 1}</Badge>
              <div className="mt-4 space-y-2">
                <div className="font-display text-xl font-semibold">{item.title}</div>
                <p className="text-sm leading-7 text-foreground/78">{item.description}</p>
                <Button asChild variant="outline" className="mt-2">
                  <Link href={item.href}>
                    {item.cta}
                    <ArrowRight className="ml-2 size-4" />
                  </Link>
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-5">
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
              Hành trình học cùng Mentor AI
            </CardTitle>
            <CardDescription>
              Luồng này giúp bạn nối mục tiêu nghề nghiệp với phiên mentor, phần học ưu tiên và phần
              củng cố kiến thức.
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
                    <div className="font-display text-xl font-semibold text-foreground">
                      {item.title}
                    </div>
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
