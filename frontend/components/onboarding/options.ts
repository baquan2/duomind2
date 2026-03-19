export const AGE_RANGES = [
  { value: "under_18", label: "Dưới 18 tuổi" },
  { value: "18_24", label: "18 - 24 tuổi" },
  { value: "25_34", label: "25 - 34 tuổi" },
  { value: "35_44", label: "35 - 44 tuổi" },
  { value: "45_plus", label: "45 tuổi trở lên" },
] as const

export const STATUS_OPTIONS = [
  {
    value: "student",
    label: "Đang đi học",
    desc: "Học sinh, sinh viên, học viên",
  },
  {
    value: "working",
    label: "Đang đi làm",
    desc: "Nhân viên, tự kinh doanh",
  },
  {
    value: "both",
    label: "Vừa học vừa làm",
    desc: "Học và làm song song",
  },
  {
    value: "other",
    label: "Khác",
    desc: "Freelance, nghỉ ngơi, tìm việc",
  },
] as const

export const EDUCATION_OPTIONS = [
  { value: "high_school", label: "THPT / Trung học" },
  { value: "college", label: "Cao đẳng" },
  { value: "university", label: "Đại học" },
  { value: "postgrad", label: "Sau đại học" },
  { value: "other", label: "Khác" },
] as const

export const GOAL_OPTIONS = [
  { value: "exam_prep", label: "Ôn thi" },
  { value: "skill_upgrade", label: "Nâng cao kỹ năng" },
  { value: "general_knowledge", label: "Mở rộng kiến thức" },
  { value: "research", label: "Nghiên cứu" },
  { value: "career_change", label: "Chuyển ngành" },
  { value: "hobby", label: "Sở thích cá nhân" },
] as const

export const TOPIC_OPTIONS = [
  { value: "technology", label: "Công nghệ" },
  { value: "science", label: "Khoa học" },
  { value: "history", label: "Lịch sử" },
  { value: "business", label: "Kinh doanh" },
  { value: "language", label: "Ngôn ngữ" },
  { value: "health", label: "Sức khỏe" },
  { value: "finance", label: "Tài chính" },
  { value: "arts", label: "Nghệ thuật" },
] as const

type Option = {
  value: string
  label: string
}

export function getOptionLabel(value: string | undefined, options: readonly Option[]) {
  return options.find((option) => option.value === value)?.label || value || "-"
}

export function getOptionLabels(
  values: string[] | undefined,
  options: readonly Option[]
) {
  if (!values?.length) {
    return "-"
  }

  return values.map((value) => getOptionLabel(value, options)).join(", ")
}
