import type { Edge, Node } from "@xyflow/react"

export interface UserProfile {
  id: string
  email?: string | null
  full_name?: string | null
  avatar_url?: string | null
  is_onboarded: boolean
  has_seen_intro_tour?: boolean
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
  target_role?: string | null
  current_focus?: string | null
  current_challenges?: string | null
  desired_outcome?: string | null
  learning_constraints?: string | null
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

export interface SourceReference {
  label: string
  url: string
  snippet?: string | null
}

export interface SaveMetadata {
  status: string
  dropped_fields?: string[]
  attempted_optional_fields?: string[]
  reason?: string | null
}

export type AnalyzeVerdict = "correct" | "incorrect" | "deep_dive"

export interface AnalyzeResult {
  session_id?: string | null
  title: string
  verdict: AnalyzeVerdict
  accuracy_score: number | null
  accuracy_assessment: "high" | "medium" | "low" | "unverifiable"
  summary: string
  key_points: string[]
  corrections: Correction[]
  knowledge_detail_data: KnowledgeDetailData
  topic_tags: string[]
  mindmap_data: MindMapData
  sources: SourceReference[]
  related_materials: SourceReference[]
  source_label?: string | null
  input_preview?: string | null
  save_metadata?: SaveMetadata | null
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

export interface KnowledgeDetailSection {
  title: string
  content: string
}

export type KnowledgeSectionKey =
  | "core_concept"
  | "mechanism"
  | "components_and_relationships"
  | "persona_based_example"
  | "real_world_applications"
  | "common_misconceptions"
  | "next_step_self_study"

export interface ContentBlueprint {
  core_definition: string
  scope_boundary: string
  mechanism: string
  components: string
  input_process_output: string
  example: string
  application: string
  misconceptions: string
  conditions_and_limits: string
  related_concepts: string
  decision_value: string
}

export interface KnowledgeSectionBriefs {
  overview: string[]
  core_takeaways: string[]
  detail_focus: string[]
  exploration: string[]
}

export interface KnowledgeTeachingAdaptation {
  focus_priority: string
  tone: string
  depth_control: string
  example_strategy: string
}

export interface KnowledgeDetailData {
  title: string
  summary: string
  content_blueprint?: ContentBlueprint
  section_briefs?: KnowledgeSectionBriefs
  active_section_keys?: KnowledgeSectionKey[]
  detailed_sections: {
    core_concept: KnowledgeDetailSection
    mechanism: KnowledgeDetailSection
    components_and_relationships: KnowledgeDetailSection
    persona_based_example: KnowledgeDetailSection
    real_world_applications: KnowledgeDetailSection
    common_misconceptions: KnowledgeDetailSection
    next_step_self_study: KnowledgeDetailSection
  }
  teaching_adaptation: KnowledgeTeachingAdaptation
}

export interface ExploreResult {
  session_id?: string | null
  title: string
  summary: string
  key_points: string[]
  knowledge_detail_data: KnowledgeDetailData
  topic_tags: string[]
  mindmap_data: MindMapData
  sources: SourceReference[]
  related_materials: SourceReference[]
  save_metadata?: SaveMetadata | null
}

export type MentorIntent =
  | "career_roles"
  | "market_outlook"
  | "skill_gap"
  | "learning_roadmap"
  | "career_fit"
  | "general_guidance"

export interface MentorCareerPath {
  role: string
  fit_reason: string
  entry_level: string
  required_skills: string[]
  next_step: string
}

export interface MentorMarketSignal {
  role_name: string
  demand_summary: string
  top_skills: string[]
  source_name: string
  source_url: string
}

export interface MentorSkillGap {
  skill: string
  gap_level: "high" | "medium" | "low" | string
  why_it_matters: string
  suggested_action: string
}

export interface MentorSource {
  label: string
  url: string
  snippet?: string | null
}

export interface MentorDecisionSummary {
  headline: string
  priority_label: string
  priority_value: string
  reason: string
  next_action: string
  confidence_note: string
}

export interface MentorMemoryItem {
  id: string
  memory_type: string
  memory_key: string
  memory_value: unknown
  confidence?: number | null
  updated_at?: string | null
}

export interface MentorMessagePayload {
  answer: string
  career_paths: MentorCareerPath[]
  market_signals: MentorMarketSignal[]
  skill_gaps: MentorSkillGap[]
  decision_summary?: MentorDecisionSummary | null
  recommended_learning_steps: string[]
  suggested_followups: string[]
  sources: MentorSource[]
  related_materials?: MentorSource[]
  answer_mode?: string | null
  request_payload?: Record<string, unknown> | null
  context_snapshot?: Record<string, unknown> | null
  generation_trace?: Record<string, unknown> | null
  save_metadata?: SaveMetadata | null
}

export interface MentorThreadSummary {
  id: string
  title: string
  status: string
  last_message_at?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface MentorMessageItem {
  id: string
  thread_id: string
  role: "user" | "assistant" | "system"
  intent?: MentorIntent | string | null
  content: string
  answer_mode?: string | null
  response_data?: MentorMessagePayload | null
  sources: MentorSource[]
  related_materials?: MentorSource[]
  request_payload?: Record<string, unknown> | null
  context_snapshot?: Record<string, unknown> | null
  generation_trace?: Record<string, unknown> | null
  created_at?: string | null
}

export interface MentorThreadDetail {
  thread: MentorThreadSummary
  messages: MentorMessageItem[]
}

export interface MentorSuggestedQuestionsResponse {
  questions: string[]
}

export interface MentorChatResponse extends MentorMessagePayload {
  thread_id: string
  thread_title: string
  message_id: string
  intent: MentorIntent
  messages: MentorMessageItem[]
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
  session_subtype?: "overview" | "deep_dive" | "critique" | null
  title: string
  user_input?: string
  summary?: string
  key_points?: string[]
  topic_tags: string[]
  verdict?: AnalyzeVerdict | null
  accuracy_score?: number | null
  accuracy_assessment?: string | null
  corrections?: Correction[]
  infographic_data?: KnowledgeDetailData | null
  mindmap_data?: MindMapData | null
  sources?: SourceReference[]
  request_payload?: Record<string, unknown> | null
  context_snapshot?: Record<string, unknown> | null
  generation_trace?: Record<string, unknown> | null
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

export interface SessionListResponse {
  sessions: LearningSession[]
  total: number
  counts: {
    all: number
    analyze: number
    explore: number
  }
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
