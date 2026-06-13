"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { MatterStatusBadge, RiskBadge } from "@/components/litigation";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationMatter, LitigationMatterEvent } from "@/types/litigation";
import { ArrowLeft, Plus } from "lucide-react";

export default function MatterDetailPage() {
  const t = useTranslations("litigation");
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
      } catch {
        router.push(ROUTES.LITIGATION_MATTERS);
      } finally {
        setLoading(false);
      }
    })();
  }, [id, router]);

  if (loading)
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  if (!matter) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link
        href={ROUTES.LITIGATION_MATTERS}
        className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> {t("matters.backToList")}
      </Link>

      <Card className="mb-6">
        <CardContent className="space-y-4 p-6">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-bold">
              {matter.case_name || matter.case_number || t("matters.unnamed")}
            </h1>
            <MatterStatusBadge value={matter.status} />
            <RiskBadge value={matter.risk} />
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground">{t("matters.detail.caseNumber")}：</span>
              {matter.case_number || "—"}
            </div>
            <div>
              <span className="text-muted-foreground">{t("matters.detail.court")}：</span>
              {matter.court || "—"}
            </div>
            <div>
              <span className="text-muted-foreground">{t("matters.detail.ourSide")}：</span>
              {matter.our_side || "—"}
            </div>
            <div>
              <span className="text-muted-foreground">{t("matters.detail.counterparty")}：</span>
              {matter.counterparty || "—"}
            </div>
            <div>
              <span className="text-muted-foreground">{t("matters.detail.stage")}：</span>
              {matter.stage || "—"}
            </div>
            <div>
              <span className="text-muted-foreground">{t("matters.detail.causeOfAction")}：</span>
              {matter.cause_of_action || "—"}
            </div>
            {matter.filing_date && (
              <div>
                <span className="text-muted-foreground">{t("matters.detail.filingDate")}：</span>
                {matter.filing_date}
              </div>
            )}
            {matter.next_deadline && (
              <div>
                <span className="text-muted-foreground">{t("matters.detail.nextDeadline")}：</span>
                {matter.next_deadline}
              </div>
            )}
          </div>
          {matter.initial_theory && (
            <div className="text-sm">
              <span className="text-muted-foreground">{t("matters.detail.theory")}：</span>
              {matter.initial_theory}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold">{t("matters.timeline")}</h2>
        <Link href={`${ROUTES.LITIGATION_MATTERS}/${id}/events/new`}>
          <Button size="sm" variant="outline">
            <Plus className="mr-1 h-3.5 w-3.5" />
            {t("matters.addEvent")}
          </Button>
        </Link>
      </div>

      {events.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-8 text-center text-sm">
          {t("matters.noEvents")}
        </p>
      ) : (
        <div className="space-y-2">
          {events.map((ev) => (
            <Card key={ev.id}>
              <CardContent className="flex items-start gap-3 p-3 text-sm">
                <span className="bg-muted shrink-0 rounded px-1.5 py-0.5 text-xs font-medium">
                  {t(`matters.eventType.${ev.event_type}`)}
                </span>
                <div className="min-w-0 flex-1">
                  <p>{ev.summary || "—"}</p>
                  <p className="text-muted-foreground mt-0.5 text-xs">
                    {ev.event_date || "—"}
                    {ev.deadline_status
                      ? ` · ${t(`matters.deadlineStatus.${ev.deadline_status}`)}`
                      : ""}
                    {ev.due_date ? ` · ${t("matters.due")}: ${ev.due_date}` : ""}
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
