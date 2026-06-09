"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type { Classification, DsarStatus, ReviewType, Severity } from "@/types/privacy";

const CLASSIFICATION_ICON: Record<Classification, string> = {
  PROCEED: "🟢",
  PIA_REQUIRED: "🟡",
  DPIA_MANDATORY: "🟠",
  STOP: "🔴",
};

const CLASSIFICATION_CLS: Record<Classification, string> = {
  PROCEED: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  PIA_REQUIRED: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  DPIA_MANDATORY: "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300",
  STOP: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
};

const SEVERITY_ICON: Record<Severity, string> = {
  blocking: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🟢",
};

const SEVERITY_CLS: Record<Severity, string> = {
  blocking: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
  high: "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300",
  medium: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  low: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
};

const DSAR_STATUS_CLS: Record<DsarStatus, string> = {
  received: "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300",
  verifying: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
  locating: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
  exemption_analysis: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  drafted: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300",
  responded: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  escalated: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
};

const BASE = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

export function TriageClassificationBadge({ value }: { value?: Classification | null }) {
  const t = useTranslations("privacy");
  if (!value) return null;
  const icon = CLASSIFICATION_ICON[value];
  const label = t(`badges.classification.${value}`);
  return <span className={cn(BASE, CLASSIFICATION_CLS[value])}>{icon} {label}</span>;
}

export function SeverityBadge({ value }: { value?: Severity | null }) {
  const t = useTranslations("privacy");
  if (!value) return null;
  const icon = SEVERITY_ICON[value];
  const label = t(`badges.severity.${value}`);
  return <span className={cn(BASE, SEVERITY_CLS[value])}>{icon} {label}</span>;
}

export function ReviewTypeBadge({ value }: { value: ReviewType }) {
  const t = useTranslations("privacy");
  return (
    <span className={cn(BASE, "bg-brand/10 text-brand")}>
      {t(`badges.reviewType.${value}`)}
    </span>
  );
}

export function DsarStatusBadge({ value }: { value: DsarStatus }) {
  const t = useTranslations("privacy");
  const label = t(`dsar.status.${value}`);
  const cls = DSAR_STATUS_CLS[value] ?? DSAR_STATUS_CLS.received;
  return <span className={cn(BASE, cls)}>{label}</span>;
}
