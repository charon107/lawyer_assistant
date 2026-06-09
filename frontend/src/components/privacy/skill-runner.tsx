"use client";

import { type ReactNode, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertCircle, ArrowLeft, Loader2, type LucideIcon } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { usePrivacyChat } from "@/hooks/use-privacy-chat";
import { ROUTES } from "@/lib/constants";
import type { PrivacyWsAction } from "@/types/privacy";

interface SkillRunnerProps {
  action: PrivacyWsAction;
  title: string;
  description: string;
  icon: LucideIcon;
  promptLabel: string;
  promptPlaceholder: string;
  subjectLabel?: string;
  subjectPlaceholder?: string;
  runLabel?: string;
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
  subjectLabel,
  subjectPlaceholder,
  runLabel = "Start Analysis",
  extraFields,
  composePrompt,
}: SkillRunnerProps) {
  const t = useTranslations("privacy");
  const { streamingText, finalOutput, reviewId, status, error, runSkill, reset } =
    usePrivacyChat();
  const [subject, setSubject] = useState("");
  const [prompt, setPrompt] = useState("");

  const isBusy = status === "connecting" || status === "running";

  const handleStart = () => {
    if (!prompt.trim()) return;
    runSkill({
      action,
      subject: subject.trim() || undefined,
      prompt: composePrompt ? composePrompt(prompt) : prompt,
    });
  };

  const handleReset = () => {
    reset();
    setSubject("");
    setPrompt("");
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.PRIVACY}
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

      {status === "idle" ? (
        <div className="flex flex-col gap-5">
          {extraFields}
          {subjectLabel && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="skill-subject">{subjectLabel}</Label>
              <Input
                id="skill-subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder={subjectPlaceholder}
              />
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
              {runLabel}
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
              {reviewId && status === "done" && (
                <Link href={`${ROUTES.PRIVACY_REVIEWS}/${reviewId}`}>
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
