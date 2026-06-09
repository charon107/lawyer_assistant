"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, ArrowRight, Check, ShieldCheck } from "lucide-react";
import { Button, Input, Label, Spinner, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";

const ROLES = [
  { value: "attorney", key: "attorney" },
  { value: "non_attorney_with_lawyer", key: "nonAttorneyWithLawyer" },
  { value: "non_attorney_without", key: "nonAttorneyWithout" },
] as const;

type UserRole = (typeof ROLES)[number]["value"];

const REGULATIONS_KEYS = [
  "regulations.0", "regulations.1", "regulations.2", "regulations.3",
  "regulations.4", "regulations.5", "regulations.6",
] as const;

const QUICK_PLAN = [0, 1, 5];
const FULL_PLAN = [0, 1, 2, 3, 4, 5];

export default function PrivacySetupPage() {
  const router = useRouter();
  const t = useTranslations("privacy");

  const STEP_TITLES = [0, 1, 2, 3, 4, 5].map((i) => t(`setup.steps.${i}`));
  const REGULATIONS = REGULATIONS_KEYS.map((k) => t(`setup.${k}`));

  const [quickMode, setQuickMode] = useState(true);
  const [stepIndex, setStepIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [userRole, setUserRole] = useState<UserRole>("attorney");
  const [practiceSetting, setPracticeSetting] = useState("");
  const [footprint, setFootprint] = useState<string[]>([REGULATIONS[0] ?? ""]);
  const [businessModel, setBusinessModel] = useState<"handler" | "entrusted" | "both">("handler");
  const [dataResidency, setDataResidency] = useState("");
  const [dpaNotes, setDpaNotes] = useState("");
  const [piaTrigger, setPiaTrigger] = useState("");
  const [dsarSystems, setDsarSystems] = useState("");
  const [dsarSla, setDsarSla] = useState("");

  const plan = quickMode ? QUICK_PLAN : FULL_PLAN;
  const lastStep = plan[plan.length - 1];

  const toggleFootprint = (r: string) =>
    setFootprint((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]));

  const buildAnswers = (step: number): Record<string, unknown> => {
    switch (step) {
      case 0:
        return { user_role: userRole, practice_setting: practiceSetting.trim() || null };
      case 1:
        return {
          regulatory_footprint: footprint,
          data_residency: dataResidency.trim() || null,
          business_model: businessModel,
        };
      case 2:
        return { dpa_playbook: { notes: dpaNotes.trim() || null } };
      case 3:
        return {
          pia_house_style: { trigger: piaTrigger.trim() || null },
          dsar_process: {
            systems_list: dsarSystems
              .split(/[、,，\n]/)
              .map((s) => s.trim())
              .filter(Boolean),
            response_sla: dsarSla.trim() || null,
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
      const res = await privacyApi.submitSetup({
        step: stepIndex,
        answers: buildAnswers(stepIndex),
        quick_mode: quickMode,
      });
      if (res.completed) {
        router.push(ROUTES.PRIVACY);
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
          href={ROUTES.PRIVACY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <ShieldCheck className="text-brand h-6 w-6" />
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
              <div className="grid gap-2 sm:grid-cols-3">
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
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="setting">{t("setup.practiceSetting")}</Label>
              <Input
                id="setting"
                value={practiceSetting}
                onChange={(e) => setPracticeSetting(e.target.value)}
                placeholder={t("setup.practiceSettingPlaceholder")}
              />
            </div>
          </div>
        )}

        {stepIndex === 1 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">{t("setup.regulationsLabel")}</p>
            <div className="flex flex-wrap gap-2">
              {REGULATIONS.map((r) => {
                const selected = footprint.includes(r);
                return (
                  <button
                    key={r}
                    type="button"
                    onClick={() => toggleFootprint(r)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-sm transition-colors",
                      selected ? "border-brand bg-brand/10 text-brand font-medium" : "border-border hover:border-brand/40",
                    )}
                  >
                    {r}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-medium">{t("setup.businessModelLabel")}</span>
              <div className="grid gap-2 sm:grid-cols-3">
                {([
                  { value: "handler", key: "handler" },
                  { value: "entrusted", key: "entrusted" },
                  { value: "both", key: "both" },
                ] as const).map((b) => (
                  <button
                    key={b.value}
                    type="button"
                    onClick={() => setBusinessModel(b.value)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      businessModel === b.value ? "border-brand bg-brand/5 ring-brand/20 ring-1" : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`setup.businessModel.${b.key}`)}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="residency">{t("setup.dataResidency")}</Label>
              <Input
                id="residency"
                value={dataResidency}
                onChange={(e) => setDataResidency(e.target.value)}
                placeholder={t("setup.dataResidencyPlaceholder")}
              />
            </div>
          </div>
        )}

        {stepIndex === 2 && (
          <div className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">{t("setup.dpaNotesDesc")}</p>
            <Textarea
              value={dpaNotes}
              onChange={(e) => setDpaNotes(e.target.value)}
              rows={8}
              placeholder={t("setup.dpaNotesPlaceholder")}
            />
          </div>
        )}

        {stepIndex === 3 && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="pia-trigger">{t("setup.piaTrigger")}</Label>
              <Input
                id="pia-trigger"
                value={piaTrigger}
                onChange={(e) => setPiaTrigger(e.target.value)}
                placeholder={t("setup.piaTriggerPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dsar-systems">{t("setup.dsarSystems")}</Label>
              <Textarea
                id="dsar-systems"
                value={dsarSystems}
                onChange={(e) => setDsarSystems(e.target.value)}
                rows={4}
                placeholder={t("setup.dsarSystemsPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="dsar-sla">{t("setup.dsarSla")}</Label>
              <Input
                id="dsar-sla"
                value={dsarSla}
                onChange={(e) => setDsarSla(e.target.value)}
                placeholder={t("setup.dsarSlaPlaceholder")}
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
