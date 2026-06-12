"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationAnalysis } from "@/types/litigation";
import { ArrowLeft } from "lucide-react";

export default function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<LitigationAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setAnalysis(await litigationApi.getAnalysis(id)); }
      catch { router.push(ROUTES.LITIGATION_ANALYSES); }
      finally { setLoading(false); }
    })();
  }, [id, router]);

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><Spinner className="text-brand h-6 w-6" /></div>;
  if (!analysis) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link href={ROUTES.LITIGATION_ANALYSES} className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline">
        <ArrowLeft className="h-3.5 w-3.5" /> 返回
      </Link>
      <Card>
        <CardContent className="p-6 space-y-4">
          <h1 className="text-xl font-bold">{analysis.analysis_type} — {analysis.subject || "未命名"}</h1>
          <div className="flex gap-2">
            {analysis.severity && <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-700 text-xs font-medium">{analysis.severity}</span>}
            {analysis.classification && <span className="rounded bg-brand/10 px-2 py-0.5 text-brand text-xs font-medium">{analysis.classification}</span>}
            <span className="text-muted-foreground text-xs">{analysis.status}</span>
          </div>
          {analysis.result_summary && <p className="text-sm font-medium">{analysis.result_summary}</p>}
          {analysis.result_memo && (
            <div className="bg-muted rounded-lg p-4 text-sm whitespace-pre-wrap max-h-[60vh] overflow-auto">
              {analysis.result_memo}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
