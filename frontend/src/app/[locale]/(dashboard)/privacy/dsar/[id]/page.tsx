"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
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
  const t = useTranslations("privacy");
  const [dsar, setDsar] = useState<PrivacyDsar | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const d = await privacyApi.getDsar(id);
      setDsar(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
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
        {t("dsar.detail.backToList")}
      </Link>

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : error || !dsar ? (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error || t("dsar.detail.notFound")}
        </p>
      ) : (
        <>
          <div className="mb-6">
            <div className="mb-2">
              <DsarStatusBadge value={dsar.status} />
            </div>
            <h1 className="flex items-center gap-2 text-2xl font-bold">
              <MailQuestion className="text-brand h-6 w-6" />
              {(dsar.request_types || []).join(" / ") || t("dsar.title")}
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              {t("dsar.detail.subject")} {dsar.data_subject_ref || "—"} · {t("dsar.received")} {dsar.date_received || "—"}
              {dsar.response_deadline ? ` · ${t("dsar.deadline")} ${dsar.response_deadline}` : ""}
              {dsar.verification_method ? ` · ${t("dsar.detail.verified")} ${dsar.verification_method}` : ""}
            </p>
          </div>

          {status === "idle" ? (
            <div className="mb-6 flex items-center gap-3">
              <Button onClick={handleDraft}>
                <MailQuestion className="mr-1.5 h-4 w-4" />
                {dsar.ack_letter ? t("dsar.detail.redraftLetters") : t("dsar.detail.draftLetters")}
              </Button>
              <span className="text-muted-foreground text-xs">
                {t("dsar.detail.aiDisclaimer")}
              </span>
            </div>
          ) : (
            <div className="mb-6 flex items-center justify-between">
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
                {status === "connecting" && t("dsar.detail.connecting")}
                {status === "running" && t("dsar.detail.drafting")}
                {status === "done" && t("dsar.detail.draftDone")}
                {status === "error" && (
                  <span className="text-destructive flex items-center gap-1.5">
                    <AlertCircle className="h-4 w-4" />
                    {t("dsar.detail.draftFailed")}
                  </span>
                )}
              </div>
              {!isBusy && (
                <Button variant="ghost" size="sm" onClick={reset}>
                  {t("dsar.detail.collapse")}
                </Button>
              )}
            </div>
          )}

          {runError && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
              {runError}
            </p>
          )}

          {isBusy && streamingText && (
            <Card className="mb-6">
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}

          {dsar.ack_letter && (
            <section className="mb-6">
              <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
                {t("dsar.detail.ackLetter")}
              </h2>
              <Card>
                <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                  <MarkdownContent content={dsar.ack_letter} />
                </CardContent>
              </Card>
            </section>
          )}
          {dsar.response_letter && (
            <section className="mb-6">
              <h2 className="mb-2 text-sm font-semibold tracking-wide uppercase">
                {t("dsar.detail.responseLetter")}
              </h2>
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
                {t("dsar.detail.exemptions")}
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
