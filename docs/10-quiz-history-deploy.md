# 10 — Quiz & Câu hỏi Tự luận

## Mục tiêu
Component quiz dùng chung cho cả ANALYZE và EXPLORE: tạo quiz, làm bài, chấm điểm, câu hỏi mở.

---

## `frontend/components/quiz/QuizContainer.tsx`

```tsx
'use client'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { generateQuiz } from '@/lib/api/quiz'
import { MultipleChoice } from './MultipleChoice'
import { OpenQuestion } from './OpenQuestion'
import { QuizResult } from './QuizResult'
import type { QuizQuestion } from '@/types'

interface Props { sessionId: string }

type Phase = 'idle' | 'loading' | 'quiz' | 'result'

export function QuizContainer({ sessionId }: Props) {
  const [phase, setPhase] = useState<Phase>('idle')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitResult, setSubmitResult] = useState<any>(null)

  const handleStart = async () => {
    setPhase('loading')
    try {
      const { data } = await generateQuiz(sessionId, 5)
      setQuestions(data.questions)
      setPhase('quiz')
      setCurrentIdx(0)
    } catch {
      setPhase('idle')
    }
  }

  const handleAnswer = (questionId: string, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }))
  }

  const handleNext = () => {
    if (currentIdx < questions.length - 1) setCurrentIdx(i => i + 1)
    else handleSubmit()
  }

  const handleSubmit = async () => {
    const { submitQuiz } = await import('@/lib/api/quiz')
    const mcqAnswers = questions
      .filter(q => q.question_type === 'multiple_choice')
      .map(q => ({ question_id: q.id, user_answer: answers[q.id] }))
    const { data } = await submitQuiz(sessionId, mcqAnswers)
    setSubmitResult(data)
    setPhase('result')
  }

  const mcqQuestions = questions.filter(q => q.question_type === 'multiple_choice')
  const openQuestions = questions.filter(q => q.question_type === 'open')
  const current = questions[currentIdx]

  if (phase === 'idle') return (
    <div className="text-center py-8 space-y-4">
      <div className="text-4xl">📝</div>
      <p className="text-gray-600">Sẵn sàng kiểm tra kiến thức?</p>
      <Button onClick={handleStart} className="bg-indigo-600 hover:bg-indigo-700 px-8">
        Bắt đầu Quiz
      </Button>
    </div>
  )

  if (phase === 'loading') return (
    <div className="text-center py-8 text-gray-500">🤖 AI đang tạo câu hỏi...</div>
  )

  if (phase === 'result') return (
    <div className="space-y-6">
      <QuizResult result={submitResult} />
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-800">💭 Câu hỏi Tư duy Phản biện</h3>
        {openQuestions.map(q => (
          <OpenQuestion key={q.id} question={q} sessionId={sessionId} />
        ))}
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      {/* Progress */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>Câu {currentIdx + 1} / {questions.length}</span>
        <span>{mcqQuestions.length} trắc nghiệm + {openQuestions.length} tự luận</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div className="bg-indigo-600 h-2 rounded-full transition-all"
          style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }} />
      </div>

      {/* Current Question */}
      {current.question_type === 'multiple_choice' ? (
        <MultipleChoice
          question={current}
          selectedAnswer={answers[current.id]}
          onAnswer={(ans) => handleAnswer(current.id, ans)}
        />
      ) : (
        <OpenQuestion question={current} sessionId={sessionId} />
      )}

      <Button onClick={handleNext} className="w-full"
        disabled={current.question_type === 'multiple_choice' && !answers[current.id]}>
        {currentIdx < questions.length - 1 ? 'Câu tiếp →' : 'Nộp bài ✅'}
      </Button>
    </div>
  )
}
```

---

## `frontend/components/quiz/MultipleChoice.tsx`

