"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Search, Plus, Loader2 } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Spinner,
} from "@/components/ui";
import { employmentApi } from "@/lib/employment";
import { ROUTES } from "@/lib/constants";
import type { Investigation, InvestigationType } from "@/types/employment";

const STATUS_LABEL: Record<string, string> = {
  open: "已开启",
  investigating: "调查中",
  memo_draft: "备忘录起草",
  closed: "已关闭",
};

const STATUS_DOT: Record<string, string> = {
  open: "bg-blue-500",
  investigating: "bg-amber-500",
  memo_draft: "bg-purple-500",
  closed: "bg-muted-foreground/40",
};

const TYPE_OPTIONS: { value: InvestigationType; label: string }[] = [
  { value: "HR", label: "HR 调查" },
  { value: "financial", label: "财务调查" },
  { value: "executive", label: "高管调查" },
  { value: "whistleblower", label: "举报调查" },
  { value: "other", label: "其他" },
];

export default function EmploymentInvestigationsPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [allegation, setAllegation] = useState("");
  const [invType, setInvType] = useState<InvestigationType>("HR");
  const [attorneyDirected, setAttorneyDirected] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await employmentApi.listInvestigations(0, 100);
        if (!cancelled) setInvestigations(list.items);
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

  const canCreate = name.trim() && !creating;

  const handleCreate = async () => {
    if (!canCreate) return;
    setCreating(true);
    setCreateError(null);
    try {
      const created = await employmentApi.openInvestigation({
        investigation_name: name.trim(),
        allegation: allegation.trim() || undefined,
        investigation_type: invType,
        attorney_directed: attorneyDirected,
      });
      setInvestigations((prev) => [created, ...prev]);
      setOpen(false);
      setName("");
      setAllegation("");
      setInvType("HR");
      setAttorneyDirected(false);
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
          href={ROUTES.EMPLOYMENT}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回劳动用工
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
              <Search className="text-brand h-6 w-6" />
              内部调查
            </h1>
            <p className="text-muted-foreground">
              结构化调查管理：日志条目、来源清单、证据缺口、备忘录。
            </p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" />
              开启调查
            </Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>开启调查</DialogTitle>
              </DialogHeader>
              <div className="flex flex-col gap-4 pt-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="inv-name">调查名称</Label>
                  <Input
                    id="inv-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="例如：2026-Q2 举报调查"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="inv-allegation">指控/事项（可选）</Label>
                  <Input
                    id="inv-allegation"
                    value={allegation}
                    onChange={(e) => setAllegation(e.target.value)}
                    placeholder="例如：财务报销违规"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label>调查类型</Label>
                  <Select value={invType} onValueChange={(v) => setInvType(v as InvestigationType)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TYPE_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={attorneyDirected}
                    onChange={(e) => setAttorneyDirected(e.target.checked)}
                    className="h-4 w-4 rounded border"
                  />
                  律师指导调查（Attorney-Directed）
                </label>

                {createError && (
                  <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
                    {createError}
                  </p>
                )}

                <div className="flex justify-end gap-2">
                  <Button variant="ghost" onClick={() => setOpen(false)} disabled={creating}>
                    取消
                  </Button>
                  <Button onClick={handleCreate} disabled={!canCreate}>
                    {creating && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                    开启
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
      ) : investigations.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-3 rounded-xl border border-dashed px-4 py-16 text-center">
          <Search className="h-10 w-10 opacity-40" />
          <p className="text-sm">还没有调查。</p>
          <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" />
            开启第一个调查
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {investigations.map((inv) => (
            <Link
              key={inv.id}
              href={`${ROUTES.EMPLOYMENT_INVESTIGATIONS}/${inv.id}`}
              className="hover:border-brand/40 flex items-center gap-4 rounded-xl border p-4 transition-colors"
            >
              <span
                className={`h-2.5 w-2.5 shrink-0 rounded-full ${STATUS_DOT[inv.status] ?? "bg-muted-foreground/40"}`}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{inv.investigation_name}</p>
                <p className="text-muted-foreground truncate text-xs">
                  {inv.investigation_type || "未分类"}
                  {inv.allegation && ` · ${inv.allegation}`}
                  {inv.attorney_directed && " · 律师指导"}
                </p>
              </div>
              <span className="text-muted-foreground text-xs">{STATUS_LABEL[inv.status]}</span>
              <time className="text-muted-foreground shrink-0 text-xs">
                {new Date(inv.created_at).toLocaleDateString("zh-CN")}
              </time>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
