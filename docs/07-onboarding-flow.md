# 07 — Onboarding Flow (Wizard 4 Bước)

## Mục tiêu
Wizard onboarding xuất hiện sau lần đăng nhập đầu tiên. AI phân loại người dùng sau bước cuối.

---

## Flow

```
Đăng nhập lần đầu
    ↓
/onboarding
    ↓
Step 1: Thông tin cơ bản (tuổi + học/làm)
    ↓
Step 2: Chi tiết (ngành học HOẶC ngành nghề — tùy Step 1)
    ↓
Step 3: Mục tiêu & sở thích
    ↓
Step 4: Xác nhận → Gọi API → AI classify → Hiển thị persona
    ↓
/dashboard
```

---

## `frontend/app/(app)/onboarding/page.tsx`

```tsx
'use client'
import { OnboardingWizard } from '@/components/onboarding/OnboardingWizard'

export default function OnboardingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <OnboardingWizard />
    </div>
  )
}
```

---

## `frontend/components/onboarding/OnboardingWizard.tsx`

```tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { StepIndicator } from './StepIndicator'
import { Step1Basic } from './steps/Step1Basic'
import { Step2Details } from './steps/Step2Details'
import { Step3Goals } from './steps/Step3Goals'
import { Step4Confirm } from './steps/Step4Confirm'
import apiClient from '@/lib/api/client'
import type { OnboardingData } from '@/types'

const TOTAL_STEPS = 4

export function OnboardingWizard() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [aiResult, setAiResult] = useState<any>(null)
  const [data, setData] = useState<Partial<OnboardingData>>({
    learning_goals: [],
    topics_of_interest: [],
    learning_style: 'mixed',
    daily_study_minutes: 30,
  })

  const updateData = (updates: Partial<OnboardingData>) => {
    setData(prev => ({ ...prev, ...updates }))
  }

  const nextStep = () => setStep(s => Math.min(s + 1, TOTAL_STEPS))
  const prevStep = () => setStep(s => Math.max(s - 1, 1))

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const { data: result } = await apiClient.post('/api/onboarding/submit', data)
      setAiResult(result)
      // Sau 3 giây → vào dashboard
      setTimeout(() => router.push('/dashboard'), 3000)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const stepComponents = [
    <Step1Basic data={data} onChange={updateData} />,
    <Step2Details data={data} onChange={updateData} />,
    <Step3Goals data={data} onChange={updateData} />,
    <Step4Confirm data={data} aiResult={aiResult} loading={loading} onSubmit={handleSubmit} />,
  ]

  return (
    <div className="w-full max-w-2xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-indigo-600">DUO MIND</h1>
        <p className="text-gray-500 mt-2">Giúp AI hiểu bạn để cá nhân hóa trải nghiệm học</p>
      </div>

      {/* Progress */}
      <div className="mb-6">
        <Progress value={(step / TOTAL_STEPS) * 100} className="h-2" />
        <StepIndicator current={step} total={TOTAL_STEPS} />
      </div>

      {/* Step Content */}
      <Card className="shadow-xl border-0">
        <CardContent className="p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.25 }}
            >
              {stepComponents[step - 1]}
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Navigation */}
      {!aiResult && (
        <div className="flex justify-between mt-6">
          <Button variant="outline" onClick={prevStep} disabled={step === 1}>
            ← Quay lại
          </Button>
          {step < TOTAL_STEPS ? (
            <Button onClick={nextStep}>
              Tiếp theo →
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={loading} className="bg-indigo-600 hover:bg-indigo-700">
              {loading ? '🤖 AI đang phân tích...' : '✨ Hoàn thành'}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
```

---

## `frontend/components/onboarding/StepIndicator.tsx`

