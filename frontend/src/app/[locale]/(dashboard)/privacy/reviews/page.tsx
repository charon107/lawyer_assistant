"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Spinner } from "@/components/ui";
import { ReviewTypeBadge, SeverityBadge, TriageClassificationBadge } from "@/components/privacy";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";
import { cn } from "@/lib/utils";
import type { PrivacyReview, ReviewType } from "@/types/privacy";

const TABS: { value: ReviewType | "all"; label: string }[] = [
  { value: "all", label: "全部" },
  { value: "triage", label: "分诊" },
  { value: "pia", label: "PIA" },
  { value: "dpa", label: "DPA" },
  { value: "gap", label: "差距分析" },
  { value: "policy_sweep", label: "政策扫描" },
];

export default function PrivacyReviewsPage() {
  const [tab, setTab] = useState<ReviewType | "all">("all");
  const [items, setItems] = useState<PrivacyReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const res = await privacyApi.listReviews(0, 100, tab === "all" ? undefined : tab);
        if (!cancelled) setItems(res.items);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tab]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.PRIVACY}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回个人信息保护
      </Link>
      <h1 className="mb-6 text-2xl font-bold">分析产出</h1>

      <div className="mb-5 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setTab(t.value)}
            className={cn(
              "rounded-md border px-3 py-1.5 text-sm transition-colors",
              tab === t.value
                ? "border-brand bg-brand/10 text-brand font-medium"
                : "text-muted-foreground hover:bg-muted",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          还没有分析产出。从概览页运行分诊 / PIA / DPA 等技能后会出现在这里。
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((r) => (
            <li key={r.id}>
              <Link
                href={`${ROUTES.PRIVACY_REVIEWS}/${r.id}`}
                className="hover:border-brand/40 flex items-start gap-3 rounded-xl border p-4 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <ReviewTypeBadge value={r.review_type} />
                    <TriageClassificationBadge value={r.classification} />
                    <SeverityBadge value={r.severity} />
                  </div>
                  <p className="truncate text-sm font-medium">{r.subject || "（未命名）"}</p>
                  <p className="text-muted-foreground line-clamp-2 text-xs">
                    {r.result_summary || "进行中"}
                  </p>
                </div>
                <time className="text-muted-foreground shrink-0 text-xs">
                  {new Date(r.created_at).toLocaleDateString("zh-CN")}
                </time>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
