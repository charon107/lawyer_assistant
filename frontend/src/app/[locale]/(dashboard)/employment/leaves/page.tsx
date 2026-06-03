"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CalendarClock, Plus } from "lucide-react";
import { Button, Dialog, DialogContent, DialogHeader, DialogTitle, Spinner } from "@/components/ui";
import { LeaveForm, LeaveUrgencyBadge, type LeaveFormValues } from "@/components/employment";
import { employmentApi } from "@/lib/employment";
import { ROUTES } from "@/lib/constants";
import type { LeaveRegistration } from "@/types/employment";

const LEAVE_TYPE_LABEL: Record<string, string> = {
  annual: "年休假",
  sick: "病假/医疗期",
  maternity: "产假",
  paternity: "陪产假",
  parental: "育儿假",
  marriage: "婚假",
  work_injury: "工伤假",
};

export default function EmploymentLeavesPage() {
  const [leaves, setLeaves] = useState<LeaveRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await employmentApi.listLeaves(0, 100);
        if (!cancelled) setLeaves(list.items);
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

  const handleCreate = async (data: LeaveFormValues) => {
    const created = await employmentApi.createLeave(data as unknown as Record<string, unknown>);
    setLeaves((prev) => [created, ...prev]);
    setOpen(false);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
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
              <CalendarClock className="text-brand h-6 w-6" />
              假期管理
            </h1>
            <p className="text-muted-foreground">
              登记员工假期，按紧急度分组查看，leave-tracker 自动预警到期事项。
            </p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" />
              登记假期
            </Button>
            <DialogContent className="sm:max-w-2xl">
              <DialogHeader>
                <DialogTitle>登记假期</DialogTitle>
              </DialogHeader>
              <LeaveForm onSubmit={handleCreate} onCancel={() => setOpen(false)} />
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
      ) : leaves.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-3 rounded-xl border border-dashed px-4 py-16 text-center">
          <CalendarClock className="h-10 w-10 opacity-40" />
          <p className="text-sm">还没有假期登记。</p>
          <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" />
            登记第一笔假期
          </Button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {leaves.map((lv) => (
            <div
              key={lv.id}
              className="hover:border-brand/40 flex items-center gap-4 rounded-xl border p-4 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">
                    {lv.employee_name || "未命名"} — {LEAVE_TYPE_LABEL[lv.leave_type] || lv.leave_type}
                  </span>
                  <LeaveUrgencyBadge leave={lv} />
                </div>
                <p className="text-muted-foreground mt-0.5 text-xs">
                  {lv.jurisdiction}
                  {lv.leave_start && ` · 开始 ${new Date(lv.leave_start).toLocaleDateString("zh-CN")}`}
                  {lv.expected_return && ` · 预计返岗 ${new Date(lv.expected_return).toLocaleDateString("zh-CN")}`}
                </p>
              </div>
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${
                  lv.status === "active"
                    ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                    : "border-muted bg-muted text-muted-foreground"
                }`}
              >
                {lv.status === "active" ? "进行中" : lv.status === "completed" ? "已完成" : "已取消"}
              </span>
              <time className="text-muted-foreground shrink-0 text-xs">
                {new Date(lv.created_at).toLocaleDateString("zh-CN")}
              </time>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
