"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertTriangle, ArrowLeft, FileSignature, Loader2, Send } from "lucide-react";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { EnforcementStatusBadge } from "@/components/ip";
import { useIpChat } from "@/hooks/use-ip-chat";
import { ROUTES } from "@/lib/constants";
import { ipApi } from "@/lib/ip";
import type { IpEnforcement } from "@/types/ip";

export default function IpEnforcementDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const t = useTranslations("ip");
  const [matter, setMatter] = useState<IpEnforcement | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);

  const reload = () =>
    ipApi
      .getEnforcement(id)
      .then(setMatter)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));

  const { streamingText, finalOutput, status, error: wsError, runSkill } = useIpChat(reload);

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const isBusy = status === "connecting" || status === "running";

  const handleDraft = () => {
    if (!matter) return;
    runSkill({
      action: matter.matter_type,
      enforcement_id: matter.id,
      prompt: t("enforcement.draftPrompt"),
    });
  };

  const handleMarkSent = async () => {
    setMarking(true);
    try {
      await ipApi.updateEnforcement(id, { status: "sent" });
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update");
    } finally {
      setMarking(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  if (error || !matter) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10">
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error || t("reviews.detail.notFound")}
        </p>
      </div>
    );
  }

  const sendGate = (matter.send_gate ?? {}) as Record<string, unknown>;
  const gateEntries = Object.entries(sendGate);
  const canMarkSent = matter.status !== "sent" && matter.status !== "closed";

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.IP_ENFORCEMENT}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("enforcement.backToList")}
      </Link>

      <div className="mb-6">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="bg-brand/10 text-brand inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium">
            {t(`enforcement.matterType.${matter.matter_type}`)}
          </span>
          <span className="text-muted-foreground text-xs">{t(`enforcement.modes.${matter.mode}`)}</span>
          <EnforcementStatusBadge value={matter.status} />
        </div>
        <h1 className="text-2xl font-bold">
          {matter.counterparty || t("enforcement.noCounterparty")}
        </h1>
        {matter.response_deadline && (
          <p className="text-muted-foreground mt-1 text-sm">
            {t("enforcement.deadline")}: {matter.response_deadline}
          </p>
        )}
      </div>

      {matter.infringement_facts && (
        <Card className="mb-6">
          <CardContent className="p-5">
            <h2 className="mb-1 text-sm font-semibold">{t("enforcement.factsLabel")}</h2>
            <p className="text-muted-foreground text-sm whitespace-pre-wrap">
              {matter.infringement_facts}
            </p>
          </CardContent>
        </Card>
      )}

      <div className="mb-6 flex items-center gap-2">
        <Button onClick={handleDraft} disabled={isBusy}>
          {isBusy ? (
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
          ) : (
            <FileSignature className="mr-1.5 h-4 w-4" />
          )}
          {matter.letter_draft ? t("enforcement.redraft") : t("enforcement.draft")}
        </Button>
        {isBusy && <span className="text-muted-foreground text-sm">{t("skillRunner.analyzing")}</span>}
      </div>

      {wsError && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {wsError}
        </p>
      )}

      {isBusy && (finalOutput || streamingText) && (
        <Card className="mb-6">
          <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
            <MarkdownContent content={finalOutput || streamingText} />
          </CardContent>
        </Card>
      )}

      {matter.letter_draft && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardContent className="p-5">
              <h2 className="mb-2 text-sm font-semibold">{t("enforcement.internalDraft")}</h2>
              <p className="text-muted-foreground mb-3 text-xs">{t("enforcement.internalHint")}</p>
              <div className="prose-sm max-w-none text-sm leading-relaxed">
                <MarkdownContent content={matter.letter_draft} />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-5">
              <h2 className="mb-2 text-sm font-semibold">{t("enforcement.outboundLetter")}</h2>
              <p className="text-muted-foreground mb-3 text-xs">{t("enforcement.outboundHint")}</p>
              {matter.outbound_letter ? (
                <div className="prose-sm max-w-none text-sm leading-relaxed">
                  <MarkdownContent content={matter.outbound_letter} />
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">{t("enforcement.noOutbound")}</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {gateEntries.length > 0 && (
        <Card className="mt-6 border-amber-300 dark:border-amber-900/50">
          <CardContent className="p-5">
            <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              {t("enforcement.sendGateTitle")}
            </h2>
            <ul className="flex flex-col gap-1.5">
              {gateEntries.map(([k, v]) => (
                <li key={k} className="flex items-start gap-2 text-sm">
                  <span className="text-muted-foreground min-w-[8rem] shrink-0">{k}</span>
                  <span>{String(v)}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {matter.letter_draft && canMarkSent && (
        <div className="mt-6 flex flex-col items-start gap-2">
          <p className="text-muted-foreground text-xs">{t("enforcement.markSentHint")}</p>
          <Button variant="outline" onClick={handleMarkSent} disabled={marking}>
            {marking ? (
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
            ) : (
              <Send className="mr-1.5 h-4 w-4" />
            )}
            {t("enforcement.markSent")}
          </Button>
        </div>
      )}
    </div>
  );
}
