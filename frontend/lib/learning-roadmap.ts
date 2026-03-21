import { BookCopy, MessagesSquare, Telescope, type LucideIcon } from "lucide-react"

import { GOAL_OPTIONS, getOptionLabel } from "@/components/onboarding/options"

export type DashboardOnboarding = {
  target_role?: string | null
  current_focus?: string | null
  current_challenges?: string | null
  desired_outcome?: string | null
  learning_constraints?: string | null
  ai_recommended_topics?: string[] | null
  learning_goals?: string[] | null
  daily_study_minutes?: number | null
}

export type DashboardAnalytics = {
  strongest_topics?: string[] | null
  weakest_topics?: string[] | null
  avg_quiz_score?: number | null
  total_sessions?: number | null
  total_quizzes?: number | null
  knowledge_depth?: string | null
  learning_pattern?: string | null
}

export type MentorLearningPathItem = {
  title: string
  description: string
  href: string
  icon: LucideIcon
  accent: string
}

export type MiniRoadmapItem = {
  title: string
  description: string
  href: string
  cta: string
}

export type ReadinessSnapshot = {
  level: string
  summary: string
  strongestLabel: string
  strongestDetail: string
  gapLabel: string
  gapDetail: string
  readinessScore: number
}

export type SkillGapSnapshotItem = {
  title: string
  topic: string
  score: number
  badge: string
  detail: string
}

export type ContextSnapshotItem = {
  label: string
  value: string
  detail: string
}

export type RoadmapExecutionRule = {
  title: string
  detail: string
}

export type ProfileReadiness = {
  score: number
  label: string
  missingItems: string[]
  summary: string
}

export function buildExplorePromptFromTopic(topic: string, targetRole?: string | null) {
  const cleanTopic = topic?.trim() || "khối kiến thức quan trọng"
  const cleanRole = targetRole?.trim()
  if (cleanRole) {
    return `Giải thích ${cleanTopic} theo cách dễ hiểu, có ví dụ thực tế và bám mục tiêu ${cleanRole}`
  }
  return `Giải thích ${cleanTopic} theo cách dễ hiểu và có ví dụ thực tế`
}

export function buildMentorQuestionForTopic(topic: string, targetRole?: string | null) {
  const cleanTopic = topic?.trim() || "khối kỹ năng còn thiếu"
  const cleanRole = targetRole?.trim()
  if (cleanRole) {
    return `Với mục tiêu ${cleanRole}, tôi đang yếu ở ${cleanTopic}. Tôi nên học theo thứ tự nào trong 14 ngày tới?`
  }
  return `Tôi đang yếu ở ${cleanTopic}. Mentor hãy giúp tôi chốt thứ tự học trong 14 ngày tới.`
}

export function buildAnalyzeStarterContent(topic: string, targetRole?: string | null) {
  const cleanTopic = topic?.trim() || "một chủ đề quan trọng"
  const cleanRole = targetRole?.trim()
  const roleLine = cleanRole ? `Mục tiêu nghề nghiệp: ${cleanRole}` : "Mục tiêu nghề nghiệp: Chưa chốt rõ"

  return [
    roleLine,
    `Chủ đề cần tự kiểm tra: ${cleanTopic}`,
    "",
    "Ghi chú hiện tại của tôi:",
    `- ${cleanTopic} là gì?`,
    `- Vì sao ${cleanTopic} quan trọng với mục tiêu trên?`,
    `- Tôi đang hiểu phần nào và còn mơ hồ ở đâu?`,
    `- Một ví dụ thực tế hoặc đầu ra nhỏ tôi có thể làm với ${cleanTopic} là gì?`,
    "",
    "Hãy phân tích xem ghi chú này đúng tới đâu, thiếu gì và cần bổ sung gì.",
  ].join("\n")
}

