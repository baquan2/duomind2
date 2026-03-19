# 08 — Tính năng ANALYZE (Phân tích nội dung)

## Mục tiêu
Trang ANALYZE: người dùng nhập nội dung → AI phân tích → hiển thị kết quả + mind map + quiz.

---

## `frontend/app/(app)/analyze/page.tsx`

```tsx
'use client'
import { useState } from 'react'
import { ContentInput } from '@/components/analyze/ContentInput'
import { AnalysisResult } from '@/components/analyze/AnalysisResult'
import { analyzeContent } from '@/lib/api/analyze'
import type { AnalyzeResult } from '@/types'

export default function AnalyzePage() {
  const [result, setResult] = useState<AnalyzeResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleAnalyze = async (content: string) => {
    setLoading(true)
    setResult(null)
    try {
      const data = await analyzeContent(content)
      setResult(data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🔍 Phân tích Kiến thức</h1>
        <p className="text-gray-500 mt-1">Nhập nội dung bạn muốn kiểm tra — AI sẽ đánh giá độ chính xác và tóm tắt</p>
      </div>
      <ContentInput onSubmit={handleAnalyze} loading={loading} />
      {result && <AnalysisResult result={result} />}
    </div>
  )
}
```

---

## `frontend/components/analyze/ContentInput.tsx`

```tsx
'use client'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'

interface Props {
  onSubmit: (content: string) => void
  loading: boolean
}

export function ContentInput({ onSubmit, loading }: Props) {
  const [content, setContent] = useState('')

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <Textarea
          placeholder="Dán hoặc nhập nội dung bạn muốn AI kiểm tra độ chính xác... (tối đa 8000 ký tự)"
          value={content}
          onChange={e => setContent(e.target.value)}
          className="min-h-[200px] text-base resize-none"
        />
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">{content.length}/8000 ký tự</span>
          <Button
            onClick={() => onSubmit(content)}
            disabled={!content.trim() || loading}
            className="bg-indigo-600 hover:bg-indigo-700 px-8"
          >
            {loading ? '🤖 Đang phân tích...' : '✨ Phân tích ngay'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

---

## `frontend/components/analyze/AnalysisResult.tsx`

```tsx
'use client'
import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AccuracyBadge } from './AccuracyBadge'
import { SummaryCard } from './SummaryCard'
import { MindMapViewer } from '@/components/mindmap/MindMapViewer'
import { QuizContainer } from '@/components/quiz/QuizContainer'
import type { AnalyzeResult } from '@/types'
import { motion } from 'framer-motion'

interface Props { result: AnalyzeResult }

export function AnalysisResult({ result }: Props) {
  const [quizGenerated, setQuizGenerated] = useState(false)

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">{result.title}</h2>
          <div className="flex gap-2 mt-2 flex-wrap">
            {result.topic_tags.map(tag => (
              <span key={tag} className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded-full">{tag}</span>
            ))}
          </div>
        </div>
        <AccuracyBadge score={result.accuracy_score} assessment={result.accuracy_assessment} />
      </div>

      <Tabs defaultValue="summary">
        <TabsList className="grid grid-cols-4 w-full">
          <TabsTrigger value="summary">📋 Tóm tắt</TabsTrigger>
          <TabsTrigger value="corrections">⚠️ Đính chính</TabsTrigger>
          <TabsTrigger value="mindmap">🗺️ Mind Map</TabsTrigger>
          <TabsTrigger value="quiz">📝 Ôn tập</TabsTrigger>
        </TabsList>

        <TabsContent value="summary">
          <SummaryCard summary={result.summary} keyPoints={result.key_points} />
        </TabsContent>

        <TabsContent value="corrections">
          {result.corrections.length === 0 ? (
            <div className="text-center py-8 text-green-600">
              <div className="text-4xl mb-2">✅</div>
              <p className="font-medium">Nội dung chính xác!</p>
              <p className="text-sm text-gray-500">AI không tìm thấy thông tin cần đính chính</p>
            </div>
          ) : (
            <div className="space-y-3">
              {result.corrections.map((c, i) => (
                <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <p className="text-sm text-red-600 line-through mb-1">❌ {c.original}</p>
                  <p className="text-sm text-green-700 font-medium mb-1">✅ {c.correction}</p>
                  <p className="text-xs text-gray-500">{c.explanation}</p>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="mindmap">
          <div className="h-96 rounded-xl overflow-hidden border">
            <MindMapViewer sessionId={result.session_id} />
          </div>
        </TabsContent>

        <TabsContent value="quiz">
          <QuizContainer sessionId={result.session_id} />
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
```

---

## `frontend/components/analyze/AccuracyBadge.tsx`

```tsx
interface Props { score: number; assessment: string }

const CONFIG = {
  high:          { color: 'bg-green-100 text-green-800 border-green-200',  emoji: '✅', label: 'Chính xác cao' },
  medium:        { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', emoji: '⚠️', label: 'Cần kiểm tra' },
  low:           { color: 'bg-red-100 text-red-800 border-red-200',         emoji: '❌', label: 'Nhiều sai sót' },
  unverifiable:  { color: 'bg-gray-100 text-gray-700 border-gray-200',     emoji: '❓', label: 'Khó xác minh' },
}

export function AccuracyBadge({ score, assessment }: Props) {
  const cfg = CONFIG[assessment as keyof typeof CONFIG] || CONFIG.unverifiable
  return (
    <div className={`flex flex-col items-center px-4 py-2 rounded-xl border ${cfg.color} min-w-[80px]`}>
      <span className="text-2xl">{cfg.emoji}</span>
      {score != null && <span className="text-xl font-bold">{score}</span>}
      <span className="text-xs font-medium">{cfg.label}</span>
    </div>
  )
}
```

---

## `frontend/components/analyze/SummaryCard.tsx`

```tsx
import { Card, CardContent } from '@/components/ui/card'

interface Props { summary: string; keyPoints: string[] }

export function SummaryCard({ summary, keyPoints }: Props) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-5">
          <p className="text-sm font-medium text-indigo-600 mb-2">📖 Tóm tắt</p>
          <p className="text-gray-700 leading-relaxed">{summary}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-5">
          <p className="text-sm font-medium text-indigo-600 mb-3">🔑 Điểm chính</p>
          <ul className="space-y-2">
            {keyPoints.map((point, i) => (
              <li key={i} className="flex gap-2 text-gray-700">
                <span className="text-indigo-400 font-bold flex-shrink-0">{i + 1}.</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
```

---

## ✅ Checklist Bước 08
- [ ] `/analyze` page render ContentInput
- [ ] Submit → loading state → gọi API
- [ ] Kết quả hiển thị với 4 tabs: Tóm tắt, Đính chính, Mind Map, Ôn tập
- [ ] AccuracyBadge hiển thị đúng màu theo assessment
- [ ] Corrections list hiện đúng hoặc "Chính xác" nếu rỗng

---

## 🤖 Codex Prompt

```
Tạo tất cả files cho tính năng ANALYZE theo code trong 08-analyze-feature.md.
Test: vào /analyze → nhập nội dung → nhấn Phân tích → xem kết quả với 4 tabs.
```
