"use client"

import { motion, useReducedMotion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  Compass,
  Layers3,
  MessagesSquare,
  Orbit,
  Play,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Workflow,
  Zap,
} from "lucide-react"
import Link from "next/link"

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

type FlowStep = {
  description: string
  icon: LucideIcon
  kicker: string
  title: string
}

const heroStats = [
  {
    detail: "Phân tích nội dung đang có sẵn hoặc khám phá một chủ đề mới bằng prompt tự nhiên với AI đồng hành.",
    label: "Chế độ cốt lõi",
    value: "Analyze + Explore",
  },
  {
    detail: "Wizard 4 bước giúp DUO MIND hiểu người học để điều chỉnh độ sâu kiến thức, ví dụ và lộ trình phù hợp.",
    label: "Onboarding AI",
    value: "4 bước",
  },
  {
    detail: "Mentor AI, infographic, mind map, quiz và lịch sử học tập nối với nhau thành một vòng lặp học sâu.",
    label: "Knowledge loop",
    value: "Mentor | Quiz",
  },
]

const marqueeSignals = [
  "Mentor AI",
  "Analyze Mode",
  "Explore Mode",
  "Mind Map",
  "Infographic",
  "Quiz tự động",
  "Open Questions",
  "Learning History",
]

const featureCards: FeatureCard[] = [
  {
    badge: "Onboarding + Mentor",
    description:
      "DUO MIND bắt đầu bằng việc hiểu mục tiêu, hồ sơ và phong cách học của bạn để AI có thể hướng dẫn đúng người, đúng mức độ và đúng nhu cầu.",
    icon: MessagesSquare,
    title: "Hiểu người học trước khi bắt đầu dạy",
  },
  {
    badge: "Analyze",
    description:
      "Dán nội dung cần kiểm tra, DUO MIND sẽ phân tích độ chính xác, tóm tắt lại, đính chính chỗ sai và chuyển nó thành bản học dễ đọc hơn.",
    icon: ScanLine,
    title: "Rà lại kiến thức để học chắc hơn",
  },
  {
    badge: "Explore",
    description:
      "Chỉ cần nhập một câu hỏi tự nhiên, hệ thống sẽ giải thích chủ đề, mở rộng bối cảnh, dựng mind map và tạo bài luyện tập ngay trên cùng một flow.",
    icon: Compass,
    title: "Khám phá chủ đề mới theo cách dễ hiểu hơn",
  },
]

const commandLayers = [
  {
    accent: "from-cyan-400/25 via-cyan-300/12 to-transparent",
    metric: "Onboarding AI",
    value: "4 bước",
  },
  {
    accent: "from-sky-400/25 via-sky-300/12 to-transparent",
    metric: "Study modes",
    value: "2 chế độ",
  },
  {
    accent: "from-amber-300/25 via-amber-200/12 to-transparent",
    metric: "Output layer",
    value: "Map + Quiz",
  },
]

const flowSteps: FlowStep[] = [
  {
    description:
      "Wizard 4 bước giúp DUO MIND hiểu mục tiêu, độ tuổi, lĩnh vực quan tâm và phong cách học để AI cá nhân hóa trải nghiệm ngay từ đầu.",
    icon: Sparkles,
    kicker: "01 / Understand",
    title: "Bắt đầu bằng onboarding thông minh",
  },
  {
    description:
      "Bạn có thể vào Analyze để rà lại nội dung đang học, mở Explore để đào sâu một chủ đề mới hoặc hỏi Mentor AI để xin định hướng rõ hơn.",
    icon: Workflow,
    kicker: "02 / Learn",
    title: "Học cùng Mentor AI, Analyze và Explore",
  },
  {
    description:
      "Mỗi phiên học đều có thể lưu lại trong history để bạn xem lại, bookmark, làm quiz tiếp tục và theo dõi tiến bộ của mình theo thời gian.",
    icon: ShieldCheck,
    kicker: "03 / Improve",
    title: "Theo dõi tiến bộ qua lịch sử học tập",
  },
]

