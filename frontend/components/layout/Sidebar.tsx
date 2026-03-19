"use client"

import {
  BookCopy,
  Compass,
  History,
  LayoutDashboard,
  LogOut,
  UserRound,
} from "lucide-react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { createClient } from "@/lib/supabase/client"
import { cn } from "@/lib/utils"

const navItems = [
  {
    href: "/dashboard",
    label: "Tổng quan",
    icon: LayoutDashboard,
  },
  {
    href: "/explore",
    label: "Khám phá",
    icon: Compass,
  },
  {
    href: "/analyze",
    label: "Phân tích",
    icon: BookCopy,
  },
  {
    href: "/history",
    label: "Lịch sử",
    icon: History,
  },
  {
    href: "/profile",
    label: "Hồ sơ",
    icon: UserRound,
  },
]

interface SidebarProps {
  displayName?: string | null
  email?: string | null
  isOnboarded?: boolean
}

export function Sidebar({
  displayName,
  email,
  isOnboarded = false,
}: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const [isSigningOut, setIsSigningOut] = useState(false)

  const handleSignOut = async () => {
    setIsSigningOut(true)
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/login")
    router.refresh()
    setIsSigningOut(false)
  }

  return (
    <aside className="sticky top-0 z-20 flex flex-col gap-5 border-b border-sidebar-border bg-sidebar px-4 py-5 text-sidebar-foreground md:h-screen md:border-b-0 md:border-r md:px-5">
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-sidebar-foreground/60">
              Duo Mind
            </div>
            <div className="font-display text-2xl font-semibold leading-none">
              Học rõ từng bước
            </div>
          </div>
          <Badge className="border-0 bg-sidebar-primary text-sidebar-primary-foreground">
            MVP
          </Badge>
        </div>
        <p className="text-sm text-sidebar-foreground/72">
          Nền tảng đã sẵn sàng cho onboarding, khám phá, phân tích và lịch sử học tập.
        </p>
      </div>

      <div className="rounded-xl border border-sidebar-border bg-sidebar-accent/50 p-3">
        <div className="font-medium">
          {displayName || email?.split("@")[0] || "Người dùng DUO MIND"}
        </div>
        <div className="text-sm text-sidebar-foreground/70">{email || "Chưa có email"}</div>
        <div className="mt-3">
          <Badge
            className={cn(
              "border-0",
              isOnboarded
                ? "bg-emerald-400/20 text-emerald-100"
                : "bg-amber-300/20 text-amber-100"
            )}
          >
            {isOnboarded ? "Đã onboarding" : "Cần onboarding"}
          </Badge>
        </div>
      </div>

      <nav className="grid gap-2 md:flex-1">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`)
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "text-sidebar-foreground/78 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className="size-4" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="space-y-3">
        <Separator className="bg-sidebar-border" />
        <Button
          variant="secondary"
          className="w-full justify-start bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/80"
          disabled={isSigningOut}
          onClick={handleSignOut}
        >
          <LogOut className="mr-2 size-4" />
          {isSigningOut ? "Đang đăng xuất..." : "Đăng xuất"}
        </Button>
      </div>
    </aside>
  )
}
