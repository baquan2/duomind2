import type { KnowledgeDetailData } from "@/types"

const SECTION_KEYS: Array<keyof KnowledgeDetailData["detailed_sections"]> = [
  "core_concept",
  "mechanism",
  "components_and_relationships",
  "persona_based_example",
  "real_world_applications",
  "common_misconceptions",
]

function normalizeSentence(text: string) {
  return text.replace(/\s+/g, " ").trim()
}

function extractLeadSentence(text: string) {
  const normalized = normalizeSentence(text)
  if (!normalized) {
    return ""
  }

  const [firstSentence] = normalized.split(/(?<=[.!?])\s+/)
  return normalizeSentence(firstSentence || normalized)
}

export function extractKnowledgeBullets(
  data: KnowledgeDetailData | null | undefined,
  limit = 5
) {
  if (!data?.detailed_sections) {
    return []
  }

  const bullets: string[] = []
  for (const key of SECTION_KEYS) {
    const sentence = extractLeadSentence(data.detailed_sections[key]?.content || "")
    if (!sentence || bullets.includes(sentence)) {
      continue
    }
    bullets.push(sentence)
    if (bullets.length >= limit) {
      break
    }
  }

  return bullets
}
