const SOURCE_PREFIX = "[DUOMIND_SOURCE]"

export function extractSourceLabel(userInput?: string | null) {
  if (!userInput) {
    return null
  }

  const [firstLine] = userInput.split("\n")
  if (!firstLine.startsWith(SOURCE_PREFIX)) {
    return null
  }

  return firstLine.replace(SOURCE_PREFIX, "").trim() || null
}

export function stripSourceLabel(userInput?: string | null) {
  if (!userInput) {
    return ""
  }

  if (!userInput.startsWith(SOURCE_PREFIX)) {
    return userInput
  }

  const [, ...rest] = userInput.split("\n\n")
  return rest.join("\n\n").trim()
}

export function buildInputPreview(content?: string | null, maxChars = 180) {
  void maxChars
  const normalized = (content || "").replace(/\s+/g, " ").trim()
  return normalized
}