export function buildCareerFocus(onboarding: DashboardOnboarding | null | undefined) {
  const targetRole = onboarding?.target_role || "một hướng nghề nghiệp cụ thể"
  const primaryTopic = onboarding?.ai_recommended_topics?.[0] || "khối kỹ năng nền tảng quan trọng nhất"
  const secondTopic =
    onboarding?.ai_recommended_topics?.[1] || "một kỹ năng ứng dụng gần với đầu ra bạn muốn"
  const studyWindow = onboarding?.daily_study_minutes
    ? `${onboarding.daily_study_minutes} phút mỗi ngày`
    : "quỹ thời gian học hiện tại"
  const primaryGoal = getOptionLabel(onboarding?.learning_goals?.[0], GOAL_OPTIONS)
  const desiredOutcome = onboarding?.desired_outcome?.trim()
  const currentChallenge = onboarding?.current_challenges?.trim()
  const currentFocus = onboarding?.current_focus?.trim()
  const learningConstraints = onboarding?.learning_constraints?.trim()

  return {
    targetRole,
    primaryTopic,
    focusSummary: desiredOutcome
      ? `Trục học hiện tại là ${targetRole}, ưu tiên ${primaryTopic} để tiến gần mục tiêu "${desiredOutcome}".`
      : `Trục học hiện tại là ${targetRole}, ưu tiên ${primaryTopic} và bám mục tiêu ${primaryGoal.toLowerCase()}.`,
    focusDetail: `Trong giai đoạn này, bạn không nên học dàn trải. Hãy lấy ${primaryTopic} làm trục chính, sau đó nối sang ${secondTopic} để tạo đầu ra gần hơn với ${targetRole}.${currentFocus ? ` Trọng tâm hiện tại của bạn là ${currentFocus}.` : ""}${currentChallenge ? ` Mentor nên đặc biệt xử lý khó khăn: ${currentChallenge}.` : ""}${learningConstraints ? ` Khi lên lộ trình, cần giữ đúng ràng buộc: ${learningConstraints}.` : ""}`,
    nextActionLabel: `Hỏi mentor về ${targetRole}`,
    nextActionHref: "/mentor",
    nextActionSummary: desiredOutcome
      ? `Trong ${studyWindow}, việc có giá trị nhất lúc này là chốt khoảng trống kỹ năng để biến mục tiêu "${desiredOutcome}" thành lộ trình thực thi rõ ràng.`
      : `Trong ${studyWindow}, việc có giá trị nhất lúc này là chốt khoảng trống kỹ năng và thứ tự học cho ${targetRole}.`,
    nextActionDetail: `Mở Mentor AI để hỏi 3 kỹ năng cần ưu tiên nhất cho ${targetRole}, sau đó dùng Khám phá hoặc Phân tích để học đúng phần đang thiếu thay vì học theo cảm tính.${currentChallenge ? ` Nên yêu cầu mentor xử lý thẳng khó khăn "${currentChallenge}".` : ""}`,
  }
}

export function buildContextSnapshot(onboarding: DashboardOnboarding | null | undefined) {
  const items: ContextSnapshotItem[] = []

  if (onboarding?.desired_outcome?.trim()) {
    items.push({
      label: "Đầu ra mong muốn",
      value: onboarding.desired_outcome.trim(),
      detail: "Đây là đích đến để mentor, lộ trình và các CTA không bị nói chung chung.",
    })
  }

  if (onboarding?.current_focus?.trim()) {
    items.push({
      label: "Trọng tâm hiện tại",
      value: onboarding.current_focus.trim(),
      detail: "Dùng để hiểu bạn đang học phần nào và tránh đề xuất lệch mạch.",
    })
  }

  if (onboarding?.current_challenges?.trim()) {
    items.push({
      label: "Khó khăn lớn nhất",
      value: onboarding.current_challenges.trim(),
      detail: "Mentor cần bám vào đây để đưa ra bước tiếp theo thực tế hơn.",
    })
  }

  if (onboarding?.learning_constraints?.trim()) {
    items.push({
      label: "Ràng buộc học tập",
      value: onboarding.learning_constraints.trim(),
      detail: "Giúp hệ thống điều chỉnh nhịp học theo hoàn cảnh thật của người dùng.",
    })
  }

  return items
}

