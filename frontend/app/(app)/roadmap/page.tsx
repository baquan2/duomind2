import {
  ArrowRight,
  BookCopy,
  CalendarRange,
  Compass,
  MessagesSquare,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react"
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
import { Progress } from "@/components/ui/progress"
import {
  buildCareerFocus,
  buildContextSnapshot,
  buildExecutionRules,
  buildExplorePromptFromTopic,
  buildMentorQuestionForTopic,
  buildMentorPrompts,
  buildMiniRoadmap,
  buildProfileReadiness,
  buildReadinessSnapshot,
  buildSkillGapSnapshot,
  type DashboardAnalytics,
  type DashboardOnboarding,
} from "@/lib/learning-roadmap"
import { mergeOnboardingWithMemories } from "@/lib/onboarding-context"
import { createClient } from "@/lib/supabase/server"

export default async function RoadmapPage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const [onboardingResponse, analyticsResponse, sessionsResponse, mentorMemoryResponse] =
    await Promise.all([
      supabase.from("user_onboarding").select("*").eq("user_id", user.id).maybeSingle(),
      supabase
        .from("knowledge_analytics")
        .select("*")
        .eq("user_id", user.id)
        .order("generated_at", { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase
        .from("learning_sessions")
        .select("id")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false })
        .limit(12),
      supabase
        .from("mentor_memory")
        .select("memory_key,memory_value")
        .eq("user_id", user.id)
        .order("updated_at", { ascending: false })
        .limit(8),
    ])

  const onboarding = mergeOnboardingWithMemories(
    onboardingResponse.data as DashboardOnboarding | null,
    mentorMemoryResponse.data ?? []
  ) as DashboardOnboarding | null
  const analytics = analyticsResponse.data as DashboardAnalytics | null
  const visibleSessionCount = sessionsResponse.data?.length ?? 0
  const careerFocus = buildCareerFocus(onboarding)
  const readiness = buildReadinessSnapshot(onboarding, analytics, visibleSessionCount)
  const skillGapSnapshot = buildSkillGapSnapshot(onboarding, analytics, visibleSessionCount)
  const miniRoadmap = buildMiniRoadmap(onboarding)
  const mentorPrompts = buildMentorPrompts(onboarding, analytics)
  const executionRules = buildExecutionRules(onboarding)
  const contextSnapshot = buildContextSnapshot(onboarding)
  const profileReadiness = buildProfileReadiness(onboarding)
  const dailyStudyMinutes = onboarding?.daily_study_minutes ?? 30
  const avgQuizScore =
    analytics?.avg_quiz_score !== null && analytics?.avg_quiz_score !== undefined
      ? `${Math.round(analytics.avg_quiz_score)}%`
      : "Chưa có"

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[2rem] border border-border/70 bg-[radial-gradient(circle_at_top_right,_rgba(250,204,21,0.24),_transparent_28%),linear-gradient(135deg,_rgba(15,118,110,0.12),_rgba(255,255,255,0.96))] p-6 shadow-sm shadow-primary/10 sm:p-8">
        <div className="absolute bottom-[-2rem] left-[-2rem] h-44 w-44 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative space-y-5">
          <Badge className="border-0 bg-primary text-primary-foreground">Lộ trình</Badge>

          <div className="max-w-4xl space-y-3">
            <h1 className="font-display text-4xl font-semibold leading-tight text-balance">
              Lộ trình hiện tại để tiến gần hơn tới {careerFocus.targetRole}
            </h1>
            <p className="text-sm leading-7 text-foreground/78 sm:text-base">
              Màn hình này gom toàn bộ tín hiệu quan trọng nhất thành một luồng rõ ràng: bạn đang ở
              đâu, khoảng trống nào cần bù trước, và nên làm gì trong 14 ngày tiếp theo.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/mentor">
                Hỏi mentor ngay
                <MessagesSquare className="ml-2 size-4" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/explore">
                Học chủ đề ưu tiên
                <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <RoadmapMetricCard
          icon={Target}
          label="Mục tiêu đang theo"
          value={careerFocus.targetRole}
          detail={careerFocus.primaryTopic}
        />
        <RoadmapMetricCard
          icon={TrendingUp}
          label="Mức sẵn sàng"
          value={`${readiness.readinessScore}/100`}
          detail={readiness.level}
        />
        <RoadmapMetricCard
          icon={CalendarRange}
          label="Quỹ học hiện tại"
          value={`${dailyStudyMinutes} phút/ngày`}
          detail="Dùng làm nhịp chuẩn cho mỗi phiên học"
        />
        <RoadmapMetricCard
          icon={Sparkles}
          label="Điểm quiz gần nhất"
          value={avgQuizScore}
          detail={`${visibleSessionCount} phiên gần nhất đang được dùng để suy luận lộ trình`}
        />
      </div>

      {profileReadiness.missingItems.length ? (
        <Card className="border border-border/70 bg-card/92">
          <CardHeader className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <CardTitle>Hồ sơ còn thiếu tín hiệu</CardTitle>
              <CardDescription>{profileReadiness.label}</CardDescription>
            </div>
            <Button asChild variant="outline">
              <Link href="/profile">
                Bổ sung hồ sơ
                <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4 text-sm leading-7 text-foreground/78">
              {profileReadiness.summary}
            </div>
            <div className="flex flex-wrap gap-2">
              {profileReadiness.missingItems.map((item) => (
                <Badge key={item} variant="outline" className="rounded-full">
                  Thiếu: {item}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle>Tóm tắt khoảng trống kỹ năng</CardTitle>
            <CardDescription>
              Không cố nói mọi thứ. Chỉ khóa 3 tín hiệu đủ để bạn quyết định thứ tự hành động.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {skillGapSnapshot.map((item) => (
              <div
                key={`${item.title}-${item.topic}`}
                className="rounded-[1.5rem] border border-border/70 bg-background/80 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-foreground">{item.title}</div>
                    <div className="mt-1 font-display text-xl font-semibold">{item.topic}</div>
                  </div>
                  <Badge variant="secondary">{item.badge}</Badge>
                </div>
                <Progress value={item.score} className="mt-4 h-2" />
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Mức ưu tiên / độ rõ hiện tại</span>
                  <span>{item.score}/100</span>
                </div>
                <p className="mt-3 text-sm leading-7 text-foreground/78">{item.detail}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="outline">
                    <Link
                      href={`/explore?prompt=${encodeURIComponent(
                        buildExplorePromptFromTopic(item.topic, careerFocus.targetRole)
                      )}`}
                    >
                      Học chủ đề này
                      <Compass className="ml-2 size-4" />
                    </Link>
                  </Button>
                  <Button asChild size="sm" variant="ghost">
                    <Link
                      href={`/mentor?question=${encodeURIComponent(
                        buildMentorQuestionForTopic(item.topic, careerFocus.targetRole)
                      )}`}
                    >
                      Hỏi mentor
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle>Tóm tắt điều hướng</CardTitle>
            <CardDescription>{careerFocus.focusSummary}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm leading-7 text-foreground/78">
            {contextSnapshot.length ? (
              <div className="grid gap-3">
                {contextSnapshot.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-2xl border border-border/70 bg-background/80 p-4"
                  >
                    <div className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                      {item.label}
                    </div>
                    <div className="mt-2 font-medium text-foreground">{item.value}</div>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.detail}</p>
                  </div>
                ))}
              </div>
            ) : null}
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
              {readiness.summary}
            </div>
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <div className="font-medium text-foreground">{readiness.strongestLabel}</div>
              <p className="mt-2">{readiness.strongestDetail}</p>
            </div>
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <div className="font-medium text-foreground">{readiness.gapLabel}</div>
              <p className="mt-2">{readiness.gapDetail}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border border-border/70 bg-card/92">
        <CardHeader>
          <CardTitle>Lộ trình thực thi 14 ngày</CardTitle>
          <CardDescription>
            Đây là phiên bản đủ gọn để người dùng làm theo ngay và đủ rõ để pitch giá trị thương mại
            của sản phẩm.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-3">
          {miniRoadmap.map((item, index) => (
            <div
              key={item.title}
              className="rounded-[1.75rem] border border-border/70 bg-[linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.92))] p-5"
            >
              <div className="flex items-center justify-between gap-3">
                <Badge variant="secondary">Chặng {index + 1}</Badge>
                <span className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                  Luồng 14 ngày
                </span>
              </div>
              <div className="mt-4 space-y-3">
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

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessagesSquare className="size-5 text-primary" />
              3 câu hỏi nên hỏi mentor tiếp theo
            </CardTitle>
            <CardDescription>
              Dùng đúng các câu hỏi này để mentor đi thẳng vào khoảng trống quan trọng, thay vì trả
              lời quá chung.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {mentorPrompts.map((prompt, index) => (
              <Link
                key={prompt}
                href={`/mentor?question=${encodeURIComponent(prompt)}`}
                className="flex rounded-2xl border border-border/70 bg-background/80 px-4 py-3 transition-colors hover:border-primary/35 hover:bg-primary/5"
              >
                <div className="mr-3 mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {index + 1}
                </div>
                <div className="text-sm leading-7 text-foreground/82">{prompt}</div>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card className="border border-border/70 bg-card/92">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Compass className="size-5 text-primary" />
              Nguyên tắc thực thi
            </CardTitle>
            <CardDescription>
              Nếu người dùng tuân theo các nguyên tắc này, giá trị của sản phẩm sẽ rõ hơn và tỷ lệ
              quay lại cũng tốt hơn.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {executionRules.map((rule) => (
              <div
                key={rule.title}
                className="rounded-2xl border border-border/70 bg-background/80 px-4 py-3"
              >
                <div className="font-medium text-foreground">{rule.title}</div>
                <p className="mt-2 text-sm leading-7 text-foreground/78">{rule.detail}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <ActionCard
          href="/mentor"
          title="1. Chốt khoảng trống với mentor"
          description="Bắt đầu ở đây nếu bạn còn mơ hồ về thứ tự học hoặc chưa rõ nên ưu tiên khoảng trống nào."
          icon={MessagesSquare}
        />
        <ActionCard
          href="/explore"
          title="2. Học chủ đề trọng tâm"
          description="Sau khi có khoảng trống rõ ràng, chuyển sang Khám phá để học sâu đúng khối kiến thức cần bù."
          icon={Compass}
        />
        <ActionCard
          href="/analyze"
          title="3. Củng cố bằng đầu ra"
          description="Dùng Phân tích với note, bài học hoặc tài liệu thật để khóa lại phần đã học."
          icon={BookCopy}
        />
      </div>
    </div>
  )
}

function RoadmapMetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Target
  label: string
  value: string
  detail: string
}) {
  return (
    <Card className="border border-border/70 bg-card/92">
      <CardHeader>
        <div className="mb-2 inline-flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-xl">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm leading-7 text-foreground/78">{detail}</CardContent>
    </Card>
  )
}

function ActionCard({
  href,
  title,
  description,
  icon: Icon,
}: {
  href: string
  title: string
  description: string
  icon: typeof Target
}) {
  return (
    <Card className="border border-border/70 bg-card/92">
      <CardHeader>
        <div className="mb-2 inline-flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button asChild>
          <Link href={href}>
            Mở ngay
            <ArrowRight className="ml-2 size-4" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}
