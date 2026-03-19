import {
  Document,
  HeadingLevel,
  Packer,
  Paragraph,
  TextRun,
} from "docx"

import type { SessionDetailResponse } from "@/types"

function slugify(text: string) {
  return (
    text
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60) || "duo-mind-session"
  )
}

function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = fileName
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

function createBullet(text: string, level = 0) {
  return new Paragraph({
    text,
    bullet: { level },
    spacing: { after: 140 },
  })
}

function createHeading(
  text: string,
  level: (typeof HeadingLevel)[keyof typeof HeadingLevel]
) {
  return new Paragraph({
    text,
    heading: level,
    spacing: { before: 220, after: 120 },
  })
}

export async function exportSessionAsWord(data: SessionDetailResponse) {
  const { session, quiz_questions } = data
  const children: Paragraph[] = [
    new Paragraph({
      text: session.title,
      heading: HeadingLevel.TITLE,
      spacing: { after: 200 },
    }),
    createBullet(
      `Loại phiên: ${session.session_type === "analyze" ? "Phân tích" : "Khám phá"}`
    ),
    createBullet(`Thời gian: ${new Date(session.created_at).toLocaleString("vi-VN")}`),
    createBullet(
      `Chủ đề: ${(session.topic_tags || []).join(", ") || "Không có"}`
    ),
  ]

  if (session.summary) {
    children.push(createHeading("Tóm tắt", HeadingLevel.HEADING_1))
    children.push(
      ...session.summary
        .split(/\n+/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => createBullet(line))
    )
  }

  if (session.key_points?.length) {
    children.push(createHeading("Điểm chính", HeadingLevel.HEADING_1))
    children.push(...session.key_points.map((point) => createBullet(point)))
  }

  if (session.corrections?.length) {
    children.push(createHeading("Đính chính", HeadingLevel.HEADING_1))
    session.corrections.forEach((item) => {
      children.push(
        createBullet(`Nội dung gốc: ${item.original}`),
        createBullet(`Gợi ý sửa: ${item.correction}`),
        createBullet(`Giải thích: ${item.explanation}`, 1)
      )
    })
  }

  if (session.infographic_data?.sections?.length) {
    children.push(createHeading("Infographic", HeadingLevel.HEADING_1))
    session.infographic_data.sections.forEach((section) => {
      children.push(createBullet(`${section.heading}: ${section.content}`))
    })
  }

  if (quiz_questions.length) {
    children.push(createHeading("Quiz", HeadingLevel.HEADING_1))
    quiz_questions.forEach((question, index) => {
      children.push(createBullet(`${index + 1}. ${question.question_text}`))
      question.options?.forEach((option) => {
        children.push(createBullet(`${option.id}. ${option.text}`, 1))
      })
      if (question.explanation) {
        children.push(createBullet(`Giải thích: ${question.explanation}`, 1))
      }
    })
  }

  const document = new Document({
    sections: [
      {
        properties: {},
        children,
      },
    ],
  })

  const blob = await Packer.toBlob(document)
  const fileName = `${slugify(session.title)}.docx`
  downloadBlob(blob, fileName)
}

export function exportSessionAsMarkdown(data: SessionDetailResponse) {
  const { session, quiz_questions } = data
  const lines: string[] = [
    `# ${session.title}`,
    "",
    `- Loại phiên: ${session.session_type === "analyze" ? "Phân tích" : "Khám phá"}`,
    `- Thời gian: ${new Date(session.created_at).toLocaleString("vi-VN")}`,
    `- Chủ đề: ${(session.topic_tags || []).join(", ") || "Không có"}`,
    "",
  ]

  if (session.summary) {
    lines.push("## Tóm tắt", "")
    session.summary
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean)
      .forEach((line) => lines.push(`- ${line}`))
    lines.push("")
  }

  if (session.key_points?.length) {
    lines.push("## Điểm chính", "")
    session.key_points.forEach((point, index) => {
      lines.push(`${index + 1}. ${point}`)
    })
    lines.push("")
  }

  if (session.corrections?.length) {
    lines.push("## Đính chính", "")
    session.corrections.forEach((item, index) => {
      lines.push(`${index + 1}. Sai: ${item.original}`)
      lines.push(`   - Đúng: ${item.correction}`)
      lines.push(`   - Giải thích: ${item.explanation}`)
    })
    lines.push("")
  }

  if (session.infographic_data?.sections?.length) {
    lines.push("## Infographic", "")
    session.infographic_data.sections.forEach((section, index) => {
      lines.push(`${index + 1}. ${section.heading}: ${section.content}`)
    })
    lines.push("")
  }

  if (quiz_questions.length) {
    lines.push("## Quiz", "")
    quiz_questions.forEach((question, index) => {
      lines.push(`${index + 1}. ${question.question_text}`)
      if (question.options?.length) {
        question.options.forEach((option) => {
          lines.push(`   - ${option.id}. ${option.text}`)
        })
      }
      if (question.explanation) {
        lines.push(`   - Giải thích: ${question.explanation}`)
      }
    })
    lines.push("")
  }

  const fileName = `${slugify(session.title)}.md`
  const blob = new Blob([lines.join("\n")], {
    type: "text/markdown;charset=utf-8",
  })
  downloadBlob(blob, fileName)
}
