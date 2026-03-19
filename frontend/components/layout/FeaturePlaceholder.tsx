import Link from "next/link"
import { ArrowRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface FeaturePlaceholderProps {
  title: string
  description: string
  stepLabel: string
  ctaHref?: string
  ctaLabel?: string
}

export function FeaturePlaceholder({
  title,
  description,
  stepLabel,
  ctaHref = "/dashboard",
  ctaLabel = "Về dashboard",
}: FeaturePlaceholderProps) {
  return (
    <div className="animate-fade-up space-y-6">
      <Badge className="border-0 bg-secondary text-secondary-foreground">
        {stepLabel}
      </Badge>
      <Card className="max-w-3xl border border-border/70 bg-card/90 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-3xl font-semibold">{title}</CardTitle>
          <CardDescription className="max-w-2xl text-base">
            {description}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href={ctaHref}>
              {ctaLabel}
              <ArrowRight className="ml-2 size-4" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
