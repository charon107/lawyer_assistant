"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { AlertTriangle, ArrowLeft } from "lucide-react";
import { Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { AnalysisTypeBadge, SeverityBadge, VerificationBadge } from "@/components/regulatory";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { RegulatoryAnalysis } from "@/types/regulatory";

export default function RegulatoryAnalysisDetailPage() {
  const t = useTranslations("regulatory");
  const params = useParams();
  const id = String(params.id);
  const [analysis, setAnalysis] = useState<RegulatoryAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const a = await regulatoryApi.getAnalysis(id);
        if (!cancelled) setAnalysis(a);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link
        href={ROUTES.REGULATORY_ANALYSES}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("analyses.back")}
      </Link>

      {error || !analysis ? (
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error || t("analyses.notFound")}
        </p>
      ) : (
        <>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <AnalysisTypeBadge value={analysis.analysis_type} />
            <SeverityBadge value={analysis.severity} />
            <VerificationBadge verified={analysis.status_verified} />
          </div>
          <h1 className="mb-4 text-2xl font-bold">{analysis.subject || t("unnamed")}</h1>

          {analysis.scope_limited && (
            <div className="border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200 mb-4 flex items-start gap-2 rounded-lg border px-4 py-3 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                {t("analyses.scopeLimited")}
                {analysis.scope_note ? `：${analysis.scope_note}` : ""}
              </span>
            </div>
          )}
          {!analysis.status_verified && (
            <div className="border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200 mb-4 flex items-start gap-2 rounded-lg border px-4 py-3 text-sm">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{t("analyses.statusUnverified")}</span>
            </div>
          )}

          <Card>
            <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
              <MarkdownContent content={analysis.result_memo || analysis.result_summary || ""} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
