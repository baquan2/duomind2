import type {
  KnowledgeReport,
  SessionListResponse,
  SessionDetailResponse,
} from "@/types"

import apiClient from "./client"

export async function getSessions(limit = 20, offset = 0) {
  const { data } = await apiClient.get<SessionListResponse>("/api/history/sessions", {
    params: { limit, offset },
  })

  return data
}

export async function getSessionDetail(id: string) {
  const { data } = await apiClient.get<SessionDetailResponse>(
    `/api/history/sessions/${id}`
  )

  return data
}

export async function toggleBookmark(id: string) {
  const { data } = await apiClient.patch<{ is_bookmarked: boolean }>(
    `/api/history/sessions/${id}/bookmark`
  )

  return data
}

export async function deleteSession(id: string) {
  const { data } = await apiClient.delete<{ success: boolean }>(
    `/api/history/sessions/${id}`
  )

  return data
}

export async function getKnowledgeReport() {
  const { data } = await apiClient.get<KnowledgeReport>(
    "/api/analytics/knowledge-report"
  )

  return data
}
