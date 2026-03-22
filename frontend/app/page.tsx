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
        primaryLabel="Trải nghiệm hành trình"
        statusLabel="Bản trình bày học thuật chứng minh cách DUO MIND biến dữ liệu người học thành định hướng, kiến thức và hành động tiếp theo"
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
      navLabel={isOnboarded ? "Vào Mentor AI" : "Tiếp tục onboarding"}
      primaryHref={isOnboarded ? "/dashboard" : "/onboarding"}
      primaryLabel={isOnboarded ? "Mở hành trình học" : "Khởi tạo hành trình"}
      statusLabel={
        isOnboarded
          ? "Bạn đang nhìn thấy bản pitch deck của chính hệ thống mà bạn có thể mở ngay để tiếp tục mentor, roadmap và kiểm chứng kiến thức"
          : "Hoàn tất onboarding để DUO MIND đọc đúng bối cảnh, tạo roadmap phù hợp và trình diễn đầy đủ vòng lặp học tập"
      }
    />
  )
}
