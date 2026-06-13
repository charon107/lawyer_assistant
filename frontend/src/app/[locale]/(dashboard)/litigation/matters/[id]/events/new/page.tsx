"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { DeadlineStatus, EventType } from "@/types/litigation";
import { ArrowLeft } from "lucide-react";

const EVENT_TYPES: EventType[] = [
  "procedure",
  "evidence",
  "substantive",
  "strategy",
  "risk_reassessment",
  "party",
  "administrative",
  "deadline",
  "closing",
];
const DEADLINE_STATUSES: DeadlineStatus[] = ["pending", "approaching", "overdue", "met", "waived"];
const SELECT_CLS = "border-input bg-background w-full rounded-lg border px-3 py-2 text-sm";

export default function NewMatterEventPage() {
  const t = useTranslations("litigation");
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const matterHref = `${ROUTES.LITIGATION_MATTERS}/${id}`;

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    event_type: "procedure" as EventType,
    event_date: "",
    summary: "",
    due_date: "",
    deadline_status: "",
  });

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await litigationApi.createMatterEvent(id, {
        event_type: form.event_type,
        event_date: form.event_date || undefined,
        summary: form.summary.trim() || undefined,
        due_date: form.due_date || undefined,
        deadline_status: form.deadline_status || undefined,
      });
      router.push(matterHref);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("matters.events.createError"));
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link
        href={matterHref}
        className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> {t("matters.events.backToMatter")}
      </Link>

      <h1 className="mb-6 text-xl font-bold">{t("matters.events.newTitle")}</h1>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border px-4 py-2 text-sm">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="event_type">{t("matters.events.typeLabel")} *</Label>
                <select
                  id="event_type"
                  className={SELECT_CLS}
                  value={form.event_type}
                  onChange={(e) => update("event_type", e.target.value)}
                >
                  {EVENT_TYPES.map((o) => (
                    <option key={o} value={o}>
                      {t(`matters.eventType.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="event_date">{t("matters.events.dateLabel")}</Label>
                <Input
                  id="event_date"
                  type="date"
                  value={form.event_date}
                  onChange={(e) => update("event_date", e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="summary">{t("matters.events.summaryLabel")}</Label>
              <Textarea
                id="summary"
                rows={3}
                value={form.summary}
                onChange={(e) => update("summary", e.target.value)}
                placeholder={t("matters.events.summaryPlaceholder")}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="due_date">{t("matters.events.dueDateLabel")}</Label>
                <Input
                  id="due_date"
                  type="date"
                  value={form.due_date}
                  onChange={(e) => update("due_date", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="deadline_status">{t("matters.events.deadlineStatusLabel")}</Label>
                <select
                  id="deadline_status"
                  className={SELECT_CLS}
                  value={form.deadline_status}
                  onChange={(e) => update("deadline_status", e.target.value)}
                >
                  <option value="">{t("matters.events.noneOption")}</option>
                  {DEADLINE_STATUSES.map((o) => (
                    <option key={o} value={o}>
                      {t(`matters.deadlineStatus.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={saving}>
              {saving ? <Spinner className="h-4 w-4" /> : t("matters.events.submit")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
