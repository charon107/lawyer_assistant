"use client";

import { type ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertCircle, AlertTriangle, ArrowLeft, Loader2, type LucideIcon } from "lucide-react";
import { Button, Card, CardContent, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { useLitigationChat } from "@/hooks/use-litigation-chat";
import { litigationApi } from "@/lib/litigation";
import { ROUTES } from "@/lib/constants";
import type { LitigationMatter, LitigationWsAction } from "@/types/litigation";

interface SkillRunnerProps {
  action: LitigationWsAction;
  title: string;
  description: string;
  icon: LucideIcon;
  promptLabel: string;
  promptPlaceholder: string;
  runLabel?: string;
  /** Preliminary-not-opinion shield shown above the form (e.g. claim_chart). */
  disclaimer?: string;
  extraFields?: ReactNode;
  composePrompt?: (prompt: string) => string;
}

export function SkillRunner({
  action,
  title,
  description,
  icon: Icon,
  promptLabel,
  promptPlaceholder,
  runLabel,
  disclaimer,
  extraFields,
  composePrompt,
}: SkillRunnerProps) {
  const t = useTranslations("litigation");
  const { streamingText, finalOutput, analysisId, status, error, runSkill, reset } =
    useLitigationChat();
  const [prompt, setPrompt] = useState("");
  const [matterId, setMatterId] = useState("");
  const [matters, setMatters] = useState<LitigationMatter[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await litigationApi.listMatters(0, 100);
        if (!cancelled) setMatters(res.items);
      } catch {
        // Optional context — silently skip the picker if it fails.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (!prompt.trim()) return;
    runSkill({
      action,
      prompt: composePrompt ? composePrompt(prompt) : prompt,
      matter_id: matterId || undefined,
    });
  };

  const handleReset = () => {
    reset();
    setPrompt("");
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.LITIGATION}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("skillRunner.back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Icon className="text-brand h-6 w-6" />
          {title}
        </h1>
        <p className="text-muted-foreground">{description}</p>
      </div>

      {disclaimer && (
        <div className="border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200 mb-6 flex items-start gap-2 rounded-lg border px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{disclaimer}</span>
        </div>
      )}

      {status === "idle" ? (
        <div className="flex flex-col gap-5">
          {extraFields}
          {matters.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="skill-matter">{t("skillRunner.matterLabel")}</Label>
              <select
                id="skill-matter"
                value={matterId}
                onChange={(e) => setMatterId(e.target.value)}
                className="border-input bg-background ring-offset-background focus-visible:ring-ring h-10 rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
              >
                <option value="">{t("skillRunner.matterNone")}</option>
                {matters.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.case_name || m.case_number || m.id}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="skill-prompt">{promptLabel}</Label>
            <Textarea
              id="skill-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={7}
              placeholder={promptPlaceholder}
            />
          </div>
          <div className="flex justify-end">
            <Button onClick={handleStart} disabled={!prompt.trim()}>
              <Icon className="mr-1.5 h-4 w-4" />
              {runLabel ?? t("skillRunner.run")}
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <div className="text-muted-foreground flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
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
            <div className="flex items-center gap-2">
              {analysisId && status === "done" && (
                <Link href={`${ROUTES.LITIGATION_ANALYSES}/${analysisId}`}>
                  <Button variant="ghost" size="sm">
                    {t("skillRunner.viewOutput")}
                  </Button>
                </Link>
              )}
              {!isBusy && (
                <Button variant="ghost" size="sm" onClick={handleReset}>
                  {t("skillRunner.newAnalysis")}
                </Button>
              )}
            </div>
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
