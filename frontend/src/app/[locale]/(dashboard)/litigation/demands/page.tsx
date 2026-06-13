"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { DemandModeBadge, DemandStatusBadge } from "@/components/litigation";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationDemand } from "@/types/litigation";
import { Plus, FileWarning } from "lucide-react";

export default function LitigationDemandsPage() {
  const t = useTranslations("litigation");
  const [demands, setDemands] = useState<LitigationDemand[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const d = await litigationApi.listDemands(0, 100);
        setDemands(d.items);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading)
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <FileWarning className="text-brand h-6 w-6" />
          {t("demands.title")}
        </h1>
        <Link href={ROUTES.LITIGATION_DEMANDS_NEW}>
          <Button size="sm">
            <Plus className="mr-1 h-4 w-4" />
            {t("demands.new")}
          </Button>
        </Link>
      </div>
      <div className="space-y-2">
        {demands.length === 0 ? (
          <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-12 text-center text-sm">
            {t("demands.empty")}
          </p>
        ) : (
          demands.map((d) => (
            <Link key={d.id} href={`${ROUTES.LITIGATION_DEMANDS}/${d.id}`}>
              <Card className="hover:border-brand/40 transition-colors">
                <CardContent className="flex items-center gap-4 p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">
                        {d.counterparty || t("demands.unspecifiedCounterparty")}
                      </span>
                      <DemandModeBadge value={d.mode} />
                      <DemandStatusBadge value={d.status} />
                    </div>
                    <p className="text-muted-foreground mt-0.5 text-xs">
                      {t(`demands.demandType.${d.demand_type}`)} · {d.recommended_action || "—"}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
