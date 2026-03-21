import { BrainCircuit, Sparkles } from "lucide-react"
import Link from "next/link"
import { redirect } from "next/navigation"

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
import { createClient } from "@/lib/supabase/server"

type LoginPageProps = {
  searchParams?: {
    error?: string | string[]
    redirect?: string | string[]
  }
}

function getSingleValue(value?: string | string[]) {
  return Array.isArray(value) ? value[0] : value
}

function sanitizeRedirect(value?: string) {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard"
  }

  return value
}

function mapAuthError(message: string) {
  const normalized = message.toLowerCase()

  if (normalized.includes("invalid login credentials")) {
    return "Email hoặc mật khẩu chưa đúng."
  }

  if (normalized.includes("email not confirmed")) {
    return "Tài khoản chưa xác nhận email. Hãy kiểm tra hộp thư và xác nhận trước khi đăng nhập."
  }

  if (normalized.includes("network")) {
    return "Không thể kết nối đến hệ thống xác thực. Hãy thử lại sau."
  }

  return "Không thể đăng nhập lúc này. Hãy thử lại."
}

export default function LoginPage({ searchParams }: LoginPageProps) {
  const error = getSingleValue(searchParams?.error)
  const redirectTo = sanitizeRedirect(getSingleValue(searchParams?.redirect))

  async function loginAction(formData: FormData) {
    "use server"

    const email = String(formData.get("email") || "").trim()
    const password = String(formData.get("password") || "")
    const requestedRedirect = sanitizeRedirect(String(formData.get("redirectTo") || ""))

    if (!email || !password) {
      redirect(
        `/login?error=${encodeURIComponent("Vui lòng nhập đầy đủ email và mật khẩu.")}&redirect=${encodeURIComponent(requestedRedirect)}`
      )
    }

    const supabase = createClient()
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (signInError) {
      redirect(
        `/login?error=${encodeURIComponent(mapAuthError(signInError.message))}&redirect=${encodeURIComponent(requestedRedirect)}`
      )
    }

    redirect(requestedRedirect)
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
              Đăng nhập để tiếp tục lộ trình, mentor và tiến trình học tập của bạn.
            </h1>
            <p className="text-lg text-white/76">
              DUO MIND được thiết kế như một AI cố vấn và bộ lập kế hoạch học tập. Sau khi đăng nhập,
              hệ thống sẽ đưa bạn đến đúng bước tiếp theo trong hành trình học tập.
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
              Nếu đây là lần đầu đăng nhập, bạn sẽ được đưa vào onboarding để khai báo vai trò mục tiêu,
              mục tiêu và bối cảnh học tập. Nếu đã có hồ sơ, bạn sẽ vào dashboard và lộ trình ngay.
            </p>
          </div>
        </div>
      </section>

      <section className="flex items-center justify-center px-5 py-10 sm:px-8">
        <Card className="w-full max-w-md border border-border/70 bg-card/92 backdrop-blur">
          <CardHeader className="space-y-3">
            <div className="inline-flex w-fit items-center gap-2 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
              <Sparkles className="size-3.5" />
              Đăng nhập
            </div>
            <div>
              <CardTitle className="text-3xl font-semibold">Chào mừng quay lại</CardTitle>
              <CardDescription className="mt-2 text-base">
                Đăng nhập bằng tài khoản Supabase để mở dashboard DUO MIND.
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" action={loginAction}>
              <input type="hidden" name="redirectTo" value={redirectTo} />

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Mật khẩu</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Nhập mật khẩu"
                  autoComplete="current-password"
                  required
                />
              </div>

              {error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : null}

              <Button className="w-full" type="submit">
                Đăng nhập
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
