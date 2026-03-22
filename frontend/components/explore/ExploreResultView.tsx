"use client"

import { motion } from "framer-motion"
import { BookOpenText, Download, Loader2 } from "lucide-react"
import type { ReactNode } from "react"
import { useMemo, useState } from "react"

import { KnowledgeDetail } from "@/components/explore/KnowledgeDetail"
import { ExploreSummary } from "@/components/explore/ExploreSummary"
import { MindMapViewer } from "@/components/mindmap/MindMapViewer"
import { QuizContainer } from "@/components/quiz/QuizContainer"
import { SourcesPanel } from "@/components/shared/SourcesPanel"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { getSessionDetail } from "@/lib/api/history"
import { exportSessionAsWord } from "@/lib/session-export"
import type { ExploreResult } from "@/types"

interface ExploreResultViewProps {
  result: ExploreResult
  showHeader?: boolean
}

const SECTION_LINKS = [
  { id: "explore-summary", label: "Tổng quan" },
  { id: "explore-sources", label: "Nguồn đã dùng" },
  { id: "explore-related", label: "Tài liệu liên quan" },
  { id: "explore-knowledge", label: "Chi tiết kiến thức" },
  { id: "explore-mindmap", label: "Mind map" },
  { id: "explore-quiz", label: "Ôn tập" },
]

export function ExploreResultView({ result, showHeader = true }: ExploreResultViewProps) {
  const [downloading, setDownloading] = useState(false)
  const hasSources = result.sources.length > 0
  const hasRelated = result.related_materials.length > 0
  const hasSavedSession = Boolean(result.session_id)
  const saveStatus = result.save_metadata?.status ?? "full"
  const canExport = hasSavedSession
  const canQuiz = hasSavedSession

  const sectionLinks = useMemo(
    () =>
      SECTION_LINKS.filter((section) => {
        if (section.id === "explore-sources" && !hasSources) {
          return false
        }
        if (section.id === "explore-related" && !hasRelated) {
          return false
        }
        if (section.id === "explore-quiz" && !canQuiz) {
          return false
        }
        return true
      }),
    [canQuiz, hasRelated, hasSources]
  )

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    })
  }

  const handleDownloadWord = async () => {
    if (!result.session_id) {
      return
    }

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
      {saveStatus !== "full" ? (
        <Alert variant="destructive">
          <AlertDescription>
            {saveStatus === "failed"
              ? "AI đã tạo kết quả nhưng chưa lưu được phiên vào database. Bạn vẫn có thể đọc nội dung bên dưới, nhưng quiz, export và lịch sử sẽ chưa hoạt động cho phiên này."
              : "Phiên đã được lưu một phần. Một số dữ liệu mở rộng có thể chưa xuất hiện đầy đủ trong lịch sử."}
          </AlertDescription>
        </Alert>
      ) : null}

      {showHeader ? (
        <div className="rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.1),_rgba(255,247,221,0.82))] p-6 shadow-sm shadow-primary/10">
          <div className="space-y-4">
            <Badge className="border-0 bg-primary text-primary-foreground">
              {result.session_id ? `Phiên ${result.session_id.slice(0, 8)}` : "Phiên tạm thời"}
            </Badge>
            <div className="space-y-3">
              <h2 className="font-display text-3xl font-semibold text-balance">{result.title}</h2>
              <p className="max-w-3xl text-sm leading-7 text-foreground/75">
                Kết quả được chia theo từng phần rõ ràng để bạn đọc nhanh, hiểu nền tảng của chủ đề
                và chuyển sang ôn tập ngay khi cần.
              </p>
            </div>
            {canExport ? (
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
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="sticky top-3 z-10 rounded-2xl border border-border/70 bg-background/92 p-2 shadow-sm backdrop-blur">
        <div className="flex flex-wrap gap-2">
          {sectionLinks.map((section) => (
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
          knowledgeDetailData={result.knowledge_detail_data}
          topicTags={result.topic_tags}
        />
      </SectionBlock>

      {hasSources ? (
        <SectionBlock
          id="explore-sources"
          eyebrow="Bước 2"
          title="Nguồn đã dùng"
          description="Đây là các nguồn AI đã dùng để kiểm tra hoặc làm chắc phần giải thích."
        >
          <SourcesPanel
            sources={result.sources}
            title="Nguồn đã dùng"
            description="Mỗi nguồn bên dưới đóng vai trò kiểm chứng cho phần trả lời phía trên."
          />
        </SectionBlock>
      ) : null}

      {hasRelated ? (
        <SectionBlock
          id="explore-related"
          eyebrow={hasSources ? "Bước 3" : "Bước 2"}
          title="Tài liệu liên quan"
          description="Các liên kết này hữu ích để đọc sâu thêm sau khi bạn đã nắm được nền tảng."
        >
          <SourcesPanel
            sources={result.related_materials}
            title="Tài liệu nên xem thêm"
            description="Đây là các tài liệu mở rộng phù hợp với chủ đề hiện tại."
          />
        </SectionBlock>
      ) : null}

      <SectionBlock
        id="explore-knowledge"
        eyebrow={hasSources && hasRelated ? "Bước 4" : hasSources || hasRelated ? "Bước 3" : "Bước 2"}
        title="Chi tiết kiến thức"
        description="Phần này đi từ khái niệm, cơ chế, ví dụ đến ứng dụng và nhầm lẫn phổ biến."
      >
        <KnowledgeDetail data={result.knowledge_detail_data} />
      </SectionBlock>

      <SectionBlock
        id="explore-mindmap"
        eyebrow={hasSources && hasRelated ? "Bước 5" : hasSources || hasRelated ? "Bước 4" : "Bước 3"}
        title="Mind map"
        description="Sơ đồ được dựng trực tiếp từ kết quả AI để bạn nhìn được toàn cảnh chủ đề."
      >
        <MindMapViewer sessionId={result.session_id} initialData={result.mindmap_data} />
      </SectionBlock>

      {canQuiz ? (
        <SectionBlock
          id="explore-quiz"
          eyebrow={hasSources && hasRelated ? "Bước 6" : hasSources || hasRelated ? "Bước 5" : "Bước 4"}
          title="Ôn tập"
          description="Sau khi xem tổng quan, bạn có thể làm quiz để kiểm tra lại phần vừa học."
        >
          <QuizContainer sessionId={result.session_id} />
        </SectionBlock>
      ) : null}
    </motion.section>
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
          <p className="text-xs font-medium uppercase tracking-[0.24em] text-primary">{eyebrow}</p>
        </div>
        <h3 className="font-display text-2xl font-semibold">{title}</h3>
        <p className="text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  )
}
