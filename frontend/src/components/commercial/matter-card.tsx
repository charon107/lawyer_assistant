"use client";

import Link from "next/link";
import { Building2, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CommercialMatter, MatterStatus } from "@/types/commercial";

/**
 * Compact card for one commercial matter in the list view.
 *
 * A "matter" is the umbrella record a counterparty's reviews and renewals
 * hang off of. The card is a link into the matter detail page.
 */

const STATUS_META: Record<MatterStatus, { label: string; cls: string }> = {
  active: {
    label: "进行中",
    cls: "border-emerald-300 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  },
  closed: {
    label: "已结束",
    cls: "border-stone-300 bg-stone-50 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300",
  },
  archived: {
    label: "已归档",
    cls: "border-stone-300 bg-stone-50 text-stone-500 dark:bg-stone-900/40 dark:text-stone-400",
  },
};

export function MatterCard({
  matter,
  href,
}: {
  matter: CommercialMatter;
  href: string;
}) {
  const status = STATUS_META[matter.status];
  const title = matter.matter_name || matter.counterparty || "未命名事项";

  return (
    <Link
      href={href}
      className="border-border hover:border-brand/40 group flex items-center gap-3 rounded-lg border p-4 transition-colors"
    >
      <span className="bg-brand/10 text-brand flex h-9 w-9 shrink-0 items-center justify-center rounded-md">
        <Building2 className="h-4.5 w-4.5" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{title}</span>
          <span
            className={cn(
              "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-xs font-medium",
              status.cls,
            )}
          >
            {status.label}
          </span>
        </div>
        <div className="text-muted-foreground mt-0.5 flex items-center gap-2 text-xs">
          {matter.counterparty && matter.matter_name && (
            <span className="truncate">{matter.counterparty}</span>
          )}
          {matter.agreement_type && <span>· {matter.agreement_type}</span>}
          {matter.owner && <span>· 负责人 {matter.owner}</span>}
        </div>
      </div>
      <ChevronRight className="text-muted-foreground group-hover:text-foreground h-4 w-4 shrink-0 transition-colors" />
    </Link>
  );
}
