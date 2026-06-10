"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type {
  AssetStatus,
  Classification,
  EnforcementStatus,
  IpCategory,
  ReviewType,
  Severity,
} from "@/types/ip";

const CLASSIFICATION_ICON: Record<Classification, string> = {
  GREEN: "🟢",
  YELLOW: "🟡",
  RED: "🔴",
  PURSUE: "🟢",
  INVESTIGATE: "🟡",
  REJECT: "🔴",
  IGNORE: "⚪",
  COMMUNICATE: "🟡",
  CEASE_DESIST: "🟠",
  LITIGATE: "🔴",
};

const GREENISH = "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300";
const AMBER = "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300";
const ORANGE = "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300";
const RED = "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300";
const NEUTRAL = "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300";

const CLASSIFICATION_CLS: Record<Classification, string> = {
  GREEN: GREENISH,
  YELLOW: AMBER,
  RED: RED,
  PURSUE: GREENISH,
  INVESTIGATE: AMBER,
  REJECT: RED,
  IGNORE: NEUTRAL,
  COMMUNICATE: AMBER,
  CEASE_DESIST: ORANGE,
  LITIGATE: RED,
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

const ENFORCEMENT_STATUS_CLS: Record<EnforcementStatus, string> = {
  intake: NEUTRAL,
  drafting: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300",
  gated: AMBER,
  sent: GREENISH,
  responded: GREENISH,
  escalated: RED,
  closed: NEUTRAL,
};

const ASSET_STATUS_CLS: Record<AssetStatus, string> = {
  pending: AMBER,
  registered: GREENISH,
  granted: GREENISH,
  lapsed: RED,
  abandoned: NEUTRAL,
};

const BASE = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

export function ClassificationBadge({ value }: { value?: Classification | null }) {
  const t = useTranslations("ip");
  if (!value) return null;
  return (
    <span className={cn(BASE, CLASSIFICATION_CLS[value])}>
      {CLASSIFICATION_ICON[value]} {t(`badges.classification.${value}`)}
    </span>
  );
}

export function SeverityBadge({ value }: { value?: Severity | null }) {
  const t = useTranslations("ip");
  if (!value) return null;
  return (
    <span className={cn(BASE, SEVERITY_CLS[value])}>
      {SEVERITY_ICON[value]} {t(`badges.severity.${value}`)}
    </span>
  );
}

export function ReviewTypeBadge({ value }: { value: ReviewType }) {
  const t = useTranslations("ip");
  return <span className={cn(BASE, "bg-brand/10 text-brand")}>{t(`badges.reviewType.${value}`)}</span>;
}

export function IpCategoryBadge({ value }: { value?: IpCategory | null }) {
  const t = useTranslations("ip");
  if (!value) return null;
  return <span className={cn(BASE, NEUTRAL)}>{t(`badges.category.${value}`)}</span>;
}

export function EnforcementStatusBadge({ value }: { value: EnforcementStatus }) {
  const t = useTranslations("ip");
  const cls = ENFORCEMENT_STATUS_CLS[value] ?? NEUTRAL;
  return <span className={cn(BASE, cls)}>{t(`enforcement.status.${value}`)}</span>;
}

export function AssetStatusBadge({ value }: { value: AssetStatus }) {
  const t = useTranslations("ip");
  const cls = ASSET_STATUS_CLS[value] ?? NEUTRAL;
  return <span className={cn(BASE, cls)}>{t(`portfolio.assetStatus.${value}`)}</span>;
}
