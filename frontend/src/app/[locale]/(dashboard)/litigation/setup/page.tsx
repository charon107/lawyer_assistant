"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { ColdStartResponse } from "@/types/litigation";
import { ArrowLeft, ArrowRight, Check, Scale } from "lucide-react";

const SELECT_CLS = "border-input bg-background w-full rounded-lg border px-3 py-2 text-sm";

const USER_ROLE_OPTS = ["lawyer", "non_lawyer_with_counsel", "non_lawyer_without"] as const;
const PRACTICE_ROLE_OPTS = ["企业法务", "律所律师", "独立执业", "其他"] as const;
const PARTY_ROLE_OPTS = ["原告方", "被告方", "兼顾-默认原告", "兼顾-默认被告", "依案件而定"] as const;
const RISK_APPETITE_OPTS = ["保守", "适中", "进取"] as const;

export default function LitigationSetupPage() {
  const t = useTranslations("litigation");
  const router = useRouter();
  const [response, setResponse] = useState<ColdStartResponse | null>(null);
  const [quickMode, setQuickMode] = useState(false);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const step = response?.step ?? 0;
  const progress = response?.progress ?? 0;

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
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <Spinner className="text-brand mx-auto h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <div className="mb-6 flex items-center gap-3">
        <Scale className="text-brand h-5 w-5" />
        <h1 className="text-xl font-bold">{t("setup.title")}</h1>
      </div>

      {/* Progress */}
      <div className="mb-6">
        <div className="bg-muted h-1.5 rounded-full">
          <div
            className="bg-brand h-1.5 rounded-full transition-all"
            style={{ width: `${Math.round(progress * 100)}%` }}
          />
        </div>
        <p className="text-muted-foreground mt-2 text-xs">
          {t("setup.stepProgress", {
            current: step + 1,
            total: quickMode ? 3 : 5,
            label: t(`setup.stepLabels.${step}`),
          })}
          {quickMode && t("setup.quickSuffix")}
        </p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border px-4 py-2 text-sm">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="space-y-4 p-6">
          {step === 0 && (
            <>
              <div className="space-y-2">
                <Label htmlFor="role">{t("setup.userRoleLabel")}</Label>
                <select
                  id="role"
                  className={SELECT_CLS}
                  value={answers.user_role || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, user_role: e.target.value }))}
                >
                  <option value="">{t("setup.selectPlaceholder")}</option>
                  {USER_ROLE_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`setup.userRoleOpt.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="practiceRole">{t("setup.practiceRoleLabel")}</Label>
                <select
                  id="practiceRole"
                  className={SELECT_CLS}
                  value={answers.practice_role || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, practice_role: e.target.value }))}
                >
                  <option value="">{t("setup.selectPlaceholder")}</option>
                  {PRACTICE_ROLE_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`setup.practiceRoleOpt.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="partyRole">{t("setup.partyRoleLabel")}</Label>
                <select
                  id="partyRole"
                  className={SELECT_CLS}
                  value={answers.party_role || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, party_role: e.target.value }))}
                >
                  <option value="">{t("setup.selectPlaceholder")}</option>
                  {PARTY_ROLE_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`setup.partyRoleOpt.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
          {step === 1 && (
            <>
              <div className="space-y-2">
                <Label htmlFor="industry">{t("setup.industryLabel")}</Label>
                <Input
                  id="industry"
                  value={answers.industry || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, industry: e.target.value }))}
                  placeholder={t("setup.industryPlaceholder")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="riskAppetite">{t("setup.riskAppetiteLabel")}</Label>
                <select
                  id="riskAppetite"
                  className={SELECT_CLS}
                  value={answers.risk_appetite || ""}
                  onChange={(e) => setAnswers((a) => ({ ...a, risk_appetite: e.target.value }))}
                >
                  <option value="">{t("setup.selectPlaceholder")}</option>
                  {RISK_APPETITE_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`setup.riskAppetiteOpt.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
          {step >= 2 && step <= 3 && (
            <div className="space-y-2">
              <Label htmlFor="notes">
                {step === 2 ? t("setup.disputeNotesLabel") : t("setup.docStyleNotesLabel")}
              </Label>
              <Textarea
                id="notes"
                rows={4}
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
            <div className="text-muted-foreground text-sm">
              <p className="mb-2">{t("setup.confirmIntro")}</p>
              <ul className="list-disc space-y-1 pl-5">
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
        </CardContent>
      </Card>

      <div className="mt-6 flex justify-between">
        <Button variant="outline" disabled={loading || step === 0} onClick={() => submit(step - 1)}>
          <ArrowLeft className="mr-1 h-4 w-4" /> {t("setup.prev")}
        </Button>
        <Button onClick={() => submit(step)} disabled={loading}>
          {loading ? (
            <Spinner className="h-4 w-4" />
          ) : step === 4 ? (
            <>
              <Check className="mr-1 h-4 w-4" /> {t("setup.finish")}
            </>
          ) : (
            <>
              {t("setup.next")} <ArrowRight className="ml-1 h-4 w-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
