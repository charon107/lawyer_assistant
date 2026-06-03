"use client";

import type { ReviewType } from "@/types/employment";

const REVIEW_TYPE_OPTIONS: { value: ReviewType; label: string; hint: string }[] = [
  { value: "hiring", label: "录用审查", hint: "入职前合规审查" },
  { value: "termination", label: "解除审查", hint: "高风险标记 + 补偿金" },
  { value: "worker_classification", label: "劳动关系认定", hint: "劳务/承揽/劳动" },
  { value: "policy", label: "制度起草", hint: "规章制度合规审查" },
  { value: "wage_hour", label: "工资工时", hint: "加班费/最低工资/工时" },
  { value: "handbook", label: "员工手册更新", hint: "手册条款对照更新" },
];

interface ReviewTypeSelectorProps {
  value: ReviewType;
  onChange: (value: ReviewType) => void;
}

export function ReviewTypeSelector({ value, onChange }: ReviewTypeSelectorProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium">审查类型</span>
      <div className="grid gap-2 sm:grid-cols-3">
        {REVIEW_TYPE_OPTIONS.map((opt) => {
          const active = value === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              aria-pressed={active}
              className={`flex flex-col items-start gap-0.5 rounded-lg border px-3.5 py-2.5 text-left transition-colors ${
                active
                  ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                  : "border-border hover:border-brand/40"
              }`}
            >
              <span className="text-sm font-medium">{opt.label}</span>
              <span className="text-muted-foreground text-xs">{opt.hint}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