export function buildProfileReadiness(onboarding: DashboardOnboarding | null | undefined) {
  const checks = [
    { ok: Boolean(onboarding?.target_role?.trim()), label: "mục tiêu nghề nghiệp" },
    { ok: Boolean(onboarding?.desired_outcome?.trim()), label: "đầu ra mong muốn" },
    { ok: Boolean(onboarding?.current_focus?.trim()), label: "trọng tâm hiện tại" },
    { ok: Boolean(onboarding?.current_challenges?.trim()), label: "khó khăn hiện tại" },
    { ok: Boolean(onboarding?.learning_constraints?.trim()), label: "ràng buộc học tập" },
    { ok: Boolean(onboarding?.learning_goals?.length), label: "mục tiêu học tập" },
    { ok: Boolean(onboarding?.ai_recommended_topics?.length), label: "chủ đề ưu tiên" },
    { ok: Boolean(onboarding?.daily_study_minutes), label: "quỹ học mỗi ngày" },
  ]

  const completed = checks.filter((item) => item.ok).length
  const score = Math.round((completed / checks.length) * 100)
  const missingItems = checks.filter((item) => !item.ok).map((item) => item.label)

  let label = "Hồ sơ đã đủ rõ để AI cá nhân hóa tốt"
  if (score < 50) {
    label = "Hồ sơ còn thiếu nhiều tín hiệu quan trọng"
  } else if (score < 80) {
    label = "Hồ sơ đã khá rõ nhưng còn vài điểm nên bổ sung"
  }

  const summary = missingItems.length
    ? `Bổ sung ${missingItems.slice(0, 3).join(", ")} để mentor và lộ trình bám sát bối cảnh hơn.`
    : "Bạn đã cung cấp đủ tín hiệu chính để mentor, dashboard và lộ trình hoạt động ổn định hơn."

  return {
    score,
    label,
    missingItems,
    summary,
  } satisfies ProfileReadiness
}

export function buildMentorLearningPath(onboarding: DashboardOnboarding | null | undefined) {
  const targetRole = onboarding?.target_role || "vai trò mục tiêu của bạn"
  const topTopic = onboarding?.ai_recommended_topics?.[0] || "khối kiến thức nền"
  const secondTopic =
    onboarding?.ai_recommended_topics?.[1] || "một kỹ năng ứng dụng gần với mục tiêu"
  const studyWindow = onboarding?.daily_study_minutes
    ? `${onboarding.daily_study_minutes} phút mỗi ngày`
    : "quỹ thời gian hiện tại"

  return [
    {
      title: "Chốt khoảng trống kỹ năng",
      description: `Bắt đầu bằng một câu hỏi mentor để chốt bạn đang thiếu gì để tiến gần tới ${targetRole}.`,
      href: "/mentor",
      icon: MessagesSquare,
      accent: "from-emerald-500/18 to-teal-500/8",
    },
    {
      title: "Học đúng chủ đề",
      description: `Khám phá sâu ${topTopic}, sau đó nối sang ${secondTopic} để biết phần nào cần học trước.`,
      href: "/explore",
      icon: Telescope,
      accent: "from-amber-500/18 to-orange-500/8",
    },
    {
      title: "Củng cố bằng phân tích",
      description: `Dùng Phân tích với note, file học hoặc tài liệu của bạn để giữ tiến độ đều theo ${studyWindow}.`,
      href: "/analyze",
      icon: BookCopy,
      accent: "from-violet-500/18 to-fuchsia-500/8",
    },
  ] satisfies MentorLearningPathItem[]
}

export function buildMiniRoadmap(onboarding: DashboardOnboarding | null | undefined) {
  const targetRole = onboarding?.target_role || "vai trò mục tiêu của bạn"
  const firstTopic = onboarding?.ai_recommended_topics?.[0] || "khối nền tảng cốt lõi"
  const secondTopic = onboarding?.ai_recommended_topics?.[1] || "một kỹ năng ứng dụng"
  const thirdTopic =
    onboarding?.ai_recommended_topics?.[2] || "một đầu ra nhỏ để chứng minh năng lực"
  const mentorQuestion = buildMentorQuestionForTopic(firstTopic, targetRole)
  const explorePrompt = buildExplorePromptFromTopic(secondTopic, targetRole)
  const analyzeContent = buildAnalyzeStarterContent(thirdTopic, targetRole)

  return [
    {
      title: "Ngày 1-3: chốt hướng",
      description: `Mở Mentor AI để chốt khoảng trống kỹ năng và thứ tự học cho ${targetRole}, tránh học dàn trải ngay từ đầu.`,
      href: `/mentor?question=${encodeURIComponent(mentorQuestion)}`,
      cta: "Mở mentor",
    },
    {
      title: "Ngày 4-9: học khối chính",
      description: `Dùng Khám phá để học sâu ${firstTopic}, sau đó nối sang ${secondTopic} để hiểu đúng phần cần ưu tiên.`,
      href: `/explore?prompt=${encodeURIComponent(explorePrompt)}`,
      cta: "Học chủ đề",
    },
    {
      title: "Ngày 10-14: củng cố",
      description: `Đưa note, bài học hoặc tài liệu của bạn vào Phân tích để chốt lại kiến thức và tạo đầu ra nhỏ từ ${thirdTopic}.`,
      href: `/analyze?content=${encodeURIComponent(analyzeContent)}`,
      cta: "Phân tích",
    },
  ] satisfies MiniRoadmapItem[]
}

