"use client";

import { Input, Label } from "@/components/ui";
import type { Playbook, PlaybookEntry, Side } from "@/types/commercial";

/**
 * Step 2 — the contract playbook. Phase A focuses on the three core
 * clauses (liability cap / indemnification / term); the user fills
 * standard / floor / never-accept for each. More clauses can be added
 * later from the profile settings page.
 */

export const CORE_CLAUSES: { clause_key: string; label: string }[] = [
  { clause_key: "liability_cap", label: "责任上限" },
  { clause_key: "indemnification", label: "赔偿条款" },
  { clause_key: "term", label: "合同期限" },
];

function emptyEntry(clause_key: string, label: string): PlaybookEntry {
  return { clause_key, label, standard: "", floor: "", never_accept: "" };
}

function defaultEntries(): PlaybookEntry[] {
  return CORE_CLAUSES.map((c) => emptyEntry(c.clause_key, c.label));
}

interface StepPlaybookProps {
  side: Side;
  value: Playbook | null;
  onChange: (next: Playbook) => void;
}

export function StepPlaybook({ side, value, onChange }: StepPlaybookProps) {
  const entries = value?.entries?.length ? value.entries : defaultEntries();

  const updateEntry = (index: number, patch: Partial<PlaybookEntry>) => {
    const next = entries.map((e, i) => (i === index ? { ...e, ...patch } : e));
    onChange({ side, entries: next });
  };

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="mb-1 text-lg font-semibold">合同手册（核心三条）</h2>
        <p className="text-muted-foreground text-sm">
          定义你能接受的标准、可退让的底线，以及绝不接受的红线。审查时 AI 会逐条对照。
        </p>
      </div>

      <div className="flex flex-col gap-5">
        {entries.map((entry, i) => (
          <div key={entry.clause_key} className="rounded-xl border p-4">
            <h3 className="mb-3 font-medium">{entry.label}</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor={`pb-${entry.clause_key}-standard`}>标准立场</Label>
                <Input
                  id={`pb-${entry.clause_key}-standard`}
                  value={entry.standard}
                  placeholder="如：12 个月费用"
                  onChange={(e) => updateEntry(i, { standard: e.target.value })}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor={`pb-${entry.clause_key}-floor`}>底线</Label>
                <Input
                  id={`pb-${entry.clause_key}-floor`}
                  value={entry.floor ?? ""}
                  placeholder="如：24 个月费用"
                  onChange={(e) => updateEntry(i, { floor: e.target.value })}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor={`pb-${entry.clause_key}-never`}>绝不接受</Label>
                <Input
                  id={`pb-${entry.clause_key}-never`}
                  value={entry.never_accept ?? ""}
                  placeholder="如：无限责任"
                  onChange={(e) => updateEntry(i, { never_accept: e.target.value })}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
