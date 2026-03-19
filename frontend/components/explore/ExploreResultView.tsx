"use client"

import { motion } from "framer-motion"
import { BookOpenText, Download, Loader2 } from "lucide-react"
import type { ReactNode } from "react"
import { useState } from "react"

import { ExploreSummary } from "@/components/explore/ExploreSummary"
import { KnowledgeDetail } from "@/components/explore/KnowledgeDetail"
import { MindMapViewer } from "@/components/mindmap/MindMapViewer"
import { QuizContainer } from "@/components/quiz/QuizContainer"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { getSessionDetail } from "@/lib/api/history"
import { exportSessionAsWord } from "@/lib/session-export"
import type { ExploreResult } from "@/types"

interface ExploreResultViewProps {
  result: ExploreResult
  showHeader?: boolean
}

const SECTION_LINKS = [
  { id: "explore-summary", label: "Tổng quan" },
  { id: "explore-knowledge", label: "Chi tiết kiến thức" },
  { id: "explore-mindmap", label: "Mind map" },
  { id: "explore-quiz", label: "Ôn tập" },
]

export function ExploreResultView({
  result,
  showHeader = true,
}: ExploreResultViewProps) {
  const [downloading, setDownloading] = useState(false)
  const coreTags = result.topic_tags.slice(0, 3)
  const knowledgeSectionCount = Object.keys(result.knowledge_detail_data?.detailed_sections ?? {}).length

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    })
  }

  const handleDownloadWord = async () => {
    try {
      setDownloading(true)
      const sessionDetail = await getSessionDetail(result.session_id)
      await exportSessionAsWord(sessionDetail)
    } finally {
      setDownloading(false)
    }
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
            <div className="space-y-4">
              <Badge className="border-0 bg-primary text-primary-foreground">
                Phiên {result.session_id.slice(0, 8)}
              </Badge>
              <div className="space-y-3">
                <h2 className="font-display text-3xl font-semibold text-balance">
                  {result.title}
                </h2>
                <p className="max-w-3xl text-sm leading-7 text-foreground/75">
                  Kết quả được chia theo từng phần rõ ràng để bạn đọc nhanh, hiểu sâu, nhìn
                  được toàn cảnh chủ đề và chuyển sang ôn tập mà không phải đoán nên bắt đầu
                  từ đâu.
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
              <Button
                type="button"
                variant="outline"
                className="rounded-full bg-background/90"
                onClick={() => void handleDownloadWord()}
                disabled={downloading}
              >
                {downloading ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : (
                  <Download className="mr-2 size-4" />
                )}
                Tải file Word
              </Button>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <ResultStat
              title="Ý chính"
              value={`${result.key_points.length}`}
              description="Các điểm quan trọng đã được AI gom lại."
            />
            <ResultStat
              title="Chi tiết kiến thức"
              value={knowledgeSectionCount ? "Sẵn sàng" : "Dự phòng"}
              description="Giải thích sâu theo logic học tập và bối cảnh persona."
            />
            <ResultStat
              title="Mind map"
              value={result.mindmap_data?.nodes?.length ? "Đã tải" : "Đang chờ"}
              description="Sơ đồ khái niệm hiển thị trong cùng phiên học."
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
        id="explore-knowledge"
        eyebrow="Bước 2"
        title="Chi tiết kiến thức"
        description="Phần này trình bày lại chủ đề theo logic học tập sâu: bản chất, cơ chế, ví dụ theo persona, ứng dụng và bước tự học tiếp."
      >
        <KnowledgeDetail data={result.knowledge_detail_data} />
      </SectionBlock>

      <SectionBlock
        id="explore-mindmap"
        eyebrow="Bước 3"
        title="Mind map"
        description="Sơ đồ được dựng trực tiếp từ kết quả AI đã tổng hợp để bạn nhìn được toàn cảnh chủ đề."
      >
        <MindMapViewer sessionId={result.session_id} initialData={result.mindmap_data} />
      </SectionBlock>

      <SectionBlock
        id="explore-quiz"
        eyebrow="Bước 4"
        title="Ôn tập"
        description="Sau khi xem tổng quan, chi tiết kiến thức và sơ đồ, bạn có thể chuyển sang quiz để kiểm tra lại."
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
  children: ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-24 space-y-3">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <BookOpenText className="size-4 text-primary" />
          <p className="text-xs font-medium uppercase tracking-[0.24em] text-primary">
            {eyebrow}
          </p>
        </div>
        <h3 className="font-display text-2xl font-semibold">{title}</h3>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  )
}
