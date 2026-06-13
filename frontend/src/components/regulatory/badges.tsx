"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type {
  AnalysisType,
  CommentDecision,
  GapStatus,
  GapType,
  ItemType,
  Materiality,
  Severity,
} from "@/types/regulatory";

const GREENISH = "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300";
const AMBER = "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300";
const ORANGE = "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300";
const RED = "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300";
const BLUE = "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300";
const PURPLE = "bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300";
const NEUTRAL = "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300";

const BASE = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

const MATERIALITY_ICON: Record<Materiality, string> = {
  always: "🔴",
  review: "🟡",
  fyi: "🟢",
};
const MATERIALITY_CLS: Record<Materiality, string> = {
  always: RED,
  review: AMBER,
  fyi: GREENISH,
};

const SEVERITY_ICON: Record<Severity, string> = {
  blocking: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🟢",
};
const SEVERITY_CLS: Record<Severity, string> = {
  blocking: RED,
  high: ORANGE,
  medium: AMBER,
  low: GREENISH,
};

const GAP_TYPE_CLS: Record<GapType, string> = {
  none: NEUTRAL,
  partial: AMBER,
  full: ORANGE,
  "new-policy": BLUE,
  watch: PURPLE,
  "comment-decision": PURPLE,
};

const GAP_STATUS_CLS: Record<GapStatus, string> = {
  open: BLUE,
  "in-progress": AMBER,
  closed: GREENISH,
  "risk-accepted": NEUTRAL,
};

const DECISION_CLS: Record<CommentDecision, string> = {
  undecided: AMBER,
  filing: BLUE,
  "not-filing": NEUTRAL,
  filed: GREENISH,
  waived: NEUTRAL,
};

export function MaterialityBadge({ value }: { value: Materiality }) {
  const t = useTranslations("regulatory");
  return (
    <span className={cn(BASE, MATERIALITY_CLS[value])}>
      {MATERIALITY_ICON[value]} {t(`badges.materiality.${value}`)}
    </span>
  );
}

export function ItemTypeBadge({ value }: { value: ItemType }) {
  const t = useTranslations("regulatory");
  return <span className={cn(BASE, "bg-brand/10 text-brand")}>{t(`badges.itemType.${value}`)}</span>;
}

export function SeverityBadge({ value }: { value?: Severity | null }) {
  const t = useTranslations("regulatory");
  if (!value) return null;
  return (
    <span className={cn(BASE, SEVERITY_CLS[value])}>
      {SEVERITY_ICON[value]} {t(`badges.severity.${value}`)}
    </span>
  );
}

export function AnalysisTypeBadge({ value }: { value: AnalysisType }) {
  const t = useTranslations("regulatory");
  return (
    <span className={cn(BASE, "bg-brand/10 text-brand")}>{t(`badges.analysisType.${value}`)}</span>
  );
}

export function GapTypeBadge({ value }: { value: GapType }) {
  const t = useTranslations("regulatory");
  return <span className={cn(BASE, GAP_TYPE_CLS[value] ?? NEUTRAL)}>{t(`badges.gapType.${value}`)}</span>;
}

export function GapStatusBadge({ value }: { value: GapStatus }) {
  const t = useTranslations("regulatory");
  return (
    <span className={cn(BASE, GAP_STATUS_CLS[value] ?? NEUTRAL)}>{t(`badges.gapStatus.${value}`)}</span>
  );
}

export function CommentDecisionBadge({ value }: { value: CommentDecision }) {
  const t = useTranslations("regulatory");
  return (
    <span className={cn(BASE, DECISION_CLS[value] ?? NEUTRAL)}>{t(`badges.decision.${value}`)}</span>
  );
}

export function VerificationBadge({ verified }: { verified: boolean }) {
  const t = useTranslations("regulatory");
  return (
    <span className={cn(BASE, verified ? GREENISH : AMBER)}>
      {verified ? "✓ " : "⚠ "}
      {t(`badges.verification.${verified ? "verified" : "unverified"}`)}
    </span>
  );
}
