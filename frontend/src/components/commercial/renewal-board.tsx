"use client";

import { CalendarClock } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  computeUrgency,
  URGENCY_META,
  URGENCY_ORDER,
  type RenewalUrgency,
} from "@/lib/renewal-urgency";
import type {
  RenewalDecision,
  RenewalRegistration,
  UrgencyBucket,
} from "@/types/commercial";

/**
 * Renewal board grouped into red / orange / yellow / green columns by how
 * close the actionable deadline is. The urgency banding is computed
 * client-side from the server-stored cancel/send dates so the board agrees
 * with the renewal-watcher agent.
 */

const DECISION_META: Record<RenewalDecision, { label: string; cls: string }> = {
  pending: { label: "待决定", cls: "text-muted-foreground" },
  renew: { label: "续约", cls: "text-emerald-700 dark:text-emerald-400" },
  terminate: { label: "终止", cls: "text-red-700 dark:text-red-400" },
  renegotiate: { label: "重新谈判", cls: "text-amber-700 dark:text-amber-400" },
};

function daysLabel(u: RenewalUrgency): string {
  if (u.daysLeft === null) return "无截止日";
  if (u.daysLeft < 0) return `已逾期 ${Math.abs(u.daysLeft)} 天`;
  if (u.daysLeft === 0) return "今天截止";
  return `剩 ${u.daysLeft} 天`;
}

function RenewalRow({
  reg,
  urgency,
  onSelect,
}: {
  reg: RenewalRegistration;
  urgency: RenewalUrgency;
  onSelect?: (reg: RenewalRegistration) => void;
}) {
  const decision = DECISION_META[reg.decision];
  const title = reg.agreement_name || reg.counterparty || "未命名续约";

  return (
    <button
      type="button"
      onClick={() => onSelect?.(reg)}
      className="border-border hover:border-brand/40 hover:bg-muted/30 flex w-full flex-col items-start gap-1 rounded-md border p-3 text-left transition-colors"
    >
      <span className="line-clamp-1 text-sm font-medium">{title}</span>
      {reg.counterparty && reg.agreement_name && (
        <span className="text-muted-foreground line-clamp-1 text-xs">
          {reg.counterparty}
        </span>
      )}
      <div className="text-muted-foreground flex items-center gap-2 text-xs">
        <CalendarClock className="h-3.5 w-3.5" />
        <span>{daysLabel(urgency)}</span>
        <span className={cn("font-medium", decision.cls)}>· {decision.label}</span>
      </div>
    </button>
  );
}

export function RenewalBoard({
  renewals,
  onSelect,
}: {
  renewals: RenewalRegistration[];
  onSelect?: (reg: RenewalRegistration) => void;
}) {
  // Bucket each registration, then sort within a bucket by days-left ascending.
  const byBucket: Record<
    UrgencyBucket,
    { reg: RenewalRegistration; urgency: RenewalUrgency }[]
  > = { red: [], orange: [], yellow: [], green: [] };

  for (const reg of renewals) {
    const urgency = computeUrgency(reg);
    byBucket[urgency.bucket].push({ reg, urgency });
  }
  for (const bucket of URGENCY_ORDER) {
    byBucket[bucket].sort((a, b) => {
      const av = a.urgency.daysLeft ?? Number.POSITIVE_INFINITY;
      const bv = b.urgency.daysLeft ?? Number.POSITIVE_INFINITY;
      return av - bv;
    });
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {URGENCY_ORDER.map((bucket) => {
        const meta = URGENCY_META[bucket];
        const items = byBucket[bucket];
        return (
          <div
            key={bucket}
            className={cn("flex flex-col gap-2 rounded-lg border p-3", meta.ring)}
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-sm font-semibold">
                <span className={cn("h-2.5 w-2.5 rounded-full", meta.dot)} aria-hidden />
                {meta.label}
              </span>
              <span className="text-muted-foreground text-xs">{items.length}</span>
            </div>
            {items.length === 0 ? (
              <p className="text-muted-foreground py-4 text-center text-xs">无</p>
            ) : (
              <div className="flex flex-col gap-2">
                {items.map(({ reg, urgency }) => (
                  <RenewalRow
                    key={reg.id}
                    reg={reg}
                    urgency={urgency}
                    onSelect={onSelect}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
