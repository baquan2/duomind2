type OnboardingSnapshot = Record<string, unknown> & {
  ai_persona?: string | null
  ai_persona_description?: string | null
  ai_recommended_topics?: string[] | null
}

type MentorMemorySnapshot = {
  memory_key?: string | null
  memory_value?: unknown
}

const MEMORY_BACKED_KEYS = [
  "age_range",
  "status",
  "education_level",
  "major",
  "school_name",
  "industry",
  "job_title",
  "years_experience",
  "target_role",
  "desired_outcome",
  "current_focus",
  "current_challenges",
  "learning_constraints",
  "learning_goals",
  "topics_of_interest",
  "learning_style",
  "daily_study_minutes",
  "ai_persona",
  "ai_persona_description",
  "ai_recommended_topics",
] as const

function hasMeaningfulValue(value: unknown): boolean {
  if (typeof value === "string") {
    return value.trim().length > 0
  }
  if (Array.isArray(value)) {
    return value.length > 0
  }
  return value !== undefined && value !== null
}

function normalizeMemoryValue(value: unknown): unknown {
  if (typeof value === "string") {
    const trimmed = value.trim()
    if (!trimmed) {
      return null
    }

    if ((trimmed.startsWith("[") && trimmed.endsWith("]")) || (trimmed.startsWith("{") && trimmed.endsWith("}"))) {
      try {
        return JSON.parse(trimmed)
      } catch {
        return trimmed
      }
    }

    if (/^\d+$/.test(trimmed)) {
      return Number(trimmed)
    }

    return trimmed
  }

  if (Array.isArray(value)) {
    return value.filter((item) => item !== null && item !== undefined && item !== "")
  }

  return value
}

export function mergeOnboardingWithMemories<T extends OnboardingSnapshot>(
  onboarding: T | null | undefined,
  mentorMemories: MentorMemorySnapshot[] | null | undefined
): T | null {
  const merged = { ...(onboarding ?? {}) } as T
  const mutableMerged = merged as Record<string, unknown>
  const memories = mentorMemories ?? []

  if (!onboarding && memories.length === 0) {
    return null
  }

  for (const key of MEMORY_BACKED_KEYS) {
    const currentValue = merged[key]
    if (hasMeaningfulValue(currentValue)) {
      continue
    }

    const memory = memories.find((item) => item.memory_key === key)
    if (!memory) {
      continue
    }

    const value = normalizeMemoryValue(memory.memory_value)
    if (!hasMeaningfulValue(value)) {
      continue
    }

    mutableMerged[key] = value
  }

  return merged
}
