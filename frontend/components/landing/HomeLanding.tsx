"use client"

import { motion, useReducedMotion } from "framer-motion"
import type { LucideIcon } from "lucide-react"
import {
  ArrowRight,
  BrainCircuit,
  Compass,
  FileText,
  MessagesSquare,
  Network,
  Route,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react"
import { useEffect, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  conclusionBullets,
  demoJourney,
  discussionCards,
  methodologyFlow,
  objectiveCards,
  openingSignals,
  pitchDeckSections,
  problemCards,
  resultComparisons,
  type PitchDeckSectionMeta,
  valueCards,
} from "@/lib/pitch-deck-content"

type HomeLandingProps = {
  navHref: string
  navLabel: string
  primaryHref: string
  primaryLabel: string
  statusLabel: string
}

const sectionIcons: Record<string, LucideIcon> = {
  opening: BrainCircuit,
  problem: Target,
  aims: Sparkles,
  methodology: Network,
  results: TrendingUp,
  discussion: MessagesSquare,
  conclusion: Route,
}

const impactSignals = [
  { label: "Biểu hiện", value: "Không biết học gì trước" },
  { label: "Hệ quả", value: "Học nhiều nhưng khó tiến bộ" },
  { label: "Khoảng trống", value: "Thiếu vòng phản hồi cá nhân hóa" },
]

const productProofPoints = [
  "Mentor AI trả lời theo đúng loại nhu cầu thay vì phản hồi một kiểu cho mọi câu hỏi.",
  "Explore buộc AI giải thích đúng bản chất chủ đề và bám thẳng câu hỏi người học vừa đặt ra.",
  "Analyze giúp biết nội dung đúng hay sai, phần trọng tâm cần nắm và nguồn tham khảo để đối chiếu.",
]

const systemPrinciples = [
  {
    title: "Question first",
    detail: "Câu hỏi và mục tiêu học tập phải đi trước, hồ sơ chỉ là ngữ cảnh hỗ trợ.",
  },
  {
    title: "Role-based AI",
    detail: "Mentor, Explore và Analyze được thiết kế theo vai trò khác nhau nên output cũng khác nhau.",
  },
  {
    title: "Evidence aware",
    detail: "Khi kiểm tra kiến thức, hệ thống ưu tiên nguồn và logic xác minh thay vì suy đoán theo trí nhớ mô hình.",
  },
]

const outputExamples = [
  {
    title: "Định hướng nghề nghiệp",
    detail: "Từ onboarding và hội thoại, hệ thống chốt vai trò mục tiêu, điểm mạnh hiện có và khoảng trống ưu tiên.",
    icon: Compass,
  },
  {
    title: "Kiến thức đúng trọng tâm",
    detail: "Explore trình bày lại khái niệm, cơ chế và cấu trúc theo đúng câu hỏi người học vừa đặt ra.",
    icon: Sparkles,
  },
  {
    title: "Sửa hiểu sai có chứng cứ",
    detail: "Analyze giúp người học biết nội dung nào đúng, nội dung nào sai và có thể mở nguồn tham khảo liên quan.",
    icon: ScanSearch,
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
  const [activeSection, setActiveSection] = useState(pitchDeckSections[0]?.id ?? "opening")
  const headlineFont = "var(--font-nunito), var(--font-be-vietnam-pro), sans-serif"

  useEffect(() => {
    const nodes = pitchDeckSections
      .map((section) => document.getElementById(section.id))
      .filter((node): node is HTMLElement => Boolean(node))

    if (!nodes.length) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio)

        if (visible[0]?.target?.id) {
          setActiveSection(visible[0].target.id)
        }
      },
      {
        rootMargin: "-18% 0px -46% 0px",
        threshold: [0.25, 0.45, 0.65],
      }
    )

    nodes.forEach((node) => observer.observe(node))
    return () => observer.disconnect()
  }, [])

  const reveal = (delay = 0, y = 28) => ({
    initial: false,
    whileInView: { opacity: 1, y: 0, scale: 1 },
    viewport: { amount: 0.25, once: true },
    transition: {
      delay,
      duration: shouldReduceMotion ? 0 : 0.72,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  })

  return (
    <main className="relative overflow-x-clip bg-[#07131d] text-slate-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="pitch-grid absolute inset-0 opacity-65" />
        <div className="pitch-noise absolute inset-0 opacity-60" />
        <div className="absolute left-[-12rem] top-16 h-80 w-80 rounded-full bg-cyan-300/12 blur-3xl" />
        <div className="absolute right-[-10rem] top-56 h-96 w-96 rounded-full bg-amber-200/10 blur-3xl" />
        <div className="absolute bottom-20 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-emerald-300/10 blur-3xl" />
      </div>

      <div className="relative">
        <div className="sticky top-0 z-50 px-3 pt-3 sm:px-4 sm:pt-4">
          <motion.div
            {...reveal()}
            className="mx-auto max-w-7xl rounded-[1.8rem] border border-white/10 bg-[#07131d]/82 px-3 py-3 shadow-[0_24px_60px_rgba(0,0,0,0.28)] backdrop-blur-2xl sm:px-4"
          >
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:gap-4">
              <div className="flex min-w-0 items-center gap-3 xl:w-[18rem] xl:shrink-0">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-white/12 bg-white/[0.06] text-cyan-100">
                  <BrainCircuit className="size-4" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold tracking-[0.24em] text-white">DUO MIND</div>
                  <div className="text-xs text-white/58">Pitch deck học thuật cho hệ thống AI cố vấn học tập</div>
                </div>
              </div>

              <div className="min-w-0 flex-1">
                <div className="rounded-[1.4rem] border border-white/8 bg-white/[0.04] px-2 py-2">
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 w-8 bg-gradient-to-r from-[#07131d] via-[#07131d]/80 to-transparent" />
                    <div className="pointer-events-none absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-[#07131d] via-[#07131d]/80 to-transparent" />
                    <div className="scrollbar-none flex gap-2 overflow-x-auto px-1">
                      {pitchDeckSections.map((section) => {
                        const Icon = sectionIcons[section.id] ?? FileText
                        const isActive = activeSection === section.id

                        return (
                          <a
                            key={section.id}
                            href={`#${section.id}`}
                            className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-2 text-[0.92rem] transition-all ${
                              isActive
                                ? "border-cyan-200/30 bg-cyan-200/14 text-white shadow-[0_10px_26px_rgba(34,211,238,0.08)]"
                                : "border-white/10 bg-transparent text-white/66 hover:border-white/18 hover:bg-white/[0.05] hover:text-white"
                            }`}
                          >
                            <Icon className="size-3.5 shrink-0" />
                            <span className="text-[0.62rem] uppercase tracking-[0.18em] text-white/40">
                              {section.index}
                            </span>
                            <span className="whitespace-nowrap">{section.navLabel}</span>
                          </a>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 xl:shrink-0 xl:justify-end">
                <Button
                  asChild
                  variant="outline"
                  className="h-10 rounded-full border-white/14 bg-white/[0.04] px-4 text-white hover:bg-white/[0.08] hover:text-white"
                >
                  <a href={navHref}>
                    {navLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </a>
                </Button>
                <Button
                  asChild
                  className="h-10 rounded-full bg-[linear-gradient(120deg,#eefbf9_0%,#7dd3fc_34%,#67e8f9_66%,#fde68a_100%)] px-4 text-slate-950 hover:brightness-105"
                >
                  <a href={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </a>
                </Button>
              </div>
            </div>
          </motion.div>
        </div>

        <section id="opening" className="flex min-h-[96vh] items-center px-4 pb-16 pt-10 scroll-mt-32">
          <div className="container grid gap-10 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
            <div className="space-y-8">
              <motion.div {...reveal(0.04)} className="space-y-4">
                <Badge className="h-auto rounded-full border border-white/10 bg-white/[0.05] px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-white/78">
                  {pitchDeckSections[0].posterLabel} • Problem / Solution / Value
                </Badge>
                <div className="flex flex-wrap gap-2 text-sm text-white/64">
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
                    Audience: Giảng viên / Hội đồng
                  </span>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5">
                    HTML5 presentation landing
                  </span>
                </div>
              </motion.div>

              <motion.div {...reveal(0.1)} className="space-y-5">
                <p className="text-sm uppercase tracking-[0.28em] text-cyan-100/75">Thesis Statement</p>
                <h1
                  className="max-w-5xl text-5xl font-semibold leading-[0.95] tracking-[-0.06em] text-white sm:text-6xl lg:text-7xl"
                  style={{ fontFamily: headlineFont }}
                >
                  {pitchDeckSections[0].title}
                </h1>
                <p className="max-w-3xl text-base leading-8 text-white/72 sm:text-lg">
                  {pitchDeckSections[0].thesis}
                </p>
              </motion.div>

              <motion.div {...reveal(0.16)} className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5 backdrop-blur-xl">
                <div className="text-xs uppercase tracking-[0.18em] text-white/44">Luận cứ trung tâm của đề tài</div>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  {[
                    {
                      title: "Vấn đề",
                      detail: "Người học thiếu định hướng cá nhân hóa và dễ học sai trọng tâm vì không biết mình đang thiếu gì.",
                    },
                    {
                      title: "Giải pháp",
                      detail: "DUO MIND dùng bối cảnh người học và pipeline AI rõ vai trò để biến dữ liệu thành gợi ý học tập có hành động.",
                    },
                    {
                      title: "Giá trị",
                      detail: "Hệ thống rút ngắn thời gian định hướng, tăng độ đúng trọng tâm và tạo vòng lặp tiến bộ có thể theo dõi.",
                    },
                  ].map((item) => (
                    <div key={item.title} className="rounded-[1.6rem] border border-white/10 bg-[#091a27]/80 p-4">
                      <div className="text-xs uppercase tracking-[0.18em] text-white/45">{item.title}</div>
                      <p className="mt-3 text-sm leading-7 text-white/74">{item.detail}</p>
                    </div>
                  ))}
                </div>
              </motion.div>

              <motion.div {...reveal(0.22)} className="flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="h-12 rounded-full bg-[linear-gradient(120deg,#eefbf9_0%,#7dd3fc_34%,#67e8f9_66%,#fde68a_100%)] px-6 text-slate-950 hover:brightness-105"
                >
                  <a href="#methodology">
                    Xem mô hình vận hành
                    <ArrowRight className="ml-2 size-4" />
                  </a>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 rounded-full border-white/14 bg-white/[0.04] px-6 text-white hover:bg-white/[0.08] hover:text-white"
                >
                  <a href={primaryHref}>
                    {primaryLabel}
                    <ArrowRight className="ml-2 size-4" />
                  </a>
                </Button>
              </motion.div>
            </div>

            <motion.div
              {...reveal(0.14)}
              className="pitch-panel relative overflow-hidden rounded-[2.6rem] border border-white/10 bg-[linear-gradient(160deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03))] p-5 sm:p-6"
            >
              <div className="pitch-beam" />
              <div className="relative space-y-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-white/40">Opening Narrative</div>
                    <div className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white" style={{ fontFamily: headlineFont }}>
                      Giá trị của website không nằm ở một câu trả lời hay, mà nằm ở khả năng dẫn người học đi đúng hướng.
                    </div>
                  </div>
                  <ShieldCheck className="mt-1 size-5 text-cyan-100" />
                </div>

                <div className="grid gap-3">
                  {openingSignals.map((item, index) => (
                    <motion.div
                      key={item.title}
                      {...reveal(0.2 + index * 0.05, 22)}
                      className="rounded-[1.7rem] border border-white/10 bg-[#081520]/92 p-4"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex size-9 items-center justify-center rounded-2xl bg-white/[0.06] text-sm font-semibold text-cyan-100">
                          {index + 1}
                        </div>
                        <div className="text-lg font-semibold text-white">{item.title}</div>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-white/68">{item.detail}</p>
                    </motion.div>
                  ))}
                </div>

                <div className="rounded-[1.8rem] border border-cyan-200/14 bg-cyan-200/[0.08] p-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-cyan-50/78">Current framing</div>
                  <p className="mt-3 text-sm leading-7 text-white/80">{statusLabel}</p>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section id="problem" className="flex min-h-[92vh] items-center px-4 py-16 scroll-mt-32">
          <div className="container grid gap-6 lg:grid-cols-[0.88fr_1.12fr] lg:items-start">
            <motion.div {...reveal()} className="space-y-6">
              <SectionHeader section={pitchDeckSections[1]} headlineFont={headlineFont} />
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5">
                <div className="text-xs uppercase tracking-[0.18em] text-white/42">Chứng minh vấn đề</div>
                <p className="mt-4 text-base leading-8 text-white/72">{pitchDeckSections[1].thesis}</p>
                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  {impactSignals.map((item) => (
                    <div key={item.label} className="rounded-[1.4rem] border border-white/10 bg-[#091925]/88 p-4">
                      <div className="text-xs uppercase tracking-[0.16em] text-white/42">{item.label}</div>
                      <div className="mt-3 text-lg font-semibold text-white">{item.value}</div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            <div className="grid gap-4 md:grid-cols-3">
              {problemCards.map((item, index) => (
                <motion.div
                  key={item.title}
                  {...reveal(0.08 + index * 0.06)}
                  className="rounded-[1.9rem] border border-white/10 bg-[#081520]/94 p-5"
                >
                  <div className="text-xs uppercase tracking-[0.2em] text-white/42">Vấn đề {index + 1}</div>
                  <div className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-white">{item.title}</div>
                  <p className="mt-4 text-sm leading-7 text-white/66">{item.detail}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="aims" className="flex min-h-[92vh] items-center px-4 py-16 scroll-mt-32">
          <div className="container grid gap-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-start">
            <motion.div {...reveal()} className="space-y-6">
              <SectionHeader section={pitchDeckSections[2]} headlineFont={headlineFont} />
              <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.03))] p-6">
                <div className="text-xs uppercase tracking-[0.2em] text-white/44">Learning framework</div>
                <div className="mt-5 grid gap-3">
                  {[
                    "Lắng nghe mục tiêu và bối cảnh trước khi gợi ý.",
                    "Chẩn đoán khoảng trống thay vì liệt kê tri thức chung.",
                    "Trả về đầu ra hành động: học gì, sửa gì, hỏi gì tiếp.",
                    "Duy trì vòng phản hồi qua mentor, explore, analyze và history.",
                  ].map((item, index) => (
                    <div key={item} className="rounded-[1.5rem] border border-white/10 bg-[#081520]/90 px-4 py-3 text-sm leading-7 text-white/72">
                      <span className="mr-3 font-semibold text-cyan-100">{index + 1}.</span>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            <div className="grid gap-4 sm:grid-cols-2">
              {objectiveCards.map((item, index) => (
                <motion.div
                  key={item.title}
                  {...reveal(0.08 + index * 0.05)}
                  className="rounded-[1.9rem] border border-white/10 bg-white/[0.05] p-5"
                >
                  <div className="text-xs uppercase tracking-[0.18em] text-white/42">Objective {index + 1}</div>
                  <div className="mt-3 text-xl font-semibold text-white">{item.title}</div>
                  <p className="mt-3 text-sm leading-7 text-white/66">{item.detail}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="methodology" className="flex min-h-[92vh] items-center px-4 py-16 scroll-mt-32">
          <div className="container space-y-8">
            <motion.div {...reveal()} className="grid gap-6 lg:grid-cols-[0.82fr_1.18fr] lg:items-end">
              <SectionHeader section={pitchDeckSections[3]} headlineFont={headlineFont} />
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5">
                <div className="text-xs uppercase tracking-[0.18em] text-white/42">Hệ thống vận hành như thế nào</div>
                <p className="mt-4 text-base leading-8 text-white/72">{pitchDeckSections[3].thesis}</p>
              </div>
            </motion.div>

            <div className="grid gap-4 lg:grid-cols-5">
              {methodologyFlow.map((item, index) => (
                <motion.div
                  key={item.step}
                  {...reveal(0.06 + index * 0.06)}
                  className="relative rounded-[2rem] border border-white/10 bg-[#081520]/92 p-5"
                >
                  {index < methodologyFlow.length - 1 ? (
                    <div className="pointer-events-none absolute right-[-1.15rem] top-1/2 hidden h-px w-9 -translate-y-1/2 bg-gradient-to-r from-cyan-200/60 to-transparent lg:block" />
                  ) : null}
                  <div className="text-xs uppercase tracking-[0.2em] text-white/42">Step {item.step}</div>
                  <div className="mt-4 text-xl font-semibold text-white">{item.title}</div>
                  <p className="mt-3 text-sm leading-7 text-white/66">{item.description}</p>
                  <div className="mt-5 rounded-[1.4rem] border border-cyan-200/14 bg-cyan-200/[0.08] px-4 py-3 text-sm text-cyan-50/88">
                    {item.output}
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              {systemPrinciples.map((item, index) => (
                <motion.div
                  key={item.title}
                  {...reveal(0.16 + index * 0.04)}
                  className="rounded-[1.9rem] border border-white/10 bg-white/[0.05] p-5"
                >
                  <div className="text-xs uppercase tracking-[0.18em] text-white/42">Principle {index + 1}</div>
                  <div className="mt-3 text-xl font-semibold text-white">{item.title}</div>
                  <p className="mt-3 text-sm leading-7 text-white/66">{item.detail}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="results" className="flex min-h-[92vh] items-center px-4 py-16 scroll-mt-32">
          <div className="container space-y-8">
            <motion.div {...reveal()} className="grid gap-6 lg:grid-cols-[0.88fr_1.12fr] lg:items-start">
              <SectionHeader section={pitchDeckSections[4]} headlineFont={headlineFont} />
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5">
                <div className="text-xs uppercase tracking-[0.18em] text-white/42">Giá trị chứng minh trên sản phẩm</div>
                <div className="mt-4 grid gap-3">
                  {productProofPoints.map((item, index) => (
                    <div key={item} className="rounded-[1.5rem] border border-white/10 bg-[#091925]/88 px-4 py-3 text-sm leading-7 text-white/72">
                      <span className="mr-3 font-semibold text-cyan-100">{index + 1}.</span>
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            <div className="grid gap-5 xl:grid-cols-[1.08fr_0.92fr]">
              <div className="grid gap-4 md:grid-cols-2">
                {resultComparisons.map((group, index) => (
                  <motion.div
                    key={group.title}
                    {...reveal(0.06 + index * 0.05)}
                    className={`rounded-[2rem] border p-5 ${
                      index === 0 ? "border-rose-200/14 bg-rose-200/[0.06]" : "border-emerald-200/14 bg-emerald-200/[0.06]"
                    }`}
                  >
                    <div className="text-xs uppercase tracking-[0.2em] text-white/44">
                      {index === 0 ? "Mô hình cũ" : "Đầu ra của DUO MIND"}
                    </div>
                    <div className="mt-3 text-2xl font-semibold text-white">{group.title}</div>
                    <div className="mt-4 space-y-3">
                      {group.bullets.map((bullet) => (
                        <div key={bullet} className="rounded-[1.4rem] border border-white/10 bg-[#081520]/92 px-4 py-3 text-sm leading-7 text-white/70">
                          {bullet}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="grid gap-4">
                {outputExamples.map((item, index) => {
                  const Icon = item.icon

                  return (
                    <motion.div
                      key={item.title}
                      {...reveal(0.1 + index * 0.05)}
                      className="rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03))] p-5"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-xs uppercase tracking-[0.18em] text-white/42">Output Example {index + 1}</div>
                          <div className="mt-3 text-xl font-semibold text-white">{item.title}</div>
                        </div>
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.05] text-cyan-100">
                          <Icon className="size-5" />
                        </div>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-white/66">{item.detail}</p>
                    </motion.div>
                  )
                })}

                <div className="grid gap-4 md:grid-cols-3">
                  {valueCards.map((item, index) => (
                    <motion.div
                      key={item.title}
                      {...reveal(0.2 + index * 0.04)}
                      className="rounded-[1.8rem] border border-white/10 bg-white/[0.05] p-4"
                    >
                      <div className="text-xs uppercase tracking-[0.18em] text-white/42">Value {index + 1}</div>
                      <div className="mt-3 text-lg font-semibold text-white">{item.title}</div>
                      <p className="mt-3 text-sm leading-7 text-white/66">{item.detail}</p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="discussion" className="flex min-h-[92vh] items-center px-4 py-16 scroll-mt-32">
          <div className="container grid gap-8 lg:grid-cols-[0.86fr_1.14fr] lg:items-start">
            <motion.div {...reveal()} className="space-y-6">
              <SectionHeader section={pitchDeckSections[5]} headlineFont={headlineFont} />
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5">
                <div className="text-xs uppercase tracking-[0.18em] text-white/42">Vì sao giải pháp này hợp lý</div>
                <p className="mt-4 text-base leading-8 text-white/72">
                  DUO MIND không xem hồ sơ người dùng là câu trả lời cho mọi thứ. Hồ sơ chỉ là lớp bối cảnh.
                  Phần quan trọng hơn là AI phải biết người học đang cần gì, cần tri thức khách quan hay cần cố vấn,
                  và từ đó chọn đúng kiểu phản hồi.
                </p>
                <div className="mt-5 rounded-[1.6rem] border border-amber-200/14 bg-amber-200/[0.08] p-4 text-sm leading-7 text-white/78">
                  Giá trị học thuật của hệ thống nằm ở việc tổ chức AI theo vai trò sư phạm và logic quyết định,
                  thay vì chỉ thêm một lớp giao diện cho chatbot tổng quát.
                </div>
              </div>
            </motion.div>

            <div className="grid gap-4 sm:grid-cols-2">
              {discussionCards.map((item, index) => (
                <motion.div
                  key={item.title}
                  {...reveal(0.08 + index * 0.05)}
                  className="rounded-[1.95rem] border border-white/10 bg-[#081520]/92 p-5"
                >
                  <div className="text-xs uppercase tracking-[0.18em] text-white/42">Principle {index + 1}</div>
                  <div className="mt-3 text-xl font-semibold text-white">{item.title}</div>
                  <p className="mt-3 text-sm leading-7 text-white/66">{item.detail}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section id="conclusion" className="flex min-h-[92vh] items-center px-4 pb-20 pt-16 scroll-mt-32">
          <div className="container space-y-8">
            <motion.div {...reveal()} className="grid gap-6 lg:grid-cols-[0.82fr_1.18fr] lg:items-end">
              <SectionHeader section={pitchDeckSections[6]} headlineFont={headlineFont} />
              <div className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5">
                <div className="text-xs uppercase tracking-[0.18em] text-white/42">Kết luận</div>
                <p className="mt-4 text-base leading-8 text-white/72">{pitchDeckSections[6].thesis}</p>
              </div>
            </motion.div>

            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="grid gap-4">
                {conclusionBullets.map((item, index) => (
                  <motion.div
                    key={item.title}
                    {...reveal(0.08 + index * 0.05)}
                    className="rounded-[2rem] border border-white/10 bg-white/[0.05] p-5"
                  >
                    <div className="text-xs uppercase tracking-[0.18em] text-white/42">Kết luận {index + 1}</div>
                    <div className="mt-3 text-xl font-semibold text-white">{item.title}</div>
                    <p className="mt-3 text-sm leading-7 text-white/66">{item.detail}</p>
                  </motion.div>
                ))}
              </div>

              <motion.div
                {...reveal(0.12)}
                className="rounded-[2.4rem] border border-cyan-200/14 bg-[linear-gradient(160deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03))] p-6"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-xs uppercase tracking-[0.2em] text-cyan-50/78">Demo journey</div>
                    <div className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white" style={{ fontFamily: headlineFont }}>
                      Hành trình người học trên website
                    </div>
                  </div>
                  <Route className="mt-1 size-5 text-cyan-100" />
                </div>

                <div className="mt-6 grid gap-4">
                  {demoJourney.map((item, index) => (
                    <motion.div
                      key={item.step}
                      {...reveal(0.18 + index * 0.05, 24)}
                      className="rounded-[1.8rem] border border-white/10 bg-[#081520]/92 p-4"
                    >
                      <div className="flex gap-4">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-white/[0.06] text-sm font-semibold text-cyan-100">
                          {item.step}
                        </div>
                        <div>
                          <div className="text-lg font-semibold text-white">{item.title}</div>
                          <p className="mt-2 text-sm leading-7 text-white/68">{item.detail}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  <Button
                    asChild
                    size="lg"
                    className="h-12 rounded-full bg-[linear-gradient(120deg,#eefbf9_0%,#7dd3fc_34%,#67e8f9_66%,#fde68a_100%)] px-6 text-slate-950 hover:brightness-105"
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
                    className="h-12 rounded-full border-white/14 bg-white/[0.04] px-6 text-white hover:bg-white/[0.08] hover:text-white"
                  >
                    <a href={navHref}>
                      {navLabel}
                      <ArrowRight className="ml-2 size-4" />
                    </a>
                  </Button>
                </div>
              </motion.div>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}

function SectionHeader({
  section,
  headlineFont,
}: {
  section: PitchDeckSectionMeta
  headlineFont: string
}) {
  return (
    <div className="space-y-5">
      <Badge className="h-auto rounded-full border border-white/10 bg-white/[0.05] px-4 py-1 text-[0.72rem] uppercase tracking-[0.24em] text-white/74">
        {section.posterLabel} • Slide {section.index}
      </Badge>
      <h2
        className="max-w-4xl text-4xl font-semibold tracking-[-0.05em] text-white sm:text-5xl"
        style={{ fontFamily: headlineFont }}
      >
        {section.title}
      </h2>
      <p className="max-w-3xl text-base leading-8 text-white/68 sm:text-lg">{section.thesis}</p>
    </div>
  )
}
