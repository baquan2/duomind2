"use client"

import {
  BookCopy,
  Compass,
  History,
  LayoutDashboard,
  LogOut,
  MessagesSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Route,
  UserRound,
} from "lucide-react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useState } from "react"

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
    href: "/mentor",
    label: "Mentor AI",
    icon: MessagesSquare,
  },
  {
    href: "/roadmap",
    label: "Lộ trình",
    icon: Route,
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
] as const

interface SidebarProps {
  displayName?: string | null
  email?: string | null
  isOnboarded?: boolean
  collapsed?: boolean
  onToggle?: () => void
}

export function Sidebar({
  displayName,
  email,
  isOnboarded = false,
  collapsed = false,
  onToggle,
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
    <aside
      className={cn(
        "top-0 z-20 flex h-full min-h-screen w-full flex-col border-b border-sidebar-border bg-sidebar px-3 py-4 text-sidebar-foreground transition-all duration-300 md:h-screen md:overflow-y-auto md:border-b-0 md:border-r",
        collapsed ? "gap-3 md:px-3" : "gap-4 md:px-4"
      )}
    >
      <div className={cn("flex items-center justify-between gap-2", collapsed && "flex-col items-center")}>
        <div className={cn("min-w-0", collapsed && "text-center")}>
          <div className="whitespace-nowrap bg-gradient-to-r from-violet-400 to-pink-500 bg-clip-text text-base font-extrabold tracking-wide text-transparent">
            {collapsed ? "DM" : "DUO MIND"}
          </div>
        </div>

        <div className={cn("flex items-center gap-1.5", collapsed && "w-full justify-center")}>
          <Button
            type="button"
            size="icon-sm"
            variant="secondary"
            className="size-9 rounded-full bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/85"
            onClick={onToggle}
          >
            {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
          </Button>
        </div>
      </div>

      <nav className="flex flex-col items-start gap-1.5 md:flex-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "inline-flex items-center rounded-full text-sm font-medium transition-colors",
                collapsed ? "mx-auto size-10 justify-center self-center" : "self-start gap-2.5 px-3 py-2",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "text-sidebar-foreground/78 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className="size-4 shrink-0" />
              {!collapsed ? <span>{item.label}</span> : null}
            </Link>
          )
        })}
      </nav>

      <div className="space-y-2.5">
        <Separator className="bg-sidebar-border" />
        <Button
          variant="secondary"
          className={cn(
            "h-9 bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/80",
            collapsed ? "w-full justify-center px-0" : "w-full justify-start"
          )}
          disabled={isSigningOut}
          onClick={handleSignOut}
        >
          <LogOut className={cn("size-4", collapsed ? "" : "mr-2")} />
          {!collapsed ? (isSigningOut ? "Đang đăng xuất..." : "Đăng xuất") : null}
        </Button>
      </div>
    </aside>
  )
}
