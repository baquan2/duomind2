import type {
  AnalyzeResult,
  ExploreResult,
  KnowledgeDetailData,
  LearningSession,
} from "@/types"
import {
  buildInputPreview,
  extractSourceLabel,
  stripSourceLabel,
} from "@/lib/analysis-source"
import { normalizeAnalyzeVerdict } from "@/lib/analyze-verdict"
import { getReadableGeneratedTitle } from "@/lib/generated-content"

export function mapSessionToAnalyzeResult(session: LearningSession): AnalyzeResult {
  const rawContent = stripSourceLabel(session.user_input)

  return {
    session_id: session.id,
    title: getReadableGeneratedTitle(
      session.title,
      session.infographic_data?.title,
      rawContent,
      session.summary
    ),
    verdict: normalizeAnalyzeVerdict(
      session.verdict,
      session.accuracy_assessment,
      session.corrections?.length ?? 0,
      session.sources?.length ?? 0
    ),
    accuracy_score: session.accuracy_score ?? null,
    accuracy_assessment:
      (session.accuracy_assessment as AnalyzeResult["accuracy_assessment"]) ??
      "unverifiable",
    summary: session.summary ?? "",
    key_points: session.key_points ?? [],
    corrections: session.corrections ?? [],
    knowledge_detail_data:
      session.infographic_data ?? buildFallbackKnowledgeDetail(session),
    topic_tags: session.topic_tags ?? [],
    mindmap_data: session.mindmap_data ?? buildFallbackMindMap(session),
    sources: session.sources ?? [],
    source_label: extractSourceLabel(session.user_input) || "Nội dung nhập tay",
    input_preview: buildInputPreview(rawContent),
  }
}

export function mapSessionToExploreResult(session: LearningSession): ExploreResult {
  return {
    session_id: session.id,
    title: session.title,
    summary: session.summary ?? "",
    key_points: session.key_points ?? [],
    knowledge_detail_data:
      session.infographic_data ?? buildFallbackKnowledgeDetail(session),
    topic_tags: session.topic_tags ?? [],
    mindmap_data: session.mindmap_data ?? buildFallbackMindMap(session),
    sources: session.sources ?? [],
  }
}

function buildFallbackKnowledgeDetail(session: LearningSession): KnowledgeDetailData {
  const keyPoints = session.key_points ?? []
  const title = session.title
  const summary = session.summary ?? ""

  return {
    title,
    summary,
    detailed_sections: {
      core_concept: {
        title: "Khái niệm cốt lõi",
        content: keyPoints[0] ?? summary ?? `Giới thiệu nhanh về ${title}.`,
      },
      mechanism: {
        title: "Bản chất / cơ chế hoạt động",
        content:
          keyPoints[1] ?? "Giải thích cơ chế ở mức nền tảng để dễ nắm bản chất.",
      },
      components_and_relationships: {
        title: "Các thành phần chính và quan hệ giữa chúng",
        content:
          keyPoints[2] ?? "Chỉ ra các thành phần quan trọng và cách chúng liên kết với nhau.",
      },
      persona_based_example: {
        title: "Ví dụ trực quan",
        content:
          keyPoints[3] ?? "Dùng ví dụ ngắn, sát thực tế để làm rõ ý chính của chủ đề.",
      },
      real_world_applications: {
        title: "Ứng dụng thực tế",
        content:
          keyPoints[4] ?? "Tập trung vào nơi kiến thức này được dùng trong thực tế.",
      },
      common_misconceptions: {
        title: "Nhầm lẫn phổ biến",
        content: "Nhắc lại các hiểu sai thường gặp để tránh học lệch từ đầu.",
      },
      next_step_self_study: {
        title: "Điểm cần nắm tiếp",
        content: "Chốt lại phần cốt lõi, cơ chế và chỗ dễ nhầm trước khi mở rộng sang ví dụ khác.",
      },
    },
    teaching_adaptation: {
      focus_priority: "ưu tiên phần cốt lõi trước",
      tone: "rõ ràng, gần gũi, thiên về sư phạm",
      depth_control: "đi từ nền tảng đến ứng dụng",
      example_strategy: "dùng ví dụ trực quan và gần thực tế",
    },
  }
}

function buildFallbackMindMap(session: LearningSession) {
  const points = session.key_points?.slice(0, 5) ?? []
  const rootX = 0
  const rootY = 0

  const nodes = [
    {
      id: "root",
      type: "root" as const,
      data: {
        label: session.title,
        description: "Chủ đề trung tâm",
      },
      position: { x: rootX, y: rootY },
    },
    ...points.map((point, index) => ({
      id: `main_${index}`,
      type: "main" as const,
      data: {
        label: point,
        description: "Ý chính",
      },
      position: { x: -280 + index * 140, y: 170 },
    })),
  ]

  const edges = points.map((_, index) => ({
    id: `edge_root_main_${index}`,
    source: "root",
    target: `main_${index}`,
    type: "smoothstep",
  }))

  return { nodes, edges }
}
