import { NextResponse } from "next/server"

import { createClient } from "@/lib/supabase/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const dynamic = "force-dynamic"

function buildBackendUnavailableResponse(error: unknown) {
  return NextResponse.json(
    {
      detail:
        "Dịch vụ AI của DUO MIND hiện chưa kết nối được với backend. Hãy kiểm tra backend `localhost:8000` đã chạy chưa rồi thử lại.",
      technical_detail: error instanceof Error ? error.message : "Backend unavailable",
    },
    { status: 503 }
  )
}

export async function POST(request: Request) {
  try {
    const payload = await request.json()
    const supabase = createClient()
    const {
      data: { session },
    } = await supabase.auth.getSession()

    if (!session?.access_token) {
      return NextResponse.json(
        { detail: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại để tiếp tục khám phá." },
        { status: 401 }
      )
    }

    const response = await fetch(`${BACKEND_URL}/api/explore/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    })

    const text = await response.text()
    let data: unknown = null

    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = { detail: text || "Không thể khám phá chủ đề lúc này." }
    }

    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    return buildBackendUnavailableResponse(error)
  }
}