export function buildReadinessSnapshot(
  onboarding: DashboardOnboarding | null | undefined,
  analytics: DashboardAnalytics | null | undefined,
  visibleSessionCount: number
) {
  const targetRole = onboarding?.target_role || "mục tiêu hiện tại"
  const strongestTopic = analytics?.strongest_topics?.[0] || onboarding?.ai_recommended_topics?.[0]
  const weakestTopic = analytics?.weakest_topics?.[0] || onboarding?.ai_recommended_topics?.[1]
  const avgQuizScore = Number(analytics?.avg_quiz_score ?? 0)
  const totalSessions = Number(analytics?.total_sessions ?? visibleSessionCount ?? 0)
  const readinessScore = Math.max(
    24,
    Math.min(91, Math.round(totalSessions * 8 + avgQuizScore * 0.45 + (strongestTopic ? 10 : 0)))
  )
  const level =
    totalSessions >= 8 || avgQuizScore >= 75
      ? "Đã có nền đủ để tăng tốc"
      : totalSessions >= 3 || avgQuizScore >= 50
        ? "Đang vào guồng học đúng"
        : "Mới khởi động, cần chốt nền tảng"

  return {
    level,
    summary:
      totalSessions > 0
        ? `Bạn đã có ${totalSessions} phiên học được lưu. Đây là lúc nên bám chặt vào ${targetRole} và ưu tiên các phiên học có đầu ra rõ, thay vì tiếp tục học lan man.`
        : `Bạn mới ở giai đoạn khởi động. Hãy dùng mentor để chốt khoảng trống kỹ năng cho ${targetRole}, rồi học đều theo lộ trình mini 14 ngày.`,
    strongestLabel: strongestTopic ? `Nổi bật nhất: ${strongestTopic}` : "Chưa có dữ liệu mạnh rõ ràng",
    strongestDetail: strongestTopic
      ? `Nếu tiếp tục giữ nhịp ở chủ đề ${strongestTopic}, bạn sẽ tạo được lợi thế rõ hơn cho ${targetRole}.`
      : "Sau 2-3 phiên học đầu, dashboard sẽ bắt đầu nhận ra khối kiến thức bạn đang bám tốt nhất.",
    gapLabel: weakestTopic ? `Cần ưu tiên: ${weakestTopic}` : "Cần thêm dữ liệu học tập",
    gapDetail: weakestTopic
      ? `Đây là phần nên được mentor và Khám phá ưu tiên tiếp theo để tránh lệch giữa kiến thức có sẵn và yêu cầu của ${targetRole}.`
      : "Hãy hoàn thành thêm một vài phiên Khám phá hoặc Phân tích để hệ thống xác định chính xác khoảng trống cần bù.",
    readinessScore,
  } satisfies ReadinessSnapshot
}

