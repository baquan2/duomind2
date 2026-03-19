"use client"

import { motion } from "framer-motion"

import { ExploreSummary } from "@/components/explore/ExploreSummary"
import { Infographic } from "@/components/explore/Infographic"
import { MindMapViewer } from "@/components/mindmap/MindMapViewer"
import { QuizContainer } from "@/components/quiz/QuizContainer"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import type { ExploreResult } from "@/types"

interface ExploreResultViewProps {
  result: ExploreResult
  showHeader?: boolean
}

const SECTION_LINKS = [
  { id: "explore-summary", label: "Tổng quan" },
  { id: "explore-infographic", label: "Infographic" },
  { id: "explore-mindmap", label: "Mind map" },
  { id: "explore-quiz", label: "Ôn tập" },
]

export function ExploreResultView({
  result,
  showHeader = true,
}: ExploreResultViewProps) {
  const coreTags = result.topic_tags.slice(0, 3)

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    })
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      className="space-y-6"
    >
      {showHeader ? (
        <div className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.1),_rgba(255,247,221,0.82))] p-6 shadow-sm shadow-primary/10">
            <div className="space-y-3">
              <Badge className="border-0 bg-primary text-primary-foreground">
                Phiên {result.session_id.slice(0, 8)}
              </Badge>
              <div className="space-y-3">
                <h2 className="font-display text-3xl font-semibold text-balance">
                  {result.title}
                </h2>
                <p className="max-w-3xl text-sm leading-7 text-foreground/75">
                  Kết quả được chia theo từng phần rõ ràng để bạn đọc nhanh, xem hình hóa
                  và chuyển sang ôn tập mà không phải đoán nên bắt đầu từ đâu.
                </p>
              </div>
              {coreTags.length ? (
                <div className="flex flex-wrap gap-2">
                  {coreTags.map((tag) => (
                    <Badge key={tag} variant="outline" className="bg-background/85">
                      {tag}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <ResultStat
              title="Ý chính"
              value={`${result.key_points.length}`}
              description="Các điểm quan trọng đã được AI gom lại."
            />
            <ResultStat
              title="Infographic"
              value={result.infographic_data?.sections?.length ? "Sẵn sàng" : "Dự phòng"}
              description="Đọc theo khối nhỏ, dễ quét và dễ nhớ hơn."
            />
            <ResultStat
              title="Mind map"
              value={result.mindmap_data?.nodes?.length ? "Đã tải" : "Đang chờ"}
              description="Sơ đồ khái niệm hiển thị ngay trong cùng phiên."
            />
          </div>
        </div>
      ) : null}

      <div className="sticky top-3 z-10 rounded-2xl border border-border/70 bg-background/92 p-2 shadow-sm backdrop-blur">
        <div className="flex flex-wrap gap-2">
          {SECTION_LINKS.map((section) => (
            <Button
              key={section.id}
              type="button"
              variant="outline"
              className="rounded-full"
              onClick={() => scrollToSection(section.id)}
            >
              {section.label}
            </Button>
          ))}
        </div>
      </div>

      <SectionBlock
        id="explore-summary"
        eyebrow="Bước 1"
        title="Tổng quan chủ đề"
        description="Đọc phần tóm tắt và các ý chính trước để nắm khung kiến thức."
      >
        <ExploreSummary
          summary={result.summary}
          keyPoints={result.key_points}
          topicTags={result.topic_tags}
        />
      </SectionBlock>

      <SectionBlock
        id="explore-infographic"
        eyebrow="Bước 2"
        title="Infographic"
        description="Phần này trình bày lại nội dung dưới dạng khối trực quan để bạn đọc nhanh hơn."
      >
        <Infographic data={result.infographic_data} />
      </SectionBlock>

      <SectionBlock
        id="explore-mindmap"
        eyebrow="Bước 3"
        title="Mind map"
        description="Sơ đồ được dựng trực tiếp từ kết quả AI đã tổng hợp, không cần chờ thêm request phụ."
      >
        <MindMapViewer sessionId={result.session_id} initialData={result.mindmap_data} />
      </SectionBlock>

      <SectionBlock
        id="explore-quiz"
        eyebrow="Bước 4"
        title="Ôn tập"
        description="Sau khi xem tổng quan, infographic và sơ đồ, bạn có thể chuyển sang quiz để kiểm tra lại."
      >
        <QuizContainer sessionId={result.session_id} />
      </SectionBlock>
    </motion.section>
  )
}

function ResultStat({
  title,
  value,
  description,
}: {
  title: string
  value: string
  description: string
}) {
  return (
    <Card className="border border-border/70 bg-card/92">
      <CardContent className="space-y-2 p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{title}</p>
        <p className="font-display text-2xl font-semibold">{value}</p>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}

function SectionBlock({
  id,
  eyebrow,
  title,
  description,
  children,
}: {
  id: string
  eyebrow: string
  title: string
  description: string
  children: React.ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-24 space-y-3">
      <div className="space-y-1">
        <p className="text-xs font-medium uppercase tracking-[0.24em] text-primary">
          {eyebrow}
        </p>
        <h3 className="font-display text-2xl font-semibold">{title}</h3>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  )
}
