"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, ScrollText } from "lucide-react";
import { Spinner } from "@/components/ui";
import { AnalysisTypeBadge, SeverityBadge } from "@/components/regulatory";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { AnalysisType, RegulatoryAnalysis } from "@/types/regulatory";

const TABS: (AnalysisType | "all")[] = ["all", "policy_diff", "policy_redraft"];

export default function RegulatoryAnalysesPage() {
  const t = useTranslations("regulatory");
  const [items, setItems] = useState<RegulatoryAnalysis[]>([]);
  const [tab, setTab] = useState<AnalysisType | "all">("all");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (which: AnalysisType | "all") => {
    setLoading(true);
    try {
      const res = await regulatoryApi.listAnalyses(0, 50, which === "all" ? undefined : which);
      setItems(res.items);
    } catch {
      // non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(tab);
  }, [tab, load]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.REGULATORY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("analyses.back")}
        </Link>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <ScrollText className="text-brand h-6 w-6" />
          {t("analyses.title")}
        </h1>
      </div>

      <div className="mb-5 flex gap-2">
        {TABS.map((tb) => (
          <button
            key={tb}
            type="button"
            onClick={() => setTab(tb)}
            className={cn(
              "rounded-full border px-3.5 py-1.5 text-sm transition-colors",
              tab === tb ? "border-brand bg-brand/5 text-brand" : "border-border hover:border-brand/40",
            )}
          >
            {t(`analyses.tabs.${tb}`)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          {t("analyses.empty")}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((a) => (
            <li key={a.id}>
              <Link
                href={`${ROUTES.REGULATORY_ANALYSES}/${a.id}`}
                className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <AnalysisTypeBadge value={a.analysis_type} />
                    <SeverityBadge value={a.severity} />
                  </div>
                  <p className="truncate text-sm font-medium">{a.subject || t("unnamed")}</p>
                  <p className="text-muted-foreground truncate text-xs">
                    {a.result_summary || t("inProgress")}
                  </p>
                </div>
                <time className="text-muted-foreground shrink-0 text-xs">
                  {new Date(a.created_at).toLocaleDateString("zh-CN")}
                </time>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
