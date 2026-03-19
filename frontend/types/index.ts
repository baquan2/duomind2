import type { Edge, Node } from "@xyflow/react"

export interface UserProfile {
  id: string
  email?: string | null
  full_name?: string | null
  avatar_url?: string | null
  is_onboarded: boolean
  created_at?: string | null
}

export interface OnboardingData {
  age_range: "under_18" | "18_24" | "25_34" | "35_44" | "45_plus"
  status: "student" | "working" | "both" | "other"
  education_level?:
    | "high_school"
    | "college"
    | "university"
    | "postgrad"
    | "other"
  major?: string | null
  school_name?: string | null
  industry?: string | null
  job_title?: string | null
  years_experience?: number | null
  learning_goals: string[]
  topics_of_interest: string[]
  learning_style: "visual" | "reading" | "practice" | "mixed"
  daily_study_minutes: number
}

export interface OnboardingResponse {
  success: boolean
  ai_persona: string
  ai_persona_description: string
  ai_recommended_topics: string[]
}

export interface Correction {
  original: string
  correction: string
  explanation: string
}

export interface AnalyzeResult {
  session_id: string
  title: string
  accuracy_score: number | null
  accuracy_assessment: "high" | "medium" | "low" | "unverifiable"
  summary: string
  key_points: string[]
  corrections: Correction[]
  topic_tags: string[]
  mindmap_data: MindMapData
  source_label?: string | null
  input_preview?: string | null
}

export interface InfographicSection {
  icon: string
  heading: string
  content: string
  highlight?: string
}

export interface InfographicData {
  type: "steps" | "comparison" | "statistics" | "timeline" | "list"
  theme_color: string
  title: string
  subtitle?: string
  sections: InfographicSection[]
  footer_note?: string
}

export interface ExploreResult {
  session_id: string
  title: string
  summary: string
  key_points: string[]
  infographic_data: InfographicData
  topic_tags: string[]
  mindmap_data: MindMapData
}

export interface MindMapNodeData extends Record<string, unknown> {
  label: string
  full_label?: string
  description?: string
  details?: string
  color?: string
}

export type MindMapNode = Node<MindMapNodeData, "root" | "main" | "sub">

export type MindMapEdge = Edge

export interface MindMapData {
  nodes: MindMapNode[]
  edges: MindMapEdge[]
}

export interface LearningSession {
  id: string
  session_type: "analyze" | "explore"
  title: string
  user_input?: string
  summary?: string
  key_points?: string[]
  topic_tags: string[]
  accuracy_score?: number | null
  accuracy_assessment?: string | null
  corrections?: Correction[]
  infographic_data?: InfographicData | null
  mindmap_data?: MindMapData | null
  language?: string
  created_at: string
  is_bookmarked: boolean
}

export interface QuizOption {
  id: string
  text: string
}

export interface QuizQuestion {
  id: string
  order_index?: number
  question_type: "multiple_choice" | "open"
  question_text: string
  options?: QuizOption[] | null
  correct_answer?: string | null
  explanation?: string
  difficulty: "easy" | "medium" | "hard"
  thinking_hints?: string[]
  sample_answer_points?: string[]
}

export interface QuizSubmissionItem {
  question_id: string
  user_answer: string
  correct_answer?: string | null
  is_correct: boolean
  explanation: string
}

export interface QuizSubmissionResult {
  attempt_id: string
  score: number
  total: number
  percentage: number
  results: QuizSubmissionItem[]
}

export interface OpenFeedbackResult {
  ai_feedback: string
  strengths?: string[]
  improvements?: string[]
  critical_thinking_score?: number | null
}

export interface SessionDetailResponse {
  session: LearningSession
  quiz_questions: QuizQuestion[]
}

export interface KnowledgeReport {
  strongest_topics: string[]
  weakest_topics: string[]
  ai_summary: string
  ai_recommendations: string[]
  learning_pattern: string
  knowledge_depth: string
  total_sessions: number
  total_quizzes: number
  avg_quiz_score?: number
  topics_covered?: string[]
}
