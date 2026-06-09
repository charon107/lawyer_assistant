"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertCircle, ArrowLeft, Loader2, Radar } from "lucide-react";
import { Button, Card, CardContent, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { usePrivacyChat } from "@/hooks/use-privacy-chat";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

type Mode = "sweep" | "query";

const SWEEP_PROMPT =
  "请扫描自上次扫描以来保存的所有分析产出（PIA / DPA / 分诊结果），对照处理规则承诺找出漂移，区分必须更新与建议更新，并起草建议语言。";

export default function PrivacyPolicyMonitorPage() {
  const t = useTranslations("privacy");
  const { streamingText, finalOutput, status, error, runSkill, reset } = usePrivacyChat();
  const [mode, setMode] = useState<Mode>("sweep");
  const [query, setQuery] = useState("");

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (mode === "sweep") {
      runSkill({ action: "policy_sweep", prompt: SWEEP_PROMPT });
    } else {
      if (!query.trim()) return;
      runSkill({ action: "policy_query", prompt: query });
    }
  };

  const handleReset = () => {
    reset();
    setQuery("");
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.PRIVACY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Radar className="text-brand h-6 w-6" />
          {t("policyMonitor.title")}
        </h1>
        <p className="text-muted-foreground">{t("policyMonitor.description")}</p>
      </div>

      {status === "idle" ? (
        <div className="flex flex-col gap-5">
          <div className="flex flex-col gap-1.5">
            <Label>{t("policyMonitor.modeLabel")}</Label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setMode("sweep")}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  mode === "sweep"
                    ? "border-brand bg-brand/10 text-brand font-medium"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {t("policyMonitor.modeSweep")}
              </button>
              <button
                type="button"
                onClick={() => setMode("query")}
                className={cn(
                  "rounded-md border px-3 py-1.5 text-sm transition-colors",
                  mode === "query"
                    ? "border-brand bg-brand/10 text-brand font-medium"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {t("policyMonitor.modeQuery")}
              </button>
            </div>
          </div>

          {mode === "sweep" ? (
            <p className="text-muted-foreground rounded-lg border border-dashed px-4 py-3 text-sm">
              {t("policyMonitor.sweepHint")}
            </p>
          ) : (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="policy-query">{t("policyMonitor.queryLabel")}</Label>
              <Textarea
                id="policy-query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={5}
                placeholder={t("policyMonitor.queryPlaceholder")}
              />
            </div>
          )}

          <div className="flex justify-end">
            <Button onClick={handleStart} disabled={mode === "query" && !query.trim()}>
              <Radar className="mr-1.5 h-4 w-4" />
              {mode === "sweep" ? t("policyMonitor.runSweep") : t("policyMonitor.runQuery")}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
              {status === "connecting" && t("policyMonitor.connecting")}
              {status === "running" && t("policyMonitor.analyzing")}
              {status === "done" && t("policyMonitor.done")}
              {status === "error" && (
                <span className="text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  {t("policyMonitor.failed")}
                </span>
              )}
            </div>
            {!isBusy && (
              <Button variant="ghost" size="sm" onClick={handleReset}>
                {t("policyMonitor.newCheck")}
              </Button>
            )}
          </div>

          {error && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {error}
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
