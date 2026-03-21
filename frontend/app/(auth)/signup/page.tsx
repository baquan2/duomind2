import { CheckCircle2, UserPlus } from "lucide-react"
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

type SignupPageProps = {
  searchParams?: {
    error?: string | string[]
    notice?: string | string[]
  }
}

function getSingleValue(value?: string | string[]) {
  return Array.isArray(value) ? value[0] : value
}

function mapSignupError(message: string) {
  const normalized = message.toLowerCase()

  if (normalized.includes("user already registered")) {
    return "Email này đã được đăng ký."
  }

  if (normalized.includes("password should be at least")) {
    return "Mật khẩu quá ngắn. Hãy đặt mật khẩu mạnh hơn."
  }

  if (normalized.includes("invalid email")) {
    return "Email không hợp lệ."
  }

  return "Không thể tạo tài khoản lúc này. Hãy thử lại."
}

export default function SignupPage({ searchParams }: SignupPageProps) {
  const error = getSingleValue(searchParams?.error)
  const notice = getSingleValue(searchParams?.notice)

  async function signupAction(formData: FormData) {
    "use server"

    const fullName = String(formData.get("fullName") || "").trim()
    const email = String(formData.get("email") || "").trim()
    const password = String(formData.get("password") || "")
    const confirmPassword = String(formData.get("confirmPassword") || "")

    if (!email || !password || !confirmPassword) {
      redirect(`/signup?error=${encodeURIComponent("Vui lòng nhập đầy đủ thông tin bắt buộc.")}`)
    }

    if (password !== confirmPassword) {
      redirect(`/signup?error=${encodeURIComponent("Mật khẩu xác nhận chưa khớp.")}`)
    }

    const supabase = createClient()
    const { data, error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        },
      },
    })

    if (signUpError) {
      redirect(`/signup?error=${encodeURIComponent(mapSignupError(signUpError.message))}`)
    }

    if (data.session) {
      redirect("/onboarding")
    }

    redirect(
      `/signup?notice=${encodeURIComponent("Tài khoản đã được tạo. Hãy kiểm tra email để xác nhận đăng ký.")}`
    )
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
      <Card className="w-full max-w-lg border border-border/70 bg-card/92 backdrop-blur">
        <CardHeader className="space-y-3">
          <div className="inline-flex w-fit items-center gap-2 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
            <UserPlus className="size-3.5" />
            Tạo tài khoản
          </div>
          <div>
            <CardTitle className="text-3xl font-semibold">Tạo tài khoản</CardTitle>
            <CardDescription className="mt-2 text-base">
              Sau khi đăng ký, người dùng mới sẽ được đưa vào flow onboarding ở bước tiếp theo.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" action={signupAction}>
            <div className="space-y-2">
              <Label htmlFor="full-name">Họ và tên</Label>
              <Input
                id="full-name"
                name="fullName"
                type="text"
                placeholder="Nguyễn Văn A"
                autoComplete="name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-email">Email</Label>
              <Input
                id="signup-email"
                name="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password">Mật khẩu</Label>
              <Input
                id="signup-password"
                name="password"
                type="password"
                placeholder="Tạo mật khẩu"
                autoComplete="new-password"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Xác nhận mật khẩu</Label>
              <Input
                id="confirm-password"
                name="confirmPassword"
                type="password"
                placeholder="Nhập lại mật khẩu"
                autoComplete="new-password"
                required
              />
            </div>

            {error ? (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            {notice ? (
              <Alert>
                <CheckCircle2 className="size-4" />
                <AlertDescription>{notice}</AlertDescription>
              </Alert>
            ) : null}

            <Button className="w-full" type="submit">
              Tạo tài khoản
            </Button>
          </form>

          <p className="mt-5 text-sm text-muted-foreground">
            Đã có tài khoản?{" "}
            <Link className="font-medium text-primary hover:underline" href="/login">
              Đăng nhập
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  )
}
