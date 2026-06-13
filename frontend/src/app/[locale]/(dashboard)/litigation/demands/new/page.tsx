"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertCircle, ArrowLeft, FileWarning, Loader2 } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { useLitigationChat } from "@/hooks/use-litigation-chat";
import { litigationApi } from "@/lib/litigation";
import { ROUTES } from "@/lib/constants";
import type { DemandMode, DemandType } from "@/types/litigation";

const DEMAND_TYPES: DemandType[] = [
  "payment",
  "breach_cure",
  "stop_infringement",
  "evidence_preservation",
  "settlement",
  "other",
];

const SELECT_CLS =
  "border-input bg-background ring-offset-background focus-visible:ring-ring h-10 rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none";

export default function LitigationDemandNewPage() {
  const t = useTranslations("litigation");
  const { streamingText, finalOutput, status, error, runSkill } = useLitigationChat();

  const [counterparty, setCounterparty] = useState("");
  const [demandType, setDemandType] = useState<DemandType>("payment");
  const [mode, setMode] = useState<DemandMode>("send");
  const [prompt, setPrompt] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [demandId, setDemandId] = useState<string | null>(null);

  const isBusy = creating || status === "connecting" || status === "running";
  const started = status !== "idle" || creating;

  async function handleCreate() {
    if (!prompt.trim() || isBusy) return;
    setCreating(true);
    setCreateError(null);
    try {
      const demand = await litigationApi.createDemand({
        demand_type: demandType,
        mode,
        counterparty: counterparty.trim() || undefined,
      });
      setDemandId(demand.id);
      runSkill({
        action: mode === "send" ? "demand_draft" : "demand_received",
        prompt,
        demand_id: demand.id,
      });
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : t("demands.create"));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.LITIGATION_DEMANDS}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("demands.backToList")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <FileWarning className="text-brand h-6 w-6" />
          {t("demands.newTitle")}
        </h1>
      </div>

      {!started ? (
        <div className="flex flex-col gap-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="demand-counterparty">{t("demands.counterpartyLabel")}</Label>
              <Input
                id="demand-counterparty"
                value={counterparty}
                onChange={(e) => setCounterparty(e.target.value)}
                placeholder={t("demands.counterpartyPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="demand-type">{t("demands.typeLabel")}</Label>
              <select
                id="demand-type"
                value={demandType}
                onChange={(e) => setDemandType(e.target.value as DemandType)}
                className={SELECT_CLS}
              >
                {DEMAND_TYPES.map((dt) => (
                  <option key={dt} value={dt}>
                    {t(`demands.demandType.${dt}`)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="demand-mode">{t("demands.modeLabel")}</Label>
            <select
              id="demand-mode"
              value={mode}
              onChange={(e) => setMode(e.target.value as DemandMode)}
              className={SELECT_CLS}
            >
              <option value="send">{t("demands.modeSend")}</option>
              <option value="receive">{t("demands.modeReceive")}</option>
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="demand-prompt">{t("demands.promptLabel")}</Label>
            <Textarea
              id="demand-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={7}
              placeholder={t("demands.promptPlaceholder")}
            />
          </div>
          {createError && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {createError}
            </p>
          )}
          <div className="flex justify-end">
            <Button onClick={handleCreate} disabled={!prompt.trim()}>
              <FileWarning className="mr-1.5 h-4 w-4" />
              {t("demands.create")}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
              {creating && t("demands.creating")}
              {status === "connecting" && t("skillRunner.connecting")}
              {status === "running" && t("skillRunner.analyzing")}
              {status === "done" && t("skillRunner.done")}
              {status === "error" && (
                <span className="text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  {t("skillRunner.failed")}
                </span>
              )}
            </div>
            {demandId && status === "done" && (
              <Link href={`${ROUTES.LITIGATION_DEMANDS}/${demandId}`}>
                <Button variant="ghost" size="sm">
                  {t("skillRunner.viewOutput")}
                </Button>
              </Link>
            )}
          </div>

          {(createError || error) && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {createError || error}
            </p>
          )}

          {(finalOutput || streamingText) && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
