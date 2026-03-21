"use client"

import { motion, useReducedMotion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import {
  ArrowRight,
  BrainCircuit,
  Compass,
  MessagesSquare,
  Play,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

type HomeLandingProps = {
  navHref: string
  navLabel: string
  primaryHref: string
  primaryLabel: string
  statusLabel: string
}

type FeatureCard = {
  badge: string
  description: string
  icon: LucideIcon
  title: string
}

const heroStats = [
  {
    label: "Giá trị cốt lõi",
    value: "Vai trò -> Khoảng trống -> Lộ trình",
    detail: "Chốt mục tiêu nghề nghiệp, khoảng trống kỹ năng và bước tiếp theo trong cùng một luồng.",
  },
  {
    label: "Ngữ cảnh onboarding",
    value: "Mục tiêu + bối cảnh",
    detail:
      "Thu dữ liệu đầu ra mong muốn, khó khăn hiện tại và ràng buộc học tập để AI hiểu đúng người học.",
  },
  {
    label: "Vòng lặp tiến bộ",
    value: "Mentor | Lộ trình | Lịch sử",
    detail:
      "Mentor, roadmap, Explore, Analyze và history được nối thành một vòng lặp có thể quay lại.",
  },
]

const featureCards: FeatureCard[] = [
  {
    badge: "Ngữ cảnh nghề nghiệp",
    title: "Hiểu đúng người học trước khi đề xuất lộ trình",
    description:
      "DUO MIND bắt đầu bằng role mục tiêu, đầu ra mong muốn, khó khăn hiện tại và quỹ học thực tế thay vì hỏi đáp chung chung.",
    icon: MessagesSquare,
  },
  {
    badge: "Mentor + roadmap",
    title: "Biến AI thành mentor và bộ lập kế hoạch học tập",
    description:
      "Dashboard và lộ trình hiện ngay hành động nên làm tiếp, khoảng trống ưu tiên và thứ tự học hợp lý để người dùng biết cần làm gì tiếp.",
    icon: TrendingUp,
  },
  {
    badge: "Explore + Analyze",
    title: "Học đúng thứ đang thiếu thay vì học theo cảm tính",
    description:
      "Người dùng có thể học chủ đề ưu tiên trong Explore hoặc đưa note, tài liệu thật vào Analyze để khóa lại kiến thức.",
    icon: Compass,
  },
]

const journey = [
  {
    step: "01 / Understand",
    title: "Khóa mục tiêu và bối cảnh",
    description:
      "Onboarding thu role mục tiêu, đầu ra mong muốn, khó khăn hiện tại và quỹ học mỗi ngày để tạo bối cảnh cá nhân hóa.",
    icon: Sparkles,
  },
  {
    step: "02 / Plan",
    title: "Chốt thứ tự học bằng mentor và roadmap",
    description:
      "Dashboard và lộ trình hiện ngay mức sẵn sàng, khoảng trống ưu tiên và hành động tiếp theo để người dùng thấy đường đi rõ hơn.",
    icon: Target,
  },
  {
    step: "03 / Execute",
    title: "Học có đầu ra và theo dõi được tiến độ",
    description:
      "Explore, Analyze và history giúp người dùng học trên đúng gap, tự kiểm tra lại hiểu biết và theo dõi tiến bộ.",
    icon: ShieldCheck,
  },
]

export function HomeLanding({
  navHref,
  navLabel,
  primaryHref,
  primaryLabel,
  statusLabel,
}: HomeLandingProps) {
  const shouldReduceMotion = useReducedMotion()
  const headlineFont = "var(--font-nunito), var(--font-be-vietnam-pro), sans-serif"

  const reveal = (delay = 0) => ({
    initial: shouldReduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 },
    transition: {
      delay,
      duration: shouldReduceMotion ? 0 : 0.72,
      ease: [0.22, 1, 0.36, 1] as const,
    },
    viewport: { amount: 0.2, once: true },
    whileInView: { opacity: 1, y: 0 },
  })

  return (
    <main className="relative overflow-hidden bg-[#04121d] text-slate-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="landing-grid absolute inset-0 opacity-70" />
        <div className="landing-noise absolute inset-0 opacity-45" />
        <div className="absolute left-[-10rem] top-14 h-72 w-72 rounded-full bg-cyan-400/18 blur-3xl animate-soft-float" />
        <div className="absolute right-[-8rem] top-40 h-80 w-80 rounded-full bg-sky-400/16 blur-3xl animate-soft-float" />
        <div className="absolute bottom-16 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-amber-300/14 blur-3xl animate-soft-float" />
      </div>

      <div className="relative">
        <section className="container px-4 pb-20 pt-6 sm:pt-8 lg:pb-28">
          <motion.nav
            {...reveal()}
            className="flex items-center justify-between gap-4 rounded-full border border-white/10 bg-white/[0.04] px-4 py-3 backdrop-blur-xl"
          >
            <a className="flex items-center gap-3" href="/">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/15 bg-white/[0.08] text-cyan-100 shadow-[0_0_32px_rgba(34,211,238,0.18)]">
                <BrainCircuit className="size-5" />
              </div>
              <div>
                <div className="text-sm font-semibold tracking-[0.28em] text-white/95">DUO MIND</div>
                <div className="text-xs text-white/55">AI cố vấn và lập kế hoạch học tập</div>
              </div>
            </a>

            <div className="hidden items-center gap-6 text-sm text-white/70 md:flex">
              <a className="transition-colors hover:text-white" href="#value">
                Giá trị
              </a>
              <a className="transition-colors hover:text-white" href="#journey">
                Hành trình
              </a>
              <a className="transition-colors hover:text-white" href="#launch">
                Bắt đầu
              </a>
            </div>

            <Button
              asChild
              className="h-11 rounded-full border border-white/12 bg-white/[0.08] px-5 text-white hover:bg-white/[0.12]"
            >
              <a href={navHref}>
                {navLabel}
                <ArrowRight className="ml-2 size-4" />
              </a>
            </Button>
          </motion.nav>

          <div className="grid gap-14 pt-12 lg:grid-cols-[minmax(0,1.02fr)_minmax(0,0.98fr)] lg:items-center lg:pt-20">
            <div className="space-y-8">
              <motion.div {...reveal(0.06)} className="space-y-4">
                <Badge className="h-auto rounded-full border border-cyan-300/25 bg-cyan-300/10 px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-cyan-50">
                  AI cố vấn và lập kế hoạch học tập
                </Badge>
                <div className="flex flex-wrap items-center gap-3 text-sm text-white/64">
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
                    {statusLabel}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
                    Vai trò mục tiêu, khoảng trống kỹ năng, lộ trình và tiến độ
                  </span>
                </div>
              </motion.div>

              <motion.div {...reveal(0.12)} className="space-y-5">
                <h1
                  className="max-w-4xl text-5xl font-semibold leading-[0.95] tracking-[-0.06em] text-white sm:text-6xl lg:text-7xl"
                  style={{ fontFamily: headlineFont }}
                >
                  DUO MIND giúp bạn biết mình đang thiếu gì,
                  <span className="mt-3 block bg-[linear-gradient(120deg,#f0f9ff_10%,#67e8f9_38%,#7dd3fc_62%,#fde68a_100%)] bg-clip-text text-transparent">
                    và học theo đúng lộ trình để tới mục tiêu nghề nghiệp.
                  </span>
                </h1>
                <p className="max-w-2xl text-base leading-8 text-white/72 sm:text-lg">
                  DUO MIND được thiết kế cho sinh viên và người đi làm trẻ đang cần một hệ thống AI
                  có thể hiểu bối cảnh thật, chốt khoảng trống kỹ năng, gợi ý lộ trình và giữ lại toàn bộ tiến
                  trình học tập theo mục tiêu nghề nghiệp đã chọn.
                </p>
              </motion.div>

              <motion.div {...reveal(0.18)} className="flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="h-12 rounded-full bg-[linear-gradient(120deg,#ecfeff_0%,#67e8f9_38%,#7dd3fc_68%,#fde68a_100%)] px-6 text-slate-950 hover:brightness-105"
                >
                  <a href={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </a>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 rounded-full border-white/12 bg-white/[0.04] px-6 text-white hover:bg-white/[0.08] hover:text-white"
                >
                  <a href="#value">
                    <Play className="mr-2 size-4" />
                    Xem giá trị
                  </a>
                </Button>
              </motion.div>

              <motion.div {...reveal(0.24)} className="grid gap-3 sm:grid-cols-3">
                {heroStats.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-[1.7rem] border border-white/10 bg-white/[0.05] p-4 backdrop-blur-xl"
                  >
                    <div className="text-xs uppercase tracking-[0.22em] text-white/45">{item.label}</div>
                    <div className="mt-3 text-3xl font-semibold text-white">{item.value}</div>
                    <p className="mt-3 text-sm leading-6 text-white/62">{item.detail}</p>
                  </div>
                ))}
              </motion.div>
            </div>

            <motion.div
              {...reveal(0.16)}
              className="rounded-[2.6rem] border border-white/10 bg-white/[0.06] p-5 backdrop-blur-2xl sm:p-6"
            >
              <div className="rounded-[2rem] border border-white/10 bg-[#071b2b]/90 p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-white/40">Command center</div>
                    <div
                      className="mt-2 text-xl font-semibold text-white"
                      style={{ fontFamily: headlineFont }}
                    >
                      Một hệ học tập AI không chỉ trả lời, mà còn giúp ra quyết định học gì tiếp theo.
                    </div>
                  </div>
                  <TrendingUp className="size-5 text-cyan-200" />
                </div>

                <div className="mt-8 flex h-36 items-end gap-2">
                  {[48, 72, 60, 92, 76, 54, 82].map((height) => (
                    <div
                      key={height}
                      className="flex-1 rounded-t-[999px] bg-[linear-gradient(180deg,rgba(254,240,138,0.95)_0%,rgba(103,232,249,0.78)_58%,rgba(8,145,178,0.24)_100%)]"
                      style={{ height: `${height}%` }}
                    />
                  ))}
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {[
                    { metric: "Target role", value: "Định vị rõ" },
                    { metric: "Skill gap", value: "Thấy ngay" },
                    { metric: "Lộ trình", value: "Có hành động" },
                  ].map((item) => (
                    <div
                      key={item.metric}
                      className="rounded-[1.3rem] border border-white/10 bg-white/[0.05] p-3"
                    >
                      <div className="text-[0.68rem] uppercase tracking-[0.18em] text-white/45">
                        {item.metric}
                      </div>
                      <div className="mt-2 text-lg font-semibold text-white">{item.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-5 grid gap-4">
                {[
                  "Mentor AI đi thẳng vào role mục tiêu, kỹ năng còn thiếu và thứ tự học hợp lý.",
                  "Lộ trình hiện ngay mức sẵn sàng, khoảng trống ưu tiên và hành động nên làm tiếp.",
                  "Explore và Analyze giúp học trên đúng gap, không học lan man.",
                ].map((item) => (
                  <div
                    key={item}
                    className="rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-4 text-sm leading-7 text-white/68"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        <section id="value" className="container px-4 py-20 lg:py-24">
          <motion.div {...reveal()} className="mx-auto max-w-3xl text-center">
            <Badge className="h-auto rounded-full border border-white/10 bg-white/[0.06] px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-white/72">
              Giá trị nổi bật
            </Badge>
            <h2
              className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl"
              style={{ fontFamily: headlineFont }}
            >
              DUO MIND được thiết kế để biến việc học thành một hành trình có mục tiêu, có thứ tự
              và có đầu ra.
            </h2>
            <p className="mt-5 text-base leading-8 text-white/64 sm:text-lg">
              Từ việc hiểu người học, gợi ý roadmap, phân tích nội dung cho đến theo dõi tiến độ,
              mỗi tính năng đều phục vụ một câu hỏi rất cụ thể: người dùng đang thiếu gì và nên làm
              gì tiếp theo.
            </p>
          </motion.div>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {featureCards.map((item, index) => {
              const Icon = item.icon
              return (
                <motion.div
                  key={item.title}
                  {...reveal(0.08 + index * 0.06)}
                  className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5 backdrop-blur-xl"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-xs uppercase tracking-[0.22em] text-white/42">{item.badge}</div>
                      <div className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-white">
                        {item.title}
                      </div>
                    </div>
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-200/18 bg-cyan-200/10 text-cyan-50">
                      <Icon className="size-5" />
                    </div>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-white/66">{item.description}</p>
                </motion.div>
              )
            })}
          </div>
        </section>

        <section id="journey" className="container px-4 pb-24">
          <motion.div
            {...reveal()}
            className="rounded-[2.4rem] border border-white/10 bg-[linear-gradient(160deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-6 sm:p-8"
          >
            <div className="grid gap-10 xl:grid-cols-[0.82fr_1.18fr] xl:items-start">
              <div>
                <Badge className="h-auto rounded-full border border-amber-200/20 bg-amber-200/10 px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-amber-50">
                  Hành trình học
                </Badge>
                <h2
                  className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl"
                  style={{ fontFamily: headlineFont }}
                >
                  DUO MIND đồng hành với người học qua ba chặng rõ ràng.
                </h2>
                <p className="mt-5 text-base leading-8 text-white/64">
                  Bạn không chỉ nhận một câu trả lời từ AI. DUO MIND bắt đầu bằng việc hiểu người
                  học, sau đó chốt hướng học rõ ràng và cuối cùng giữ lại tiến trình để bạn quay
                  lại đúng điểm đang cần.
                </p>
              </div>

              <div className="grid gap-5 md:grid-cols-3">
                {journey.map((item, index) => {
                  const Icon = item.icon
                  return (
                    <motion.div
                      key={item.title}
                      {...reveal(0.08 + index * 0.08)}
                      className="relative rounded-[1.8rem] border border-white/10 bg-[#061320]/90 p-5"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-xs uppercase tracking-[0.22em] text-white/42">{item.step}</div>
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/[0.05] text-cyan-50">
                          <Icon className="size-4" />
                        </div>
                      </div>
                      <div className="mt-6 text-2xl font-semibold tracking-[-0.04em] text-white">
                        {item.title}
                      </div>
                      <p className="mt-4 text-sm leading-7 text-white/66">{item.description}</p>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          </motion.div>
        </section>

        <section id="launch" className="container px-4 pb-20">
          <motion.div
            {...reveal()}
            className="relative overflow-hidden rounded-[2.8rem] border border-cyan-200/12 bg-[linear-gradient(130deg,rgba(3,17,30,0.96),rgba(8,33,51,0.92))] p-8 sm:p-10"
          >
            <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
              <div className="max-w-3xl">
                <Badge className="h-auto rounded-full border border-white/10 bg-white/[0.06] px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-white/74">
                  Sẵn sàng bắt đầu
                </Badge>
                <h2
                  className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl"
                  style={{ fontFamily: headlineFont }}
                >
                  DUO MIND là nơi bạn chốt mục tiêu nghề nghiệp, học đúng thứ đang thiếu và theo
                  dõi được tiến độ trong một hệ duy nhất.
                </h2>
                <p className="mt-5 text-base leading-8 text-white/66">
                  Đăng ký để hoàn thành onboarding và mở ra flow học tập bám theo role mục tiêu,
                  gồm Mentor AI, roadmap, Explore, Analyze và history được cá nhân hóa theo chính
                  bạn.
                </p>
              </div>

              <div className="flex flex-wrap gap-3 lg:justify-end">
                <Button
                  asChild
                  size="lg"
                  className="h-12 rounded-full bg-[linear-gradient(120deg,#ecfeff_0%,#67e8f9_38%,#7dd3fc_68%,#fde68a_100%)] px-6 text-slate-950 hover:brightness-105"
                >
                  <a href={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </a>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 rounded-full border-white/12 bg-white/[0.04] px-6 text-white hover:bg-white/[0.08] hover:text-white"
                >
                  <a href="#value">Xem lại giá trị</a>
                </Button>
              </div>
            </div>
          </motion.div>
        </section>
      </div>
    </main>
  )
}
