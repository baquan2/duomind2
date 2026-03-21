"use client"

import { motion } from "framer-motion"
import {
  BookOpenCheck,
  ExternalLink,
  FileText,
  Network,
  Sparkles,
  Target,
  TriangleAlert,
} from "lucide-react"
import type { ReactNode } from "react"

import { AnalysisVerdictBadge } from "@/components/analyze/AccuracyBadge"
import { SummaryCard } from "@/components/analyze/SummaryCard"
import { KnowledgeDetail } from "@/components/explore/KnowledgeDetail"
import { MindMapViewer } from "@/components/mindmap/MindMapViewer"
import { QuizContainer } from "@/components/quiz/QuizContainer"
import { SourcesPanel } from "@/components/shared/SourcesPanel"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { getReadableGeneratedTitle } from "@/lib/generated-content"
import type { AnalyzeResult as AnalyzeResultData } from "@/types"

interface AnalysisResultProps {
  result: AnalyzeResultData
}

const QUICK_LINKS = [
  { href: "#kien-thuc-dung", label: "Kiến thức đúng" },
  { href: "#tong-quan", label: "Tổng quan" },
  { href: "#nguon-xac-minh", label: "Nguồn" },
  { href: "#dinh-chinh", label: "Đính chính" },
  { href: "#mind-map", label: "Mind map" },
  { href: "#on-tap", label: "Ôn tập" },
]

