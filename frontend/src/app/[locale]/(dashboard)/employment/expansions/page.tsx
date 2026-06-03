"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, MapPin, Plus, Loader2 } from "lucide-react";
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
import type { Expansion, EmploymentStructure } from "@/types/employment";

const STRUCTURE_LABEL: Record<string, string> = {
  direct: "直接用工",
  labor_dispatch: "劳务派遣",
  outsourcing: "业务外包",
};

const STATUS_DOT: Record<string, string> = {
  active: "bg-emerald-500",
  completed: "bg-muted-foreground/40",
  cancelled: "bg-muted-foreground/40",
};

export default function EmploymentExpansionsPage() {
  const [expansions, setExpansions] = useState<Expansion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [open, setOpen] = useState(false);
  const [province, setProvince] = useState("");
  const [headcount, setHeadcount] = useState("");
  const [structure, setStructure] = useState<EmploymentStructure>("direct");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await employmentApi.listExpansions(0, 100);
        if (!cancelled) setExpansions(list.items);
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

  const canCreate = province.trim() && !creating;

  const handleCreate = async () => {
    if (!canCreate) return;
    setCreating(true);
    setCreateError(null);
    try {
      const slug = province.trim().toLowerCase().replace(/\s+/g, "-");
      const created = await employmentApi.createExpansion({
        slug,
        province: province.trim(),
        headcount: headcount.trim() || undefined,
        employment_structure: structure,
      });
      setExpansions((prev) => [created, ...prev]);
      setOpen(false);
      setProvince("");
      setHeadcount("");
      setStructure("direct");
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
              <MapPin className="text-brand h-6 w-6" />
              异地扩张
            </h1>
            <p className="text-muted-foreground">
              省际扩张合规分析：劳动关系结构、地方法规差异、追踪事项。
            </p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" />
              新建扩张
            </Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>新建异地扩张</DialogTitle>
              </DialogHeader>
              <div className="flex flex-col gap-4 pt-2">
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="exp-province">目标省份</Label>
                  <Input
                    id="exp-province"
                    value={province}
                    onChange={(e) => setProvince(e.target.value)}
                    placeholder="例如：广东"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="exp-hc">预计人数（可选）</Label>
                  <Input
                    id="exp-hc"
                    value={headcount}
                    onChange={(e) => setHeadcount(e.target.value)}
                    placeholder="例如：10-20"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label>用工结构</Label>
                  <Select value={structure} onValueChange={(v) => setStructure(v as EmploymentStructure)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="direct">直接用工</SelectItem>
                      <SelectItem value="labor_dispatch">劳务派遣</SelectItem>
                      <SelectItem value="outsourcing">业务外包</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

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
      ) : expansions.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-3 rounded-xl border border-dashed px-4 py-16 text-center">
          <MapPin className="h-10 w-10 opacity-40" />
          <p className="text-sm">还没有异地扩张记录。</p>
          <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" />
            新建第一个扩张
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {expansions.map((exp) => (
            <Link
              key={exp.id}
              href={`${ROUTES.EMPLOYMENT_EXPANSIONS}/${exp.slug}`}
              className="hover:border-brand/40 flex items-center gap-4 rounded-xl border p-4 transition-colors"
            >
              <span
                className={`h-2.5 w-2.5 shrink-0 rounded-full ${STATUS_DOT[exp.status] ?? "bg-muted-foreground/40"}`}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{exp.province}</p>
                <p className="text-muted-foreground truncate text-xs">
                  {STRUCTURE_LABEL[exp.employment_structure ?? ""] || "未指定结构"}
                  {exp.headcount && ` · ${exp.headcount} 人`}
                </p>
              </div>
              <span className="text-muted-foreground text-xs">
                {exp.status === "active" ? "进行中" : exp.status === "completed" ? "已完成" : "已取消"}
              </span>
              <time className="text-muted-foreground shrink-0 text-xs">
                {new Date(exp.created_at).toLocaleDateString("zh-CN")}
              </time>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
