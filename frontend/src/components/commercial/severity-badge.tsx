"use client";

import { cn } from "@/lib/utils";
import type { SeverityAxis, SeverityLevel } from "@/types/commercial";

/**
 * Dual-axis severity indicator — legal risk × commercial friction.
 *
 * The commercial review scores every deviation on two independent
 * axes, so a single colored badge would lose information. We render
 * two compact chips side by side.
 */

const LEVEL_META: Record<SeverityLevel, { label: string; dot: string; text: string }> = {
  green: { label: "低", dot: "bg-emerald-500", text: "text-emerald-700 dark:text-emerald-400" },
  yellow: { label: "中", dot: "bg-amber-500", text: "text-amber-700 dark:text-amber-400" },
  orange: { label: "高", dot: "bg-orange-500", text: "text-orange-700 dark:text-orange-400" },
  red: { label: "严重", dot: "bg-red-600", text: "text-red-700 dark:text-red-400" },
};

function AxisChip({ axis, level }: { axis: string; level: SeverityLevel }) {
  const meta = LEVEL_META[level];
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs">
      <span className={cn("h-2 w-2 shrink-0 rounded-full", meta.dot)} aria-hidden />
      <span className="text-muted-foreground">{axis}</span>
      <span className={cn("font-semibold", meta.text)}>{meta.label}</span>
    </span>
  );
}

export function SeverityBadge({ severity, className }: { severity: SeverityAxis; className?: string }) {
  return (
    <div className={cn("flex flex-wrap items-center gap-1.5", className)}>
      <AxisChip axis="法律风险" level={severity.legal_risk} />
      <AxisChip axis="商业摩擦" level={severity.commercial} />
    </div>
  );
}
