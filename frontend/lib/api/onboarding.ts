import apiClient from "@/lib/api/client"
import type { OnboardingData, OnboardingResponse } from "@/types"

export async function submitOnboarding(data: OnboardingData) {
  const response = await apiClient.post<OnboardingResponse>("/api/onboarding/submit", data)
  return response.data
}