const neuralBars = [52, 74, 62, 94, 78, 56, 84]

const floatingNotes = [
  {
    className: "left-[-1.5rem] top-[4.5rem] sm:left-[-3rem]",
    title: "Onboarding AI",
    value: "Persona ready",
  },
  {
    className: "right-[-0.5rem] top-[-1rem] sm:right-[-2rem]",
    title: "Mentor AI",
    value: "Roadmap active",
  },
  {
    className: "bottom-[-1rem] left-[6%] sm:left-[-1rem]",
    title: "Learning history",
    value: "Sessions saved",
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
    initial: shouldReduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 28 },
    transition: {
      delay,
      duration: shouldReduceMotion ? 0 : 0.82,
      ease: [0.22, 1, 0.36, 1] as const,
    },
    viewport: { amount: 0.25, once: true },
    whileInView: { opacity: 1, y: 0 },
  })

  return (
    <main className="relative overflow-hidden bg-[#04121d] text-slate-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="landing-grid absolute inset-0 opacity-70" />
        <div className="landing-noise absolute inset-0 opacity-45" />
        <div className="landing-scanlines absolute inset-0 opacity-30" />
        <div className="absolute left-[-10rem] top-14 h-72 w-72 rounded-full bg-cyan-400/18 blur-3xl animate-soft-float" />
        <div
          className="absolute right-[-8rem] top-40 h-80 w-80 rounded-full bg-sky-400/16 blur-3xl animate-soft-float"
          style={{ animationDelay: "1.4s" }}
        />
        <div
          className="absolute bottom-16 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-amber-300/14 blur-3xl animate-soft-float"
          style={{ animationDelay: "2.4s" }}
        />
      </div>

      <div className="relative">
        <section className="container px-4 pb-20 pt-6 sm:pt-8 lg:pb-28">
          <motion.nav
            {...reveal()}
            className="flex items-center justify-between gap-4 rounded-full border border-white/10 bg-white/[0.04] px-4 py-3 backdrop-blur-xl"
          >
            <Link className="flex items-center gap-3" href="/">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/15 bg-white/[0.08] text-cyan-100 shadow-[0_0_32px_rgba(34,211,238,0.18)]">
                <BrainCircuit className="size-5" />
              </div>
              <div>
                <div className="text-sm font-semibold tracking-[0.28em] text-white/95">DUO MIND</div>
                <div className="text-xs text-white/55">Phân tích, khám phá và học sâu cùng AI</div>
              </div>
            </Link>

            <div className="hidden items-center gap-6 text-sm text-white/70 md:flex">
              <Link className="transition-colors hover:text-white" href="#signal-stack">
                Tính năng
              </Link>
              <Link className="transition-colors hover:text-white" href="#motion-loop">
                Hành trình
              </Link>
              <Link className="transition-colors hover:text-white" href="#launch">
                Bắt đầu
              </Link>
            </div>

            <Button
              asChild
              className="h-11 rounded-full border border-white/12 bg-white/[0.08] px-5 text-white shadow-[0_18px_50px_rgba(8,15,26,0.38)] hover:bg-white/[0.12]"
            >
              <Link href={navHref}>
                {navLabel}
                <ArrowRight className="ml-2 size-4" />
              </Link>
            </Button>
          </motion.nav>

          <div className="grid gap-14 pt-12 lg:grid-cols-[minmax(0,1.02fr)_minmax(0,0.98fr)] lg:items-center lg:pt-20">
            <div className="space-y-8">
              <motion.div {...reveal(0.06)} className="space-y-4">
                <Badge className="h-auto rounded-full border border-cyan-300/25 bg-cyan-300/10 px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-cyan-50">
                  Nền tảng học tập AI
                </Badge>
                <div className="flex flex-wrap items-center gap-3 text-sm text-white/64">
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
                    {statusLabel}
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
                    Mentor AI, Analyze, Explore, Quiz và History
                  </span>
                </div>
              </motion.div>

              <motion.div {...reveal(0.12)} className="space-y-5">
                <h1
                  className="max-w-4xl text-5xl font-semibold leading-[0.95] tracking-[-0.06em] text-white sm:text-6xl lg:text-7xl"
                  style={{ fontFamily: headlineFont }}
                >
                  DUO MIND giúp bạn học đúng thứ cần học,
                  <span className="mt-3 block bg-[linear-gradient(120deg,#f0f9ff_10%,#67e8f9_38%,#7dd3fc_62%,#fde68a_100%)] bg-clip-text text-transparent">
                    theo cách phù hợp nhất với bạn.
                  </span>
                </h1>
                <p className="max-w-2xl text-base leading-8 text-white/72 sm:text-lg">
                  DUO MIND là nền tảng học tập AI-powered kết hợp onboarding thông minh, Mentor AI,
                  chế độ Phân tích và Khám phá để biến nội dung rời rạc thành lộ trình rõ ràng, dễ hiểu
                  và có thể theo dõi tiến bộ theo thời gian.
                </p>
              </motion.div>

              <motion.div {...reveal(0.18)} className="flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="h-12 rounded-full bg-[linear-gradient(120deg,#ecfeff_0%,#67e8f9_38%,#7dd3fc_68%,#fde68a_100%)] px-6 text-slate-950 shadow-[0_24px_70px_rgba(14,165,233,0.26)] hover:brightness-105"
                >
                  <Link href={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </Link>
                </Button>

                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 rounded-full border-white/12 bg-white/[0.04] px-6 text-white hover:bg-white/[0.08] hover:text-white"
                >
                  <Link href="#signal-stack">
                    <Play className="mr-2 size-4" />
                    Xem tính năng
                  </Link>
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
              animate={
                shouldReduceMotion
                  ? undefined
                  : {
                      y: [0, -10, 0],
                    }
              }
              transition={
                shouldReduceMotion
                  ? undefined
                  : {
                      duration: 7.5,
                      ease: "easeInOut",
                      repeat: Infinity,
                    }
              }
              className="relative mx-auto w-full max-w-[39rem]"
            >
              <div className="landing-beam" />
              <div className="absolute inset-[-12%] rounded-[2.8rem] border border-cyan-200/10 bg-cyan-300/5 blur-2xl" />

              <div className="landing-panel-glow relative overflow-hidden rounded-[2.6rem] border border-white/10 bg-white/[0.06] p-5 backdrop-blur-2xl sm:p-6">
                <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.7),transparent)]" />

                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.26em] text-cyan-100/70">
                      Trung tâm học tập DUO MIND
                    </div>
                    <div
                      className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-white"
                      style={{ fontFamily: headlineFont }}
                    >
                      Một hệ học tập AI không chỉ trả lời, mà còn dẫn đường.
                    </div>
                  </div>
                  <div className="rounded-full border border-white/10 bg-white/[0.05] px-4 py-2 text-xs text-white/68">
                    Mentor AI + Analyze + Explore
                  </div>
                </div>

                <div className="mt-6 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
                  <div className="rounded-[2rem] border border-white/10 bg-[#071b2b]/90 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-xs uppercase tracking-[0.22em] text-white/40">
                          Hệ sinh thái DUO MIND
                        </div>
                        <div className="mt-2 text-xl font-semibold text-white">Các năng lực học tập cốt lõi</div>
                      </div>
                      <BarChart3 className="size-5 text-cyan-200" />
                    </div>

                    <div className="mt-8 flex h-36 items-end gap-2">
                      {neuralBars.map((height, index) => (
                        <motion.div
                          key={height + index}
                          animate={
                            shouldReduceMotion
                              ? undefined
                              : {
                                  scaleY: [0.92, 1, 0.94, 1],
                                }
                          }
                          transition={
                            shouldReduceMotion
                              ? undefined
                              : {
                                  delay: index * 0.12,
                                  duration: 2.8,
                                  ease: "easeInOut",
                                  repeat: Infinity,
                                }
                          }
                          className="flex-1 origin-bottom rounded-t-[999px] bg-[linear-gradient(180deg,rgba(254,240,138,0.95)_0%,rgba(103,232,249,0.78)_58%,rgba(8,145,178,0.24)_100%)] shadow-[0_12px_34px_rgba(34,211,238,0.18)]"
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>

                    <div className="mt-6 grid gap-3 sm:grid-cols-3">
                      {commandLayers.map((item) => (
                        <div
                          key={item.metric}
                          className={`rounded-[1.3rem] border border-white/10 bg-gradient-to-br ${item.accent} p-3`}
                        >
                          <div className="text-[0.68rem] uppercase tracking-[0.18em] text-white/45">
                            {item.metric}
                          </div>
                          <div className="mt-2 text-lg font-semibold text-white">{item.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid gap-4">
                    <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-4">
                      <div className="flex items-center gap-2 text-sm text-cyan-50">
                        <Orbit className="size-4" />
                        Mentor AI
                      </div>
                      <p className="mt-3 text-sm leading-7 text-white/68">
                        Hỏi về hướng nghề nghiệp, kỹ năng còn thiếu và lộ trình học phù hợp với hồ sơ của bạn.
                      </p>
                    </div>

                    <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-4">
                      <div className="flex items-center gap-2 text-sm text-cyan-50">
                        <Layers3 className="size-4" />
                        Chế độ Phân tích
                      </div>
                      <p className="mt-3 text-sm leading-7 text-white/68">
                        Kiểm tra độ chính xác, tóm tắt ý chính, đính chính lỗi sai và cấu trúc lại nội dung để dễ học hơn.
                      </p>
                    </div>

                    <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-4">
                      <div className="flex items-center gap-2 text-sm text-cyan-50">
                        <Zap className="size-4" />
                        Chế độ Khám phá
                      </div>
                      <p className="mt-3 text-sm leading-7 text-white/68">
                        Nhập một prompt tự nhiên để DUO MIND giải thích chủ đề, tạo mind map, infographic và câu hỏi luyện tập.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-5 rounded-[2rem] border border-white/10 bg-[#07111b]/90 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-[0.2em] text-white/40">Knowledge relay</div>
                      <div className="mt-2 text-sm text-white/70">
                        Từ một phiên học, DUO MIND có thể tạo insight, trực quan hóa kiến thức và lưu lại tiến trình cho lần học sau.
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <div className="rounded-full border border-cyan-200/15 bg-cyan-200/10 px-3 py-1.5 text-xs text-cyan-50">
                        Mentor AI
                      </div>
                      <div className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1.5 text-xs text-white/68">
                        Mind Map
                      </div>
                      <div className="rounded-full border border-amber-200/15 bg-amber-200/10 px-3 py-1.5 text-xs text-amber-50">
                        History & Quiz
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {floatingNotes.map((item, index) => (
                <motion.div
                  key={item.title}
                  animate={
                    shouldReduceMotion
                      ? undefined
                      : {
                          y: [0, -8, 0],
                        }
                  }
                  transition={
                    shouldReduceMotion
                      ? undefined
                      : {
                          delay: index * 0.4,
                          duration: 5 + index,
                          ease: "easeInOut",
                          repeat: Infinity,
                        }
                  }
                  className={`absolute ${item.className} rounded-full border border-white/10 bg-[#061624]/85 px-4 py-2 backdrop-blur-xl`}
                >
                  <div className="text-[0.68rem] uppercase tracking-[0.18em] text-white/40">{item.title}</div>
                  <div className="mt-1 text-sm font-medium text-white/86">{item.value}</div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        <section className="border-y border-white/8 bg-white/[0.02]">
          <div className="overflow-hidden">
            <div className="landing-marquee-track flex min-w-max gap-3 py-4">
              {marqueeSignals.concat(marqueeSignals).map((item, index) => (
                <div
                  key={`${item}-${index}`}
                  className="rounded-full border border-white/10 bg-white/[0.05] px-4 py-2 text-sm text-white/68"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="signal-stack" className="container px-4 py-20 lg:py-24">
          <motion.div {...reveal()} className="mx-auto max-w-3xl text-center">
            <Badge className="h-auto rounded-full border border-white/10 bg-white/[0.06] px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-white/72">
              Tính năng nổi bật
            </Badge>
            <h2
              className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl"
              style={{ fontFamily: headlineFont }}
            >
              DUO MIND được thiết kế để biến việc học
              <span className="block text-white/72">thành một hành trình có định hướng và có chiều sâu.</span>
            </h2>
            <p className="mt-5 text-base leading-8 text-white/64 sm:text-lg">
              Từ hiểu người học, gợi ý lộ trình, phân tích nội dung cho đến mở rộng kiến thức mới,
              mọi tính năng đều được nối lại thành một flow học tập rõ ràng thay vì các công cụ rời rạc.
            </p>
          </motion.div>

          <div className="mt-12 grid gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <motion.div
              {...reveal(0.08)}
              whileHover={shouldReduceMotion ? undefined : { y: -8 }}
              className="rounded-[2.2rem] border border-white/10 bg-[linear-gradient(145deg,rgba(7,24,37,0.94),rgba(5,18,29,0.98))] p-6 shadow-[0_28px_90px_rgba(0,0,0,0.28)]"
            >
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.22em] text-cyan-100/58">Learning ecosystem</div>
                  <div
                    className="mt-2 text-2xl font-semibold tracking-[-0.05em] text-white"
                    style={{ fontFamily: headlineFont }}
                  >
                    Các mảnh ghép của DUO MIND liên kết với nhau trong một flow duy nhất.
                  </div>
                </div>
                <div className="rounded-full border border-white/10 bg-white/[0.05] px-4 py-2 text-sm text-white/64">
                  Cá nhân hóa từ đầu, giữ tiến độ về sau
                </div>
              </div>

              <div className="mt-8 grid gap-4 md:grid-cols-[0.95fr_1.05fr]">
                <div className="rounded-[1.8rem] border border-white/10 bg-white/[0.04] p-4">
                  <div className="flex items-center gap-2 text-sm text-cyan-50">
                    <BrainCircuit className="size-4" />
                    Hệ học tập DUO MIND
                  </div>
                  <div className="mt-5 space-y-3">
                    {[
                      "Onboarding 4 bước giúp hệ thống hiểu mục tiêu, độ tuổi, ngành học và phong cách tiếp nhận kiến thức",
                      "Mentor AI tư vấn định hướng, kỹ năng còn thiếu và bước đi tiếp theo theo đúng hồ sơ của bạn",
                      "Analyze, Explore, Quiz và History biến mỗi phiên học thành kiến thức có thể xem lại và tái sử dụng",
                    ].map((item, index) => (
                      <div
                        key={item}
                        className="flex gap-3 rounded-[1.3rem] border border-white/10 bg-[#081521] px-4 py-3 text-sm text-white/70"
                      >
                        <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-300/10 text-cyan-100">
                          {index + 1}
                        </div>
                        <span className="leading-7">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid gap-4">
                  {[
                    {
                      icon: Zap,
                      title: "Cá nhân hóa bằng AI",
                      description:
                        "DUO MIND dùng dữ liệu onboarding để điều chỉnh persona, độ khó, ví dụ và gợi ý học tập phù hợp với từng người dùng.",
                    },
                    {
                      icon: Layers3,
                      title: "Học từ nội dung thật",
                      description:
                        "Bạn có thể đem chính nội dung đang học vào Analyze hoặc đặt một câu hỏi mới trong Explore để biến kiến thức thành thứ dễ hấp thụ hơn.",
                    },
                    {
                      icon: ShieldCheck,
                      title: "Theo dõi được tiến bộ",
                      description:
                        "Lịch sử học, bookmark, quiz và các bản tổng hợp giúp người học không mất dấu tiến trình sau mỗi lần quay lại.",
                    },
                  ].map((item) => {
                    const Icon = item.icon

                    return (
                      <div
                        key={item.title}
                        className="rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-4"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-cyan-300/10 text-cyan-100">
                            <Icon className="size-4" />
                          </div>
                          <div className="text-lg font-semibold text-white">{item.title}</div>
                        </div>
                        <p className="mt-3 text-sm leading-7 text-white/68">{item.description}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
            </motion.div>

            <div className="grid gap-5">
              {featureCards.map((item, index) => {
                const Icon = item.icon

                return (
                  <motion.div
                    key={item.title}
                    {...reveal(0.12 + index * 0.06)}
                    whileHover={shouldReduceMotion ? undefined : { y: -6, scale: 1.01 }}
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
          </div>
        </section>

        <section id="motion-loop" className="container px-4 pb-24">
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
                  Bạn không chỉ nhận một câu trả lời từ AI. DUO MIND bắt đầu bằng việc hiểu người học,
                  sau đó hỗ trợ học sâu bằng nhiều chế độ khác nhau và cuối cùng giữ lại toàn bộ tiến trình
                  để bạn tiếp tục ở bất kỳ phiên nào sau đó.
                </p>
              </div>

              <div className="grid gap-5 md:grid-cols-3">
                {flowSteps.map((item, index) => {
                  const Icon = item.icon

                  return (
                    <motion.div
                      key={item.title}
                      {...reveal(0.08 + index * 0.08)}
                      whileHover={shouldReduceMotion ? undefined : { y: -8 }}
                      className="relative rounded-[1.8rem] border border-white/10 bg-[#061320]/90 p-5"
                    >
                      <div className="absolute inset-x-6 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(125,211,252,0.8),transparent)]" />
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-xs uppercase tracking-[0.22em] text-white/42">{item.kicker}</div>
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
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(103,232,249,0.18),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(253,230,138,0.16),transparent_28%)]" />
            <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
              <div className="max-w-3xl">
                <Badge className="h-auto rounded-full border border-white/10 bg-white/[0.06] px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-white/74">
                  Sẵn sàng bắt đầu
                </Badge>
                <h2
                  className="mt-5 text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl"
                  style={{ fontFamily: headlineFont }}
                >
                  DUO MIND là nơi bạn phân tích, khám phá và phát triển tri thức cùng AI trong một không gian duy nhất.
                </h2>
                <p className="mt-5 text-base leading-8 text-white/66">
                  Đăng ký để hoàn thành onboarding và mở toàn bộ hệ sinh thái học tập gồm Mentor AI,
                  Analyze, Explore, mind map, infographic, quiz và lịch sử học tập cá nhân hóa theo chính bạn.
                </p>
              </div>

              <div className="flex flex-wrap gap-3 lg:justify-end">
                <Button
                  asChild
                  size="lg"
                  className="h-12 rounded-full bg-[linear-gradient(120deg,#ecfeff_0%,#67e8f9_38%,#7dd3fc_68%,#fde68a_100%)] px-6 text-slate-950 shadow-[0_22px_60px_rgba(14,165,233,0.24)] hover:brightness-105"
                >
                  <Link href={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </Link>
                </Button>

                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 rounded-full border-white/12 bg-white/[0.04] px-6 text-white hover:bg-white/[0.08] hover:text-white"
                >
                  <Link href="#signal-stack">Xem lại phần giữa trang</Link>
                </Button>
              </div>
            </div>
          </motion.div>
        </section>
      </div>
    </main>
  )
}
