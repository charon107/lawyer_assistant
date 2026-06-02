import type { ColdStartStep } from "@/types/commercial";

/**
 * Depth gates how many steps the cold-start wizard runs — mirrors the
 * backend `cold_start_service` plan:
 *   - quick → [0, 1]            (mode + team only; defaults-only profile)
 *   - full  → [0, 1, 2, 3, 4]   (adds playbook, escalation, seed files)
 *
 * Keeping this a pure function lets the wizard render its progress rail,
 * "完成配置" button, and back/next navigation off a single source of truth.
 */
export function planForMode(quickMode: boolean): ColdStartStep[] {
  return quickMode ? [0, 1] : [0, 1, 2, 3, 4];
}
