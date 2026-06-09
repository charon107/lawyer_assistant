"use client";

import { cn } from "@/lib/utils";
import type { Classification, DsarStatus, ReviewType, Severity } from "@/types/privacy";

const CLASSIFICATION_META: Record<Classification, { label: string; cls: string }> = {
  PROCEED: { label: "🟢 可直接推进", cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" },
  PIA_REQUIRED: { label: "🟡 需影响评估", cls: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300" },
  DPIA_MANDATORY: { label: "🟠 法定评估强制", cls: "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300" },
  STOP: { label: "🔴 停止", cls: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300" },
};

const SEVERITY_META: Record<Severity, { label: string; cls: string }> = {
  blocking: { label: "🔴 阻断", cls: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300" },
  high: { label: "🟠 高", cls: "bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-300" },
  medium: { label: "🟡 中", cls: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300" },
  low: { label: "🟢 低", cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" },
};

const REVIEW_TYPE_LABEL: Record<ReviewType, string> = {
  triage: "处理活动分诊",
  pia: "影响评估 (PIA)",
  dpa: "DPA 审查",
  gap: "法规差距分析",
  policy_sweep: "处理规则扫描",
};

const DSAR_STATUS_LABEL: Record<DsarStatus, { label: string; cls: string }> = {
  received: { label: "已收到", cls: "bg-stone-100 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300" },
  verifying: { label: "验证中", cls: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300" },
  locating: { label: "数据定位中", cls: "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300" },
  exemption_analysis: { label: "豁免分析中", cls: "bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300" },
  drafted: { label: "已起草", cls: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300" },
  responded: { label: "已回复", cls: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300" },
  escalated: { label: "已升级", cls: "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300" },
};

const BASE = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

export function TriageClassificationBadge({ value }: { value?: Classification | null }) {
  if (!value) return null;
  const meta = CLASSIFICATION_META[value];
  return <span className={cn(BASE, meta.cls)}>{meta.label}</span>;
}

export function SeverityBadge({ value }: { value?: Severity | null }) {
  if (!value) return null;
  const meta = SEVERITY_META[value];
  return <span className={cn(BASE, meta.cls)}>{meta.label}</span>;
}

export function ReviewTypeBadge({ value }: { value: ReviewType }) {
  return (
    <span className={cn(BASE, "bg-brand/10 text-brand")}>{REVIEW_TYPE_LABEL[value] ?? value}</span>
  );
}

export function DsarStatusBadge({ value }: { value: DsarStatus }) {
  const meta = DSAR_STATUS_LABEL[value] ?? DSAR_STATUS_LABEL.received;
  return <span className={cn(BASE, meta.cls)}>{meta.label}</span>;
}

export { REVIEW_TYPE_LABEL };
