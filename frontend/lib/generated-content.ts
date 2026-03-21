import type { KnowledgeDetailData, KnowledgeSectionKey } from "@/types"

const TITLE_FILLER_ENDINGS = new Set([
  "la",
  "cac",
  "nhung",
  "mot",
  "duoc",
  "dung",
  "de",
  "voi",
  "cua",
  "va",
  "hay",
  "hoac",
])

const OVERVIEW_SECTION_KEYS: KnowledgeSectionKey[] = [
  "core_concept",
  "mechanism",
  "components_and_relationships",
  "real_world_applications",
]

const TAKEAWAY_SECTION_KEYS: KnowledgeSectionKey[] = [
  "core_concept",
  "mechanism",
  "persona_based_example",
  "common_misconceptions",
]

function normalizeText(text?: string | null) {
  return (text || "").replace(/\s+/g, " ").trim()
}

function foldText(text?: string | null) {
  return normalizeText(text)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
}

function cleanTitleCandidate(text?: string | null) {
  const normalized = normalizeText(text).replace(/[?!.:,;]+$/g, "").trim()
  if (!normalized) {
    return ""
  }

  const words = normalized.split(/\s+/)
  while (words.length && TITLE_FILLER_ENDINGS.has(foldText(words[words.length - 1]))) {
    words.pop()
  }

  return words.slice(0, 8).join(" ").trim()
}

function extractCoreTitleCandidate(text?: string | null) {
  const normalized = normalizeText(text)
  if (!normalized) {
    return ""
  }

  const explicitPatterns = [
    /^(?:khái niệm|khai niem|định nghĩa|dinh nghia)\s+(?:của|cua)\s+(.+?)\s+(?:là|la)\b/i,
    /^(?:khái niệm|khai niem|định nghĩa|dinh nghia)\s+(?:về|ve)\s+(.+?)\s+(?:là|la)\b/i,
    /^(.+?)\s+(?:là|la)\s+(?:một|mot|quá trình|qua trinh|hệ thống|he thong|ngôn ngữ|ngon ngu)\b/i,
  ]

  for (const pattern of explicitPatterns) {
    const match = normalized.match(pattern)
    if (match?.[1]) {
      const cleaned = cleanTitleCandidate(match[1])
      if (cleaned) {
        return cleaned
      }
    }
  }

  return cleanTitleCandidate(normalized.split(/[.:;]/, 1)[0] || normalized)
}

function titleNeedsCleanup(title?: string | null) {
  const normalized = cleanTitleCandidate(title)
  if (!normalized) {
    return true
  }

  const folded = foldText(normalized)
  if (
    folded.startsWith("khai niem cua ") ||
    folded.startsWith("dinh nghia cua ") ||
    folded.startsWith("khai niem ve ") ||
    folded.startsWith("dinh nghia ve ")
  ) {
    return true
  }

  const words = normalized.split(/\s+/)
  return words.length > 8 || TITLE_FILLER_ENDINGS.has(foldText(words[words.length - 1]))
}

function hasTrailingEllipsis(text?: string | null) {
  const normalized = normalizeText(text)
  return normalized.endsWith("...") || normalized.endsWith("…")
}

function splitBullets(text?: string | null) {
  const normalized = normalizeText(text)
  if (!normalized) {
    return []
  }

  const fromLines = normalized
    .split(/\n+/)
    .map((line) => normalizeText(line.replace(/^[-*•]\s*/, "")))
    .filter(Boolean)

  if (fromLines.length > 1) {
    return fromLines
  }

  return normalized
    .split(/(?<=[.!?])\s+/)
    .map((line) => normalizeText(line.replace(/^[-*•]\s*/, "")))
    .filter(Boolean)
}

function firstSentence(text?: string | null) {
  const normalized = normalizeText(text)
  if (!normalized) {
    return ""
  }

  const [first] = normalized.split(/(?<=[.!?])\s+/)
  return normalizeText(first || normalized)
}

function bulletsFromSections(
  data: KnowledgeDetailData | undefined,
  keys: KnowledgeSectionKey[],
  limit: number
) {
  if (!data) {
    return []
  }

  const bullets: string[] = []
  for (const key of keys) {
    const section = data.detailed_sections?.[key]
    const candidate = firstSentence(section?.content)
    if (!candidate || hasTrailingEllipsis(candidate) || bullets.includes(candidate)) {
      continue
    }
    bullets.push(candidate)
    if (bullets.length >= limit) {
      break
    }
  }

  return bullets
}

export function getReadableGeneratedTitle(
  title?: string | null,
  ...fallbackTexts: Array<string | null | undefined>
) {
  const candidates = [title, ...fallbackTexts]
  for (const candidate of candidates) {
    const extracted = extractCoreTitleCandidate(candidate)
    if (extracted && !titleNeedsCleanup(extracted)) {
      return extracted
    }
  }

  return cleanTitleCandidate(title) || extractCoreTitleCandidate(fallbackTexts[0]) || "Phan tich noi dung"
}

export function getAnalyzeOverviewBullets(
  summary: string,
  keyPoints: string[],
  knowledgeDetailData?: KnowledgeDetailData,
  limit = 5
) {
  const summaryBullets = splitBullets(summary).filter((item) => !hasTrailingEllipsis(item))
  if (summaryBullets.length >= 3) {
    return summaryBullets.slice(0, limit)
  }

  const detailSummaryBullets = splitBullets(knowledgeDetailData?.summary).filter(
    (item) => !hasTrailingEllipsis(item)
  )
  if (detailSummaryBullets.length) {
    return detailSummaryBullets.slice(0, limit)
  }

  const sectionBullets = bulletsFromSections(knowledgeDetailData, OVERVIEW_SECTION_KEYS, limit)
  if (sectionBullets.length) {
    return sectionBullets
  }

  const overview = knowledgeDetailData?.section_briefs?.overview
    ?.map((item) => normalizeText(item))
    .filter((item) => item && !hasTrailingEllipsis(item))
  if (overview?.length) {
    return overview.slice(0, limit)
  }

  return keyPoints
    .map((item) => normalizeText(item))
    .filter((item) => item && !hasTrailingEllipsis(item))
    .slice(0, limit)
}

export function getAnalyzeTakeawayBullets(
  keyPoints: string[],
  knowledgeDetailData?: KnowledgeDetailData,
  limit = 5
) {
  const cleanedKeyPoints = keyPoints
    .map((item) => normalizeText(item))
    .filter((item) => item && !hasTrailingEllipsis(item))
  if (cleanedKeyPoints.length >= 3) {
    return cleanedKeyPoints.slice(0, limit)
  }

  const sectionBullets = bulletsFromSections(knowledgeDetailData, TAKEAWAY_SECTION_KEYS, limit)
  if (sectionBullets.length) {
    return sectionBullets
  }

  const takeaways = knowledgeDetailData?.section_briefs?.core_takeaways
    ?.map((item) => normalizeText(item))
    .filter((item) => item && !hasTrailingEllipsis(item))
  if (takeaways?.length) {
    return takeaways.slice(0, limit)
  }

  return []
}
