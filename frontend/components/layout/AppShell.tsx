"use client"

import { useEffect, useState, type ReactNode } from "react"

import { Sidebar } from "@/components/layout/Sidebar"
import { cn } from "@/lib/utils"

const SIDEBAR_STORAGE_KEY = "duomind_sidebar_collapsed"

interface AppShellProps {
  displayName?: string | null
  email?: string | null
  isOnboarded?: boolean
  children: ReactNode
}

export function AppShell({
  displayName,
  email,
  isOnboarded = false,
  children,
}: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const storedValue = window.localStorage.getItem(SIDEBAR_STORAGE_KEY)
    setCollapsed(storedValue === "true")
  }, [])

  const handleToggleSidebar = () => {
    setCollapsed((previous) => {
      const nextValue = !previous
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(nextValue))
      return nextValue
    })
  }

  return (
    <div className="min-h-screen">
      <div
        className={cn(
          "z-30 transition-[width] duration-300 ease-out md:fixed md:inset-y-0 md:left-0",
          collapsed ? "md:w-[84px]" : "md:w-[248px]"
        )}
      >
        <Sidebar
          displayName={displayName}
          email={email}
          isOnboarded={isOnboarded}
          collapsed={collapsed}
          onToggle={handleToggleSidebar}
        />
      </div>

      <main
        className={cn(
          "min-h-screen min-w-0",
          collapsed ? "md:ml-[84px]" : "md:ml-[248px]"
        )}
      >
        <div
          className={cn(
            "mx-auto flex min-h-screen w-full flex-col gap-6 px-4 py-5 transition-[max-width,padding] duration-300 md:px-8 md:py-8",
            collapsed ? "max-w-[98rem]" : "max-w-[92rem]"
          )}
        >
          {children}
        </div>
      </main>
    </div>
  )
}
