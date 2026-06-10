"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, ArrowRight, Check, Lightbulb } from "lucide-react";
import { Button, Input, Label, Spinner, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { ipApi } from "@/lib/ip";

const ROLES = [
  { value: "attorney", key: "attorney" },
  { value: "patent_agent", key: "patentAgent" },
  { value: "non_attorney_with_lawyer", key: "nonAttorneyWithLawyer" },
  { value: "non_attorney_without", key: "nonAttorneyWithout" },
] as const;

type UserRole = (typeof ROLES)[number]["value"];

const IP_SCOPE_KEYS = ["商标", "著作权", "专利", "商业秘密", "开源"] as const;
const STANCES = [
  { value: "激进", key: "aggressive" },
  { value: "适度", key: "balanced" },
  { value: "保守", key: "conservative" },
] as const;

const QUICK_PLAN = [0, 1, 5];
const FULL_PLAN = [0, 1, 2, 3, 4, 5];

export default function IpSetupPage() {
  const router = useRouter();
  const t = useTranslations("ip");

  const STEP_TITLES = [0, 1, 2, 3, 4, 5].map((i) => t(`setup.steps.${i}`));

  const [quickMode, setQuickMode] = useState(true);
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [userRole, setUserRole] = useState<UserRole>("attorney");
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [ipScope, setIpScope] = useState<string[]>(["商标"]);
  const [jurisdictions, setJurisdictions] = useState("中国大陆（CNIPA）");
  const [stance, setStance] = useState<string>("适度");
  const [brandMarks, setBrandMarks] = useState("");

  const plan = quickMode ? QUICK_PLAN : FULL_PLAN;
  const lastStep = plan[plan.length - 1];

  const toggleScope = (s: string) =>
    setIpScope((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));

  const buildAnswers = (step: number): Record<string, unknown> => {
    switch (step) {
      case 0:
        return { user_role: userRole, company_name: companyName.trim() || null };
      case 1:
        return {
          industry: industry.trim() || null,
          ip_scope: ipScope,
          registration_jurisdictions: jurisdictions
            .split(/[、,，\n]/)
            .map((s) => s.trim())
            .filter(Boolean),
        };
      case 2:
        return { enforcement_posture: { default_stance: stance } };
      case 3:
        return {
          brand_protection: {
            monitored_marks: brandMarks
              .split(/[、,，\n]/)
              .map((s) => s.trim())
              .filter(Boolean),
          },
        };
      default:
        return {};
    }
  };

  const goNext = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await ipApi.submitSetup({
        step: stepIndex,
        answers: buildAnswers(stepIndex),
        quick_mode: quickMode,
      });
      if (res.completed) {
        router.push(ROUTES.IP);
        return;
      }
      setStepIndex(res.step);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit, please retry");
    } finally {
      setSubmitting(false);
    }
  };

  const goBack = () => {
    setError(null);
    const idx = plan.indexOf(stepIndex);
    const prev = idx > 0 ? plan[idx - 1] : undefined;
    if (prev !== undefined) setStepIndex(prev);
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.IP}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Lightbulb className="text-brand h-6 w-6" />
          {t("setup.title")}
        </h1>
        <p className="text-muted-foreground">{t("setup.description")}</p>
      </div>

      <ol className="mb-6 flex items-center gap-2">
        {plan.map((step, i) => {
          const done = step < stepIndex;
          const active = step === stepIndex;
          return (
            <li key={step} className="flex flex-1 items-center gap-2">
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
                {STEP_TITLES[step]}
              </span>
              {i < plan.length - 1 && <div className="bg-muted hidden h-px flex-1 sm:block" />}
            </li>
          );
        })}
      </ol>

      <div className="rounded-2xl border p-6">
        {stepIndex === 0 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.modeLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={() => setQuickMode(true)}
                  className={cn(
                    "flex flex-col items-start gap-0.5 rounded-lg border px-3.5 py-2.5 text-left transition-colors",
                    quickMode ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                  )}
                >
                  <span className="text-sm font-medium">{t("setup.quickMode")}</span>
                  <span className="text-muted-foreground text-xs">{t("setup.quickModeHint")}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setQuickMode(false)}
                  className={cn(
                    "flex flex-col items-start gap-0.5 rounded-lg border px-3.5 py-2.5 text-left transition-colors",
                    !quickMode ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                  )}
                >
                  <span className="text-sm font-medium">{t("setup.fullMode")}</span>
                  <span className="text-muted-foreground text-xs">{t("setup.fullModeHint")}</span>
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.yourRole")}</span>
              <div className="grid gap-2 sm:grid-cols-2">
                {ROLES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setUserRole(r.value)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      userRole === r.value ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`setup.roles.${r.key}`)}
                  </button>
                ))}
              </div>
              {userRole === "patent_agent" && (
                <p className="text-muted-foreground text-xs">{t("setup.patentAgentNote")}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="company">{t("setup.companyName")}</Label>
              <Input
                id="company"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder={t("setup.companyNamePlaceholder")}
              />
            </div>
          </div>
        )}

        {stepIndex === 1 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="industry">{t("setup.industry")}</Label>
              <Input
                id="industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder={t("setup.industryPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.ipScopeLabel")}</span>
              <div className="flex flex-wrap gap-2">
                {IP_SCOPE_KEYS.map((s) => {
                  const selected = ipScope.includes(s);
                  return (
                    <button
                      key={s}
                      type="button"
                      onClick={() => toggleScope(s)}
                      className={cn(
                        "rounded-full border px-3 py-1.5 text-sm transition-colors",
                        selected ? "border-brand bg-brand/10 text-brand font-medium" : "border-border hover:border-brand/40",
                      )}
                    >
                      {s}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="juris">{t("setup.jurisdictionsLabel")}</Label>
              <Input
                id="juris"
                value={jurisdictions}
                onChange={(e) => setJurisdictions(e.target.value)}
                placeholder={t("setup.jurisdictionsPlaceholder")}
              />
            </div>
          </div>
        )}

        {stepIndex === 2 && (
          <div className="flex flex-col gap-4">
            <span className="text-sm font-medium">{t("setup.stanceLabel")}</span>
            <p className="text-muted-foreground text-sm">{t("setup.stanceDesc")}</p>
            <div className="grid gap-2 sm:grid-cols-3">
              {STANCES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setStance(s.value)}
                  className={cn(
                    "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                    stance === s.value ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                  )}
                >
                  {t(`setup.stances.${s.key}`)}
                </button>
              ))}
            </div>
          </div>
        )}

        {stepIndex === 3 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="marks">{t("setup.brandMarksLabel")}</Label>
              <Textarea
                id="marks"
                value={brandMarks}
                onChange={(e) => setBrandMarks(e.target.value)}
                rows={4}
                placeholder={t("setup.brandMarksPlaceholder")}
              />
            </div>
          </div>
        )}

        {stepIndex === 4 && (
          <div className="flex flex-col gap-3">
            <p className="text-muted-foreground text-sm">{t("setup.seedNote")}</p>
            <p className="text-muted-foreground text-xs">{t("setup.seedSkip")}</p>
          </div>
        )}

        {stepIndex === 5 && (
          <div className="flex flex-col items-center gap-4 py-8 text-center">
            <div className="bg-brand/10 flex h-14 w-14 items-center justify-center rounded-2xl">
              <Check className="text-brand h-7 w-7" />
            </div>
            <h2 className="text-lg font-semibold">{t("setup.readyTitle")}</h2>
            <p className="text-muted-foreground max-w-md text-sm">{t("setup.readyDesc")}</p>
          </div>
        )}
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mt-4 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      <div className="mt-6 flex items-center justify-between">
        <Button variant="ghost" onClick={goBack} disabled={stepIndex === plan[0] || submitting}>
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          {t("setup.prevStep")}
        </Button>
        <Button onClick={goNext} disabled={submitting}>
          {submitting && <Spinner className="mr-1.5 h-4 w-4" />}
          {stepIndex === lastStep ? t("setup.finishSetup") : t("setup.nextStep")}
          {!submitting && stepIndex !== lastStep && <ArrowRight className="ml-1.5 h-4 w-4" />}
        </Button>
      </div>
    </div>
  );
}