export function buildSkillGapSnapshot(
  onboarding: DashboardOnboarding | null | undefined,
  analytics: DashboardAnalytics | null | undefined,
  visibleSessionCount: number
) {
  const recommendedTopics = onboarding?.ai_recommended_topics ?? []
  const firstTopic = analytics?.strongest_topics?.[0] || recommendedTopics[0] || "khối nền tảng cốt lõi"
  const secondTopic = analytics?.weakest_topics?.[0] || recommendedTopics[1] || "khối kỹ năng còn thiếu"
  const thirdTopic = recommendedTopics[2] || "một đầu ra nhỏ để chứng minh năng lực"
  const readiness = buildReadinessSnapshot(onboarding, analytics, visibleSessionCount).readinessScore
  const totalSessions = Number(analytics?.total_sessions ?? visibleSessionCount ?? 0)

  return [
    {
      title: "Nền đang có",
      topic: firstTopic,
      score: Math.max(52, Math.min(92, readiness + 8)),
      badge: "Giữ đà",
      detail: `Tiếp tục học đều quanh ${firstTopic} để giữ lợi thế hiện có và làm trục chính cho mục tiêu đang theo đuổi.`,
    },
    {
      title: "Khoảng trống ưu tiên",
      topic: secondTopic,
      score: Math.max(48, Math.min(95, 100 - readiness + 18)),
      badge: "Bù ngay",
      detail: `Đây là phần nên được mentor và Khám phá xử lý trước để tránh lệch với yêu cầu thị trường và vai trò mục tiêu.`,
    },
    {
      title: "Đầu ra cần chứng minh",
      topic: thirdTopic,
      score: Math.max(36, Math.min(84, 32 + totalSessions * 6)),
      badge: "Làm đầu ra",
      detail: `Hãy biến phần này thành note, bản phân tích hoặc mini project để chứng minh bạn thật sự dùng được kiến thức.`,
    },
  ] satisfies SkillGapSnapshotItem[]
}

export function buildMentorPrompts(
  onboarding: DashboardOnboarding | null | undefined,
  analytics: DashboardAnalytics | null | undefined
) {
  const targetRole = onboarding?.target_role || "vai trò mục tiêu hiện tại"
  const focusTopic =
    analytics?.weakest_topics?.[0] || onboarding?.ai_recommended_topics?.[0] || "khối kỹ năng quan trọng nhất"
  const secondTopic = onboarding?.ai_recommended_topics?.[1] || "một kỹ năng ứng dụng"
  const studyWindow = onboarding?.daily_study_minutes
    ? `${onboarding.daily_study_minutes} phút mỗi ngày`
    : "quỹ thời gian hiện tại"
  const desiredOutcome = onboarding?.desired_outcome?.trim()
  const currentChallenge = onboarding?.current_challenges?.trim()

  return [
    `Với mục tiêu ${targetRole}, trong ${studyWindow} tôi nên học ${focusTopic} như thế nào để có đầu ra rõ trong 2 tuần${desiredOutcome ? ` và tiến gần "${desiredOutcome}"` : ""}?`,
    `Nếu tôi đang yếu ở ${focusTopic}${currentChallenge ? ` và khó ở chỗ "${currentChallenge}"` : ""}, mentor hãy tách giúp tôi 3 mức học từ nền tảng đến ứng dụng thực tế.`,
    `Sau khi học ${focusTopic} và ${secondTopic}, tôi nên làm đầu ra nhỏ nào để chứng minh mình tiến gần hơn tới ${targetRole}${desiredOutcome ? ` và đạt "${desiredOutcome}"` : ""}?`,
  ]
}

export function buildExecutionRules(onboarding: DashboardOnboarding | null | undefined) {
  const studyWindow = onboarding?.daily_study_minutes
    ? `${onboarding.daily_study_minutes} phút`
    : "30-45 phút"
  const learningConstraints = onboarding?.learning_constraints?.trim()

  return [
    {
      title: "Mỗi phiên chỉ một mục tiêu",
      detail: `Trong mỗi block ${studyWindow}, chỉ giải quyết một khoảng trống rõ ràng thay vì mở nhiều chủ đề cùng lúc.`,
    },
    {
      title: "Cứ 3 ngày phải có đầu ra",
      detail: "Sau 2-3 phiên học, hãy chốt thành note, câu trả lời mentor, bản phân tích hoặc mini project nhỏ.",
    },
    {
      title: "Dùng mentor để khóa thứ tự ưu tiên",
      detail: "Khi bị rối hoặc đổi hướng, hỏi mentor trước rồi mới sang Khám phá hoặc Phân tích để tiết kiệm thời gian.",
    },
    {
      title: "Giữ đúng ràng buộc thực tế",
      detail: learningConstraints
        ? `Lộ trình hiện tại cần bám sát ràng buộc "${learningConstraints}" thay vì giả định bạn có nguồn lực lý tưởng.`
        : "Nếu quỹ thời gian, thiết bị hoặc áp lực công việc thay đổi, hãy cập nhật hồ sơ để mentor điều chỉnh lại lộ trình.",
    },
  ] satisfies RoadmapExecutionRule[]
}
