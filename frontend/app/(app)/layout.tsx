import { redirect } from "next/navigation"
import type { ReactNode } from "react"

import { Sidebar } from "@/components/layout/Sidebar"
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
    <div className="min-h-screen md:grid md:grid-cols-[280px_1fr]">
      <Sidebar
        displayName={profile?.full_name || user.user_metadata.full_name || null}
        email={user.email}
        isOnboarded={Boolean(profile?.is_onboarded)}
      />
      <main className="min-h-screen">
        <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-4 py-5 md:px-8 md:py-8">
          {children}
        </div>
      </main>
    </div>
  )
}
