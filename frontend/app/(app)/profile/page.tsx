import { redirect } from "next/navigation"

import { ProfileEditor } from "@/components/profile/ProfileEditor"
import { mergeOnboardingWithMemories } from "@/lib/onboarding-context"
import { createClient } from "@/lib/supabase/server"

export default async function ProfilePage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const [profileResponse, onboardingResponse, mentorMemoryResponse] = await Promise.all([
    supabase.from("profiles").select("*").eq("id", user.id).maybeSingle(),
    supabase.from("user_onboarding").select("*").eq("user_id", user.id).maybeSingle(),
    supabase
      .from("mentor_memory")
      .select("id,memory_type,memory_key,memory_value,confidence,updated_at")
      .eq("user_id", user.id)
      .order("updated_at", { ascending: false })
      .limit(8),
  ])
  const mergedOnboarding = mergeOnboardingWithMemories(
    onboardingResponse.data,
    mentorMemoryResponse.data ?? []
  )

  return (
    <ProfileEditor
      userId={user.id}
      email={profileResponse.data?.email ?? user.email}
      createdAt={profileResponse.data?.created_at ?? null}
      initialFullName={profileResponse.data?.full_name ?? user.user_metadata?.full_name ?? null}
      initialOnboarding={mergedOnboarding}
      mentorMemories={mentorMemoryResponse.data ?? []}
    />
  )
}
