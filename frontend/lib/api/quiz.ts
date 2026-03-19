import type {
  OpenFeedbackResult,
  QuizQuestion,
  QuizSubmissionResult,
} from "@/types"

import apiClient from "./client"

export async function generateQuiz(sessionId: string, numQuestions = 5) {
  const { data } = await apiClient.post<{ questions: QuizQuestion[] }>(
    "/api/quiz/generate",
    {
      session_id: sessionId,
      num_questions: numQuestions,
      include_open: true,
    }
  )

  return data
}

export async function getQuiz(sessionId: string) {
  const { data } = await apiClient.get<{ questions: QuizQuestion[] }>(
    `/api/quiz/${sessionId}`
  )

  return data
}

export async function submitQuiz(
  sessionId: string,
  answers: Array<{ question_id: string; user_answer: string }>
) {
  const { data } = await apiClient.post<QuizSubmissionResult>("/api/quiz/submit", {
    session_id: sessionId,
    answers,
  })

  return data
}

export async function getOpenFeedback(questionId: string, userAnswer: string) {
  const { data } = await apiClient.post<OpenFeedbackResult>(
    "/api/quiz/open-feedback",
    {
      question_id: questionId,
      user_answer: userAnswer,
    }
  )

  return data
}
