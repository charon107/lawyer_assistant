"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { AnalysisTypeBadge, NotificationArea, SeverityBadge } from "@/components/regulatory";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type {
  RegulatoryAnalysis,
  RegulatoryModuleStatusResponse,
} from "@/types/regulatory";
import {
  Landmark,
  RadioTower,
  GitCompareArrows,
  FileSearch,
  ListChecks,
  MessagesSquare,
  ScrollText,
  ArrowRight,
  Sparkles,
  Settings2,
  type LucideIcon,
} from "lucide-react";

const QUICK_ACTIONS: { href: string; icon: LucideIcon; key: string }[] = [
  { href: ROUTES.REGULATORY_FEED, icon: RadioTower, key: "feed" },
  { href: ROUTES.REGULATORY_POLICY_DIFF, icon: GitCompareArrows, key: "policyDiff" },
  { href: ROUTES.REGULATORY_GAPS, icon: ListChecks, key: "gaps" },
  { href: ROUTES.REGULATORY_COMMENTS, icon: MessagesSquare, key: "comments" },
  { href: ROUTES.REGULATORY_POLICY_REDRAFT, icon: FileSearch, key: "policyRedraft" },
  { href: ROUTES.REGULATORY_ANALYSES, icon: ScrollText, key: "analyses" },
  { href: ROUTES.REGULATORY_SETTINGS, icon: Settings2, key: "settings" },
];

export default function RegulatoryPage() {
  const t = useTranslations("regulatory");
  const router = useRouter();
  const [status, setStatus] = useState<RegulatoryModuleStatusResponse | null>(null);
  const [analyses, setAnalyses] = useState<RegulatoryAnalysis[]>([]);
  const [openGaps, setOpenGaps] = useState(0);
  const [pendingComments, setPendingComments] = useState(0);
  const [itemCount, setItemCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await regulatoryApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        if (s.configured) {
          const [aList, gaps, comments, items] = await Promise.all([
            regulatoryApi.listAnalyses(0, 6),
            regulatoryApi.gapStatusReport(),
            regulatoryApi.listComments(0, 1),
            regulatoryApi.listItems(0, 1),
          ]);
          if (!cancelled) {
            setAnalyses(aList.items);
            setOpenGaps(gaps.overdue.length + gaps.due_soon.length + gaps.open_gaps.length);
            setPendingComments(comments.pending_within_30d);
            setItemCount(items.total);
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t("inProgress"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [t]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Landmark className="text-brand h-6 w-6" />
          {t("title")}
        </h1>
        <p className="text-muted-foreground">{t("description")}</p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {!status?.configured ? (
        <Card className="border-brand/20 bg-brand/5">
          <CardContent className="flex flex-col items-start gap-4 p-6">
            <div className="bg-brand/10 flex h-11 w-11 items-center justify-center rounded-xl">
              <Sparkles className="text-brand h-5 w-5" />
            </div>
            <div>
              <h2 className="mb-1 text-lg font-semibold">{t("unconfiguredTitle")}</h2>
              <p className="text-muted-foreground text-sm">{t("unconfiguredDesc")}</p>
            </div>
            <Button onClick={() => router.push(ROUTES.REGULATORY_SETUP)}>
              {t("startSetup")}
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <NotificationArea />

          <div className="mb-6 grid grid-cols-3 gap-3">
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold">{itemCount}</p>
                <p className="text-muted-foreground text-xs">{t("stats.items")}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-destructive text-2xl font-bold">{openGaps}</p>
                <p className="text-muted-foreground text-xs">{t("stats.openGaps")}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-amber-500">{pendingComments}</p>
                <p className="text-muted-foreground text-xs">{t("stats.pendingComments")}</p>
              </CardContent>
            </Card>
          </div>

          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {QUICK_ACTIONS.map((a) => (
              <Link key={a.href} href={a.href}>
                <Card className="hover:border-brand/40 h-full transition-colors">
                  <CardContent className="flex flex-col gap-2 p-5">
                    <a.icon className="text-brand h-5 w-5" />
                    <h3 className="font-medium">{t(`actions.${a.key}.title`)}</h3>
                    <p className="text-muted-foreground text-sm">{t(`actions.${a.key}.desc`)}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide uppercase">{t("recentOutputs")}</h2>
              <Link href={ROUTES.REGULATORY_ANALYSES}>
                <Button variant="ghost" size="sm">
                  {t("viewAll")}
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            {analyses.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                {t("noOutputs")}
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {analyses.map((a) => (
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
          </section>
        </>
      )}
    </div>
  );
}
