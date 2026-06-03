"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MapPin, Loader2, AlertCircle } from "lucide-react";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { useEmploymentChat } from "@/hooks/use-employment-chat";
import { employmentApi } from "@/lib/employment";
import { ROUTES } from "@/lib/constants";
import type { Expansion } from "@/types/employment";

export default function ExpansionDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;

  const [expansion, setExpansion] = useState<Expansion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { streamingText, finalOutput, status: wsStatus, error: wsError, runSkill } =
    useEmploymentChat();

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    employmentApi
      .listExpansions(0, 100)
      .then((list) => {
        if (!cancelled) {
          const found = list.items.find((e) => e.slug === slug);
          setExpansion(found ?? null);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [slug]);

  const handleAnalyze = () => {
    if (!expansion) return;
    runSkill({
      action: "expansion_analyze",
      expansion_id: expansion.id,
      prompt: `分析 ${expansion.province} 的劳动用工合规要求`,
    });
  };

  const wsBusy = wsStatus === "connecting" || wsStatus === "running";

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.EMPLOYMENT_EXPANSIONS}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回扩张列表
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <MapPin className="text-brand h-6 w-6" />
          {expansion?.province || slug}
        </h1>
        {expansion && (
          <p className="text-muted-foreground text-sm">
            {expansion.employment_structure === "direct"
              ? "直接用工"
              : expansion.employment_structure === "labor_dispatch"
                ? "劳务派遣"
                : expansion.employment_structure === "outsourcing"
                  ? "业务外包"
                  : "未指定结构"}
            {expansion.headcount && ` · ${expansion.headcount} 人`}
          </p>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      )}

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive flex items-center gap-1.5 rounded-lg border px-4 py-2.5 text-sm">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      )}

      {!loading && !error && expansion && (
        <div className="flex flex-col gap-6">
          <Button onClick={handleAnalyze} disabled={wsBusy} className="w-fit">
            {wsBusy ? (
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
            ) : (
              <MapPin className="mr-1.5 h-4 w-4" />
            )}
            运行合规分析
          </Button>

          {wsError && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {wsError}
            </p>
          )}

          {(finalOutput || streamingText) && (
            <Card>
              <CardContent className="prose-sm max-w-none p-6 text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </CardContent>
            </Card>
          )}

          {/* Structure analysis (stored) */}
          {expansion.analysis_result && (
            <Card>
              <CardContent className="p-6">
                <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">结构化分析</h2>
                <pre className="text-muted-foreground overflow-auto text-xs">
                  {JSON.stringify(expansion.analysis_result, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}

          {/* Tracking items */}
          {expansion.tracking_items && expansion.tracking_items.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">追踪事项</h2>
              <div className="flex flex-col gap-2">
                {expansion.tracking_items.map((item, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-lg border px-3 py-2">
                    <span className="text-sm font-medium">{(item as Record<string, unknown>).item as string || `事项 ${i + 1}`}</span>
                    <span className="text-muted-foreground text-xs">
                      {(item as Record<string, unknown>).owner as string || ""}
                    </span>
                    <span className="text-muted-foreground text-xs">
                      {(item as Record<string, unknown>).deadline as string || ""}
                    </span>
                    <span
                      className={`ml-auto rounded-full border px-2 py-0.5 text-xs ${
                        (item as Record<string, unknown>).status === "done"
                          ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                          : "border-muted bg-muted text-muted-foreground"
                      }`}
                    >
                      {((item as Record<string, unknown>).status as string) || "pending"}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
