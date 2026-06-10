"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft } from "lucide-react";
import { Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { ClassificationBadge, IpCategoryBadge, ReviewTypeBadge, SeverityBadge } from "@/components/ip";
import { ROUTES } from "@/lib/constants";
import { ipApi } from "@/lib/ip";
import type { IpReview } from "@/types/ip";

export default function IpReviewDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("ip");
  const [review, setReview] = useState<IpReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await ipApi.getReview(id);
        if (!cancelled) setReview(r);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.IP_REVIEWS}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("reviews.detail.backToList")}
      </Link>

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : error || !review ? (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error || t("reviews.detail.notFound")}
        </p>
      ) : (
        <>
          <div className="mb-6">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <ReviewTypeBadge value={review.review_type} />
              <IpCategoryBadge value={review.ip_category} />
              <ClassificationBadge value={review.classification} />
              <SeverityBadge value={review.severity} />
            </div>
            <h1 className="text-2xl font-bold">{review.subject || t("reviews.unnamed")}</h1>
            {review.result_summary && (
              <p className="text-muted-foreground mt-1">{review.result_summary}</p>
            )}
            <time className="text-muted-foreground mt-2 block text-xs">
              {new Date(review.created_at).toLocaleString("zh-CN")}
            </time>
          </div>

          {review.result_memo ? (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={review.result_memo} />
              </CardContent>
            </Card>
          ) : (
            <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
              {t("reviews.detail.noMemo")}
            </p>
          )}
        </>
      )}
    </div>
  );
}
