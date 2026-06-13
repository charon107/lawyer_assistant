"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import {
  AlertCircle,
  ArrowLeft,
  Loader2,
  Plus,
  RadioTower,
} from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { MarkdownContent } from "@/components/chat";
import { ItemTypeBadge, MaterialityBadge, VerificationBadge } from "@/components/regulatory";
import { useRegulatoryChat } from "@/hooks/use-regulatory-chat";
import { ROUTES } from "@/lib/constants";
import { regulatoryApi } from "@/lib/regulatory";
import type { Materiality, RegulatoryRegItem } from "@/types/regulatory";

const TIER_ORDER: Materiality[] = ["always", "review", "fyi"];

export default function RegulatoryFeedPage() {
  const t = useTranslations("regulatory");
  const [items, setItems] = useState<RegulatoryRegItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPaste, setShowPaste] = useState(false);
  const [pasteTitle, setPasteTitle] = useState("");
  const [pasteRegulator, setPasteRegulator] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [saving, setSaving] = useState(false);

  const { streamingText, finalOutput, status, error, runSkill } = useRegulatoryChat(() => {
    void load();
  });

  const load = useCallback(async () => {
    try {
      const res = await regulatoryApi.listItems(0, 100);
      setItems(res.items);
    } catch {
      // non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const isBusy = status === "connecting" || status === "running";

  async function savePaste() {
    if (!pasteText.trim()) return;
    setSaving(true);
    try {
      await regulatoryApi.createItem({
        title: pasteTitle || pasteText.slice(0, 40),
        regulator: pasteRegulator || undefined,
        summary: pasteText,
      });
      setPasteTitle("");
      setPasteRegulator("");
      setPasteText("");
      setShowPaste(false);
      await load();
    } catch {
      // surfaced via empty state
    } finally {
      setSaving(false);
    }
  }

  const grouped = TIER_ORDER.map((tier) => ({
    tier,
    rows: items.filter((it) => it.materiality === tier),
  }));

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <div className="mb-8">
        <Link
          href={ROUTES.REGULATORY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("feed.back")}
        </Link>
        <div className="flex items-center justify-between">
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <RadioTower className="text-brand h-6 w-6" />
            {t("feed.title")}
          </h1>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowPaste((v) => !v)}>
              <Plus className="mr-1.5 h-4 w-4" />
              {t("feed.manualPaste")}
            </Button>
            <Button
              size="sm"
              disabled={isBusy}
              onClick={() => runSkill({ action: "reg_feed_watch", prompt: t("feed.checkPrompt") })}
            >
              {isBusy ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <RadioTower className="mr-1.5 h-4 w-4" />
              )}
              {t("feed.checkNow")}
            </Button>
          </div>
        </div>
        <p className="text-muted-foreground mt-1">{t("feed.description")}</p>
      </div>

      {showPaste && (
        <Card className="mb-6">
          <CardContent className="flex flex-col gap-3 p-5">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="paste-title">{t("feed.pasteTitle")}</Label>
                <Input id="paste-title" value={pasteTitle} onChange={(e) => setPasteTitle(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="paste-reg">{t("feed.pasteRegulator")}</Label>
                <Input
                  id="paste-reg"
                  value={pasteRegulator}
                  onChange={(e) => setPasteRegulator(e.target.value)}
                />
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="paste-text">{t("feed.pasteText")}</Label>
              <Textarea
                id="paste-text"
                rows={5}
                value={pasteText}
                onChange={(e) => setPasteText(e.target.value)}
                placeholder={t("feed.pastePlaceholder")}
              />
            </div>
            <div className="flex justify-end">
              <Button size="sm" onClick={savePaste} disabled={saving || !pasteText.trim()}>
                {saving ? <Spinner className="mr-1.5 h-4 w-4" /> : null}
                {t("feed.pasteSave")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {(status !== "idle" || error) && (
        <Card className="mb-6">
          <CardContent className="p-5">
            <div className="text-muted-foreground mb-2 flex items-center gap-2 text-sm">
              {isBusy && <Loader2 className="text-brand h-4 w-4 animate-spin" />}
              {status === "running" && t("feed.checking")}
              {status === "done" && t("feed.checkDone")}
              {status === "error" && (
                <span className="text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </span>
              )}
            </div>
            {(finalOutput || streamingText) && (
              <div className="prose-sm max-w-none text-sm leading-relaxed">
                <MarkdownContent content={finalOutput || streamingText} />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
          {t("feed.empty")}
        </p>
      ) : (
        <div className="flex flex-col gap-6">
          {grouped.map(
            ({ tier, rows }) =>
              rows.length > 0 && (
                <section key={tier}>
                  <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold">
                    <MaterialityBadge value={tier} />
                    <span className="text-muted-foreground">({rows.length})</span>
                  </h2>
                  <ul className="flex flex-col gap-2">
                    {rows.map((it) => (
                      <li
                        key={it.id}
                        className="flex items-start gap-3 rounded-xl border p-4"
                      >
                        <div className="min-w-0 flex-1">
                          <div className="mb-1 flex flex-wrap items-center gap-2">
                            <ItemTypeBadge value={it.item_type} />
                            <VerificationBadge verified={it.status_verified} />
                            {it.source_tag && (
                              <span className="text-muted-foreground text-xs">{it.source_tag}</span>
                            )}
                          </div>
                          <p className="truncate text-sm font-medium">{it.title || t("unnamed")}</p>
                          <p className="text-muted-foreground truncate text-xs">
                            {it.regulator || "—"}
                            {it.summary ? ` · ${it.summary}` : ""}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </section>
              ),
          )}
        </div>
      )}
    </div>
  );
}