```tsx
interface Props { current: number; total: number }

export function StepIndicator({ current, total }: Props) {
  const labels = ['Cơ bản', 'Chi tiết', 'Mục tiêu', 'Hoàn thành']
  return (
    <div className="flex justify-between mt-3">
      {Array.from({ length: total }, (_, i) => (
        <div key={i} className="flex flex-col items-center flex-1">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors
            ${i + 1 < current ? 'bg-indigo-600 text-white' :
              i + 1 === current ? 'bg-indigo-600 text-white ring-4 ring-indigo-100' :
              'bg-gray-100 text-gray-400'}`}>
            {i + 1 < current ? '✓' : i + 1}
          </div>
          <span className={`text-xs mt-1 ${i + 1 === current ? 'text-indigo-600 font-medium' : 'text-gray-400'}`}>
            {labels[i]}
          </span>
        </div>
      ))}
    </div>
  )
}
```

---

## `frontend/components/onboarding/steps/Step1Basic.tsx`

```tsx
'use client'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'

const AGE_RANGES = [
  { value: 'under_18', label: 'Dưới 18 tuổi' },
  { value: '18_24', label: '18 – 24 tuổi' },
  { value: '25_34', label: '25 – 34 tuổi' },
  { value: '35_44', label: '35 – 44 tuổi' },
  { value: '45_plus', label: '45 tuổi trở lên' },
]

const STATUS_OPTIONS = [
  { value: 'student', label: '🎓 Đang đi học', desc: 'Học sinh, sinh viên, học viên' },
  { value: 'working', label: '💼 Đang đi làm', desc: 'Nhân viên, tự kinh doanh' },
  { value: 'both', label: '⚡ Vừa học vừa làm', desc: 'Học và làm song song' },
  { value: 'other', label: '🌟 Khác', desc: 'Freelance, nghỉ ngơi, tìm việc...' },
]

interface Props {
  data: any
  onChange: (d: any) => void
}

