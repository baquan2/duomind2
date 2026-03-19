# 06 — Frontend Setup (Next.js + Supabase Auth)

## Mục tiêu
Setup Next.js App Router với Supabase Auth, layout chính, routing bảo vệ, và API client.

---

## `frontend/lib/supabase/client.ts`

```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

## `frontend/lib/supabase/server.ts`

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {}
        },
      },
    }
  )
}
```

---

## `frontend/lib/api/client.ts`

```typescript
import axios from 'axios'
import { createClient } from '@/lib/supabase/client'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor: tự gắn Bearer token
apiClient.interceptors.request.use(async (config) => {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

export default apiClient
```

---

## `frontend/lib/api/analyze.ts`

```typescript
import apiClient from './client'

export const analyzeContent = async (content: string, language = 'vi') => {
  const { data } = await apiClient.post('/api/analyze/', { content, language })
  return data
}

export const exploreTopicApi = async (prompt: string, language = 'vi') => {
  const { data } = await apiClient.post('/api/explore/', { prompt, language })
  return data
}
```

## `frontend/lib/api/quiz.ts`

```typescript
import apiClient from './client'

export const generateQuiz = (sessionId: string, numQuestions = 5) =>
  apiClient.post('/api/quiz/generate', { session_id: sessionId, num_questions: numQuestions, include_open: true })

export const getQuiz = (sessionId: string) =>
  apiClient.get(`/api/quiz/${sessionId}`)

export const submitQuiz = (sessionId: string, answers: any[]) =>
  apiClient.post('/api/quiz/submit', { session_id: sessionId, answers })

export const getOpenFeedback = (questionId: string, userAnswer: string) =>
  apiClient.post('/api/quiz/open-feedback', { question_id: questionId, user_answer: userAnswer })
```

## `frontend/lib/api/history.ts`

```typescript
import apiClient from './client'

export const getSessions = (limit = 20, offset = 0) =>
  apiClient.get('/api/history/sessions', { params: { limit, offset } })

export const getSessionDetail = (id: string) =>
  apiClient.get(`/api/history/sessions/${id}`)

export const toggleBookmark = (id: string) =>
  apiClient.patch(`/api/history/sessions/${id}/bookmark`)

export const getKnowledgeReport = () =>
  apiClient.get('/api/analytics/knowledge-report')
```

---

## `frontend/types/index.ts`

```typescript
export interface UserProfile {
  id: string
  email: string
  full_name?: string
  is_onboarded: boolean
  created_at: string
}

export interface OnboardingData {
  age_range: string
  status: string
  education_level?: string
  major?: string
  industry?: string
  job_title?: string
  learning_goals: string[]
  topics_of_interest: string[]
  learning_style: string
  daily_study_minutes: number
}

export interface AnalyzeResult {
  session_id: string
  title: string
  accuracy_score: number
  accuracy_assessment: 'high' | 'medium' | 'low' | 'unverifiable'
  summary: string
  key_points: string[]
  corrections: Correction[]
  topic_tags: string[]
}

export interface Correction {
  original: string
  correction: string
  explanation: string
}

export interface ExploreResult {
  session_id: string
  title: string
  summary: string
  key_points: string[]
  infographic_data: InfographicData
  topic_tags: string[]
}

export interface InfographicData {
  type: 'steps' | 'comparison' | 'statistics' | 'timeline' | 'list'
  theme_color: string
  title: string
  subtitle?: string
  sections: InfographicSection[]
  footer_note?: string
}

export interface InfographicSection {
  icon: string
  heading: string
  content: string
  highlight?: string
}

export interface MindMapData {
  nodes: MindMapNode[]
  edges: MindMapEdge[]
}

export interface MindMapNode {
  id: string
  type: 'root' | 'main' | 'sub'
  data: { label: string; description?: string; color?: string }
  position: { x: number; y: number }
}

export interface MindMapEdge {
  id: string
  source: string
  target: string
  type?: string
}

export interface LearningSession {
  id: string
  session_type: 'analyze' | 'explore'
  title: string
  topic_tags: string[]
  accuracy_score?: number
  created_at: string
  is_bookmarked: boolean
}

export interface QuizQuestion {
  id: string
  question_type: 'multiple_choice' | 'open'
  question_text: string
  options?: { id: string; text: string }[]
  explanation?: string
  difficulty: 'easy' | 'medium' | 'hard'
  thinking_hints?: string[]
}
```

