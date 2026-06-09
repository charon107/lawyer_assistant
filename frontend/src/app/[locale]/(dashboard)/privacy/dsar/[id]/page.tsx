"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, ArrowLeft, Loader2, MailQuestion } from "lucide-react";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { DsarStatusBadge } from "@/components/privacy";
import { usePrivacyChat } from "@/hooks/use-privacy-chat";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";
import type { PrivacyDsar } from "@/types/privacy";

export default function PrivacyDsarDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [dsar, setDsar] = useState<PrivacyDsar | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const d = await privacyApi.getDsar(id);
      setDsar(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [id]);

  const { streamingText, finalOutput, status, error: runError, runSkill, reset } =
    usePrivacyChat(() => {
      void reload();
    });

  useEffect(() => {
    void reload();
  }, [reload]);

  const isBusy = status === "connecting" || status === "running";

  const handleDraft = () => {
    runSkill({
      action: "dsar",
      dsar_id: id,
      prompt:
        "请按工作流处理本权利请求：分类、按风险校准验证身份、遍历系统清单定位、豁免分析（每项标注需律师审核），并起草确认函与实质回复函。两份对外函件不带工作成果抬头。",
    });
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.PRIVACY_DSAR}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回请求列表
      </Link>

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : error || !dsar ? (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error || "未找到该请求"}
        </p>
      ) : (
        <>
          <div className="mb-6">
            <div className="mb-2">
              <DsarStatusBadge value={dsar.status} />
            </div>
            <h1 className="flex items-center gap-2 text-2xl font-bold">
              <MailQuestion className="text-brand h-6 w-6" />
              {(dsar.request_types || []).join(" / ") || "权利请求"}
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              主体 {dsar.data_subject_ref || "—"} · 收到 {dsar.date_received || "—"}
              {dsar.response_deadline ? ` · 截止 ${dsar.response_deadline}` : ""}
              {dsar.verification_method ? ` · 验证 ${dsar.verification_method}` : ""}
            </p>
          </div>

          {/* Draft action */}
          {status === "idle" ? (
            <div className="mb-6 flex items-center gap-3">
              <Button onClick={handleDraft}>
                <MailQuestion className="mr-1.5 h-4 w-4" />
                {dsar.ack_letter ? "重新起草两函" : "起草确认函与实质回复函"}
              </Button>
              <span className="text-muted-foreground text-xs">
                AI 起草，发送前须由律师审核。
              </span>
            </div>
          ) : (
            <div className="mb-6 flex items-center justify-between">
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
                {status === "connecting" && "正在连接……"}
                {status === "running" && "AI 正在起草……"}
                {status === "done" && "起草完成"}
                {status === "error" && (
                  <span className="text-destructive flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4" />
                    起草失败
                  </span>
                )}
              </div>
              {!isBusy && (
                <Button variant="ghost" size="sm" onClick={reset}>
                  收起
                </Button>
              )}
            </div>
          )}

          {runError && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
              {runError}
            </p>
          )}

          {/* Live stream while running */}
          {isBusy && streamingText && (
            <Card className="mb-6">
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}

          {/* Persisted letters */}
          {dsar.ack_letter && (
            <section className="mb-6">
              <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">确认函</h2>
              <Card>
                <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                  <MarkdownContent content={dsar.ack_letter} />
                </CardContent>
              </Card>
            </section>
          )}
          {dsar.response_letter && (
            <section className="mb-6">
              <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">实质回复函</h2>
              <Card>
                <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                  <MarkdownContent content={dsar.response_letter} />
                </CardContent>
              </Card>
            </section>
          )}

          {dsar.exemptions && dsar.exemptions.length > 0 && (
            <section>
              <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
                豁免分析（需律师审核）
              </h2>
              <Card>
                <CardContent className="p-6 text-sm">
                  <pre className="text-muted-foreground whitespace-pre-wrap break-words">
                    {JSON.stringify(dsar.exemptions, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            </section>
          )}
        </>
      )}
    </div>
  );
}
