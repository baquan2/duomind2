import axios from "axios"
import type { OnboardingData, OnboardingResponse } from "@/types"

export async function submitOnboarding(data: OnboardingData) {
  const response = await axios.post<OnboardingResponse>("/api/onboarding/submit", data)
  return response.data
}

export async function getMyOnboarding() {
  const response = await axios.get<Partial<OnboardingData> | null>("/api/onboarding/me")
  return response.data
}
