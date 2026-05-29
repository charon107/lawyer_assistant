"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, AlertCircle } from "lucide-react";
import { Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { DeviationCard, ReviewBadges } from "@/components/commercial";
import { commercialApi } from "@/lib/commercial";
import { ROUTES } from "@/lib/constants";
import type { ContractReview, ResultStatus } from "@/types/commercial";

/**
 * Read-only detail view for a single past contract review.
 *
 * Linked from the history list on `/commercial`. Re-renders the
 * persisted memo (markdown) + structured deviations using the same
 * components the live review page uses — there's no streaming here,
 * everything comes from the stored row.
 */

const STATUS_PILL: Record<ResultStatus, { label: string; cls: string }> = {
  green: {
    label: "绿色 · 可接受",
    cls: "border-emerald-300 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  },
  yellow: {
    label: "黄色 · 需要关注",
    cls: "border-amber-300 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  },
  red: {
    label: "红色 · 不建议接受",
    cls: "border-red-300 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
  },
  in_progress: {
    label: "审查进行中",
    cls: "border-muted bg-muted text-muted-foreground",
  },
};

export default function CommercialReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [review, setReview] = useState<ContractReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoading(true);
    commercialApi
      .getReview(id)
      .then((r) => {
        if (!cancelled) setReview(r);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  const structured = review?.result_json ?? null;
  const pill = STATUS_PILL[review?.result_status ?? "in_progress"];

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.COMMERCIAL}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回商事合同
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <FileText className="text-brand h-6 w-6" />
          {review?.agreement_name || review?.counterparty || "审查详情"}
        </h1>
        {review && (
          <div className="text-muted-foreground flex items-center gap-3 text-sm">
            <span
              className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${pill.cls}`}
            >
              {pill.label}
            </span>
            <time>{new Date(review.created_at).toLocaleString("zh-CN")}</time>
          </div>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      )}

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive flex items-center gap-1.5 rounded-lg border px-4 py-2.5 text-sm">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      )}

      {!loading && !error && review && (
        <div className="flex flex-col gap-6">
          {/* Memo narrative */}
          {review.result_memo && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={review.result_memo} />
              </CardContent>
            </Card>
          )}

          {/* Structured deviations + badges */}
          {structured && (
            <div className="flex flex-col gap-4">
              <ReviewBadges
                favorable={structured.favorable_terms}
                missing={structured.missing_terms}
              />
              {structured.deviations.length > 0 && (
                <div>
                  <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
                    偏差明细（{structured.deviations.length}）
                  </h2>
                  <div className="flex flex-col gap-3">
                    {structured.deviations.map((d) => (
                      <DeviationCard key={d.clause_key} item={d} />
                    ))}
                  </div>
                </div>
              )}
              {structured.required_approver && (
                <p className="text-muted-foreground text-sm">
                  建议上报：
                  <span className="text-foreground font-medium">
                    {structured.required_approver}
                  </span>
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