---

## `frontend/store/userStore.ts`

```typescript
import { create } from 'zustand'
import { UserProfile } from '@/types'

interface UserStore {
  user: UserProfile | null
  isLoading: boolean
  setUser: (user: UserProfile | null) => void
  setLoading: (loading: boolean) => void
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user }),
  setLoading: (isLoading) => set({ isLoading }),
}))
```

---

## `frontend/app/layout.tsx`

```tsx
import type { Metadata } from 'next'
import { Outfit, Space_Grotesk } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers/Providers'

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
})

export const metadata: Metadata = {
  title: 'DUO MIND — Hệ thống Giáo dục Thông minh',
  description: 'Phân tích, đối chiếu và học tập với AI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className={`${outfit.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

---

## `frontend/components/providers/Providers.tsx`

```tsx
'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 60 * 1000, retry: 1 } }
  }))

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
```

---

## `frontend/middleware.ts` — Route Protection

```typescript
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()
  const { pathname } = request.nextUrl

  // Chưa đăng nhập → redirect về /login
  if (!user && pathname.startsWith('/(app)') || 
      !user && ['/dashboard', '/analyze', '/explore', '/history', '/onboarding', '/profile'].some(p => pathname.startsWith(p))) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  // Đã đăng nhập, vào trang auth → redirect về /dashboard
  if (user && (pathname === '/login' || pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
}
```

---

## `frontend/app/(auth)/login/page.tsx`

```tsx
'use client'
import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()
  const supabase = createClient()

  const handleLogin = async () => {
    setLoading(true)
    setError('')
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      router.push('/dashboard')
      router.refresh()
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="text-3xl font-bold text-indigo-600 mb-1">DUO MIND</div>
          <CardTitle className="text-gray-600 font-normal">Đăng nhập để học cùng AI</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input placeholder="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} />
          <Input placeholder="Mật khẩu" type="password" value={password} onChange={e => setPassword(e.target.value)} />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button className="w-full" onClick={handleLogin} disabled={loading}>
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </Button>
          <p className="text-center text-sm text-gray-500">
            Chưa có tài khoản? <a href="/signup" className="text-indigo-600 hover:underline">Đăng ký</a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
```

---

## `frontend/app/(app)/layout.tsx` — App Shell

```tsx
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Sidebar } from '@/components/layout/Sidebar'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/login')

  // Kiểm tra onboarding
  const { data: profile } = await supabase
    .from('profiles')
    .select('is_onboarded')
    .eq('id', user.id)
    .single()

  if (profile && !profile.is_onboarded) {
    // Cho phép vào /onboarding
    // redirect sẽ handle ở middleware
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
```

---

## ✅ Checklist Bước 06

- [ ] Supabase client (browser + server) đã tạo
- [ ] API client với token interceptor hoạt động
- [ ] TypeScript types đầy đủ
- [ ] Zustand user store
- [ ] Middleware route protection
- [ ] Login page hoạt động
- [ ] App shell layout với Sidebar placeholder
- [ ] Test: đăng nhập → redirect /dashboard

---

## ➡️ Bước Tiếp theo
Đọc `07-onboarding-flow.md` để build wizard onboarding.

---

## 🤖 Codex Prompt

```
Trong thư mục frontend/, tạo các file theo code trong 06-frontend-setup.md:
1. lib/supabase/client.ts và server.ts
2. lib/api/client.ts, analyze.ts, quiz.ts, history.ts
3. types/index.ts
4. store/userStore.ts
5. app/layout.tsx và components/providers/Providers.tsx
6. middleware.ts
7. app/(auth)/login/page.tsx
8. app/(app)/layout.tsx

Test: npm run dev → truy cập /login → đăng nhập thành công → redirect /dashboard
```
