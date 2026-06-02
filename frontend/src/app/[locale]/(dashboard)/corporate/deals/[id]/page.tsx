"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Badge, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { corporateApi } from "@/lib/corporate";
import type {
  ClosingChecklistItem,
  CorporateDeal,
  DiligenceIssue,
  MaterialContractItem,
  VdrDocument,
} from "@/types/corporate";
import { ArrowLeft } from "lucide-react";

type Tab = "diligence" | "checklist" | "material" | "vdr";

const TABS: { key: Tab; label: string }[] = [
  { key: "diligence", label: "尽调问题" },
  { key: "checklist", label: "交割检查表" },
  { key: "material", label: "重大合同" },
  { key: "vdr", label: "数据室" },
];

const SEVERITY_VARIANT: Record<string, "destructive" | "default" | "secondary"> = {
  blocking: "destructive",
  high: "destructive",
  medium: "default",
  low: "secondary",
};

export default function CorporateDealDetailPage() {
  const params = useParams();
  const dealId = String(params.id);

  const [deal, setDeal] = useState<CorporateDeal | null>(null);
  const [tab, setTab] = useState<Tab>("diligence");
  const [diligence, setDiligence] = useState<DiligenceIssue[]>([]);
  const [checklist, setChecklist] = useState<ClosingChecklistItem[]>([]);
  const [material, setMaterial] = useState<MaterialContractItem[]>([]);
  const [vdr, setVdr] = useState<VdrDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [d, dil, chk, mat, docs] = await Promise.all([
        corporateApi.getDeal(dealId),
        corporateApi.listDiligence(dealId),
        corporateApi.listChecklist(dealId),
        corporateApi.listMaterialContracts(dealId),
        corporateApi.listVdr(dealId),
      ]);
      setDeal(d);
      setDiligence(dil.items);
      setChecklist(chk.items);
      setMaterial(mat.items);
      setVdr(docs.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [dealId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.CORPORATE_DEALS}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
      >
        <ArrowLeft className="h-4 w-4" />
        交易工作区
      </Link>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {deal && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold">{deal.code}</h1>
          <p className="text-muted-foreground text-sm">
            {deal.counterparty || "—"} · {deal.deal_type || "并购交易"} · {deal.status}
          </p>
        </div>
      )}

      <div className="mb-4 flex gap-2 border-b">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm ${
              tab === t.key
                ? "border-brand text-brand font-medium"
                : "text-muted-foreground border-transparent"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "diligence" && (
        <ul className="flex flex-col gap-2">
          {diligence.length === 0 && <Empty text="还没有尽调发现。" />}
          {diligence.map((i) => (
            <li key={i.id}>
              <Card>
                <CardContent className="flex items-start gap-3 p-4">
                  <Badge variant={SEVERITY_VARIANT[i.severity] ?? "default"}>{i.severity}</Badge>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{i.title}</p>
                    {i.finding && (
                      <p className="text-muted-foreground mt-1 text-xs">{i.finding}</p>
                    )}
                    {i.source_doc && (
                      <p className="text-muted-foreground mt-1 text-xs">来源：{i.source_doc}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      {tab === "checklist" && (
        <ul className="flex flex-col gap-2">
          {checklist.length === 0 && <Empty text="还没有交割检查表事项。" />}
          {checklist.map((c) => (
            <li key={c.id} className="flex items-center gap-3 rounded-xl border p-4">
              <Badge variant={c.blocking ? "destructive" : "secondary"}>
                {c.blocking ? "阻断" : "一般"}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{c.item}</p>
                <p className="text-muted-foreground text-xs">
                  {c.item_type} · {c.status}
                  {c.approval_threshold ? ` · ${c.approval_threshold}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}

      {tab === "material" && (
        <ul className="flex flex-col gap-2">
          {material.length === 0 && <Empty text="还没有重大合同清单条目。" />}
          {material.map((m) => (
            <li key={m.id} className="flex items-center gap-3 rounded-xl border p-4">
              <Badge variant={m.disclosed ? "default" : "secondary"}>
                {m.disclosed ? "已披露" : "待披露"}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{m.contract}</p>
                <p className="text-muted-foreground text-xs">
                  {m.counterparty || "—"}
                  {m.threshold_basis ? ` · ${m.threshold_basis}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}

      {tab === "vdr" && (
        <ul className="flex flex-col gap-2">
          {vdr.length === 0 && <Empty text="还没有数据室文档。" />}
          {vdr.map((d) => (
            <li key={d.id} className="flex items-center gap-3 rounded-xl border p-4">
              <Badge variant={d.priority === "high" ? "destructive" : "secondary"}>
                {d.priority === "high" ? "高优" : "普通"}
              </Badge>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm">{d.filename}</p>
                <p className="text-muted-foreground text-xs">
                  {d.category || "未分类"} · {d.status}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
      {text}
    </p>
  );
}
