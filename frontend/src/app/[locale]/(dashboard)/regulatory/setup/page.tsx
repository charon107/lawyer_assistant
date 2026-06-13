"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Input, Label, Spinner, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { ColdStartResponse } from "@/types/regulatory";
import { ArrowLeft, ArrowRight, Check, Landmark } from "lucide-react";

const USER_ROLE_OPTS = ["lawyer", "non_lawyer_with_counsel", "non_lawyer_without"] as const;
const PRACTICE_SETTING_OPTS = ["独立执业", "中大型律所", "法务内部", "政府法援诊所"] as const;

const FULL_PLAN = [0, 1, 2, 3, 4, 5];
const QUICK_PLAN = [0, 1, 2, 5];

export default function RegulatorySetupPage() {
  const t = useTranslations("regulatory");
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
      const r = await regulatoryApi.submitSetup({
        step: stepNum,
        answers: { ...answers },
        quick_mode: quickMode,
      });
      setResponse(r);
      setAnswers({});
      if (r.completed) {
        router.push(ROUTES.REGULATORY);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : t("setup.submitError"));
    } finally {
      setLoading(false);
    }
  }

  useState(() => {
    (async () => {
      try {
        const r = await regulatoryApi.getSetupStatus();
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
      <div className="mb-8">
        <Link
          href={ROUTES.REGULATORY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("setup.back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Landmark className="text-brand h-6 w-6" />
          {t("setup.title")}
        </h1>
        <p className="text-muted-foreground">{t("setup.description")}</p>
      </div>

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
              <span className="text-sm font-medium">{t("setup.practiceSettingLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-4">
                {PRACTICE_SETTING_OPTS.map((o) => (
                  <button
                    key={o}
                    type="button"
                    onClick={() => setAnswers((a) => ({ ...a, practice_setting: o }))}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      answers.practice_setting === o
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {o}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="watchlist">{t("setup.watchlistLabel")}</Label>
            <Textarea
              id="watchlist"
              rows={5}
              value={answers.watchlist_text || ""}
              onChange={(e) => setAnswers((a) => ({ ...a, watchlist_text: e.target.value }))}
              placeholder={t("setup.watchlistPlaceholder")}
            />
          </div>
        )}

        {step === 2 && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="threshold">{t("setup.thresholdLabel")}</Label>
            <p className="text-muted-foreground text-xs">{t("setup.thresholdHint")}</p>
            <Textarea
              id="threshold"
              rows={6}
              value={answers.materiality_text || ""}
              onChange={(e) => setAnswers((a) => ({ ...a, materiality_text: e.target.value }))}
              placeholder={t("setup.thresholdPlaceholder")}
            />
          </div>
        )}

        {step === 3 && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="library">{t("setup.libraryLabel")}</Label>
            <Textarea
              id="library"
              rows={5}
              value={answers.policy_library_text || ""}
              onChange={(e) => setAnswers((a) => ({ ...a, policy_library_text: e.target.value }))}
              placeholder={t("setup.libraryPlaceholder")}
            />
          </div>
        )}

        {step === 4 && (
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="feeds">{t("setup.feedLabel")}</Label>
            <p className="text-muted-foreground text-xs">{t("setup.feedHint")}</p>
            <Input
              id="feeds"
              value={answers.feed_text || ""}
              onChange={(e) => setAnswers((a) => ({ ...a, feed_text: e.target.value }))}
              placeholder={t("setup.feedPlaceholder")}
            />
          </div>
        )}

        {step === 5 && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="bg-brand/10 flex h-14 w-14 items-center justify-center rounded-2xl">
              <Check className="text-brand h-7 w-7" />
            </div>
            <h2 className="text-lg font-semibold">{t("setup.confirmIntro")}</h2>
            <ul className="text-muted-foreground max-w-md list-disc space-y-1 pl-5 text-left text-sm">
              <li>
                {t("setup.confirmUserRole")}：
                {response.partial_config?.steps?.["0"]?.answers?.user_role || t("setup.notSet")}
              </li>
              <li>
                {t("setup.confirmPracticeSetting")}：
                {response.partial_config?.steps?.["0"]?.answers?.practice_setting ||
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

      <div className="mt-6 flex items-center justify-between">
        <Button variant="ghost" disabled={loading || step === 0} onClick={() => submit(step - 1)}>
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
