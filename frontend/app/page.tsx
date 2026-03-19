import { redirect } from "next/navigation"

import { createClient } from "@/lib/supabase/server"

export default async function HomePage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("is_onboarded")
    .eq("id", user.id)
    .maybeSingle()

  if (!profile?.is_onboarded) {
    redirect("/onboarding")
  }

  redirect("/dashboard")
}
