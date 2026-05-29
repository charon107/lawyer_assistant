"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, FileSearch, Loader2, AlertCircle } from "lucide-react";
import {
  Button,
  Input,
  Label,
  Card,
  CardContent,
  Spinner,
} from "@/components/ui";
import { ToolCallCard, MarkdownContent } from "@/components/chat";
import {
  ContractUploader,
  DeviationCard,
  ReviewBadges,
} from "@/components/commercial";
import { useCommercialChat } from "@/hooks/use-commercial-chat";
import { commercialApi } from "@/lib/commercial";
import { ROUTES } from "@/lib/constants";
import type { ContractReviewResult, Side } from "@/types/commercial";

/**
 * Vendor-agreement review page.
 *
 * The review itself streams over the commercial WebSocket (text deltas
 * + tool calls). Once it finishes we pull the persisted row by id to get
 * the *structured* result (`result_json`) and render deviation cards —
 * the stream only carries the markdown narrative.
 */
export default function CommercialReviewPage() {
  const {
    reviewId,
    streamingText,
    finalOutput,
    toolCalls,
    status,
    error,
    startReview,
    reset,
  } = useCommercialChat();

  const [counterparty, setCounterparty] = useState("");
  const [agreementName, setAgreementName] = useState("");
  const [contractText, setContractText] = useState("");
  const [side, setSide] = useState<Side>("purchasing");
  const [structured, setStructured] = useState<ContractReviewResult | null>(null);
  const [loadingStructured, setLoadingStructured] = useState(false);

  // Default the side from the user's saved profile.
  useEffect(() => {
    let cancelled = false;
    commercialApi
      .getStatus()
      .then((s) => {
        if (!cancelled && s.side && s.side !== "both") setSide(s.side);
      })
      .catch(() => {
        /* fall back to purchasing */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // When the stream completes, fetch the structured result for cards.
  useEffect(() => {
    if (status !== "done" || !reviewId) return;
    let cancelled = false;
    setLoadingStructured(true);
    commercialApi
      .getReview(reviewId)
      .then((r) => {
        if (!cancelled) setStructured(r.result_json ?? null);
      })
      .catch(() => {
        /* the markdown narrative is still shown regardless */
      })
      .finally(() => {
        if (!cancelled) setLoadingStructured(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, reviewId]);

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (!contractText.trim()) return;
    setStructured(null);
    startReview({
      review_type: "vendor",
      side,
      counterparty: counterparty.trim() || undefined,
      agreement_name: agreementName.trim() || undefined,
      contract_text: contractText,
    });
  };

  const handleReset = () => {
    reset();
    setStructured(null);
    setContractText("");
    setCounterparty("");
    setAgreementName("");
  };

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
          <FileSearch className="text-brand h-6 w-6" />
          审查新合同
        </h1>
        <p className="text-muted-foreground">
          上传或粘贴供应商协议，AI 会逐条对照你的合同手册产出偏差报告。
        </p>
      </div>

      {/* Input form — hidden once a review is in flight or finished. */}
      {status === "idle" ? (
        <div className="flex flex-col gap-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="counterparty">对方主体（可选）</Label>
              <Input
                id="counterparty"
                value={counterparty}
                onChange={(e) => setCounterparty(e.target.value)}
                placeholder="例如：某某科技有限公司"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="agreement-name">协议名称（可选）</Label>
              <Input
                id="agreement-name"
                value={agreementName}
                onChange={(e) => setAgreementName(e.target.value)}
                placeholder="例如：云服务采购协议"
              />
            </div>
          </div>

          <ContractUploader value={contractText} onTextChange={setContractText} />

          <div className="flex justify-end">
            <Button onClick={handleStart} disabled={!contractText.trim()}>
              <FileSearch className="mr-1.5 h-4 w-4" />
              开始审查
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {/* Status banner */}
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
              {status === "connecting" && "正在连接……"}
              {status === "running" && "AI 正在审查合同……"}
              {status === "done" && "审查完成"}
              {status === "error" && (
                <span className="text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  审查失败
                </span>
              )}
            </div>
            {!isBusy && (
              <Button variant="ghost" size="sm" onClick={handleReset}>
                审查另一份
              </Button>
            )}
          </div>

          {error && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {error}
            </p>
          )}

          {/* Tool calls */}
          {toolCalls.length > 0 && (
            <div className="flex flex-col gap-2">
              {toolCalls.map((tc) => (
                <ToolCallCard key={tc.id} toolCall={tc} defaultCollapsed />
              ))}
            </div>
          )}

          {/* Streamed narrative */}
          {(finalOutput || streamingText) && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}

          {/* Structured deviations */}
          {loadingStructured && (
            <div className="flex items-center justify-center py-6">
              <Spinner className="text-brand h-5 w-5" />
            </div>
          )}
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