```tsx
import { Card, CardContent } from '@/components/ui/card'
import type { QuizQuestion } from '@/types'

interface Props {
  question: QuizQuestion
  selectedAnswer?: string
  onAnswer: (answer: string) => void
}

export function MultipleChoice({ question, selectedAnswer, onAnswer }: Props) {
  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex items-start gap-3">
          <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded font-medium flex-shrink-0">
            {question.difficulty}
          </span>
          <p className="text-gray-800 font-medium leading-relaxed">{question.question_text}</p>
        </div>
        <div className="space-y-2">
          {question.options?.map(option => (
            <button key={option.id} onClick={() => onAnswer(option.id)}
              className={`w-full text-left p-3 rounded-lg border-2 transition-all
                ${selectedAnswer === option.id
                  ? 'border-indigo-500 bg-indigo-50 font-medium'
                  : 'border-gray-100 hover:border-indigo-200 hover:bg-gray-50'}`}>
              <span className="text-indigo-600 font-bold mr-2">{option.id}.</span>
              {option.text}
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## `frontend/components/quiz/OpenQuestion.tsx`

```tsx
'use client'
import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { getOpenFeedback } from '@/lib/api/quiz'
import type { QuizQuestion } from '@/types'

interface Props { question: QuizQuestion; sessionId: string }

