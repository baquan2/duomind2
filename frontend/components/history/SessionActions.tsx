"use client"

import { Eye, FileText, Loader2, ScrollText, Trash2 } from "lucide-react"
import Link from "next/link"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { deleteSession, getSessionDetail } from "@/lib/api/history"
import { exportSessionAsMarkdown, exportSessionAsWord } from "@/lib/session-export"

interface SessionActionsProps {
  sessionId: string
  sessionTitle: string
  showViewButton?: boolean
  onDeleteSuccess?: () => void
  compact?: boolean
}

export function SessionActions({
  sessionId,
  sessionTitle,
  showViewButton = true,
  onDeleteSuccess,
  compact = false,
}: SessionActionsProps) {
  const [isExporting, setIsExporting] = useState<"md" | "word" | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [open, setOpen] = useState(false)

  const handleExport = async (format: "md" | "word") => {
    setIsExporting(format)
    try {
      const data = await getSessionDetail(sessionId)
      if (format === "md") {
        exportSessionAsMarkdown(data)
      } else {
        await exportSessionAsWord(data)
      }
    } finally {
      setIsExporting(null)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await deleteSession(sessionId)
      setOpen(false)
      onDeleteSuccess?.()
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <>
      <div className="flex flex-wrap gap-2">
        {showViewButton ? (
          <Button asChild variant="outline" size={compact ? "sm" : "default"}>
            <Link href={`/history/${sessionId}`}>
              <Eye className="mr-1.5 size-4" />
              Xem
            </Link>
          </Button>
        ) : null}

        <Button
          type="button"
          variant="outline"
          size={compact ? "sm" : "default"}
          onClick={() => void handleExport("md")}
          disabled={Boolean(isExporting)}
        >
          {isExporting === "md" ? (
            <Loader2 className="mr-1.5 size-4 animate-spin" />
          ) : (
            <ScrollText className="mr-1.5 size-4" />
          )}
          Tải MD
        </Button>

        <Button
          type="button"
          variant="outline"
          size={compact ? "sm" : "default"}
          onClick={() => void handleExport("word")}
          disabled={Boolean(isExporting)}
        >
          {isExporting === "word" ? (
            <Loader2 className="mr-1.5 size-4 animate-spin" />
          ) : (
            <FileText className="mr-1.5 size-4" />
          )}
          Tải Word
        </Button>

        <Button
          type="button"
          variant="destructive"
          size={compact ? "sm" : "default"}
          onClick={() => setOpen(true)}
        >
          <Trash2 className="mr-1.5 size-4" />
          Xóa
        </Button>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Xóa phiên học?</DialogTitle>
            <DialogDescription>
              Phiên{" "}
              <span className="font-medium text-foreground">{sessionTitle}</span>{" "}
              sẽ bị xóa cùng quiz và dữ liệu liên quan.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Hủy
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? (
                <>
                  <Loader2 className="mr-1.5 size-4 animate-spin" />
                  Đang xóa
                </>
              ) : (
                <>
                  <Trash2 className="mr-1.5 size-4" />
                  Xóa phiên
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
