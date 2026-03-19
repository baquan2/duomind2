import type {
  MentorChatResponse,
  MentorSuggestedQuestionsResponse,
  MentorThreadDetail,
  MentorThreadSummary,
} from "@/types"

import apiClient from "./client"

export async function getMentorThreads() {
  const { data } = await apiClient.get<MentorThreadSummary[]>("/api/mentor/threads")
  return data
}

export async function createMentorThread(title?: string) {
  const { data } = await apiClient.post<MentorThreadSummary>("/api/mentor/threads", {
    title,
  })
  return data
}

export async function getMentorThreadDetail(threadId: string) {
  const { data } = await apiClient.get<MentorThreadDetail>(`/api/mentor/threads/${threadId}`)
  return data
}

export async function getMentorSuggestedQuestions() {
  const { data } = await apiClient.get<MentorSuggestedQuestionsResponse>(
    "/api/mentor/suggested-questions"
  )
  return data
}

export async function sendMentorMessage(message: string, threadId?: string | null) {
  const { data } = await apiClient.post<MentorChatResponse>("/api/mentor/chat", {
    thread_id: threadId,
    message,
    language: "vi",
  })
  return data
}
