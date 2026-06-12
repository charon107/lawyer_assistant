"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationMatter, PortfolioStatus } from "@/types/litigation";
import { Plus, ArrowRight, Gavel } from "lucide-react";

export default function LitigationMattersPage() {
  const [matters, setMatters] = useState<LitigationMatter[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [mList, p] = await Promise.all([
          litigationApi.listMatters(0, 100),
          litigationApi.portfolioStatus(),
        ]);
        setMatters(mList.items);
        setPortfolio(p);
      } catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><Spinner className="text-brand h-6 w-6" /></div>;

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold"><Gavel className="text-brand h-6 w-6" />案件管理</h1>
        <Link href={`${ROUTES.LITIGATION_MATTERS}/new`}>
          <Button size="sm"><Plus className="mr-1 h-4 w-4" />新建案件</Button>
        </Link>
      </div>

      {portfolio && (
        <div className="mb-6 grid grid-cols-4 gap-3">
          {[
            ["总案件", portfolio.total],
            ["进行中", portfolio.active],
            ["高风险", portfolio.anomalies.high_risk],
            ["逾期待办", portfolio.anomalies.overdue],
          ].map(([label, val]) => (
            <Card key={label as string}>
              <CardContent className="p-4 text-center">
                <p className="text-xl font-bold">{val as number}</p>
                <p className="text-muted-foreground text-xs">{label as string}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="space-y-2">
        {matters.length === 0 ? (
          <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-12 text-center text-sm">暂无案件。</p>
        ) : (
          matters.map((m) => (
            <Link key={m.id} href={`${ROUTES.LITIGATION_MATTERS}/${m.id}`}>
              <Card className="hover:border-brand/40 transition-colors">
                <CardContent className="flex items-center gap-4 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{m.case_name || m.case_number || "未命名案件"}</span>
                      <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                        m.status === "active" ? "bg-green-100 text-green-700" :
                        m.status === "closed" ? "bg-gray-100 text-gray-600" : "bg-amber-100 text-amber-700"
                      }`}>{m.status}</span>
                      {m.risk && <span className="text-muted-foreground text-xs">风险: {m.risk}</span>}
                    </div>
                    <p className="text-muted-foreground truncate text-xs mt-0.5">
                      {[m.court, m.cause_of_action, m.counterparty].filter(Boolean).join(" · ") || "—"}
                    </p>
                  </div>
                  <ArrowRight className="text-muted-foreground h-4 w-4 shrink-0" />
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
