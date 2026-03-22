"use client"

import { FileUp, Type, Upload, Wand2, X } from "lucide-react"
import { useEffect, useRef, useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import type { AnalyzeMode } from "@/lib/api/analyze"
import { cn } from "@/lib/utils"

interface ContentInputProps {
  onSubmitText: (content: string, analysisGoal?: string, mode?: AnalyzeMode) => void | Promise<void>
  onSubmitFile: (file: File, analysisGoal?: string, mode?: AnalyzeMode) => void | Promise<void>
  loading: boolean
  initialContent?: string
}

type InputMode = "text" | "file"

const MAX_CONTENT_LENGTH = 8000
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
const ACCEPTED_FILE_TYPES = ".txt,.md,.docx"

export function ContentInput({
  onSubmitText,
  onSubmitFile,
  loading,
  initialContent = "",
}: ContentInputProps) {
  const [mode, setMode] = useState<InputMode>("text")
  const [content, setContent] = useState(initialContent)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [analysisMode, setAnalysisMode] = useState<AnalyzeMode>("auto")
  const [inputError, setInputError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (!initialContent.trim()) {
      return
    }

    setMode("text")
    setSelectedFile(null)
    setInputError(null)
    setContent(initialContent)
  }, [initialContent])

  const handleSubmit = () => {
    if (mode === "text") {
      const nextValue = content.trim()
      if (!nextValue) {
        setInputError("Hãy dán câu hỏi hoặc ghi chú bạn muốn AI kiểm tra.")
        return
      }
      const minLength = analysisMode === "deep_dive" ? 12 : 20
      const minWords = analysisMode === "deep_dive" ? 3 : 4
      if (nextValue.length < minLength || nextValue.split(/\s+/).length < minWords) {
        setInputError("Nội dung còn quá ngắn. Hãy ghi ít nhất 1 câu hỏi hoặc 2-3 dòng ghi chú cụ thể.")
        return
      }

      setInputError(null)
      void onSubmitText(nextValue, undefined, analysisMode)
      return
    }

    if (!selectedFile) {
      setInputError("Hãy chọn một file văn bản trước khi phân tích.")
      return
    }
    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setInputError("File vượt quá 5MB. Hãy chọn file nhỏ hơn.")
      return
    }

    setInputError(null)
    void onSubmitFile(selectedFile, undefined, analysisMode)
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
            Dán câu hỏi để đào sâu hoặc tải file/ghi chú để phản biện. Analyze hỗ trợ cả hai
            kiểu làm việc trong cùng một giao diện.
          </CardDescription>
        </div>

        <div className="rounded-2xl border border-border/70 bg-background/80 p-2">
          <div className="mb-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Chế độ phân tích
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              { value: "auto", label: "Tự nhận diện" },
              { value: "deep_dive", label: "Đào sâu" },
              { value: "critique", label: "Kiểm tra nội dung" },
            ].map((item) => (
              <button
                key={item.value}
                type="button"
                onClick={() => {
                  setAnalysisMode(item.value as AnalyzeMode)
                  setInputError(null)
                }}
                className={cn(
                  "inline-flex items-center rounded-full px-4 py-2 text-sm font-medium transition-all",
                  analysisMode === item.value
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-foreground/70 hover:bg-muted hover:text-foreground"
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 rounded-2xl border border-border/70 bg-background/80 p-2">
          <button
            type="button"
            onClick={() => {
              setMode("text")
              setInputError(null)
            }}
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
            onClick={() => {
              setMode("file")
              setInputError(null)
            }}
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
              placeholder="Dán câu hỏi, đoạn ghi chú hoặc nội dung cần AI phân tích vào đây."
              value={content}
              maxLength={MAX_CONTENT_LENGTH}
              onChange={(event) => {
                setContent(event.target.value)
                if (inputError) {
                  setInputError(null)
                }
              }}
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
                <p className="text-sm font-medium text-foreground">Chế độ nhập tay</p>
                <p className="text-sm text-muted-foreground">
                  {analysisMode === "deep_dive"
                    ? "Dùng cho câu hỏi hoặc chủ đề cần đào sâu hẹp và chặt."
                    : analysisMode === "critique"
                      ? "Dùng cho ghi chú, câu trả lời hoặc nội dung cần kiểm tra."
                      : "Hệ thống sẽ tự nhận diện giữa đào sâu và kiểm tra nội dung."}{" "}
                  {content.length}/{MAX_CONTENT_LENGTH} ký tự. Nhấn{" "}
                  <span className="font-medium text-foreground">Ctrl + Enter</span> để gửi nhanh.
                </p>
              </div>

              <Button onClick={handleSubmit} disabled={!canSubmit || loading} className="sm:min-w-40">
                {loading
                  ? "Đang phân tích..."
                  : analysisMode === "deep_dive"
                    ? "Đào sâu nội dung"
                    : "Phân tích nội dung"}
                <Wand2 className="ml-2 size-4" />
              </Button>
            </div>

            {inputError ? <p className="text-sm text-destructive">{inputError}</p> : null}
          </>
        ) : (
          <>
            <div className="rounded-3xl border border-dashed border-primary/35 bg-[linear-gradient(135deg,_rgba(15,118,110,0.06),_rgba(255,247,221,0.45))] p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div className="space-y-2">
                  <p className="text-base font-semibold text-foreground">Tải file văn bản để phân tích</p>
                  <p className="text-sm leading-6 text-muted-foreground">
                    Hỗ trợ <span className="font-medium text-foreground">TXT</span>,{" "}
                    <span className="font-medium text-foreground">MD</span> và{" "}
                    <span className="font-medium text-foreground">DOCX</span>. Giới hạn tối đa 5MB.
                  </p>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setInputError(null)
                    fileInputRef.current?.click()
                  }}
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
                  setSelectedFile(event.target.files?.[0] ?? null)
                  setInputError(null)
                }}
              />
            </div>

            {selectedFile ? (
              <div className="rounded-2xl border border-border/70 bg-background p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-foreground">File đã chọn</p>
                    <p className="text-sm text-muted-foreground">{selectedFile.name}</p>
                    <p className="text-xs text-muted-foreground">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                  </div>

                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedFile(null)
                      setInputError(null)
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
                <p className="text-sm font-medium text-foreground">Chế độ tải file</p>
                <p className="text-sm text-muted-foreground">
                  Hệ thống sẽ trích nội dung văn bản rồi tự nhận diện nên đào sâu hay phản biện,
                  trừ khi bạn đã chốt mode ngay từ đầu.
                </p>
              </div>

              <Button onClick={handleSubmit} disabled={!canSubmit || loading} className="sm:min-w-40">
                {loading ? "Đang phân tích..." : "Phân tích file"}
                <Wand2 className="ml-2 size-4" />
              </Button>
            </div>

            {inputError ? <p className="text-sm text-destructive">{inputError}</p> : null}
          </>
        )}
      </CardContent>
    </Card>
  )
}