export function OpenQuestion({ question }: Props) {
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const { data } = await getOpenFeedback(question.id, answer)
      setFeedback(data)
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = feedback?.critical_thinking_score >= 7 ? 'text-green-600' :
    feedback?.critical_thinking_score >= 4 ? 'text-yellow-600' : 'text-red-600'

  return (
    <Card className="border-purple-100">
      <CardContent className="p-6 space-y-4">
        <div className="flex items-start gap-2">
          <span className="text-purple-600 text-lg">💭</span>
          <p className="text-gray-800 font-medium">{question.question_text}</p>
        </div>

        {question.thinking_hints && (
          <div className="bg-purple-50 rounded-lg p-3">
            <p className="text-xs text-purple-700 font-medium mb-1">Gợi ý suy nghĩ:</p>
            <ul className="text-xs text-purple-600 space-y-1">
              {question.thinking_hints.map((hint, i) => <li key={i}>• {hint}</li>)}
            </ul>
          </div>
        )}

        {!feedback ? (
          <>
            <Textarea
              placeholder="Viết suy nghĩ của bạn... (không có đúng/sai, quan trọng là lập luận)"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              className="min-h-[120px] resize-none"
            />
            <Button onClick={handleSubmit} disabled={!answer.trim() || loading}
              className="bg-purple-600 hover:bg-purple-700">
              {loading ? '🤖 AI đang đánh giá...' : '📤 Gửi câu trả lời'}
            </Button>
          </>
        ) : (
          <div className="space-y-3">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Câu trả lời của bạn:</p>
              <p className="text-gray-700 text-sm">{answer}</p>
            </div>
            <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
              <div className="flex items-center justify-between mb-2">
                <p className="font-medium text-purple-800">📊 Đánh giá từ AI</p>
                <span className={`text-lg font-bold ${scoreColor}`}>
                  {feedback.critical_thinking_score}/10
                </span>
              </div>
              <p className="text-gray-700 text-sm">{feedback.ai_feedback}</p>
              {feedback.improvements?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1">Cần cải thiện:</p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    {feedback.improvements.map((imp: string, i: number) => <li key={i}>• {imp}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

---

## `frontend/components/quiz/QuizResult.tsx`

```tsx
interface Props { result: any }

export function QuizResult({ result }: Props) {
  const pct = result?.percentage || 0
  const color = pct >= 80 ? 'text-green-600' : pct >= 60 ? 'text-yellow-600' : 'text-red-600'
  const emoji = pct >= 80 ? '🎉' : pct >= 60 ? '👍' : '💪'

  return (
    <div className="bg-white rounded-2xl border p-6 text-center space-y-3">
      <div className="text-4xl">{emoji}</div>
      <div className={`text-4xl font-bold ${color}`}>{pct}%</div>
      <p className="text-gray-600">{result?.score}/{result?.total} câu đúng</p>
      {pct >= 80 && <p className="text-green-600 text-sm font-medium">Xuất sắc! Bạn nắm vững kiến thức này.</p>}
      {pct >= 60 && pct < 80 && <p className="text-yellow-600 text-sm">Khá tốt! Hãy ôn lại những điểm còn yếu.</p>}
      {pct < 60 && <p className="text-red-600 text-sm">Cần ôn thêm. Xem lại phần tóm tắt nhé!</p>}
    </div>
  )
}
```

---

## ✅ Checklist Bước 10
- [ ] QuizContainer: idle → loading → quiz → result
- [ ] MultipleChoice: chọn đáp án, highlight selection
- [ ] OpenQuestion: gửi → AI feedback hiển thị
- [ ] QuizResult: điểm số + emoji + nhận xét
- [ ] Quiz gắn với cả ANALYZE và EXPLORE sessions

---

## 🤖 Codex Prompt

```
Tạo các quiz components theo code trong 10-quiz-openquestion.md.
Test: từ tab Ôn tập trong ANALYZE → nhấn Bắt đầu Quiz → làm bài → xem kết quả → thử câu hỏi tự luận.
```

---
---

# 11 — Lịch sử Học & AI Tổng hợp Kiến thức

## `frontend/app/(app)/history/page.tsx`

```tsx
'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSessions, getKnowledgeReport } from '@/lib/api/history'
import { SessionCard } from '@/components/history/SessionCard'
import { KnowledgeReport } from '@/components/history/KnowledgeReport'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function HistoryPage() {
  const { data: sessionsData, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => getSessions().then(r => r.data),
  })

  const [reportLoading, setReportLoading] = useState(false)
  const [report, setReport] = useState<any>(null)

  const handleGenerateReport = async () => {
    setReportLoading(true)
    try {
      const { data } = await getKnowledgeReport()
      setReport(data)
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📚 Lịch sử Học tập</h1>
          <p className="text-gray-500 mt-1">Xem lại và phân tích hành trình học của bạn</p>
        </div>
        <Button onClick={handleGenerateReport} disabled={reportLoading}
          className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
          {reportLoading ? '🤖 Đang phân tích...' : '✨ Báo cáo AI'}
        </Button>
      </div>

      {report && <KnowledgeReport report={report} />}

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">Tất cả</TabsTrigger>
          <TabsTrigger value="analyze">🔍 Phân tích</TabsTrigger>
          <TabsTrigger value="explore">🔭 Khám phá</TabsTrigger>
        </TabsList>

        {['all', 'analyze', 'explore'].map(tab => (
          <TabsContent key={tab} value={tab}>
            {isLoading ? (
              <div className="space-y-3">
                {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />)}
              </div>
            ) : (
              <div className="space-y-3">
                {(sessionsData?.sessions || [])
                  .filter((s: any) => tab === 'all' || s.session_type === tab)
                  .map((session: any) => (
                    <SessionCard key={session.id} session={session} />
                  ))}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
```

---

## `frontend/components/history/SessionCard.tsx`

```tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toggleBookmark } from '@/lib/api/history'
import type { LearningSession } from '@/types'

interface Props { session: LearningSession }

export function SessionCard({ session }: Props) {
  const router = useRouter()
  const [bookmarked, setBookmarked] = useState(session.is_bookmarked)

  const handleBookmark = async (e: React.MouseEvent) => {
    e.stopPropagation()
    const { data } = await toggleBookmark(session.id)
    setBookmarked(data.is_bookmarked)
  }

  const typeLabel = session.session_type === 'analyze' ? '🔍 Phân tích' : '🔭 Khám phá'
  const typeColor = session.session_type === 'analyze'
    ? 'bg-blue-50 text-blue-700' : 'bg-purple-50 text-purple-700'

  return (
    <div onClick={() => router.push(`/history/${session.id}`)}
      className="bg-white rounded-xl border p-4 hover:shadow-md transition-all cursor-pointer group">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${typeColor}`}>{typeLabel}</span>
            {session.accuracy_score != null && (
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                ${session.accuracy_score >= 70 ? 'bg-green-50 text-green-700' :
                  session.accuracy_score >= 40 ? 'bg-yellow-50 text-yellow-700' :
                  'bg-red-50 text-red-700'}`}>
                {session.accuracy_score}% chính xác
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-800 truncate group-hover:text-indigo-600 transition-colors">
            {session.title}
          </h3>
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            {session.topic_tags?.slice(0, 3).map(tag => (
              <span key={tag} className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded">{tag}</span>
            ))}
            <span className="text-xs text-gray-400 ml-auto">
              {new Date(session.created_at).toLocaleDateString('vi-VN')}
            </span>
          </div>
        </div>
        <button onClick={handleBookmark} className="text-lg hover:scale-110 transition-transform">
          {bookmarked ? '⭐' : '☆'}
        </button>
      </div>
    </div>
  )
}
```

---

## `frontend/components/history/KnowledgeReport.tsx`

```tsx
interface Props { report: any }

export function KnowledgeReport({ report }: Props) {
  const patternLabel: Record<string, string> = {
    consistent: '📅 Học đều đặn',
    sporadic: '⚡ Học không thường xuyên',
    intensive: '🔥 Học chuyên sâu',
    new: '🌱 Mới bắt đầu',
  }
  const depthLabel: Record<string, string> = {
    surface: '🌊 Kiến thức bề mặt',
    intermediate: '🏊 Kiến thức trung cấp',
    deep: '🤿 Kiến thức sâu',
  }

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-100 space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-2xl">🤖</span>
        <h3 className="font-bold text-gray-800 text-lg">Báo cáo Kiến thức từ AI</h3>
      </div>

      <p className="text-gray-700 leading-relaxed">{report.ai_summary}</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-indigo-600">{report.total_sessions}</div>
          <div className="text-xs text-gray-500 mt-1">Bài học</div>
        </div>
        <div className="bg-white rounded-xl p-3 text-center">
          <div className="text-2xl font-bold text-purple-600">{report.total_quizzes}</div>
          <div className="text-xs text-gray-500 mt-1">Quiz đã làm</div>
        </div>
        <div className="bg-white rounded-xl p-3 text-center">
          <div className="text-sm font-semibold text-gray-700">{patternLabel[report.learning_pattern] || '—'}</div>
        </div>
        <div className="bg-white rounded-xl p-3 text-center">
          <div className="text-sm font-semibold text-gray-700">{depthLabel[report.knowledge_depth] || '—'}</div>
        </div>
      </div>

      {report.ai_recommendations?.length > 0 && (
        <div className="bg-white rounded-xl p-4">
          <p className="text-sm font-semibold text-indigo-700 mb-2">🎯 AI gợi ý tiếp theo:</p>
          <ul className="space-y-1">
            {report.ai_recommendations.map((rec: string, i: number) => (
              <li key={i} className="text-sm text-gray-700 flex gap-2">
                <span className="text-indigo-400">→</span>{rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
```

---

## ✅ Checklist Bước 11
- [ ] `/history` hiển thị danh sách sessions có filter
- [ ] SessionCard: title, type badge, accuracy, tags, bookmark
- [ ] KnowledgeReport: stats + AI summary + recommendations
- [ ] `/history/[id]` trang chi tiết session

---

## 🤖 Codex Prompt

```
Tạo components history theo code trong 11-history-analytics.md.
Tạo thêm app/(app)/history/[id]/page.tsx để hiển thị chi tiết 1 session (load từ API và render lại AnalysisResult hoặc ExploreResult).
Test: /history → xem danh sách → nhấn Báo cáo AI → xem KnowledgeReport.
```

---
---

# 12 — Layout & Sidebar

## `frontend/components/layout/Sidebar.tsx`

```tsx
'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'

const NAV_ITEMS = [
  { href: '/dashboard',  icon: '🏠', label: 'Trang chủ' },
  { href: '/analyze',    icon: '🔍', label: 'Phân tích' },
  { href: '/explore',    icon: '🔭', label: 'Khám phá' },
  { href: '/history',    icon: '📚', label: 'Lịch sử' },
  { href: '/profile',    icon: '👤', label: 'Hồ sơ' },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const supabase = createClient()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <aside className="w-64 bg-white border-r flex flex-col h-screen">
      {/* Logo */}
      <div className="p-6 border-b">
        <div className="text-xl font-bold text-indigo-600">DUO MIND</div>
        <div className="text-xs text-gray-400 mt-0.5">AI Learning Platform</div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map(({ href, icon, label }) => {
          const active = pathname === href
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all
                ${active
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-indigo-600'}`}>
              <span className="text-lg">{icon}</span>
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t">
        <button onClick={handleLogout}
          className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm text-gray-500 hover:bg-red-50 hover:text-red-600 transition-all">
          <span>🚪</span> Đăng xuất
        </button>
      </div>
    </aside>
  )
}
```

---

## `frontend/app/(app)/dashboard/page.tsx`

```tsx
import { createClient } from '@/lib/supabase/server'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  const { data: profile } = await supabase.from('profiles').select('*').eq('id', user!.id).single()
  const { data: onboarding } = await supabase.from('user_onboarding').select('*').eq('user_id', user!.id).single()

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Welcome */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold">Xin chào! 👋</h1>
        <p className="text-white/80 mt-1">Sẵn sàng học hôm nay chưa?</p>
        {onboarding?.ai_persona && (
          <div className="mt-3 bg-white/20 rounded-lg px-3 py-2 inline-block">
            <span className="text-sm">🤖 AI persona: <strong>{onboarding.ai_persona}</strong></span>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-4">
        <a href="/analyze" className="group bg-white rounded-2xl border p-6 hover:shadow-md transition-all hover:border-blue-200">
          <div className="text-3xl mb-3">🔍</div>
          <h3 className="font-bold text-gray-800 group-hover:text-blue-600">Phân tích Kiến thức</h3>
          <p className="text-gray-500 text-sm mt-1">Nhập nội dung để AI kiểm tra độ chính xác</p>
        </a>
        <a href="/explore" className="group bg-white rounded-2xl border p-6 hover:shadow-md transition-all hover:border-purple-200">
          <div className="text-3xl mb-3">🔭</div>
          <h3 className="font-bold text-gray-800 group-hover:text-purple-600">Khám phá Chủ đề</h3>
          <p className="text-gray-500 text-sm mt-1">Tìm hiểu bất kỳ chủ đề nào với AI</p>
        </a>
      </div>
    </div>
  )
}
```

---

## ✅ Checklist Bước 12
- [ ] Sidebar hiển thị đúng active state
- [ ] Dashboard với welcome banner + quick actions
- [ ] Logout hoạt động

---
---

# 13 — Deploy

## Backend — Railway

```bash
# 1. Push code lên GitHub
git add . && git commit -m "Initial commit"
git push origin main

# 2. Railway Dashboard → New Project → Deploy from GitHub
# Chọn repo → chọn thư mục backend/

# 3. Thêm biến môi trường trong Railway Settings:
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
GEMINI_API_KEY=...
SECRET_KEY=...
ENVIRONMENT=production
FRONTEND_URL=https://your-app.vercel.app
```

## Frontend — Vercel

```bash
# 1. Vercel Dashboard → New Project → Import from GitHub
# Chọn repo → Root Directory: frontend/

# 2. Thêm biến môi trường:
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# 3. Deploy!
```

## Checklist Deploy
- [ ] Backend chạy trên Railway, /health trả về OK
- [ ] Frontend chạy trên Vercel
- [ ] CORS: FRONTEND_URL trong Railway = URL Vercel thật
- [ ] Supabase Auth: thêm Vercel URL vào "Redirect URLs"
- [ ] Test end-to-end: đăng ký → onboarding → analyze → quiz

---

## 🤖 Codex Prompt

```
Deploy DUO MIND:
1. Tạo railway.toml trong backend/ đúng config
2. Đảm bảo requirements.txt đầy đủ
3. Tạo vercel.json trong frontend/ nếu cần
4. Kiểm tra tất cả biến môi trường đã được config
5. Test production URLs hoạt động end-to-end
```