export function Step1Basic({ data, onChange }: Props) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-1">Xin chào! 👋</h2>
        <p className="text-gray-500 text-sm">Cho AI biết một chút về bạn để cá nhân hóa nội dung học</p>
      </div>

      {/* Độ tuổi */}
      <div>
        <Label className="text-base font-medium">Độ tuổi của bạn?</Label>
        <RadioGroup
          value={data.age_range}
          onValueChange={v => onChange({ age_range: v })}
          className="grid grid-cols-2 gap-2 mt-3"
        >
          {AGE_RANGES.map(({ value, label }) => (
            <div key={value} className={`flex items-center space-x-2 p-3 rounded-lg border-2 cursor-pointer transition-colors
              ${data.age_range === value ? 'border-indigo-500 bg-indigo-50' : 'border-gray-100 hover:border-gray-300'}`}>
              <RadioGroupItem value={value} id={value} />
              <Label htmlFor={value} className="cursor-pointer font-normal">{label}</Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      {/* Trạng thái */}
      <div>
        <Label className="text-base font-medium">Bạn đang?</Label>
        <div className="grid grid-cols-2 gap-3 mt-3">
          {STATUS_OPTIONS.map(({ value, label, desc }) => (
            <button key={value} onClick={() => onChange({ status: value })}
              className={`p-4 rounded-xl border-2 text-left transition-all
                ${data.status === value ? 'border-indigo-500 bg-indigo-50' : 'border-gray-100 hover:border-indigo-200'}`}>
              <div className="font-medium text-gray-800">{label}</div>
              <div className="text-xs text-gray-500 mt-1">{desc}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

---

## `frontend/components/onboarding/steps/Step2Details.tsx`

```tsx
'use client'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface Props { data: any; onChange: (d: any) => void }

export function Step2Details({ data, onChange }: Props) {
  const isStudent = ['student', 'both'].includes(data.status)
  const isWorking = ['working', 'both'].includes(data.status)

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold text-gray-800">Thông tin chi tiết 📋</h2>
        <p className="text-gray-500 text-sm mt-1">AI dùng thông tin này để điều chỉnh độ khó và ví dụ phù hợp</p>
      </div>

      {isStudent && (
        <div className="space-y-4 p-4 bg-blue-50 rounded-xl">
          <p className="font-medium text-blue-800 text-sm">🎓 Thông tin học tập</p>
          <div>
            <Label>Trình độ</Label>
            <Select onValueChange={v => onChange({ education_level: v })} value={data.education_level}>
              <SelectTrigger><SelectValue placeholder="Chọn trình độ" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="high_school">THPT / Trung học</SelectItem>
                <SelectItem value="college">Cao đẳng</SelectItem>
                <SelectItem value="university">Đại học</SelectItem>
                <SelectItem value="postgrad">Sau đại học</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Chuyên ngành / Môn học chính</Label>
            <Input placeholder="VD: Công nghệ thông tin, Y khoa, Kinh tế..."
              value={data.major || ''} onChange={e => onChange({ major: e.target.value })} />
          </div>
          <div>
            <Label>Trường (tùy chọn)</Label>
            <Input placeholder="Tên trường của bạn"
              value={data.school_name || ''} onChange={e => onChange({ school_name: e.target.value })} />
          </div>
        </div>
      )}

      {isWorking && (
        <div className="space-y-4 p-4 bg-green-50 rounded-xl">
          <p className="font-medium text-green-800 text-sm">💼 Thông tin công việc</p>
          <div>
            <Label>Ngành nghề</Label>
            <Input placeholder="VD: Công nghệ, Y tế, Giáo dục, Marketing..."
              value={data.industry || ''} onChange={e => onChange({ industry: e.target.value })} />
          </div>
          <div>
            <Label>Chức vụ / Vị trí</Label>
            <Input placeholder="VD: Developer, Marketing Manager, Giáo viên..."
              value={data.job_title || ''} onChange={e => onChange({ job_title: e.target.value })} />
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## `frontend/components/onboarding/steps/Step3Goals.tsx`

```tsx
'use client'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

const GOALS = [
  { value: 'exam_prep', label: '📝 Ôn thi' },
  { value: 'skill_upgrade', label: '🚀 Nâng cao kỹ năng' },
  { value: 'general_knowledge', label: '🌍 Mở rộng kiến thức' },
  { value: 'research', label: '🔬 Nghiên cứu' },
  { value: 'career_change', label: '🔄 Chuyển ngành' },
  { value: 'hobby', label: '🎯 Sở thích cá nhân' },
]

const TOPICS = [
  { value: 'technology', label: '💻 Công nghệ' },
  { value: 'science', label: '🔭 Khoa học' },
  { value: 'history', label: '📜 Lịch sử' },
  { value: 'business', label: '📊 Kinh doanh' },
  { value: 'language', label: '🗣️ Ngôn ngữ' },
  { value: 'health', label: '❤️ Sức khỏe' },
  { value: 'finance', label: '💰 Tài chính' },
  { value: 'arts', label: '🎨 Nghệ thuật' },
]

interface Props { data: any; onChange: (d: any) => void }

export function Step3Goals({ data, onChange }: Props) {
  const toggleArray = (key: string, value: string) => {
    const arr: string[] = data[key] || []
    const updated = arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value]
    onChange({ [key]: updated })
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-800">Mục tiêu & Sở thích 🎯</h2>
        <p className="text-gray-500 text-sm mt-1">Chọn nhiều nếu muốn</p>
      </div>

      <div>
        <Label className="text-base font-medium">Mục tiêu học tập</Label>
        <div className="grid grid-cols-2 gap-2 mt-3">
          {GOALS.map(({ value, label }) => {
            const selected = (data.learning_goals || []).includes(value)
            return (
              <button key={value} onClick={() => toggleArray('learning_goals', value)}
                className={`p-3 rounded-lg border-2 text-sm text-left transition-all
                  ${selected ? 'border-indigo-500 bg-indigo-50 font-medium' : 'border-gray-100 hover:border-gray-300'}`}>
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <Label className="text-base font-medium">Chủ đề quan tâm</Label>
        <div className="grid grid-cols-2 gap-2 mt-3">
          {TOPICS.map(({ value, label }) => {
            const selected = (data.topics_of_interest || []).includes(value)
            return (
              <button key={value} onClick={() => toggleArray('topics_of_interest', value)}
                className={`p-3 rounded-lg border-2 text-sm text-left transition-all
                  ${selected ? 'border-purple-500 bg-purple-50 font-medium' : 'border-gray-100 hover:border-gray-300'}`}>
                {label}
              </button>
            )
          })}
        </div>
      </div>

      <div>
        <Label className="text-base font-medium">
          Thời gian học mỗi ngày: <span className="text-indigo-600">{data.daily_study_minutes} phút</span>
        </Label>
        <Slider
          value={[data.daily_study_minutes || 30]}
          onValueChange={([v]) => onChange({ daily_study_minutes: v })}
          min={10} max={120} step={10}
          className="mt-4"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>10 phút</span><span>120 phút</span>
        </div>
      </div>
    </div>
  )
}
```

---

## `frontend/components/onboarding/steps/Step4Confirm.tsx`

```tsx
'use client'
import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'

interface Props {
  data: any
  aiResult: any
  loading: boolean
  onSubmit: () => void
}

export function Step4Confirm({ data, aiResult, loading }: Props) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="text-4xl"
        >
          🤖
        </motion.div>
        <p className="text-gray-600 font-medium">AI đang phân tích hồ sơ của bạn...</p>
        <p className="text-gray-400 text-sm">Chỉ mất vài giây</p>
      </div>
    )
  }

  if (aiResult) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center py-6 space-y-4 text-center">
        <div className="text-5xl">🎉</div>
        <h3 className="text-xl font-bold text-gray-800">Chào mừng bạn đến với DUO MIND!</h3>
        <div className="bg-indigo-50 rounded-xl p-4 w-full text-left">
          <p className="text-sm text-indigo-600 font-medium mb-1">AI xác định bạn là:</p>
          <Badge className="bg-indigo-600 mb-2">{aiResult.ai_persona}</Badge>
          <p className="text-gray-700 text-sm">{aiResult.ai_persona_description}</p>
        </div>
        {aiResult.ai_recommended_topics?.length > 0 && (
          <div className="w-full">
            <p className="text-sm text-gray-500 mb-2">Chủ đề được gợi ý cho bạn:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {aiResult.ai_recommended_topics.map((t: string) => (
                <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
              ))}
            </div>
          </div>
        )}
        <p className="text-gray-400 text-sm">Đang chuyển đến bảng điều khiển...</p>
      </motion.div>
    )
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">Xác nhận thông tin ✅</h2>
      <div className="bg-gray-50 rounded-xl p-4 space-y-2 text-sm">
        <p><span className="text-gray-500">Độ tuổi:</span> <span className="font-medium">{data.age_range}</span></p>
        <p><span className="text-gray-500">Trạng thái:</span> <span className="font-medium">{data.status}</span></p>
        {data.major && <p><span className="text-gray-500">Chuyên ngành:</span> <span className="font-medium">{data.major}</span></p>}
        {data.industry && <p><span className="text-gray-500">Ngành:</span> <span className="font-medium">{data.industry}</span></p>}
        <p><span className="text-gray-500">Mục tiêu:</span> <span className="font-medium">{(data.learning_goals || []).join(', ')}</span></p>
      </div>
      <p className="text-gray-500 text-sm">Nhấn "Hoàn thành" để AI phân tích và cá nhân hóa trải nghiệm của bạn.</p>
    </div>
  )
}
```

---

## ✅ Checklist Bước 07

- [ ] `/onboarding` page render wizard
- [ ] Step 1: chọn tuổi và trạng thái
- [ ] Step 2: form học/làm hiển thị đúng theo Step 1
- [ ] Step 3: multi-select goals + topics + slider
- [ ] Step 4: confirm → submit → loading → AI result → redirect dashboard
- [ ] Data flow: state tích lũy qua các step, gửi 1 lần ở cuối
- [ ] Sau submit: `is_onboarded = true` trong DB

---

## ➡️ Bước Tiếp theo
Đọc `08-analyze-feature.md` để build tính năng ANALYZE.

---

## 🤖 Codex Prompt

```
Tạo tất cả components onboarding trong frontend/ theo code trong 07-onboarding-flow.md:
1. app/(app)/onboarding/page.tsx
2. components/onboarding/OnboardingWizard.tsx
3. components/onboarding/StepIndicator.tsx
4. components/onboarding/steps/Step1Basic.tsx
5. components/onboarding/steps/Step2Details.tsx
6. components/onboarding/steps/Step3Goals.tsx
7. components/onboarding/steps/Step4Confirm.tsx

Test: đăng nhập tài khoản mới → tự redirect /onboarding → hoàn thành wizard → AI trả về persona → redirect /dashboard
```
