"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type {
  LitigationModuleStatusResponse,
  LitigationAnalysis,
  PortfolioStatus,
} from "@/types/litigation";
import {
  Scale,
  FileWarning,
  FileSearch,
  Gavel,
  ShieldCheck,
  Clock,
  FileClock,
  ScrollText,
  Eye,
  ArrowRight,
  Sparkles,
  Settings2,
} from "lucide-react";

const QUICK_ACTIONS = [
  { href: ROUTES.LITIGATION_MATTERS, icon: Gavel, key: "matters", label: "案件管理", desc: "登记、更新、结案与组合概览" },
  { href: ROUTES.LITIGATION_DEMANDS, icon: FileWarning, key: "demands", label: "律师函", desc: "起草发送或接收分流" },
  { href: ROUTES.LITIGATION_ANALYSES, icon: ScrollText, key: "analyses", label: "分析产出", desc: "简报、大事记、要件分析等" },
  { href: `${ROUTES.LITIGATION}/matter-briefing`, icon: FileSearch, key: "briefing", label: "案件简报", desc: "单案深度简报" },
  { href: `${ROUTES.LITIGATION}/chronology`, icon: Clock, key: "chronology", label: "大事记", desc: "按理论标注重要性" },
  { href: `${ROUTES.LITIGATION}/claim-chart`, icon: FileClock, key: "claimChart", label: "要件分析", desc: "缺口优先 · 草案非认定" },
  { href: `${ROUTES.LITIGATION}/subpoena`, icon: ShieldCheck, key: "subpoena", label: "调查令分流", desc: "分类+异议框架" },
  { href: `${ROUTES.LITIGATION}/legal-hold`, icon: Eye, key: "legalHold", label: "证据保全", desc: "发出/更新/解除" },
  { href: ROUTES.LITIGATION_SETTINGS, icon: Settings2, key: "settings", label: "设置", desc: "画像与风险校准" },
];

export default function LitigationPage() {
  const router = useRouter();
  const [status, setStatus] = useState<LitigationModuleStatusResponse | null>(null);
  const [analyses, setAnalyses] = useState<LitigationAnalysis[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await litigationApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        if (s.configured) {
          const [aList, p] = await Promise.all([
            litigationApi.listAnalyses(0, 6),
            litigationApi.portfolioStatus(),
          ]);
          if (!cancelled) {
            setAnalyses(aList.items);
            setPortfolio(p);
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

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
          <Scale className="text-brand h-6 w-6" />
          争议解决
        </h1>
        <p className="text-muted-foreground">案件管理 · 律师函 · 证据保全 · 庭审准备</p>
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
              <h2 className="mb-1 text-lg font-semibold">尚未配置争议解决模块</h2>
              <p className="text-muted-foreground text-sm">完成冷启动设置以配置风险校准、当事人角色和文书风格。</p>
            </div>
            <Button onClick={() => router.push(ROUTES.LITIGATION_SETUP)}>
              开始设置
              <ArrowRight className="ml-1.5 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {portfolio && (
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold">{portfolio.total}</p>
                  <p className="text-muted-foreground text-xs">总案件</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold">{portfolio.active}</p>
                  <p className="text-muted-foreground text-xs">进行中</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-destructive">{portfolio.anomalies.overdue}</p>
                  <p className="text-muted-foreground text-xs">逾期待办</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-amber-500">{portfolio.anomalies.high_risk}</p>
                  <p className="text-muted-foreground text-xs">高风险</p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {QUICK_ACTIONS.map((a) => (
              <Link key={a.href} href={a.href}>
                <Card className="hover:border-brand/40 h-full transition-colors">
                  <CardContent className="flex flex-col gap-2 p-5">
                    <a.icon className="text-brand h-5 w-5" />
                    <h3 className="font-medium">{a.label}</h3>
                    <p className="text-muted-foreground text-sm">{a.desc}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold tracking-wide uppercase">
                最近分析产出
              </h2>
              <Link href={ROUTES.LITIGATION_ANALYSES}>
                <Button variant="ghost" size="sm">
                  查看全部
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </div>
            {analyses.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
                暂无分析产出。使用上方工具开始。
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {analyses.map((a) => (
                  <li key={a.id}>
                    <Link
                      href={`${ROUTES.LITIGATION_ANALYSES}/${a.id}`}
                      className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="rounded bg-brand/10 px-2 py-0.5 text-brand text-xs font-medium">
                            {a.analysis_type}
                          </span>
                          {a.severity && (
                            <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                              a.severity === "blocking" ? "bg-red-100 text-red-700" :
                              a.severity === "high" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-600"
                            }`}>
                              {a.severity}
                            </span>
                          )}
                        </div>
                        <p className="truncate text-sm font-medium">{a.subject || "未命名"}</p>
                        <p className="text-muted-foreground truncate text-xs">
                          {a.result_summary || "处理中..."}
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