export function AnalysisResult({ result }: AnalysisResultProps) {
  const sourceLabel = result.source_label || "Nội dung nhập tay"
  const hasSources = result.sources.length > 0
  const displayTitle = getReadableGeneratedTitle(
    result.title,
    result.knowledge_detail_data?.title,
    result.input_preview,
    result.summary
  )
  const links = hasSources
    ? QUICK_LINKS
    : QUICK_LINKS.filter((link) => link.href !== "#nguon-xac-minh")
  const highlightedSources = result.sources.slice(0, 3)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
      className="space-y-5"
    >
      <div className="rounded-[2rem] border border-border/70 bg-[linear-gradient(135deg,_rgba(15,118,110,0.08),_rgba(255,247,221,0.78))] p-6 shadow-sm shadow-primary/10">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.22em] text-primary">
            <Sparkles className="size-3.5" />
            Kết quả phân tích
          </div>

          <div className="space-y-3">
            <h2 className="font-display text-3xl font-semibold text-balance">
              {displayTitle}
            </h2>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="bg-background/85">
                <FileText className="mr-1 size-3.5" />
                Nguồn đầu vào: {sourceLabel}
              </Badge>
              {hasSources ? (
                <Badge variant="outline" className="bg-background/85">
                  Đã đối chiếu {result.sources.length} nguồn web
                </Badge>
              ) : null}
            </div>
          </div>

          {result.input_preview ? (
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Nội dung đầu vào
              </p>
              <p className="mt-2 text-sm leading-6 text-foreground/80">
                {result.input_preview}
              </p>
            </div>
          ) : null}

          <div className="flex flex-wrap items-start gap-3">
            <AnalysisVerdictBadge verdict={result.verdict} compact />
            <div className="flex flex-wrap gap-2">
              {links.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="inline-flex items-center rounded-full border border-border/70 bg-background/80 px-3 py-1.5 text-sm font-medium text-foreground/80 transition-colors hover:border-primary/30 hover:text-primary"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </div>

          {hasSources ? (
            <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Nguồn tham khảo nhanh
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {highlightedSources.map((source) => (
                  <a
                    key={`${source.label}-${source.url}`}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex max-w-full items-center gap-2 rounded-full border border-border/70 bg-card px-3 py-1.5 text-sm text-foreground/80 transition-colors hover:border-primary/30 hover:text-primary"
                  >
                    <span className="truncate">{source.label}</span>
                    <ExternalLink className="size-3.5 shrink-0" />
                  </a>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <section id="tong-quan" className="space-y-4 scroll-mt-24">
        <SectionTitle
          icon={<Target className="size-5 text-primary" />}
          title="Tổng quan và điểm chính"
          description="Đọc phần tóm tắt trước để nắm ý cốt lõi, sau đó quét nhanh các điểm quan trọng."
        />
        <SummaryCard
          summary={result.summary}
          keyPoints={result.key_points}
          knowledgeDetailData={result.knowledge_detail_data}
        />
      </section>

      <section id="kien-thuc-dung" className="space-y-4 scroll-mt-24">
        <SectionTitle
          icon={<BookOpenCheck className="size-5 text-primary" />}
          title="Kiến thức đúng cần nắm"
          description="Phần này trình bày lại chủ đề theo đúng trục khái niệm, cơ chế, ví dụ và ứng dụng để bạn hiểu đúng sau khi xem phần đánh giá."
        />
        <KnowledgeDetail data={result.knowledge_detail_data} />
      </section>

      {hasSources ? (
        <section id="nguon-xac-minh" className="space-y-4 scroll-mt-24">
          <SectionTitle
            icon={<BookOpenCheck className="size-5 text-primary" />}
            title="Nguồn xác minh"
            description="Các nguồn này được dùng để kiểm tra lại tính đúng sai của nội dung và giảm việc model trả lời theo trí nhớ mơ hồ."
          />
          <SourcesPanel
            sources={result.sources}
            title="Nguồn tham khảo"
            description="Mỗi nguồn đều mở trực tiếp ra trang web hoặc bài viết liên quan để bạn kiểm tra lại nội dung phân tích."
          />
        </section>
      ) : null}

      <section id="dinh-chinh" className="space-y-4 scroll-mt-24">
        <SectionTitle
          icon={<TriangleAlert className="size-5 text-primary" />}
          title="Điểm cần đính chính"
          description="Các nhận định dưới đây là những chỗ AI cho rằng cần sửa lại để nội dung chính xác hơn."
        />

        {result.corrections.length === 0 ? (
          <Card className="border border-emerald-200 bg-emerald-50/80">
            <CardContent className="flex flex-col items-center gap-3 px-6 py-12 text-center text-emerald-800">
              <BookOpenCheck className="size-10" />
              <div className="space-y-1">
                <p className="font-medium">Nội dung hiện tại khá chính xác</p>
                <p className="text-sm text-emerald-700/80">
                  AI chưa phát hiện điểm sai nổi bật trong phần nội dung bạn đã gửi.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {result.corrections.map((correction, index) => (
              <Card
                key={`${correction.original}-${index}`}
                className="border border-amber-200/80 bg-amber-50/75"
              >
                <CardContent className="space-y-4 p-5">
                  <div className="flex items-start gap-3">
                    <TriangleAlert className="mt-0.5 size-5 shrink-0 text-amber-700" />
                    <div className="min-w-0 flex-1 space-y-3">
                      <div className="space-y-1">
                        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                          Nội dung gốc
                        </p>
                        <p className="text-sm text-rose-700 line-through">
                          {correction.original}
                        </p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                          Gợi ý sửa
                        </p>
                        <p className="font-medium text-emerald-700">
                          {correction.correction}
                        </p>
                      </div>

                      <div className="space-y-1">
                        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
                          Lý do
                        </p>
                        <p className="text-sm leading-6 text-muted-foreground">
                          {correction.explanation}
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section id="mind-map" className="space-y-4 scroll-mt-24">
        <SectionTitle
          icon={<Network className="size-5 text-primary" />}
          title="Mind map"
          description="Sơ đồ này tóm lại các mối liên hệ chính trong nội dung để bạn nhìn tổng thể nhanh hơn."
        />
        <MindMapViewer sessionId={result.session_id} initialData={result.mindmap_data} />
      </section>

      <section id="on-tap" className="space-y-4 scroll-mt-24">
        <SectionTitle
          icon={<BookOpenCheck className="size-5 text-primary" />}
          title="Ôn tập ngay"
          description="Tạo quiz từ chính nội dung vừa phân tích để kiểm tra mức độ hiểu bài trong cùng phiên."
        />
        <QuizContainer sessionId={result.session_id} />
      </section>
    </motion.div>
  )
}

function SectionTitle({
  icon,
  title,
  description,
}: {
  icon: ReactNode
  title: string
  description: string
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="font-display text-2xl font-semibold">{title}</h3>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  )
}
