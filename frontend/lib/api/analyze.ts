import axios from "axios"

import type { AnalyzeResult, ExploreResult } from "@/types"

const aiApiClient = axios.create({
  baseURL: "",
})

export async function analyzeContent(
  content: string,
  language = "vi",
  analysisGoal?: string
) {
  const { data } = await aiApiClient.post<AnalyzeResult>("/api/analyze", {
    content,
    language,
    analysis_goal: analysisGoal?.trim() || undefined,
  })
  return data
}

export async function analyzeFile(file: File, language = "vi", analysisGoal?: string) {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("language", language)
  if (analysisGoal?.trim()) {
    formData.append("analysis_goal", analysisGoal.trim())
  }

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
