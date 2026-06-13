"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, Check, Settings2 } from "lucide-react";
import { Button, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { RegulatoryProfile } from "@/types/regulatory";

type JsonField = "watchlist" | "policy_library" | "materiality_threshold" | "feed_config";
const JSON_FIELDS: JsonField[] = ["watchlist", "policy_library", "materiality_threshold", "feed_config"];

function toText(v: unknown): string {
  if (v == null) return "";
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return "";
  }
}

export default function RegulatorySettingsPage() {
  const t = useTranslations("regulatory");
  const [profile, setProfile] = useState<RegulatoryProfile | null>(null);
  const [drafts, setDrafts] = useState<Record<JsonField, string>>({
    watchlist: "",
    policy_library: "",
    materiality_threshold: "",
    feed_config: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const p = await regulatoryApi.getProfile();
        if (cancelled) return;
        setProfile(p);
        setDrafts({
          watchlist: toText(p.watchlist),
          policy_library: toText(p.policy_library),
          materiality_threshold: toText(p.materiality_threshold),
          feed_config: toText(p.feed_config),
        });
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function save() {
    setError(null);
    setSaved(false);
    const body: Record<string, unknown> = {};
    for (const f of JSON_FIELDS) {
      const raw = drafts[f].trim();
      if (!raw) continue;
      try {
        body[f] = JSON.parse(raw);
      } catch {
        setError(t("settings.invalidJson", { field: t(`settings.fields.${f}`) }));
        return;
      }
    }
    setSaving(true);
    try {
      const p = await regulatoryApi.updateProfile(body);
      setProfile(p);
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "error");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.REGULATORY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("settings.back")}
        </Link>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Settings2 className="text-brand h-6 w-6" />
          {t("settings.title")}
        </h1>
        <p className="text-muted-foreground mt-1">{t("settings.description")}</p>
      </div>

      {!profile ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          {t("settings.notConfigured")}
        </p>
      ) : (
        <div className="flex flex-col gap-5">
          {JSON_FIELDS.map((f) => (
            <div key={f} className="flex flex-col gap-1.5">
              <Label htmlFor={f}>{t(`settings.fields.${f}`)}</Label>
              <Textarea
                id={f}
                rows={5}
                className="font-mono text-xs"
                value={drafts[f]}
                onChange={(e) => setDrafts((d) => ({ ...d, [f]: e.target.value }))}
              />
            </div>
          ))}

          {error && (
            <p className="border-destructive/30 bg-destructive/5 text-destructive rounded-lg border px-4 py-2.5 text-sm">
              {error}
            </p>
          )}
          {saved && (
            <p className="border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300 flex items-center gap-1.5 rounded-lg border px-4 py-2.5 text-sm">
              <Check className="h-4 w-4" />
              {t("settings.saved")}
            </p>
          )}

          <div className="flex justify-end">
            <Button onClick={save} disabled={saving}>
              {saving ? <Spinner className="mr-1.5 h-4 w-4" /> : null}
              {t("settings.save")}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
