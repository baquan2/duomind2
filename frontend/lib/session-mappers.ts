import type {
  AnalyzeResult,
  ExploreResult,
  InfographicData,
  LearningSession,
} from "@/types"
import {
  buildInputPreview,
  extractSourceLabel,
  stripSourceLabel,
} from "@/lib/analysis-source"

const FALLBACK_THEME = "#0f766e"

export function mapSessionToAnalyzeResult(session: LearningSession): AnalyzeResult {
  const rawContent = stripSourceLabel(session.user_input)

  return {
    session_id: session.id,
    title: session.title,
    accuracy_score: session.accuracy_score ?? null,
    accuracy_assessment:
      (session.accuracy_assessment as AnalyzeResult["accuracy_assessment"]) ??
      "unverifiable",
    summary: session.summary ?? "",
    key_points: session.key_points ?? [],
    corrections: session.corrections ?? [],
    topic_tags: session.topic_tags ?? [],
    mindmap_data: session.mindmap_data ?? buildFallbackMindMap(session),
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
    infographic_data:
      session.infographic_data ?? buildFallbackInfographic(session),
    topic_tags: session.topic_tags ?? [],
    mindmap_data: session.mindmap_data ?? buildFallbackMindMap(session),
  }
}

function buildFallbackInfographic(session: LearningSession): InfographicData {
  const sections =
    session.key_points?.map((point, index) => ({
      icon: `${index + 1}`,
      heading: `Key point ${index + 1}`,
      content: point,
    })) ?? []

  return {
    type: "list",
    theme_color: FALLBACK_THEME,
    title: session.title,
    subtitle: session.summary ?? "",
    sections,
    footer_note: "Infographic fallback generated from stored session data.",
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
