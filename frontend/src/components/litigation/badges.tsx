"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type {
  AnalysisType,
  DemandMode,
  DemandStatus,
  MatterStatus,
  Risk,
  Severity,
} from "@/types/litigation";

const GREENISH = "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300";
const AMBER = "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300";
const ORANGE = "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300";
const RED = "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300";
const BLUE = "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300";
const PURPLE = "bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300";
const NEUTRAL = "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300";

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

const MATTER_STATUS_CLS: Record<MatterStatus, string> = {
  active: BLUE,
  settled: GREENISH,
  dismissed: NEUTRAL,
  judgment_won: GREENISH,
  judgment_lost: RED,
  withdrawn: NEUTRAL,
  closed: NEUTRAL,
  archived: NEUTRAL,
};

const DEMAND_MODE_CLS: Record<DemandMode, string> = {
  send: BLUE,
  receive: PURPLE,
};

const DEMAND_STATUS_CLS: Record<DemandStatus, string> = {
  intake: NEUTRAL,
  drafting: BLUE,
  gated: AMBER,
  sent: GREENISH,
  received: BLUE,
  responded: GREENISH,
  escalated: RED,
  closed: NEUTRAL,
};

const RISK_CLS: Record<Risk, string> = {
  低: GREENISH,
  中: AMBER,
  高: ORANGE,
  严重: RED,
};

const BASE = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

export function SeverityBadge({ value }: { value?: Severity | null }) {
  const t = useTranslations("litigation");
  if (!value) return null;
  return (
    <span className={cn(BASE, SEVERITY_CLS[value])}>
      {SEVERITY_ICON[value]} {t(`badges.severity.${value}`)}
    </span>
  );
}

export function AnalysisTypeBadge({ value }: { value: AnalysisType }) {
  const t = useTranslations("litigation");
  return <span className={cn(BASE, "bg-brand/10 text-brand")}>{t(`badges.analysisType.${value}`)}</span>;
}

export function MatterStatusBadge({ value }: { value: MatterStatus }) {
  const t = useTranslations("litigation");
  const cls = MATTER_STATUS_CLS[value] ?? NEUTRAL;
  return <span className={cn(BASE, cls)}>{t(`badges.matterStatus.${value}`)}</span>;
}

export function DemandModeBadge({ value }: { value: DemandMode }) {
  const t = useTranslations("litigation");
  return <span className={cn(BASE, DEMAND_MODE_CLS[value] ?? NEUTRAL)}>{t(`badges.demandMode.${value}`)}</span>;
}

export function DemandStatusBadge({ value }: { value: DemandStatus }) {
  const t = useTranslations("litigation");
  const cls = DEMAND_STATUS_CLS[value] ?? NEUTRAL;
  return <span className={cn(BASE, cls)}>{t(`badges.demandStatus.${value}`)}</span>;
}

export function RiskBadge({ value }: { value?: Risk | null }) {
  const t = useTranslations("litigation");
  if (!value) return null;
  return <span className={cn(BASE, RISK_CLS[value] ?? NEUTRAL)}>{t(`badges.risk.${value}`)}</span>;
}
