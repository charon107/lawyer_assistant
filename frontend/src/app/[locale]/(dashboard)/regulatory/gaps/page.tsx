"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, Eye, ListChecks } from "lucide-react";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { GapTypeBadge, SeverityBadge } from "@/components/regulatory";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { RegulatoryGap, RegulatoryGapStatusReport } from "@/types/regulatory";

type BucketKey = "overdue" | "due_soon" | "open_gaps" | "in_progress" | "observations" | "recently_closed";

const BUCKETS: { key: BucketKey; tone: string }[] = [
  { key: "overdue", tone: "text-destructive" },
  { key: "due_soon", tone: "text-orange-500" },
  { key: "open_gaps", tone: "text-amber-500" },
  { key: "in_progress", tone: "text-blue-500" },
  { key: "observations", tone: "text-purple-500" },
  { key: "recently_closed", tone: "text-emerald-500" },
];

export default function RegulatoryGapsPage() {
  const t = useTranslations("regulatory");
  const [report, setReport] = useState<RegulatoryGapStatusReport | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setReport(await regulatoryApi.gapStatusReport());
    } catch {
      // non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function closeGap(gap: RegulatoryGap) {
    const resolution = window.prompt(t("gaps.closePrompt"));
    if (!resolution) return;
    await regulatoryApi.closeGap(gap.id, { resolution });
    await load();
  }

  async function acceptGap(gap: RegulatoryGap) {
    const accepted_by = window.prompt(t("gaps.acceptByPrompt"));
    if (!accepted_by) return;
    const accepted_rationale = window.prompt(t("gaps.acceptRationalePrompt"));
    if (!accepted_rationale) return;
    await regulatoryApi.acceptGapRisk(gap.id, { accepted_by, accepted_rationale });
    await load();
  }

  const isObservation = (k: BucketKey) => k === "observations";
  const canAct = (k: BucketKey) =>
    k === "overdue" || k === "due_soon" || k === "open_gaps" || k === "in_progress";

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.REGULATORY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("gaps.back")}
        </Link>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <ListChecks className="text-brand h-6 w-6" />
          {t("gaps.title")}
        </h1>
        <p className="text-muted-foreground mt-1">{t("gaps.description")}</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : !report ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          {t("gaps.empty")}
        </p>
      ) : (
        <div className="flex flex-col gap-6">
          {report.suggest_dashboard && (
            <p className="border-brand/30 bg-brand/5 text-brand rounded-lg border px-4 py-2.5 text-sm">
              {t("gaps.dashboardHint")}
            </p>
          )}
          {BUCKETS.map(({ key, tone }) => {
            const rows = report[key];
            if (!rows || rows.length === 0) return null;
            return (
              <section key={key}>
                <h2 className={`mb-2 text-sm font-semibold ${tone}`}>
                  {t(`gaps.buckets.${key}`)} ({rows.length})
                  {isObservation(key) && (
                    <span className="text-muted-foreground ml-2 inline-flex items-center gap-1 font-normal">
                      <Eye className="h-3.5 w-3.5" />
                      {t("gaps.observationNote")}
                    </span>
                  )}
                </h2>
                <ul className="flex flex-col gap-2">
                  {rows.map((g) => (
                    <li key={g.id}>
                      <Card>
                        <CardContent className="flex items-start gap-3 p-4">
                          <div className="min-w-0 flex-1">
                            <div className="mb-1 flex flex-wrap items-center gap-2">
                              <GapTypeBadge value={g.gap_type} />
                              <SeverityBadge value={g.severity} />
                              {g.due && (
                                <span className="text-muted-foreground text-xs">
                                  {t("gaps.due")}: {g.due}
                                </span>
                              )}
                            </div>
                            <p className="text-sm font-medium">{g.policy_affected || t("unnamed")}</p>
                            <p className="text-muted-foreground text-xs">
                              {g.regulation_citation || g.regulation || "—"}
                              {g.owner ? ` · ${t("gaps.owner")}: ${g.owner}` : ""}
                            </p>
                            {g.requirement && (
                              <p className="text-muted-foreground mt-1 line-clamp-2 text-xs">
                                {g.requirement}
                              </p>
                            )}
                          </div>
                          {canAct(key) && (
                            <div className="flex shrink-0 flex-col gap-1.5">
                              <Button variant="outline" size="sm" onClick={() => closeGap(g)}>
                                {t("gaps.close")}
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => acceptGap(g)}>
                                {t("gaps.acceptRisk")}
                              </Button>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
