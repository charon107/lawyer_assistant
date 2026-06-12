"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationMatter, LitigationMatterEvent } from "@/types/litigation";
import { ArrowLeft, Plus } from "lucide-react";

export default function MatterDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [matter, setMatter] = useState<LitigationMatter | null>(null);
  const [events, setEvents] = useState<LitigationMatterEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [m, eList] = await Promise.all([
          litigationApi.getMatter(id),
          litigationApi.listMatterEvents(id, 0, 200),
        ]);
        setMatter(m);
        setEvents(eList.items);
      } catch { router.push(ROUTES.LITIGATION_MATTERS); }
      finally { setLoading(false); }
    })();
  }, [id, router]);

  if (loading) return <div className="flex min-h-[40vh] items-center justify-center"><Spinner className="text-brand h-6 w-6" /></div>;
  if (!matter) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link href={ROUTES.LITIGATION_MATTERS} className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline">
        <ArrowLeft className="h-3.5 w-3.5" /> 返回案件列表
      </Link>

      <Card className="mb-6">
        <CardContent className="p-6 space-y-4">
          <h1 className="text-xl font-bold">{matter.case_name || matter.case_number || "未命名案件"}</h1>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">案号：</span>{matter.case_number || "—"}</div>
            <div><span className="text-muted-foreground">法院：</span>{matter.court || "—"}</div>
            <div><span className="text-muted-foreground">当事人地位：</span>{matter.our_side || "—"}</div>
            <div><span className="text-muted-foreground">对方：</span>{matter.counterparty || "—"}</div>
            <div><span className="text-muted-foreground">状态：</span>{matter.status}</div>
            <div><span className="text-muted-foreground">阶段：</span>{matter.stage || "—"}</div>
            <div><span className="text-muted-foreground">风险：</span>{matter.risk || "—"}</div>
            <div><span className="text-muted-foreground">案由：</span>{matter.cause_of_action || "—"}</div>
            {matter.filing_date && <div><span className="text-muted-foreground">立案日：</span>{matter.filing_date}</div>}
            {matter.next_deadline && <div><span className="text-muted-foreground">下一期限：</span>{matter.next_deadline}</div>}
          </div>
          {matter.initial_theory && (
            <div className="text-sm"><span className="text-muted-foreground">案件理论：</span>{matter.initial_theory}</div>
          )}
        </CardContent>
      </Card>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold">事件时间线</h2>
        <Link href={`${ROUTES.LITIGATION_MATTERS}/${id}/events/new`}>
          <Button size="sm" variant="outline"><Plus className="mr-1 h-3.5 w-3.5" />添加事件</Button>
        </Link>
      </div>

      {events.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">暂无事件。</p>
      ) : (
        <div className="space-y-2">
          {events.map((ev) => (
            <Card key={ev.id}>
              <CardContent className="flex items-start gap-3 p-3 text-sm">
                <span className="bg-muted rounded px-1.5 py-0.5 text-xs font-medium shrink-0">{ev.event_type}</span>
                <div className="min-w-0 flex-1">
                  <p>{ev.summary || "—"}</p>
                  <p className="text-muted-foreground text-xs mt-0.5">
                    {ev.event_date || "—"}
                    {ev.deadline_status ? ` · ${ev.deadline_status}` : ""}
                    {ev.due_date ? ` · 到期: ${ev.due_date}` : ""}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
