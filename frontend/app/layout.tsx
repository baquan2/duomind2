import type { Metadata } from "next"
import { Outfit, Space_Grotesk } from "next/font/google"
import type { ReactNode } from "react"

import { Providers } from "@/components/providers/Providers"

import "./globals.css"

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
})

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
})

export const metadata: Metadata = {
  title: "DUO MIND - Hệ thống giáo dục thông minh",
  description: "Phân tích, đối chiếu và học tập cùng AI",
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body
        className={`${outfit.variable} ${spaceGrotesk.variable} min-h-screen bg-background font-sans text-foreground antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
