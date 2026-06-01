"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Building2, Loader2, Plus } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
  Spinner,
  Textarea,
} from "@/components/ui";
import { MatterCard } from "@/components/commercial";
import { commercialApi } from "@/lib/commercial";
import { ROUTES } from "@/lib/constants";
import type { CommercialMatter } from "@/types/commercial";

/**
 * Commercial matters list.
 *
 * A "matter" is the umbrella record a counterparty's reviews and renewals
 * hang off of. This page lists them and lets the user create a new one
 * through a dialog. Each card links into the matter detail page.
 */
export default function CommercialMattersPage() {
  const [matters, setMatters] = useState<CommercialMatter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [open, setOpen] = useState(false);
  const [counterparty, setCounterparty] = useState("");
  const [matterName, setMatterName] = useState("");
  const [agreementType, setAgreementType] = useState("");
  const [owner, setOwner] = useState("");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await commercialApi.listMatters(0, 100);
        if (!cancelled) setMatters(list.items);
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

  const canCreate = (!!counterparty.trim() || !!matterName.trim()) && !creating;

  const handleCreate = async () => {
    if (!canCreate) return;
    setCreating(true);
    setCreateError(null);
    try {
      const created = await commercialApi.createMatter({
        counterparty: counterparty.trim() || undefined,
        matter_name: matterName.trim() || undefined,
        agreement_type: agreementType.trim() || undefined,
        owner: owner.trim() || undefined,
        notes: notes.trim() || undefined,
      });
      setMatters((prev) => [created, ...prev]);
      setOpen(false);
      setCounterparty("");
      setMatterName("");
      setAgreementType("");
      setOwner("");
      setNotes("");
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.COMMERCIAL}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回商事合同
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
              <Building2 className="text-brand h-6 w-6" />
              事项管理
            </h1>
            <p className="text-muted-foreground">
              按对方主体归集审查与续约，集中跟踪每个合作事项。
            </p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" />
              新建事项
            </Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>新建事项</DialogTitle>
              </DialogHeader>
              <div className="flex flex-col gap-4 pt-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="m-counterparty">对方主体</Label>
                  <Input
                    id="m-counterparty"
                    value={counterparty}
                    onChange={(e) => setCounterparty(e.target.value)}
                    placeholder="例如：某某科技有限公司"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="m-name">事项名称</Label>
                  <Input
                    id="m-name"
                    value={matterName}
                    onChange={(e) => setMatterName(e.target.value)}
                    placeholder="例如：2026 年度云服务合作"
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="m-type">协议类型</Label>
                    <Input
                      id="m-type"
                      value={agreementType}
                      onChange={(e) => setAgreementType(e.target.value)}
                      placeholder="例如：采购框架"
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="m-owner">负责人</Label>
                    <Input
                      id="m-owner"
                      value={owner}
                      onChange={(e) => setOwner(e.target.value)}
                      placeholder="可选"
                    />
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="m-notes">备注</Label>
                  <Textarea
                    id="m-notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    placeholder="可选"
                  />
                </div>

                {createError && (
                  <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
                    {createError}
                  </p>
                )}

                <p className="text-muted-foreground text-xs">
                  对方主体与事项名称至少填写一项。
                </p>

                <div className="flex justify-end gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => setOpen(false)}
                    disabled={creating}
                  >
                    取消
                  </Button>
                  <Button onClick={handleCreate} disabled={!canCreate}>
                    {creating && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                    创建
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : matters.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-3 rounded-xl border border-dashed px-4 py-16 text-center">
          <Building2 className="h-10 w-10 opacity-40" />
          <p className="text-sm">还没有事项。</p>
          <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" />
            新建第一个事项
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {matters.map((m) => (
            <MatterCard
              key={m.id}
              matter={m}
              href={`${ROUTES.COMMERCIAL_MATTERS}/${m.id}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
