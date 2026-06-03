"use client";

import { cn } from "@/lib/utils";
import type { LeaveRegistration } from "@/types/employment";

export type LeaveUrgency = "immediate" | "this_week" | "coming_up" | "no_action";

const URGENCY_META: Record<
  LeaveUrgency,
  { label: string; dot: string; ring: string }
> = {
  immediate: {
    label: "立即处理",
    dot: "bg-red-500",
    ring: "border-red-200 dark:border-red-800",
  },
  this_week: {
    label: "本周关注",
    dot: "bg-orange-500",
    ring: "border-orange-200 dark:border-orange-800",
  },
  coming_up: {
    label: "即将到期",
    dot: "bg-yellow-500",
    ring: "border-yellow-200 dark:border-yellow-800",
  },
  no_action: {
    label: "无需行动",
    dot: "bg-emerald-500",
    ring: "border-emerald-200 dark:border-emerald-800",
  },
};

export function computeLeaveUrgency(leave: LeaveRegistration): LeaveUrgency {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const dateFields = [
    leave.medical_period_end,
    leave.maternity_return_date,
    leave.work_injury_period_end,
    leave.annual_carryover_deadline,
    leave.expected_return,
  ];

  let minDays = Infinity;

  for (const field of dateFields) {
    if (!field) continue;
    const d = new Date(field);
    if (isNaN(d.getTime())) continue;
    const diff = Math.ceil((d.getTime() - today.getTime()) / 86_400_000);
    if (diff < minDays) minDays = diff;
  }

  if (minDays === Infinity) return "no_action";
  if (minDays <= 3) return "immediate";
  if (minDays <= 7) return "this_week";
  if (minDays <= 30) return "coming_up";
  return "no_action";
}

interface LeaveUrgencyBadgeProps {
  leave: LeaveRegistration;
}

export function LeaveUrgencyBadge({ leave }: LeaveUrgencyBadgeProps) {
  const urgency = computeLeaveUrgency(leave);
  const meta = URGENCY_META[urgency];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        meta.ring,
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", meta.dot)} aria-hidden />
      {meta.label}
    </span>
  );
}
