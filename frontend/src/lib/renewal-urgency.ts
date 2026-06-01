/**
 * Client-side urgency banding for renewal registrations.
 *
 * Mirrors the backend `renewal_calc.urgency_bucket` thresholds so the
 * board and the watcher agent agree on what "red" means:
 *   red < 14 ≤ orange < 45 ≤ yellow < 90 ≤ green
 * Past-due (negative days) is red.
 *
 * The board sorts by the nearest actionable deadline. We prefer the
 * "send-by" date (when notice must actually go out) and fall back to the
 * calendar cancel date, then the effective-relative date.
 */

import type { RenewalRegistration, UrgencyBucket } from "@/types/commercial";

const RED_BELOW = 14;
const ORANGE_BELOW = 45;
const YELLOW_BELOW = 90;

const MS_PER_DAY = 1000 * 60 * 60 * 24;

export const URGENCY_ORDER: UrgencyBucket[] = ["red", "orange", "yellow", "green"];

export const URGENCY_META: Record<
  UrgencyBucket,
  { label: string; ring: string; dot: string; text: string }
> = {
  red: {
    label: "紧急",
    ring: "border-red-300 dark:border-red-900",
    dot: "bg-red-600",
    text: "text-red-700 dark:text-red-400",
  },
  orange: {
    label: "临近",
    ring: "border-orange-300 dark:border-orange-900",
    dot: "bg-orange-500",
    text: "text-orange-700 dark:text-orange-400",
  },
  yellow: {
    label: "关注",
    ring: "border-amber-300 dark:border-amber-900",
    dot: "bg-amber-500",
    text: "text-amber-700 dark:text-amber-400",
  },
  green: {
    label: "充裕",
    ring: "border-emerald-300 dark:border-emerald-900",
    dot: "bg-emerald-500",
    text: "text-emerald-700 dark:text-emerald-400",
  },
};

/** Classify days-remaining into a band. Negative (past-due) is red. */
export function urgencyBucket(daysLeft: number): UrgencyBucket {
  if (daysLeft < RED_BELOW) return "red";
  if (daysLeft < ORANGE_BELOW) return "orange";
  if (daysLeft < YELLOW_BELOW) return "yellow";
  return "green";
}

/** The deadline the board acts on: send-by → cancel-by → effective-relative. */
export function actionableDeadline(r: RenewalRegistration): string | null {
  return r.send_by_effective ?? r.cancel_by_calendar ?? r.cancel_by_effective ?? null;
}

/** Whole days from today (local midnight) until the given ISO date. */
export function daysUntil(isoDate: string): number {
  const target = new Date(isoDate);
  const today = new Date();
  const t = Date.UTC(target.getFullYear(), target.getMonth(), target.getDate());
  const n = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  return Math.round((t - n) / MS_PER_DAY);
}

export interface RenewalUrgency {
  bucket: UrgencyBucket;
  daysLeft: number | null;
  deadline: string | null;
}

/** Compute the urgency view-model for one registration. */
export function computeUrgency(r: RenewalRegistration): RenewalUrgency {
  const deadline = actionableDeadline(r);
  if (!deadline) {
    // No deadline computed (e.g. auto_renew off / no notice window) — treat
    // as low urgency so it sorts last rather than alarming the user.
    return { bucket: "green", daysLeft: null, deadline: null };
  }
  const daysLeft = daysUntil(deadline);
  return { bucket: urgencyBucket(daysLeft), daysLeft, deadline };
}
