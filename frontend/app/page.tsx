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
        statusLabel="Chốt mục tiêu nghề nghiệp, nhìn ra khoảng trống kỹ năng và học theo lộ trình rõ ràng"
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
          ? "Quay lại DUO MIND để tiếp tục roadmap, mentor và tiến trình học tập"
          : "Hoàn tất onboarding để DUO MIND cá nhân hóa roadmap và mentor cho bạn"
      }
    />
  )
}
