import { redirect } from "next/navigation"
import type { ReactNode } from "react"

import { AppShell } from "@/components/layout/AppShell"
import { createClient } from "@/lib/supabase/server"

export default async function AppLayout({ children }: { children: ReactNode }) {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("full_name, is_onboarded")
    .eq("id", user.id)
    .maybeSingle()

  if (!profile?.is_onboarded) {
    return <main className="min-h-screen">{children}</main>
  }

  return (
    <AppShell
      displayName={profile?.full_name || user.user_metadata.full_name || null}
      email={user.email}
      isOnboarded={Boolean(profile?.is_onboarded)}
    >
      {children}
    </AppShell>
  )
}
