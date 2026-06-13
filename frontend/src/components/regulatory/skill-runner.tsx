"use client";

import { type ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertCircle, AlertTriangle, ArrowLeft, Loader2, type LucideIcon } from "lucide-react";
import { Button, Card, CardContent, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { useRegulatoryChat } from "@/hooks/use-regulatory-chat";
import { regulatoryApi } from "@/lib/regulatory";
import { ROUTES } from "@/lib/constants";
import type { RegulatoryRegItem, RegulatoryWsAction } from "@/types/regulatory";

interface SkillRunnerProps {
  action: RegulatoryWsAction;
  title: string;
  description: string;
  icon: LucideIcon;
  promptLabel: string;
  promptPlaceholder: string;
  runLabel?: string;
  /** Hard-rule notice shown above the form (e.g. policy-redraft 写新文件不覆盖源). */
  disclaimer?: string;
  /** Whether to show the reg-item picker (policy-diff targets a tracked item). */
  showItemPicker?: boolean;
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
  showItemPicker = false,
  extraFields,
  composePrompt,
}: SkillRunnerProps) {
  const t = useTranslations("regulatory");
  const { streamingText, finalOutput, analysisId, status, error, runSkill, reset } =
    useRegulatoryChat();
  const [prompt, setPrompt] = useState("");
  const [regItemId, setRegItemId] = useState("");
  const [items, setItems] = useState<RegulatoryRegItem[]>([]);

  useEffect(() => {
    if (!showItemPicker) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await regulatoryApi.listItems(0, 100);
        if (!cancelled) setItems(res.items);
      } catch {
        // Optional context — silently skip the picker if it fails.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [showItemPicker]);

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (!prompt.trim()) return;
    runSkill({
      action,
      prompt: composePrompt ? composePrompt(prompt) : prompt,
      reg_item_id: regItemId || undefined,
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
          href={ROUTES.REGULATORY}
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
          {showItemPicker && items.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="skill-item">{t("skillRunner.itemLabel")}</Label>
              <select
                id="skill-item"
                value={regItemId}
                onChange={(e) => setRegItemId(e.target.value)}
                className="border-input bg-background ring-offset-background focus-visible:ring-ring h-10 rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:outline-none"
              >
                <option value="">{t("skillRunner.itemNone")}</option>
                {items.map((it) => (
                  <option key={it.id} value={it.id}>
                    {it.title || it.regulator || it.id}
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
              rows={8}
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
                <Link href={`${ROUTES.REGULATORY_ANALYSES}/${analysisId}`}>
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
