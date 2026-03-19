import type { Metadata } from "next"
import { Be_Vietnam_Pro, Nunito } from "next/font/google"
import type { ReactNode } from "react"

import { Providers } from "@/components/providers/Providers"

import "./globals.css"

const beVietnamPro = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  variable: "--font-be-vietnam-pro",
  weight: ["400", "500", "600", "700"],
})

const nunito = Nunito({
  subsets: ["latin", "vietnamese"],
  variable: "--font-nunito",
  weight: ["600", "700", "800"],
})

export const metadata: Metadata = {
  title: "DUO MIND - Hệ thống giáo dục thông minh",
  description: "Phân tích, đối chiếu và học tập cùng AI",
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body
        className={`${beVietnamPro.variable} ${nunito.variable} min-h-screen bg-background font-sans text-foreground antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
