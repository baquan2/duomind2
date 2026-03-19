"use client"

import { FileUp, Type, Upload, Wand2, X } from "lucide-react"
import { useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface ContentInputProps {
  onSubmitText: (content: string) => void | Promise<void>
  onSubmitFile: (file: File) => void | Promise<void>
  loading: boolean
}

type InputMode = "text" | "file"

const MAX_CONTENT_LENGTH = 8000
const ACCEPTED_FILE_TYPES = ".txt,.md,.docx"

export function ContentInput({
  onSubmitText,
  onSubmitFile,
  loading,
}: ContentInputProps) {
  const [mode, setMode] = useState<InputMode>("text")
  const [content, setContent] = useState("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleSubmit = () => {
    if (mode === "text") {
      const nextValue = content.trim()
      if (!nextValue) {
        return
      }

      void onSubmitText(nextValue)
      return
    }

    if (!selectedFile) {
      return
    }

    void onSubmitFile(selectedFile)
  }

  const canSubmit = mode === "text" ? Boolean(content.trim()) : Boolean(selectedFile)

  return (
    <Card className="border border-border/70 bg-card/92">
      <CardHeader className="space-y-4">
        <div className="space-y-2">
          <CardTitle className="flex items-center gap-2 text-xl">
            {mode === "text" ? (
              <Type className="size-5 text-primary" />
            ) : (
              <FileUp className="size-5 text-primary" />
            )}
            Gửi nội dung cần phân tích
          </CardTitle>
          <CardDescription>
            Bạn có thể dán trực tiếp nội dung hoặc tải file văn bản để hệ thống
            chấm độ chính xác, tóm tắt, đính chính và tạo mind map.
          </CardDescription>
        </div>

        <div className="flex flex-wrap gap-2 rounded-2xl border border-border/70 bg-background/80 p-2">
          <button
            type="button"
            onClick={() => setMode("text")}
            className={cn(
              "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all",
              mode === "text"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-foreground/70 hover:bg-muted hover:text-foreground"
            )}
          >
            <Type className="size-4" />
            Nhập nội dung
          </button>

          <button
            type="button"
            onClick={() => setMode("file")}
            className={cn(
              "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all",
              mode === "file"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-foreground/70 hover:bg-muted hover:text-foreground"
            )}
          >
            <FileUp className="size-4" />
            Tải file
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {mode === "text" ? (
          <>
            <Textarea
              placeholder="Dán ghi chú, bài viết, bài học, transcript hoặc phần giải thích bạn muốn AI đối chiếu..."
              value={content}
              maxLength={MAX_CONTENT_LENGTH}
              onChange={(event) => setContent(event.target.value)}
              className="min-h-[240px] resize-none bg-background text-base"
              onKeyDown={(event) => {
                if (event.key === "Enter" && event.ctrlKey) {
                  event.preventDefault()
                  handleSubmit()
                }
              }}
            />

            <div className="flex flex-col gap-3 rounded-2xl border border-border/70 bg-muted/30 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">
                  Chế độ nhập tay
                </p>
                <p className="text-sm text-muted-foreground">
                  {content.length}/{MAX_CONTENT_LENGTH} ký tự. Nhấn{" "}
                  <span className="font-medium text-foreground">Ctrl + Enter</span>{" "}
                  để gửi nhanh.
                </p>
              </div>

              <Button
                onClick={handleSubmit}
                disabled={!canSubmit || loading}
                className="sm:min-w-40"
              >
                {loading ? "Đang phân tích..." : "Phân tích nội dung"}
                <Wand2 className="ml-2 size-4" />
              </Button>
            </div>
          </>
        ) : (
          <>
            <div className="rounded-3xl border border-dashed border-primary/35 bg-[linear-gradient(135deg,_rgba(15,118,110,0.06),_rgba(255,247,221,0.45))] p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <p className="text-base font-semibold text-foreground">
                    Tải file văn bản để phân tích
                  </p>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Hỗ trợ <span className="font-medium text-foreground">TXT</span>,{" "}
                    <span className="font-medium text-foreground">MD</span> và{" "}
                    <span className="font-medium text-foreground">DOCX</span>. Không
                    hỗ trợ PDF theo cấu hình hiện tại. Giới hạn tối đa 5MB.
                  </p>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="mr-2 size-4" />
                  Chọn file
                </Button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_FILE_TYPES}
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0] ?? null
                  setSelectedFile(file)
                }}
              />
            </div>

            {selectedFile ? (
              <div className="rounded-2xl border border-border/70 bg-background p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-foreground">
                      File đã chọn
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                  </div>

                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null)
                      if (fileInputRef.current) {
                        fileInputRef.current.value = ""
                      }
                    }}
                  >
                    <X className="mr-1.5 size-4" />
                    Bỏ file
                  </Button>
                </div>
              </div>
            ) : null}

            <div className="flex flex-col gap-3 rounded-2xl border border-border/70 bg-muted/30 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">
                  Chế độ tải file
                </p>
                <p className="text-sm text-muted-foreground">
                  Hệ thống sẽ trích nội dung văn bản, phân tích logic chính và lưu
                  tên file vào lịch sử để bạn xem lại sau.
                </p>
              </div>

              <Button
                onClick={handleSubmit}
                disabled={!canSubmit || loading}
                className="sm:min-w-40"
              >
                {loading ? "Đang phân tích..." : "Phân tích file"}
                <Wand2 className="ml-2 size-4" />
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
