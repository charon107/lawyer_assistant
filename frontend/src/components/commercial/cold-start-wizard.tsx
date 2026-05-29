"use client";

import { useState } from "react";
import { Button, Spinner } from "@/components/ui";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { commercialApi } from "@/lib/commercial";
import type {
  ColdStartStep,
  EscalationRule,
  Playbook,
  Side,
} from "@/types/commercial";
import { StepMode } from "./steps/step-mode";
import { StepTeam, type TeamAnswers } from "./steps/step-team";
import { StepPlaybook } from "./steps/step-playbook";
import { StepEscalation } from "./steps/step-escalation";
import { StepSeedFiles } from "./steps/step-seed-files";

/**
 * Cold-start wizard — drives the 5-step interview defined by
 * `cold_start_service`. Each "下一步" submits the current step's answers
 * via `commercialApi.submitSetupStep`, accumulating server-side. The
 * final step (4) materializes the `commercial_profiles` row.
 *
 * Answer key shapes are kept in lockstep with
 * `_compile_profile_kwargs` (backend):
 *   step 1 → team fields, step 2 → playbook_{side}, step 3 → escalation_matrix
 */

const STEP_TITLES = ["配置方式", "团队信息", "合同手册", "上报矩阵", "历史合同"];
const LAST_STEP: ColdStartStep = 4;

interface ColdStartWizardProps {
  /** Called once the final step is submitted and the profile is built. */
  onComplete: () => void;
}

export function ColdStartWizard({ onComplete }: ColdStartWizardProps) {
  const [stepIndex, setStepIndex] = useState<ColdStartStep>(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Per-step answer state.
  const [quickMode, setQuickMode] = useState(true);
  const [usedBy, setUsedBy] = useState<"lawyer" | "non_lawyer">("lawyer");
  const [team, setTeam] = useState<TeamAnswers>({ side: "purchasing" });
  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [escalation, setEscalation] = useState<EscalationRule[]>([]);

  // A playbook is stored per concrete side; "both" defaults to purchasing.
  const effectiveSide: Side = team.side === "sales" ? "sales" : "purchasing";

  const buildAnswers = (step: ColdStartStep): Record<string, unknown> => {
    switch (step) {
      case 0:
        return { used_by: usedBy };
      case 1:
        return { ...team };
      case 2: {
        const pb = playbook ?? { side: effectiveSide, entries: [] };
        return effectiveSide === "sales"
          ? { playbook_sales: pb }
          : { playbook_purchasing: pb };
      }
      case 3:
        return { escalation_matrix: escalation };
      case 4:
        return {};
      default:
        return {};
    }
  };

  const goNext = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await commercialApi.submitSetupStep({
        step: stepIndex,
        answers: buildAnswers(stepIndex),
        quick_mode: quickMode,
      });
      if (res.completed) {
        onComplete();
        return;
      }
      setStepIndex(res.step);
    } catch (e) {
      setError(e instanceof Error ? e.message : "提交失败，请重试");
    } finally {
      setSubmitting(false);
    }
  };

  const goBack = () => {
    setError(null);
    setStepIndex((prev) => (prev > 0 ? ((prev - 1) as ColdStartStep) : prev));
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Progress rail */}
      <ol className="flex items-center gap-2">
        {STEP_TITLES.map((title, i) => {
          const done = i < stepIndex;
          const active = i === stepIndex;
          return (
            <li key={title} className="flex flex-1 items-center gap-2">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-medium transition-colors",
                  done && "border-brand bg-brand text-white",
                  active && "border-brand text-brand",
                  !done && !active && "text-muted-foreground border-muted",
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </div>
              <span
                className={cn(
                  "hidden text-xs sm:block",
                  active ? "text-foreground font-medium" : "text-muted-foreground",
                )}
              >
                {title}
              </span>
              {i < STEP_TITLES.length - 1 && (
                <div className="bg-muted hidden h-px flex-1 sm:block" />
              )}
            </li>
          );
        })}
      </ol>

      {/* Step body */}
      <div className="rounded-2xl border p-6">
        {stepIndex === 0 && (
          <StepMode
            quickMode={quickMode}
            usedBy={usedBy}
            onQuickModeChange={setQuickMode}
            onUsedByChange={setUsedBy}
          />
        )}
        {stepIndex === 1 && <StepTeam value={team} onChange={setTeam} />}
        {stepIndex === 2 && (
          <StepPlaybook side={effectiveSide} value={playbook} onChange={setPlaybook} />
        )}
        {stepIndex === 3 && <StepEscalation value={escalation} onChange={setEscalation} />}
        {stepIndex === 4 && <StepSeedFiles />}
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {/* Controls */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={goBack}
          disabled={stepIndex === 0 || submitting}
        >
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          上一步
        </Button>
        <Button onClick={goNext} disabled={submitting}>
          {submitting && <Spinner className="mr-1.5 h-4 w-4" />}
          {stepIndex === LAST_STEP ? "完成配置" : "下一步"}
          {!submitting && stepIndex !== LAST_STEP && (
            <ArrowRight className="ml-1.5 h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
