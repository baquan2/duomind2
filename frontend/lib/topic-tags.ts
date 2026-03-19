const TAG_STOP_WORDS = new Set([
  "va",
  "voi",
  "cua",
  "cho",
  "la",
  "mot",
  "nhung",
  "trong",
  "khi",
  "the",
  "hay",
  "ban",
  "duoc",
  "gi",
  "giai",
  "thich",
  "don",
  "gian",
  "co",
  "ban",
  "tong",
  "quan",
  "vi",
  "du",
])

const TAG_FILLER_PHRASES = [
  "la gi",
  "hoat dong nhu the nao",
  "nhu the nao",
  "ra sao",
  "giai thich don gian",
  "giai thich",
  "don gian",
  "co ban",
  "tong quan",
  "vi du",
]

function stripAccents(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
}

function cleanTag(tag: string) {
  let cleaned = tag.replace(/[#*_`~[\]{}()<>]+/g, " ").trim()
  cleaned = cleaned.replace(/\s*[:|/,-]\s*/g, " ").replace(/\s{2,}/g, " ").trim()

  let accentless = stripAccents(cleaned.toLowerCase())
  TAG_FILLER_PHRASES.forEach((phrase) => {
    accentless = accentless.replace(phrase, " ")
  })

  const parts = accentless
    .replace(/\s{2,}/g, " ")
    .trim()
    .split(" ")
    .map((part) => part.trim())
    .filter((part) => part && !TAG_STOP_WORDS.has(part) && !/^\d+$/.test(part))

  return parts.slice(0, 4).join(" ").trim()
}

export function compactTopicTags(tags: string[] | undefined, limit = 4) {
  if (!tags?.length) {
    return []
  }

  const normalized: string[] = []

  for (const rawTag of tags) {
    const cleaned = cleanTag(rawTag)
    if (!cleaned) {
      continue
    }

    if (!normalized.some((item) => item.toLowerCase() === cleaned.toLowerCase())) {
      normalized.push(cleaned)
    }

    if (normalized.length >= limit) {
      break
    }
  }

  return normalized
}
