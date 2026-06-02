"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, CardContent, Input, Label, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { corporateApi } from "@/lib/corporate";
import type { CorporateDeal, DealSide } from "@/types/corporate";
import { Plus, ArrowLeft } from "lucide-react";

const SIDE_LABEL: Record<string, string> = {
  buyer: "收购方",
  seller: "出售方",
  na: "—",
};

export default function CorporateDealsPage() {
  const [deals, setDeals] = useState<CorporateDeal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // create form state
  const [code, setCode] = useState("");
  const [counterparty, setCounterparty] = useState("");
  const [side, setSide] = useState<DealSide>("buyer");

  async function load() {
    try {
      const list = await corporateApi.listDeals(0, 100);
      setDeals(list.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await corporateApi.createDeal({
        code: code.trim(),
        counterparty: counterparty.trim() || null,
        side,
      });
      setCode("");
      setCounterparty("");
      setShowForm(false);
      setLoading(true);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="w-full py-10">
      <Link
        href={ROUTES.CORPORATE}
        className="text-muted-foreground hover:text-foreground mb-6 inline-flex items-center gap-1.5 text-sm"
      >
        <ArrowLeft className="h-4 w-4" />
        公司并购
      </Link>

      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">交易工作区</h1>
          <p className="text-muted-foreground mt-1 text-sm">管理所有并购交易，按交易归集尽调与交割数据。</p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>
          <Plus className="mr-1.5 h-4 w-4" />
          新建交易
        </Button>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-8 rounded-lg border px-4 py-3 text-sm">
          {error}
        </p>
      )}

      {showForm && (
        <Card className="mb-8">
          <CardContent className="p-6">
            <form onSubmit={handleCreate} className="flex flex-col gap-5">
              <div>
                <Label htmlFor="code">交易代码 *</Label>
                <Input
                  id="code"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="如 acme-2026"
                  required
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="counterparty">对方当事人</Label>
                <Input
                  id="counterparty"
                  value={counterparty}
                  onChange={(e) => setCounterparty(e.target.value)}
                  placeholder="目标公司 / 交易对手"
                  className="mt-1.5"
                />
              </div>
              <div>
                <Label htmlFor="side">我方视角</Label>
                <select
                  id="side"
                  value={side}
                  onChange={(e) => setSide(e.target.value as DealSide)}
                  className="border-input bg-background mt-1.5 h-9 w-full rounded-md border px-3 text-sm"
                >
                  <option value="buyer">收购方</option>
                  <option value="seller">出售方</option>
                  <option value="na">不适用</option>
                </select>
              </div>
              <div className="flex gap-3 pt-1">
                <Button type="submit" disabled={creating || !code.trim()}>
                  {creating ? "创建中…" : "创建"}
                </Button>
                <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>
                  取消
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex min-h-[20vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : deals.length === 0 ? (
        <div className="rounded-xl border border-dashed px-6 py-14 text-center">
          <p className="text-muted-foreground text-sm">
            还没有交易。点击「新建交易」创建第一笔。
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
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {d.code}
                    {d.counterparty ? ` · ${d.counterparty}` : ""}
                  </p>
                  <p className="text-muted-foreground mt-0.5 truncate text-xs">
                    {SIDE_LABEL[d.side ?? "na"]} · {d.deal_type || "并购交易"} · {d.status}
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
    </div>
  );
}
