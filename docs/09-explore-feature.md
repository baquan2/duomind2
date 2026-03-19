# 09 — Tính năng EXPLORE + Mind Map + Infographic

## Mục tiêu
Trang EXPLORE: nhập prompt tự nhiên → AI tìm kiếm → trả về tóm tắt + infographic + mind map + quiz.

---

## `frontend/app/(app)/explore/page.tsx`

```tsx
'use client'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { exploreTopicApi } from '@/lib/api/analyze'
import { Infographic } from '@/components/explore/Infographic'
import { MindMapViewer } from '@/components/mindmap/MindMapViewer'
import { QuizContainer } from '@/components/quiz/QuizContainer'
import { SummaryCard } from '@/components/analyze/SummaryCard'
import { motion } from 'framer-motion'
import type { ExploreResult } from '@/types'

const EXAMPLE_PROMPTS = [
  "Trí tuệ nhân tạo (AI) là gì và hoạt động như thế nào?",
  "Blockchain và tiền mã hóa — giải thích đơn giản",
  "Nguyên nhân và hậu quả của biến đổi khí hậu",
  "Cách thị trường chứng khoán hoạt động",
]

export default function ExplorePage() {
  const [prompt, setPrompt] = useState('')
  const [result, setResult] = useState<ExploreResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleExplore = async (p?: string) => {
    const query = p || prompt
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const data = await exploreTopicApi(query)
      setResult(data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">🔭 Khám phá Kiến thức</h1>
        <p className="text-gray-500 mt-1">Nhập bất kỳ chủ đề gì — AI sẽ tìm kiếm và giải thích cho bạn</p>
      </div>

      <Card>
        <CardContent className="p-6 space-y-4">
          <Textarea
            placeholder="Ví dụ: Trí tuệ nhân tạo là gì? | Lịch sử Việt Nam | Cách học lập trình hiệu quả..."
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            className="min-h-[100px] text-base resize-none"
            onKeyDown={e => { if (e.key === 'Enter' && e.ctrlKey) handleExplore() }}
          />
          <div className="flex items-center justify-between">
            <div className="flex gap-2 flex-wrap">
              {EXAMPLE_PROMPTS.map(p => (
                <button key={p} onClick={() => { setPrompt(p); handleExplore(p) }}
                  className="text-xs text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full hover:bg-indigo-100 transition-colors">
                  {p.substring(0, 30)}...
                </button>
              ))}
            </div>
            <Button onClick={() => handleExplore()} disabled={!prompt.trim() || loading}
              className="bg-purple-600 hover:bg-purple-700 px-8 ml-4 flex-shrink-0">
              {loading ? '🔍 Đang tìm...' : '🚀 Khám phá'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {result && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-xl font-semibold text-gray-800">{result.title}</h2>
          </div>

          <Tabs defaultValue="summary">
            <TabsList className="grid grid-cols-4 w-full">
              <TabsTrigger value="summary">📋 Tóm tắt</TabsTrigger>
              <TabsTrigger value="infographic">📊 Infographic</TabsTrigger>
              <TabsTrigger value="mindmap">🗺️ Mind Map</TabsTrigger>
              <TabsTrigger value="quiz">📝 Ôn tập</TabsTrigger>
            </TabsList>

            <TabsContent value="summary">
              <SummaryCard summary={result.summary} keyPoints={result.key_points} />
            </TabsContent>

            <TabsContent value="infographic">
              <Infographic data={result.infographic_data} />
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
      )}
    </div>
  )
}
```

---

## `frontend/components/explore/Infographic.tsx`

