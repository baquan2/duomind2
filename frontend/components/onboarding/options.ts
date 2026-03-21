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
    desc: "Học sinh, sinh viên hoặc học viên đang theo chương trình học.",
  },
  {
    value: "working",
    label: "Đang đi làm",
    desc: "Nhân viên, chuyên viên, freelancer hoặc người đang làm việc toàn thời gian.",
  },
  {
    value: "both",
    label: "Vừa học vừa làm",
    desc: "Đang học và đi làm song song, quỹ thời gian cần được tối ưu.",
  },
  {
    value: "other",
    label: "Khác",
    desc: "Đang tìm việc, chuyển hướng hoặc ở trạng thái linh hoạt.",
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
  { value: "hobby", label: "Học vì sở thích" },
] as const

export const TARGET_ROLE_OPTIONS = [
  {
    value: "Frontend Developer",
    label: "Lập trình viên Frontend",
    desc: "Xây dựng giao diện web và sản phẩm hướng người dùng.",
  },
  {
    value: "Backend Developer",
    label: "Lập trình viên Backend",
    desc: "Thiết kế API, dữ liệu và logic phía máy chủ.",
  },
  {
    value: "Full-stack Developer",
    label: "Lập trình viên Full-stack",
    desc: "Có thể làm cả frontend lẫn backend ở mức thực chiến.",
  },
  {
    value: "Data Analyst",
    label: "Chuyên viên phân tích dữ liệu",
    desc: "Phân tích dữ liệu, làm dashboard và rút insight kinh doanh.",
  },
  {
    value: "Business Analyst",
    label: "Chuyên viên phân tích nghiệp vụ",
    desc: "Làm rõ bài toán, quy trình và kết nối nghiệp vụ với sản phẩm.",
  },
  {
    value: "Digital Marketing Specialist",
    label: "Chuyên viên Digital Marketing",
    desc: "Phụ trách nội dung, kênh số, hiệu quả chiến dịch và tăng trưởng.",
  },
  {
    value: "Performance Marketing Specialist",
    label: "Chuyên viên Performance Marketing",
    desc: "Tối ưu quảng cáo, phễu chuyển đổi và hiệu quả ngân sách.",
  },
  {
    value: "Product Manager",
    label: "Quản lý sản phẩm",
    desc: "Định hướng sản phẩm, lộ trình phát triển và giá trị người dùng.",
  },
  {
    value: "UI/UX Designer",
    label: "Nhà thiết kế UI/UX",
    desc: "Thiết kế trải nghiệm, giao diện và hệ thống thiết kế.",
  },
  {
    value: "QA Engineer",
    label: "Kỹ sư kiểm thử",
    desc: "Kiểm thử sản phẩm, tìm lỗi và đảm bảo chất lượng phát hành.",
  },
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

export function getOptionLabels(values: string[] | undefined, options: readonly Option[]) {
  if (!values?.length) {
    return "-"
  }

  return values.map((value) => getOptionLabel(value, options)).join(", ")
}
