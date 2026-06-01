"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  Loader2,
  Pencil,
} from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  Input,
  Label,
  Spinner,
  Textarea,
} from "@/components/ui";
import { cn } from "@/lib/utils";
import { commercialApi } from "@/lib/commercial";
import { ROUTES } from "@/lib/constants";
import type {
  CommercialMatter,
  CommercialMatterUpdate,
  MatterStatus,
} from "@/types/commercial";

const STATUS_META: Record<MatterStatus, { label: string; cls: string }> = {
  active: {
    label: "进行中",
    cls: "border-emerald-300 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300",
  },
  closed: {
    label: "已结束",
    cls: "border-stone-300 bg-stone-50 text-stone-600 dark:bg-stone-900/40 dark:text-stone-300",
  },
  archived: {
    label: "已归档",
    cls: "border-stone-300 bg-stone-50 text-stone-500 dark:bg-stone-900/40 dark:text-stone-400",
  },
};

const STATUS_OPTIONS: { value: MatterStatus; label: string }[] = [
  { value: "active", label: "进行中" },
  { value: "closed", label: "已结束" },
  { value: "archived", label: "已归档" },
];

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-muted-foreground text-xs">{label}</span>
      <span className="text-sm">{value || <span className="text-muted-foreground">—</span>}</span>
    </div>
  );
}

export default function CommercialMatterDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const [matter, setMatter] = useState<CommercialMatter | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<CommercialMatterUpdate>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const m = await commercialApi.getMatter(id);
        if (!cancelled) setMatter(m);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const startEdit = () => {
    if (!matter) return;
    setDraft({
      counterparty: matter.counterparty,
      matter_name: matter.matter_name,
      agreement_type: matter.agreement_type,
      status: matter.status,
      owner: matter.owner,
      notes: matter.notes,
    });
    setSaveError(null);
    setEditing(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await commercialApi.updateMatter(id, draft);
      setMatter(updated);
      setEditing(false);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  if (error || !matter) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <Link
          href={ROUTES.COMMERCIAL_MATTERS}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回事项列表
        </Link>
        <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
          {error || "事项不存在"}
        </p>
      </div>
    );
  }

  const status = STATUS_META[matter.status];
  const title = matter.matter_name || matter.counterparty || "未命名事项";

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link
        href={ROUTES.COMMERCIAL_MATTERS}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        返回事项列表
      </Link>

      <div className="mb-6 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="bg-brand/10 text-brand flex h-10 w-10 shrink-0 items-center justify-center rounded-lg">
            <Building2 className="h-5 w-5" />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold">{title}</h1>
              <span
                className={cn(
                  "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-xs font-medium",
                  status.cls,
                )}
              >
                {status.label}
              </span>
            </div>
            {matter.counterparty && matter.matter_name && (
              <p className="text-muted-foreground text-sm">{matter.counterparty}</p>
            )}
          </div>
        </div>
        {!editing && (
          <Button variant="outline" size="sm" onClick={startEdit}>
            <Pencil className="mr-1.5 h-4 w-4" />
            编辑
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-6">
          {editing ? (
            <div className="flex flex-col gap-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="e-counterparty">对方主体</Label>
                  <Input
                    id="e-counterparty"
                    value={draft.counterparty ?? ""}
                    onChange={(e) =>
                      setDraft((d) => ({ ...d, counterparty: e.target.value }))
                    }
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="e-name">事项名称</Label>
                  <Input
                    id="e-name"
                    value={draft.matter_name ?? ""}
                    onChange={(e) =>
                      setDraft((d) => ({ ...d, matter_name: e.target.value }))
                    }
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="e-type">协议类型</Label>
                  <Input
                    id="e-type"
                    value={draft.agreement_type ?? ""}
                    onChange={(e) =>
                      setDraft((d) => ({ ...d, agreement_type: e.target.value }))
                    }
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="e-owner">负责人</Label>
                  <Input
                    id="e-owner"
                    value={draft.owner ?? ""}
                    onChange={(e) => setDraft((d) => ({ ...d, owner: e.target.value }))}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="e-status">状态</Label>
                  <select
                    id="e-status"
                    value={draft.status ?? "active"}
                    onChange={(e) =>
                      setDraft((d) => ({ ...d, status: e.target.value as MatterStatus }))
                    }
                    className="border-border bg-background h-9 rounded-md border px-3 text-sm"
                  >
                    {STATUS_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="e-notes">备注</Label>
                <Textarea
                  id="e-notes"
                  rows={3}
                  value={draft.notes ?? ""}
                  onChange={(e) => setDraft((d) => ({ ...d, notes: e.target.value }))}
                />
              </div>

              {saveError && (
                <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
                  {saveError}
                </p>
              )}

              <div className="flex justify-end gap-2">
                <Button
                  variant="ghost"
                  onClick={() => setEditing(false)}
                  disabled={saving}
                >
                  取消
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  {saving && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                  保存
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2">
              <Field label="对方主体" value={matter.counterparty} />
              <Field label="事项名称" value={matter.matter_name} />
              <Field label="协议类型" value={matter.agreement_type} />
              <Field label="负责人" value={matter.owner} />
              <div className="sm:col-span-2">
                <Field label="备注" value={matter.notes} />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
