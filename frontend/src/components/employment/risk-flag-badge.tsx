"use client";

import { cn } from "@/lib/utils";

const FLAG_META: Record<string, { label: string; risk: string; color: "red" | "amber" | "green" }> = {
  recent_complaint: { label: "近期投诉/举报", risk: "报复索赔", color: "red" },
  protected_leave: { label: "受保护休假/医疗期", risk: "法定保护期", color: "red" },
  special_protection: { label: "特殊保护群体+时机", risk: "不得解除", color: "red" },
  whistleblower: { label: "检举/控告", risk: "打击报复", color: "red" },
  weak_evidence: { label: "书面证据薄弱", risk: "'为什么现在'", color: "amber" },
  disparate_treatment: { label: "差别对待", risk: "选择性解除", color: "amber" },
  broken_promise: { label: "合同/规章承诺", risk: "违约", color: "amber" },
  hours_misclassification: { label: "工时制度分类错误", risk: "加班费争议", color: "amber" },
};

const COLOR_CLASSES: Record<string, string> = {
  red: "border-red-300 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300",
  amber: "border-amber-300 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300",
  green: "border-emerald-300 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
};

interface RiskFlagBadgeProps {
  flagId: string;
}

export function RiskFlagBadge({ flagId }: RiskFlagBadgeProps) {
  const meta = FLAG_META[flagId];
  if (!meta) {
    return (
      <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium border-muted bg-muted text-muted-foreground">
        {flagId}
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        COLOR_CLASSES[meta.color],
      )}
      title={meta.risk}
    >
      {meta.label}
    </span>
  );
}

interface RiskFlagListProps {
  flags: string[];
}

export function RiskFlagList({ flags }: RiskFlagListProps) {
  if (!flags || flags.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {flags.map((f) => (
        <RiskFlagBadge key={f} flagId={f} />
      ))}
    </div>
  );
}
