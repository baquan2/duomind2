import type { AnalyzeVerdict } from "@/types"

export function deriveAnalyzeVerdict(
  assessment?: string | null,
  correctionsCount = 0,
  sourcesCount = 0
): AnalyzeVerdict {
  if (sourcesCount > 0 && assessment === "high" && correctionsCount === 0) {
    return "correct"
  }

  return "incorrect"
}

export function normalizeAnalyzeVerdict(
  verdict?: string | null,
  assessment?: string | null,
  correctionsCount = 0,
  sourcesCount = 0
): AnalyzeVerdict {
  if (verdict === "correct" || verdict === "incorrect" || verdict === "deep_dive") {
    return verdict
  }

  return deriveAnalyzeVerdict(assessment, correctionsCount, sourcesCount)
}

export function getAnalyzeVerdictMeta(verdict: AnalyzeVerdict) {
  if (verdict === "correct") {
    return {
      label: "Thong tin dung",
      shortLabel: "Dung",
      description: "Noi dung hien tai bam dung kien thuc cot loi va co nguon doi chieu ho tro.",
    }
  }

  if (verdict === "deep_dive") {
    return {
      label: "Dao sau",
      shortLabel: "Dao sau",
      description: "Phien nay uu tien giai thich he thong va co che, khong dung nhu mot lan cham bai dung/sai.",
    }
  }

  return {
    label: "Thong tin sai",
    shortLabel: "Sai",
    description:
      "Noi dung con diem sai, thieu, hoac chua du can cu xac minh nen khong nen xem la dung.",
  }
}
