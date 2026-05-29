"use client";

import { Badge } from "@/components/ui";
import { SeverityBadge } from "./severity-badge";
import type { DeviationCategory, DeviationItem } from "@/types/commercial";

/**
 * One deviation between a vendor agreement and the user's playbook.
 *
 * Renders the contract quote, why it matters, and (when the agent
 * supplied them) a suggested rewrite + fallback position.
 */

const CATEGORY_META: Record<DeviationCategory, { label: string; tone: string }> = {
  missing: { label: "条款缺失", tone: "border-amber-300 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300" },
  weaker_than_standard: { label: "弱于标准", tone: "border-amber-300 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300" },
  weaker_than_floor: { label: "跌破底线", tone: "border-orange-300 bg-orange-50 text-orange-800 dark:bg-orange-950/40 dark:text-orange-300" },
  non_standard: { label: "非标准", tone: "border-stone-300 bg-stone-50 text-stone-700 dark:bg-stone-900 dark:text-stone-300" },
  unacceptable: { label: "不可接受", tone: "border-red-300 bg-red-50 text-red-800 dark:bg-red-950/40 dark:text-red-300" },
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-muted-foreground mb-1 text-[11px] font-semibold tracking-wide uppercase">{label}</p>
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}

export function DeviationCard({ item }: { item: DeviationItem }) {
  const category = CATEGORY_META[item.category] ?? CATEGORY_META.non_standard;

  return (
    <div className="rounded-xl border p-4">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{item.clause_label}</h3>
          <p className="text-muted-foreground font-mono text-[11px]">{item.clause_key}</p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${category.tone}`}>
            {category.label}
          </span>
          <SeverityBadge severity={item.severity} />
        </div>
      </div>

      <div className="grid gap-3">
        <Field label="手册立场">{item.playbook_position}</Field>
        <Field label="合同原文">
          <blockquote className="border-brand/30 text-muted-foreground border-l-2 pl-3 italic">
            {item.contract_quote}
          </blockquote>
        </Field>
        <Field label="为何重要">{item.why_it_matters}</Field>
        {item.suggested_rewrite && (
          <Field label="建议改写">
            <p className="bg-muted rounded-md p-2.5">{item.suggested_rewrite}</p>
          </Field>
        )}
        {item.fallback && (
          <Field label="退一步可接受">
            <p className="text-muted-foreground">{item.fallback}</p>
          </Field>
        )}
      </div>
    </div>
  );
}

/** Small recap chips used at the top of a finished review. */
export function ReviewBadges({
  favorable,
  missing,
}: {
  favorable: string[];
  missing: string[];
}) {
  if (favorable.length === 0 && missing.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {favorable.map((t) => (
        <Badge key={`fav-${t}`} variant="secondary" className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
          有利 · {t}
        </Badge>
      ))}
      {missing.map((t) => (
        <Badge key={`miss-${t}`} variant="outline">
          缺失 · {t}
        </Badge>
      ))}
    </div>
  );
}
