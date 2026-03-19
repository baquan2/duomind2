import { redirect } from "next/navigation"

import { ProfileEditor } from "@/components/profile/ProfileEditor"
import { createClient } from "@/lib/supabase/server"

export default async function ProfilePage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const [profileResponse, onboardingResponse] = await Promise.all([
    supabase.from("profiles").select("*").eq("id", user.id).maybeSingle(),
    supabase.from("user_onboarding").select("*").eq("user_id", user.id).maybeSingle(),
  ])

  return (
    <ProfileEditor
      userId={user.id}
      email={profileResponse.data?.email ?? user.email}
      createdAt={profileResponse.data?.created_at ?? null}
      initialFullName={profileResponse.data?.full_name ?? user.user_metadata?.full_name ?? null}
      initialOnboarding={onboardingResponse.data}
    />
  )
}
