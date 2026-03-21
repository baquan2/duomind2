import { NextResponse } from "next/server"

import { createClient } from "@/lib/supabase/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const dynamic = "force-dynamic"

export async function GET() {
  try {
    const supabase = createClient()
    const {
      data: { session },
    } = await supabase.auth.getSession()

    if (!session?.access_token) {
      return NextResponse.json(null, { status: 200 })
    }

    const response = await fetch(`${BACKEND_URL}/api/onboarding/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
      cache: "no-store",
    })

    const text = await response.text()
    let data: unknown = null

    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = null
    }

    return NextResponse.json(data, { status: response.status })
  } catch {
    return NextResponse.json(null, { status: 200 })
  }
}
