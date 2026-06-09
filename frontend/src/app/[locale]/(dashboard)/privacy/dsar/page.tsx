"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, MailQuestion, Plus } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner } from "@/components/ui";
import { DsarStatusBadge } from "@/components/privacy";
import { ROUTES } from "@/lib/constants";
import { privacyApi } from "@/lib/privacy";
import { cn } from "@/lib/utils";
import type { DsarRequestType, PrivacyDsar } from "@/types/privacy";

export default function PrivacyDsarPage() {
  const t = useTranslations("privacy");

  const REQUEST_TYPES: { value: DsarRequestType; label: string }[] = [
    { value: "access", label: t("dsar.types.access") },
    { value: "copy", label: t("dsar.types.copy") },
    { value: "delete", label: t("dsar.types.delete") },
    { value: "correct", label: t("dsar.types.correct") },
    { value: "explain", label: t("dsar.types.explain") },
    { value: "restrict", label: t("dsar.types.restrict") },
  ];

  const [items, setItems] = useState<PrivacyDsar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [types, setTypes] = useState<DsarRequestType[]>([]);
  const [subjectRef, setSubjectRef] = useState("");
  const [received, setReceived] = useState("");
  const [verification, setVerification] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await privacyApi.listDsar(0, 100);
      setItems(res.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function toggleType(rt: DsarRequestType) {
    setTypes((prev) => (prev.includes(rt) ? prev.filter((x) => x !== rt) : [...prev, rt]));
  }

  async function handleCreate() {
    if (types.length === 0) return;
    setSubmitting(true);
    try {
      await privacyApi.createDsar({
        request_types: types,
        data_subject_ref: subjectRef.trim() || undefined,
        date_received: received || undefined,
        verification_method: verification.trim() || undefined,
      });
      setShowForm(false);
      setTypes([]);
      setSubjectRef("");
      setReceived("");
      setVerification("");
      setLoading(true);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.PRIVACY}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("back")}
      </Link>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <MailQuestion className="text-brand h-6 w-6" />
          {t("dsar.title")}
        </h1>
        <Button onClick={() => setShowForm((s) => !s)}>
          <Plus className="mr-1.5 h-4 w-4" />
          {t("dsar.newRequest")}
        </Button>
      </div>

      <p className="text-muted-foreground mb-6 text-sm">{t("dsar.description")}</p>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {showForm && (
        <Card className="mb-6">
          <CardContent className="flex flex-col gap-4 p-6">
            <div className="flex flex-col gap-1.5">
              <Label>{t("dsar.requestTypes")}</Label>
              <div className="flex flex-wrap gap-2">
                {REQUEST_TYPES.map((rt) => (
                  <button
                    key={rt.value}
                    type="button"
                    onClick={() => toggleType(rt.value)}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-sm transition-colors",
                      types.includes(rt.value)
                        ? "border-brand bg-brand/10 text-brand font-medium"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {rt.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dsar-ref">{t("dsar.subjectRef")}</Label>
                <Input
                  id="dsar-ref"
                  value={subjectRef}
                  onChange={(e) => setSubjectRef(e.target.value)}
                  placeholder={t("dsar.subjectRefPlaceholder")}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dsar-received">{t("dsar.dateReceived")}</Label>
                <Input
                  id="dsar-received"
                  type="date"
                  value={received}
                  onChange={(e) => setReceived(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="dsar-verify">{t("dsar.verificationMethod")}</Label>
                <Input
                  id="dsar-verify"
                  value={verification}
                  onChange={(e) => setVerification(e.target.value)}
                  placeholder={t("dsar.verificationPlaceholder")}
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={types.length === 0 || submitting}>
                {submitting ? t("dsar.creating") : t("dsar.createArchive")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          {t("dsar.empty")}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((d) => (
            <li key={d.id}>
              <Link
                href={`${ROUTES.PRIVACY_DSAR}/${d.id}`}
                className="hover:border-brand/40 flex items-center gap-3 rounded-xl border p-4 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1">
                    <DsarStatusBadge value={d.status} />
                  </div>
                  <p className="truncate text-sm font-medium">
                    {(d.request_types || []).join(" / ") || "Request"} · {d.data_subject_ref || "—"}
                  </p>
                  <p className="text-muted-foreground truncate text-xs">
                    {t("dsar.received")} {d.date_received || "—"}
                    {d.response_deadline ? ` · ${t("dsar.deadline")} ${d.response_deadline}` : ""}
                  </p>
                </div>
                {d.escalation_flag && (
                  <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950/40 dark:text-red-300">
                    {t("dsar.escalated")}
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
