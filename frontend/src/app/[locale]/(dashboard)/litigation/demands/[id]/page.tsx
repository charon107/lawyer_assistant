"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationDemand } from "@/types/litigation";
import { ArrowLeft } from "lucide-react";

export default function DemandDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [demand, setDemand] = useState<LitigationDemand | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { setDemand(await litigationApi.getDemand(id)); }
      catch { router.push(ROUTES.LITIGATION_DEMANDS); }
      finally { setLoading(false); }
    })();
  }, [id, router]);

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><Spinner className="text-brand h-6 w-6" /></div>;
  if (!demand) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link href={ROUTES.LITIGATION_DEMANDS} className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline">
        <ArrowLeft className="h-3.5 w-3.5" /> 返回
      </Link>
      <Card>
        <CardContent className="p-6 space-y-4">
          <h1 className="text-xl font-bold">律师函 — {demand.counterparty || "未指定"}</h1>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">类型：</span>{demand.demand_type}</div>
            <div><span className="text-muted-foreground">模式：</span>{demand.mode === "send" ? "发送" : "接收"}</div>
            <div><span className="text-muted-foreground">状态：</span>{demand.status}</div>
            <div><span className="text-muted-foreground">推荐行动：</span>{demand.recommended_action || "—"}</div>
            {demand.response_deadline && <div><span className="text-muted-foreground">回复截止：</span>{demand.response_deadline}</div>}
          </div>
          {demand.letter_draft && (
            <div className="bg-muted rounded-lg p-4 text-sm whitespace-pre-wrap">{demand.letter_draft.slice(0, 2000)}{demand.letter_draft.length > 2000 ? "..." : ""}</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
