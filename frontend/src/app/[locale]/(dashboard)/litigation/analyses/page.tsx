"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Card, CardContent, Spinner } from "@/components/ui";
import { AnalysisTypeBadge, SeverityBadge } from "@/components/litigation";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationAnalysis } from "@/types/litigation";
import { ScrollText } from "lucide-react";

export default function LitigationAnalysesPage() {
  const t = useTranslations("litigation");
  const [analyses, setAnalyses] = useState<LitigationAnalysis[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setAnalyses((await litigationApi.listAnalyses(0, 100)).items);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading)
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-bold">
        <ScrollText className="text-brand h-6 w-6" />
        {t("analyses.title")}
      </h1>
      {analyses.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-12 text-center text-sm">
          {t("analyses.empty")}
        </p>
      ) : (
        <div className="space-y-2">
          {analyses.map((a) => (
            <Link key={a.id} href={`${ROUTES.LITIGATION_ANALYSES}/${a.id}`}>
              <Card className="hover:border-brand/40 transition-colors">
                <CardContent className="flex items-center gap-3 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <AnalysisTypeBadge value={a.analysis_type} />
                      <SeverityBadge value={a.severity} />
                      <span className="text-sm font-medium">{a.subject || t("unnamed")}</span>
                    </div>
                    <p className="text-muted-foreground mt-0.5 truncate text-xs">
                      {a.result_summary || t("inProgress")}
                    </p>
                  </div>
                  <time className="text-muted-foreground shrink-0 text-xs">
                    {new Date(a.created_at).toLocaleDateString("zh-CN")}
                  </time>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
