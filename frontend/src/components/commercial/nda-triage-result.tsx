"use client";

import { ShieldCheck, ShieldAlert, ShieldX, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResultStatus } from "@/types/commercial";

/**
 * Three-color triage verdict for NDA reviews.
 *
 * NDAs are high-volume and mostly boilerplate, so the headline value is
 * a fast green / yellow / red call — "sign as-is", "negotiate first", or
 * "do not sign". The per-clause deviation cards still render below; this
 * card is the at-a-glance verdict.
 */

const TRIAGE_META: Record<
  ResultStatus,
  {
    label: string;
    sub: string;
    Icon: typeof ShieldCheck;
    cls: string;
    iconCls: string;
  }
> = {
  green: {
    label: "绿色 · 可直接签署",
    sub: "条款符合标准，无需谈判即可签署。",
    Icon: ShieldCheck,
    cls: "border-emerald-300 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/40",
    iconCls: "text-emerald-600 dark:text-emerald-400",
  },
  yellow: {
    label: "黄色 · 需谈判后签署",
    sub: "存在需要协商的条款，请先处理偏差再签署。",
    Icon: ShieldAlert,
    cls: "border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/40",
    iconCls: "text-amber-600 dark:text-amber-400",
  },
  red: {
    label: "红色 · 不建议签署",
    sub: "包含不可接受的条款，需重大修改或升级处理。",
    Icon: ShieldX,
    cls: "border-red-300 bg-red-50 dark:border-red-900 dark:bg-red-950/40",
    iconCls: "text-red-600 dark:text-red-400",
  },
  in_progress: {
    label: "三色分流中……",
    sub: "AI 正在评估保密协议条款。",
    Icon: Loader2,
    cls: "border-border bg-muted/40",
    iconCls: "text-muted-foreground animate-spin",
  },
};

export function NdaTriageResult({
  status,
  summary,
  className,
}: {
  status: ResultStatus;
  summary?: string | null;
  className?: string;
}) {
  const meta = TRIAGE_META[status];
  const { Icon } = meta;
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border p-4",
        meta.cls,
        className,
      )}
    >
      <Icon className={cn("mt-0.5 h-6 w-6 shrink-0", meta.iconCls)} aria-hidden />
      <div className="flex flex-col gap-0.5">
        <span className="text-sm font-semibold">{meta.label}</span>
        <span className="text-muted-foreground text-sm">{summary || meta.sub}</span>
      </div>
    </div>
  );
}
