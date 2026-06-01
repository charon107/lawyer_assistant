"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  AlertCircle,
  Sparkles,
  UserCheck,
  Loader2,
} from "lucide-react";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent, ToolCallCard } from "@/components/chat";
import { DeviationCard, ReviewBadges } from "@/components/commercial";
import { useCommercialChat } from "@/hooks/use-commercial-chat";
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

/** Which downstream action (if any) the user has launched on this review. */
type DownstreamAction = "summarize" | "escalate";

export default function CommercialReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [review, setReview] = useState<ContractReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Downstream actions (summarize / escalate) stream over the same WS the
  // live review uses. We track which one is in flight so we can re-fetch
  // the persisted row once the agent writes its result back.
  const {
    streamingText,
    finalOutput,
    toolCalls,
    status: wsStatus,
    error: wsError,
    summarizeReview,
    escalateReview,
  } = useCommercialChat();
  const [activeAction, setActiveAction] = useState<DownstreamAction | null>(null);
  const refetchedForRef = useRef<DownstreamAction | null>(null);

  const fetchReview = useCallback(() => {
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

  useEffect(() => {
    const cleanup = fetchReview();
    return cleanup;
  }, [fetchReview]);

  // When a downstream action finishes, pull the persisted row so the new
  // stakeholder_summary / required_approver render. Guard with a ref so we
  // only re-fetch once per completed action.
  useEffect(() => {
    if (wsStatus !== "done" || !activeAction) return;
    if (refetchedForRef.current === activeAction) return;
    refetchedForRef.current = activeAction;
    fetchReview();
  }, [wsStatus, activeAction, fetchReview]);

  const handleSummarize = () => {
    if (!id) return;
    refetchedForRef.current = null;
    setActiveAction("summarize");
    summarizeReview(id);
  };

  const handleEscalate = () => {
    if (!id) return;
    refetchedForRef.current = null;
    setActiveAction("escalate");
    escalateReview(id);
  };

  const structured = review?.result_json ?? null;
  const pill = STATUS_PILL[review?.result_status ?? "in_progress"];
  const wsBusy = wsStatus === "connecting" || wsStatus === "running";
  // Downstream actions only make sense once the original review has finished.
  const reviewDone = !!review && review.result_status !== "in_progress";

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
          {/* Downstream actions — only after the original review finished. */}
          {reviewDone && (
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSummarize}
                disabled={wsBusy}
              >
                {wsBusy && activeAction === "summarize" ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-1.5 h-4 w-4" />
                )}
                生成业务摘要
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleEscalate}
                disabled={wsBusy}
              >
                {wsBusy && activeAction === "escalate" ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <UserCheck className="mr-1.5 h-4 w-4" />
                )}
                确定审批人
              </Button>
              {wsBusy && (
                <span className="text-muted-foreground text-sm">
                  {activeAction === "summarize"
                    ? "正在生成业务摘要……"
                    : "正在判定审批人……"}
                </span>
              )}
            </div>
          )}

          {wsError && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {wsError}
            </p>
          )}

          {/* Live tool calls during a downstream action */}
          {activeAction && toolCalls.length > 0 && (
            <div className="flex flex-col gap-2">
              {toolCalls.map((tc) => (
                <ToolCallCard key={tc.id} toolCall={tc} defaultCollapsed />
              ))}
            </div>
          )}

          {/* Live streamed narrative during a downstream action */}
          {activeAction && (finalOutput || streamingText) && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}

          {/* Persisted stakeholder summary */}
          {review.stakeholder_summary && (
            <Card>
              <CardContent className="p-6">
                <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold tracking-wide uppercase">
                  <Sparkles className="text-brand h-4 w-4" />
                  业务摘要
                </h2>
                <div className="prose-sm max-w-none text-sm leading-relaxed">
                  <MarkdownContent content={review.stakeholder_summary} />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Persisted required approver */}
          {review.required_approver && (
            <div className="border-brand/30 bg-brand/5 flex items-center gap-2 rounded-lg border px-4 py-3 text-sm">
              <UserCheck className="text-brand h-4 w-4 shrink-0" />
              <span>
                建议审批人：
                <span className="font-medium">{review.required_approver}</span>
                {review.escalation_sent && (
                  <span className="text-muted-foreground ml-2">· 已上报</span>
                )}
              </span>
            </div>
          )}

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
            </div>
          )}
        </div>
      )}
    </div>
  );
}
