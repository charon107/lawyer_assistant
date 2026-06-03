"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, FileText, AlertCircle } from "lucide-react";
import { Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { RiskFlagList } from "@/components/employment";
import { employmentApi } from "@/lib/employment";
import { ROUTES } from "@/lib/constants";
import type { EmploymentReview } from "@/types/employment";

const REVIEW_TYPE_LABEL: Record<string, string> = {
  hiring: "录用审查",
  termination: "解除审查",
  worker_classification: "劳动关系认定",
  policy: "制度审查",
  wage_hour: "工资工时",
  handbook: "员工手册更新",
};

export default function EmploymentReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [review, setReview] = useState<EmploymentReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    employmentApi
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

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.EMPLOYMENT}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回劳动用工
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <FileText className="text-brand h-6 w-6" />
          {review
            ? `${REVIEW_TYPE_LABEL[review.review_type] || review.review_type}${review.employee_name ? ` · ${review.employee_name}` : ""}`
            : "审查详情"}
        </h1>
        {review && (
          <div className="text-muted-foreground flex items-center gap-3 text-sm">
            {review.result_status && (
              <span
                className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                  review.result_status === "green"
                    ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                    : review.result_status === "yellow"
                      ? "border-amber-300 bg-amber-50 text-amber-700"
                      : review.result_status === "red"
                        ? "border-red-300 bg-red-50 text-red-700"
                        : "border-muted bg-muted text-muted-foreground"
                }`}
              >
                {review.result_status === "green"
                  ? "通过"
                  : review.result_status === "yellow"
                    ? "需关注"
                    : review.result_status === "red"
                      ? "高风险"
                      : "进行中"}
              </span>
            )}
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
          {/* High risk flags */}
          {review.high_risk_flags && review.high_risk_flags.length > 0 && (
            <div>
              <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">高风险标记</h2>
              <RiskFlagList flags={review.high_risk_flags} />
            </div>
          )}

          {/* Result summary */}
          {review.result_summary && (
            <Card>
              <CardContent className="p-6">
                <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">审查结论</h2>
                <p className="text-sm leading-relaxed">{review.result_summary}</p>
              </CardContent>
            </Card>
          )}

          {/* Full memo */}
          {review.result_memo && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={review.result_memo} />
              </CardContent>
            </Card>
          )}

          {/* Metadata */}
          <div className="text-muted-foreground flex flex-wrap gap-4 text-xs">
            {review.employee_name && <span>员工：{review.employee_name}</span>}
            {review.position && <span>岗位：{review.position}</span>}
            {review.jurisdiction && <span>管辖地：{review.jurisdiction}</span>}
            {review.required_approver && <span>建议审批人：{review.required_approver}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
