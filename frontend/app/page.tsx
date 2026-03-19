import { HomeLanding } from "@/components/landing/HomeLanding"
import { createClient } from "@/lib/supabase/server"

export default async function HomePage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    return (
      <HomeLanding
        navHref="/login"
        navLabel="Đăng nhập"
        primaryHref="/signup"
        primaryLabel="Bắt đầu ngay"
        statusLabel="Phân tích, khám phá và học tập cùng AI trong một hệ duy nhất"
      />
    )
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("is_onboarded")
    .eq("id", user.id)
    .maybeSingle()

  const isOnboarded = Boolean(profile?.is_onboarded)

  return (
    <HomeLanding
      navHref={isOnboarded ? "/mentor" : "/onboarding"}
      navLabel={isOnboarded ? "Mentor AI" : "Tiếp tục"}
      primaryHref={isOnboarded ? "/dashboard" : "/onboarding"}
      primaryLabel={isOnboarded ? "Mở dashboard" : "Hoàn tất onboarding"}
      statusLabel={
        isOnboarded
          ? "Trở lại DUO MIND để tiếp tục học, khám phá và theo dõi tiến bộ"
          : "Hoàn tất onboarding để DUO MIND cá nhân hóa lộ trình học cho bạn"
      }
    />
  )
}
