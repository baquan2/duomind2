export function extractSummaryBullets(
  summary: string | undefined,
  fallbackPoints: string[] = [],
  limit = 5
) {
  const hasEllipsis = (value: string) => value.endsWith("...")

  const normalized = (summary || "").trim()
  if (!normalized) {
    return fallbackPoints.slice(0, limit)
  }

  const fromLines = normalized
    .split(/\n+/)
    .map((line) => line.replace(/^[-*]\s*/, "").trim())
    .filter((line) => line && !hasEllipsis(line))

  if (fromLines.length > 1) {
    return fromLines.slice(0, limit)
  }

  const fromSentences = normalized
    .split(/(?<=[.!?])\s+/)
    .map((line) => line.replace(/^[-*]\s*/, "").trim())
    .filter((line) => line && !hasEllipsis(line))

  if (fromSentences.length > 1) {
    return fromSentences.slice(0, limit)
  }

  if (hasEllipsis(normalized)) {
    return fallbackPoints.slice(0, limit)
  }

  return [normalized]
}
