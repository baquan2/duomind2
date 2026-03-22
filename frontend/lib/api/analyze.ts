import axios from "axios"

import type { AnalyzeResult, ExploreResult } from "@/types"

const aiApiClient = axios.create({
  baseURL: "",
})

export type AnalyzeMode = "auto" | "deep_dive" | "critique"

export async function analyzeContent(
  content: string,
  language = "vi",
  analysisGoal?: string,
  mode: AnalyzeMode = "auto"
) {
  const { data } = await aiApiClient.post<AnalyzeResult>("/api/analyze", {
    content,
    language,
    analysis_goal: analysisGoal?.trim() || undefined,
    mode,
  })
  return data
}

export async function analyzeFile(
  file: File,
  language = "vi",
  analysisGoal?: string,
  mode: AnalyzeMode = "auto"
) {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("language", language)
  if (analysisGoal?.trim()) {
    formData.append("analysis_goal", analysisGoal.trim())
  }
  formData.append("mode", mode)

  const { data } = await aiApiClient.post<AnalyzeResult>("/api/analyze/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })

  return data
}

export async function exploreTopicApi(prompt: string, language = "vi") {
  const { data } = await aiApiClient.post<ExploreResult>("/api/explore", {
    prompt,
    language,
  })
  return data
}
