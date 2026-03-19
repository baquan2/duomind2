import type { AnalyzeResult, ExploreResult } from "@/types"

import apiClient from "./client"

export async function analyzeContent(content: string, language = "vi") {
  const { data } = await apiClient.post<AnalyzeResult>("/api/analyze/", {
    content,
    language,
  })
  return data
}

export async function analyzeFile(file: File, language = "vi") {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("language", language)

  const { data } = await apiClient.post<AnalyzeResult>("/api/analyze/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  })

  return data
}

export async function exploreTopicApi(prompt: string, language = "vi") {
  const { data } = await apiClient.post<ExploreResult>("/api/explore/", {
    prompt,
    language,
  })
  return data
}
