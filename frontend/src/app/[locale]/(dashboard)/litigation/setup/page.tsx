"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Input, Label, Spinner, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { ColdStartResponse } from "@/types/litigation";
import { ArrowLeft, ArrowRight, Check, Scale } from "lucide-react";

const USER_ROLE_OPTS = ["lawyer", "non_lawyer_with_counsel", "non_lawyer_without"] as const;
const PRACTICE_ROLE_OPTS = ["企业法务", "律所律师", "独立执业", "其他"] as const;
const PARTY_ROLE_OPTS = ["原告方", "被告方", "兼顾-默认原告", "兼顾-默认被告", "依案件而定"] as const;
const RISK_APPETITE_OPTS = ["保守", "适中", "进取"] as const;

const FULL_PLAN = [0, 1, 2, 3, 4];
const QUICK_PLAN = [0, 1, 4];

export default function LitigationSetupPage() {
  const t = useTranslations("litigation");
  const router = useRouter();
  const [response, setResponse] = useState<ColdStartResponse | null>(null);
  const [quickMode, setQuickMode] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = response?.step ?? 0;

  async function submit(stepNum: number) {
    setLoading(true);
    setError(null);
    try {
      const r = await litigationApi.submitSetup({
        step: stepNum,
        answers: { ...answers },
        quick_mode: quickMode,
      });
      setResponse(r);
      setAnswers({});
      if (r.completed) {
        router.push(ROUTES.LITIGATION);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("setup.submitError"));
    } finally {
      setLoading(false);
    }
  }

  // Initialize
  useState(() => {
    (async () => {
      try {
        const r = await litigationApi.getSetupStatus();
        setResponse(r);
        setQuickMode(!!r.partial_config?.quick_mode);
      } catch {
        /* empty */
      }
    })();
  });

  if (!response || response.completed) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <Spinner className="text-brand mx-auto h-6 w-6" />
      </div>
    );
  }

  const plan = quickMode ? QUICK_PLAN : FULL_PLAN;
  const lastStep = plan[plan.length - 1];

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      {/* Header */}
      <div className="mb-8">
        <Link
          href={ROUTES.LITIGATION}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("setup.back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Scale className="text-brand h-6 w-6" />
          {t("setup.title")}
        </h1>
        <p className="text-muted-foreground">{t("setup.description")}</p>
      </div>

      {/* Step rail */}
      <ol className="mb-6 flex items-center gap-2">
        {plan.map((s, i) => {
          const done = s < step;
          const active = s === step;
          return (
            <li key={s} className="flex flex-1 items-center gap-2">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-medium transition-colors",
                  done && "border-brand bg-brand text-white",
                  active && "border-brand text-brand",
                  !done && !active && "text-muted-foreground border-muted",
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </div>
              <span
                className={cn(
                  "hidden text-xs sm:block",
                  active ? "text-foreground font-medium" : "text-muted-foreground",
                )}
              >
                {t(`setup.stepLabels.${s}`)}
              </span>
              {i < plan.length - 1 && <div className="bg-muted hidden h-px flex-1 sm:block" />}
            </li>
          );
        })}
      </ol>

      {/* Step body */}
      <div className="rounded-2xl border p-6">
        {step === 0 && (
          <div className="flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.userRoleLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-3">
                {USER_ROLE_OPTS.map((o) => (
                  <button
                    key={o}
                    type="button"
                    onClick={() => setAnswers((a) => ({ ...a, user_role: o }))}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      answers.user_role === o
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`setup.userRoleOpt.${o}`)}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.practiceRoleLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-4">
                {PRACTICE_ROLE_OPTS.map((o) => (
                  <button
                    key={o}
                    type="button"
                    onClick={() => setAnswers((a) => ({ ...a, practice_role: o }))}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      answers.practice_role === o
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`setup.practiceRoleOpt.${o}`)}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.partyRoleLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-3">
                {PARTY_ROLE_OPTS.map((o) => (
                  <button
                    key={o}
                    type="button"
                    onClick={() => setAnswers((a) => ({ ...a, party_role: o }))}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      answers.party_role === o
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`setup.partyRoleOpt.${o}`)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="industry">{t("setup.industryLabel")}</Label>
              <Input
                id="industry"
                value={answers.industry || ""}
                onChange={(e) => setAnswers((a) => ({ ...a, industry: e.target.value }))}
                placeholder={t("setup.industryPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.riskAppetiteLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-3">
                {RISK_APPETITE_OPTS.map((o) => (
                  <button
                    key={o}
                    type="button"
                    onClick={() => setAnswers((a) => ({ ...a, risk_appetite: o }))}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      answers.risk_appetite === o
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`setup.riskAppetiteOpt.${o}`)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {(step === 2 || step === 3) && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="notes">
              {step === 2 ? t("setup.disputeNotesLabel") : t("setup.docStyleNotesLabel")}
            </Label>
            <Textarea
              id="notes"
              rows={5}
              value={answers.notes || ""}
              onChange={(e) => setAnswers((a) => ({ ...a, notes: e.target.value }))}
              placeholder={
                step === 2
                  ? t("setup.disputeNotesPlaceholder")
                  : t("setup.docStyleNotesPlaceholder")
              }
            />
          </div>
        )}

        {step === 4 && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="bg-brand/10 flex h-14 w-14 items-center justify-center rounded-2xl">
              <Check className="text-brand h-7 w-7" />
            </div>
            <h2 className="text-lg font-semibold">{t("setup.confirmIntro")}</h2>
            <ul className="text-muted-foreground max-w-md list-disc space-y-1 pl-5 text-left text-sm">
              <li>
                {t("setup.confirmPracticeRole")}：
                {response.partial_config?.steps?.["0"]?.answers?.practice_role ||
                  t("setup.notSet")}
              </li>
              <li>
                {t("setup.confirmPartyRole")}：
                {response.partial_config?.steps?.["0"]?.answers?.party_role || t("setup.notSet")}
              </li>
              <li>
                {t("setup.confirmRiskAppetite")}：
                {response.partial_config?.steps?.["1"]?.answers?.risk_appetite ||
                  t("setup.notSet")}
              </li>
            </ul>
          </div>
        )}
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mt-4 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {/* Controls */}
      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="ghost"
          disabled={loading || step === 0}
          onClick={() => submit(step - 1)}
        >
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          {t("setup.prev")}
        </Button>
        <Button onClick={() => submit(step)} disabled={loading}>
          {loading ? (
            <Spinner className="mr-1.5 h-4 w-4" />
          ) : step === lastStep ? (
            <>
              <Check className="mr-1.5 h-4 w-4" />
              {t("setup.finish")}
            </>
          ) : (
            <>
              {t("setup.next")}
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
