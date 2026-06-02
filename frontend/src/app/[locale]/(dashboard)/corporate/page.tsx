"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { corporateApi } from "@/lib/corporate";
import type {
  CorporateDeal,
  CorporateModuleStatusResponse,
} from "@/types/corporate";
import { Building2, FileSearch, Table2, ArrowRight, Briefcase } from "lucide-react";

const DEAL_STATUS_DOT: Record<string, string> = {
  active: "bg-emerald-500",
  closed: "bg-muted-foreground/40",
  archived: "bg-muted-foreground/40",
};

export default function CorporatePage() {
  const [status, setStatus] = useState<CorporateModuleStatusResponse | null>(null);
  const [deals, setDeals] = useState<CorporateDeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await corporateApi.getStatus();
        if (cancelled) return;
        setStatus(s);
        const list = await corporateApi.listDeals(0, 10);
        if (!cancelled) setDeals(list.items);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="w-full py-10">
      {/* Header */}
      <div className="mb-10">
        <h1 className="flex items-center gap-3 text-2xl font-bold tracking-tight">
          <Building2 className="text-brand h-6 w-6" />
          公司并购
        </h1>
        <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-relaxed">
          并购交易全流程：数据室尽调、表格化批量审查、重大合同披露清单与交割检查表，依据《公司法》（2024 修订）。
        </p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-8 rounded-lg border px-4 py-3 text-sm">
          {error}
        </p>
      )}

      {status && !status.configured && (
        <Card className="border-brand/20 bg-brand/5 mb-10">
          <CardContent className="p-6 text-sm leading-relaxed">
            <p className="text-muted-foreground">
              尚未完成公司并购模块配置。你仍可创建交易并开始尽调；完成冷启动配置后，
              技能将更贴合你的尽调结构与重要性阈值。
            </p>
          </CardContent>
        </Card>
      )}

      {/* Quick actions */}
      <section className="mb-10">
        <h2 className="text-foreground mb-4 text-sm font-semibold tracking-wide uppercase">
          快捷操作
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Link href={ROUTES.CORPORATE_DEALS}>
            <Card className="hover:border-brand/40 group h-full transition-colors">
              <CardContent className="flex flex-col gap-3 p-6">
                <Briefcase className="text-brand h-5 w-5" />
                <h3 className="text-sm font-semibold">交易工作区</h3>
                <p className="text-muted-foreground text-xs leading-relaxed">
                  新建并管理并购交易，按交易归集数据室、尽调发现与交割清单。
                </p>
              </CardContent>
            </Card>
          </Link>
          <Link href={ROUTES.CORPORATE_DEALS}>
            <Card className="hover:border-brand/40 group h-full transition-colors">
              <CardContent className="flex flex-col gap-3 p-6">
                <FileSearch className="text-brand h-5 w-5" />
                <h3 className="text-sm font-semibold">尽调问题提取</h3>
                <p className="text-muted-foreground text-xs leading-relaxed">
                  进入交易，用 AI 对数据室文件按类别与重要性阈值提取问题。
                </p>
              </CardContent>
            </Card>
          </Link>
          <Link href={ROUTES.CORPORATE_DEALS}>
            <Card className="hover:border-brand/40 group h-full transition-colors">
              <CardContent className="flex flex-col gap-3 p-6">
                <Table2 className="text-brand h-5 w-5" />
                <h3 className="text-sm font-semibold">表格化审查</h3>
                <p className="text-muted-foreground text-xs leading-relaxed">
                  一行一文件、一列一数据点，每格附逐字来源，导出 Excel。
                </p>
              </CardContent>
            </Card>
          </Link>
        </div>
      </section>

      {/* Recent deals */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-foreground text-sm font-semibold tracking-wide uppercase">
            近期交易
          </h2>
          <Link href={ROUTES.CORPORATE_DEALS}>
            <Button variant="ghost" size="sm">
              全部交易
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>
        {deals.length === 0 ? (
          <div className="rounded-xl border border-dashed px-6 py-12 text-center">
            <p className="text-muted-foreground text-sm">
              还没有交易。前往「交易工作区」创建第一笔并购交易。
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-3">
            {deals.map((d) => (
              <li key={d.id}>
                <Link
                  href={`${ROUTES.CORPORATE_DEALS}/${d.id}`}
                  className="hover:border-brand/40 flex items-center gap-4 rounded-xl border px-5 py-4 transition-colors"
                >
                  <span
                    className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                      DEAL_STATUS_DOT[d.status] ?? "bg-muted-foreground/40"
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      {d.code}
                      {d.counterparty ? ` · ${d.counterparty}` : ""}
                    </p>
                    <p className="text-muted-foreground mt-0.5 truncate text-xs">
                      {d.deal_type || "并购交易"}
                    </p>
                  </div>
                  <time className="text-muted-foreground shrink-0 text-xs">
                    {new Date(d.created_at).toLocaleDateString("zh-CN")}
                  </time>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
