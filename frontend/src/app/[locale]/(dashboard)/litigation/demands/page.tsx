"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationDemand } from "@/types/litigation";
import { Plus, FileWarning } from "lucide-react";

export default function LitigationDemandsPage() {
  const [demands, setDemands] = useState<LitigationDemand[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const d = await litigationApi.listDemands(0, 100); setDemands(d.items); }
      catch { /* ignore */ }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><Spinner className="text-brand h-6 w-6" /></div>;

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold"><FileWarning className="text-brand h-6 w-6" />律师函</h1>
        <Link href={`${ROUTES.LITIGATION_DEMANDS}/new`}>
          <Button size="sm"><Plus className="mr-1 h-4 w-4" />新建</Button>
        </Link>
      </div>
      <div className="space-y-2">
        {demands.length === 0 ? (
          <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-12 text-center text-sm">暂无律师函。</p>
        ) : demands.map((d) => (
          <Link key={d.id} href={`${ROUTES.LITIGATION_DEMANDS}/${d.id}`}>
            <Card className="hover:border-brand/40 transition-colors">
              <CardContent className="flex items-center gap-4 p-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{d.counterparty || "未指定对方"}</span>
                    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                      d.mode === "send" ? "bg-blue-100 text-blue-700" : "bg-purple-100 text-purple-700"
                    }`}>{d.mode === "send" ? "发送" : "接收"}</span>
                    <span className="text-muted-foreground text-xs">{d.status}</span>
                  </div>
                  <p className="text-muted-foreground text-xs mt-0.5">{d.demand_type} · {d.recommended_action || "—"}</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
