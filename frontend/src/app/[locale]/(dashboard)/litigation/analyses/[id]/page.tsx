"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Card, CardContent, Spinner } from "@/components/ui";
import { AnalysisTypeBadge, SeverityBadge } from "@/components/litigation";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationAnalysis } from "@/types/litigation";
import { ArrowLeft } from "lucide-react";

export default function AnalysisDetailPage() {
  const t = useTranslations("litigation");
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<LitigationAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setAnalysis(await litigationApi.getAnalysis(id));
      } catch {
        router.push(ROUTES.LITIGATION_ANALYSES);
      } finally {
        setLoading(false);
      }
    })();
  }, [id, router]);

  if (loading)
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  if (!analysis) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link
        href={ROUTES.LITIGATION_ANALYSES}
        className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> {t("back")}
      </Link>
      <Card>
        <CardContent className="space-y-4 p-6">
          <div className="flex flex-wrap items-center gap-2">
            <AnalysisTypeBadge value={analysis.analysis_type} />
            <SeverityBadge value={analysis.severity} />
            <h1 className="text-xl font-bold">{analysis.subject || t("unnamed")}</h1>
          </div>
          {analysis.result_summary && <p className="text-sm font-medium">{analysis.result_summary}</p>}
          {analysis.result_memo && (
            <div className="bg-muted max-h-[60vh] overflow-auto rounded-lg p-4 text-sm whitespace-pre-wrap">
              {analysis.result_memo}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