```tsx
import type { InfographicData } from '@/types'

interface Props { data: InfographicData }

export function Infographic({ data }: Props) {
  const color = data.theme_color || '#6366f1'

  return (
    <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-6 text-white" style={{ backgroundColor: color }}>
        <h3 className="text-xl font-bold">{data.title}</h3>
        {data.subtitle && <p className="text-white/80 mt-1 text-sm">{data.subtitle}</p>}
      </div>

      {/* Sections */}
      <div className="p-4 space-y-3">
        {data.sections.map((section, i) => (
          <div key={i} className="flex gap-4 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
            <div className="text-2xl flex-shrink-0 w-10 h-10 flex items-center justify-center
              rounded-full text-white text-sm font-bold"
              style={{ backgroundColor: color }}>
              {section.icon || (i + 1)}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-gray-800">{section.heading}</p>
                {section.highlight && (
                  <span className="text-sm font-bold px-2 py-1 rounded-lg text-white"
                    style={{ backgroundColor: color }}>
                    {section.highlight}
                  </span>
                )}
              </div>
              <p className="text-gray-600 text-sm mt-1">{section.content}</p>
            </div>
          </div>
        ))}
      </div>

      {data.footer_note && (
        <div className="px-4 pb-4">
          <p className="text-xs text-gray-400 italic text-center">{data.footer_note}</p>
        </div>
      )}
    </div>
  )
}
```

---

## `frontend/components/mindmap/MindMapViewer.tsx`

```tsx
'use client'
import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Node, Edge, Background, Controls, MiniMap,
  useNodesState, useEdgesState, NodeTypes
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { CustomNode } from './CustomNode'
import apiClient from '@/lib/api/client'

const nodeTypes: NodeTypes = {
  root: CustomNode,
  main: CustomNode,
  sub: CustomNode,
}

interface Props { sessionId: string }

export function MindMapViewer({ sessionId }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await apiClient.get(`/api/history/sessions/${sessionId}`)
        const mindmapData = data.session?.mindmap_data
        if (mindmapData?.nodes) {
          setNodes(mindmapData.nodes)
          setEdges(mindmapData.edges || [])
        }
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [sessionId])

  if (loading) return (
    <div className="h-full flex items-center justify-center text-gray-400">
      🗺️ Đang tải mind map...
    </div>
  )

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      className="bg-slate-50"
    >
      <Background color="#e2e8f0" gap={20} />
      <Controls />
      <MiniMap />
    </ReactFlow>
  )
}
```

---

## `frontend/components/mindmap/CustomNode.tsx`

```tsx
import { Handle, Position } from '@xyflow/react'

interface Props {
  data: { label: string; description?: string; color?: string }
  type: string
}

const STYLES = {
  root: 'bg-indigo-600 text-white border-indigo-700 text-base font-bold px-6 py-3',
  main: 'bg-white border-2 text-gray-800 font-medium px-4 py-2',
  sub:  'bg-gray-50 border text-gray-600 text-sm px-3 py-2',
}

export function CustomNode({ data, type }: Props) {
  const style = STYLES[type as keyof typeof STYLES] || STYLES.sub
  const borderColor = type === 'main' && data.color ? { borderColor: data.color } : {}

  return (
    <div className={`rounded-xl shadow-sm max-w-[180px] text-center ${style}`} style={borderColor}>
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <p className="truncate">{data.label}</p>
      {data.description && type !== 'root' && (
        <p className="text-xs opacity-60 mt-1 truncate">{data.description}</p>
      )}
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
```

---

## ✅ Checklist Bước 09
- [ ] `/explore` page với textarea + example prompts
- [ ] Submit → 4 tabs kết quả
- [ ] Infographic renderer hiển thị đúng kiểu (steps/list/comparison/...)
- [ ] MindMapViewer load data từ session và render ReactFlow
- [ ] CustomNode hiển thị đúng style theo type (root/main/sub)

---

## 🤖 Codex Prompt

```
Tạo tất cả files cho tính năng EXPLORE, Infographic, và MindMapViewer theo code trong 09-explore-feature.md.
Cài thêm: npm install @xyflow/react
Test: /explore → nhập prompt → xem Infographic và Mind Map tabs.
```
