"use client"

import { BrainCircuit, Sparkles } from "lucide-react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import type { FormEvent } from "react"
import { Suspense, useState } from "react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { createClient } from "@/lib/supabase/client"

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = createClient()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const redirectTo = searchParams.get("redirect") || "/dashboard"

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError("")

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (signInError) {
      setError(signInError.message)
      setLoading(false)
      return
    }

    router.push(redirectTo)
    router.refresh()
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
      <section className="hidden overflow-hidden bg-[radial-gradient(circle_at_top_left,_rgba(255,209,102,0.55),_transparent_32%),linear-gradient(160deg,_hsl(var(--sidebar-background)),_hsl(171_38%_13%))] p-10 text-sidebar-foreground lg:flex lg:flex-col lg:justify-between">
        <div className="space-y-5">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-white/15 bg-white/8 px-3 py-1 text-sm text-white/88 backdrop-blur">
            <BrainCircuit className="size-4" />
            DUO MIND
          </div>
          <div className="max-w-xl space-y-4">
            <h1 className="font-display text-5xl font-semibold leading-tight">
              Phân tích kiến thức và học sâu hơn với AI đồng hành.
            </h1>
            <p className="text-lg text-white/76">
              Đăng nhập để mở onboarding, khám phá, phân tích và quiz trong cùng một
              hành trình học tập.
            </p>
          </div>
        </div>

        <div className="grid max-w-xl gap-4">
          <div className="rounded-2xl border border-white/10 bg-white/8 p-5 backdrop-blur">
            <div className="flex items-center gap-2 text-sm font-medium text-white/90">
              <Sparkles className="size-4" />
              Sẵn sàng với DUO MIND
            </div>
            <p className="mt-2 text-sm leading-6 text-white/70">
              Sau đăng nhập, người dùng mới sẽ vào onboarding wizard. Người dùng cũ có
              thể tiếp tục dashboard, lịch sử và các phiên học đang mở.
            </p>
          </div>
        </div>
      </section>

      <section className="flex items-center justify-center px-5 py-10 sm:px-8">
        <Card className="w-full max-w-md border border-border/70 bg-card/92 backdrop-blur">
          <CardHeader className="space-y-3">
            <div className="inline-flex w-fit items-center gap-2 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
              <Sparkles className="size-3.5" />
              Cấu hình đăng nhập
            </div>
            <div>
              <CardTitle className="text-3xl font-semibold">Đăng nhập</CardTitle>
              <CardDescription className="mt-2 text-base">
                Truy cập dashboard DUO MIND bằng Supabase Auth.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Mật khẩu</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Nhập mật khẩu"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>

              {error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : null}

              <Button className="w-full" type="submit" disabled={loading}>
                {loading ? "Đang đăng nhập..." : "Đăng nhập"}
              </Button>
            </form>

            <p className="mt-5 text-sm text-muted-foreground">
              Chưa có tài khoản?{" "}
              <Link className="font-medium text-primary hover:underline" href="/signup">
                Đăng ký
              </Link>
            </p>
          </CardContent>
        </Card>
      </section>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <LoginForm />
    </Suspense>
  )
}
