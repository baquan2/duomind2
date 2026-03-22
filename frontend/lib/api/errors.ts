import axios from "axios"

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    const technicalDetail = error.response?.data?.technical_detail
    const message = error.response?.data?.message
    if (typeof detail === "string" && detail.trim()) {
      return detail
    }
    if (typeof message === "string" && message.trim()) {
      return message
    }
    if (typeof technicalDetail === "string" && technicalDetail.trim()) {
      return `Lỗi kỹ thuật: ${technicalDetail}`
    }
  }

  return fallback
}
