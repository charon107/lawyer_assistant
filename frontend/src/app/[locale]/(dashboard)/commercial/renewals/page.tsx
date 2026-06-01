"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CalendarClock, Plus } from "lucide-react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  Spinner,
} from "@/components/ui";
import { RenewalBoard, RenewalForm } from "@/components/commercial";
import { commercialApi } from "@/lib/commercial";
import { ROUTES } from "@/lib/constants";
import type {
  RenewalRegistration,
  RenewalRegistrationCreate,
} from "@/types/commercial";

/**
 * Renewal board page.
 *
 * Lists every registered renewal grouped into urgency columns (red / orange
 * / yellow / green) by how close the actionable notice deadline is. New
 * renewals are registered through a dialog form; the cancel/send deadlines
 * are computed server-side from effective date + term + notice.
 */
export default function CommercialRenewalsPage() {
  const [renewals, setRenewals] = useState<RenewalRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await commercialApi.listRenewals(0, 200);
        if (!cancelled) setRenewals(list.items);
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

  const handleRegister = async (data: RenewalRegistrationCreate) => {
    const created = await commercialApi.registerRenewal(data);
    setRenewals((prev) => [created, ...prev]);
    setOpen(false);
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
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
              <CalendarClock className="text-brand h-6 w-6" />
              续约看板
            </h1>
            <p className="text-muted-foreground">
              登记续约期限，按紧急度分列提醒哪些合同要尽快决定续 / 退。
            </p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <Button onClick={() => setOpen(true)}>
              <Plus className="mr-1.5 h-4 w-4" />
              登记续约
            </Button>
            <DialogContent className="sm:max-w-2xl">
              <DialogHeader>
                <DialogTitle>登记续约</DialogTitle>
              </DialogHeader>
              <RenewalForm onSubmit={handleRegister} onCancel={() => setOpen(false)} />
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
      ) : renewals.length === 0 ? (
        <div className="text-muted-foreground flex flex-col items-center gap-3 rounded-xl border border-dashed px-4 py-16 text-center">
          <CalendarClock className="h-10 w-10 opacity-40" />
          <p className="text-sm">还没有登记任何续约。</p>
          <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" />
            登记第一笔续约
          </Button>
        </div>
      ) : (
        <RenewalBoard renewals={renewals} />
      )}
    </div>
  );
}
