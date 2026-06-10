"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, Megaphone, Plus } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { EnforcementStatusBadge } from "@/components/ip";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { ipApi } from "@/lib/ip";
import type { EnforcementMode, IpEnforcement, MatterType } from "@/types/ip";

export default function IpEnforcementPage() {
  const t = useTranslations("ip");
  const router = useRouter();
  const [items, setItems] = useState<IpEnforcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [matterType, setMatterType] = useState<MatterType>("cease_desist");
  const [mode, setMode] = useState<EnforcementMode>("send");
  const [counterparty, setCounterparty] = useState("");
  const [facts, setFacts] = useState("");

  const MODE_OPTIONS: Record<MatterType, { value: EnforcementMode; label: string }[]> = {
    cease_desist: [
      { value: "send", label: t("enforcement.modes.send") },
      { value: "receive", label: t("enforcement.modes.receive") },
    ],
    takedown: [
      { value: "send", label: t("enforcement.modes.send") },
      { value: "respond", label: t("enforcement.modes.respond") },
      { value: "counter", label: t("enforcement.modes.counter") },
    ],
  };

  const load = () => {
    setLoading(true);
    ipApi
      .listEnforcement(0, 100)
      .then((res) => setItems(res.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const row = await ipApi.createEnforcement({
        matter_type: matterType,
        mode,
        counterparty: counterparty.trim() || null,
        infringement_facts: facts.trim() || null,
      });
      router.push(`${ROUTES.IP_ENFORCEMENT}/${row.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Link
        href={ROUTES.IP}
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {t("skillRunner.back")}
      </Link>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Megaphone className="text-brand h-6 w-6" />
          {t("enforcement.title")}
        </h1>
        <Button onClick={() => setShowForm((v) => !v)} variant={showForm ? "ghost" : "default"}>
          <Plus className="mr-1.5 h-4 w-4" />
          {t("enforcement.newMatter")}
        </Button>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}

      {showForm && (
        <Card className="mb-6">
          <CardContent className="flex flex-col gap-4 p-6">
            <div className="flex flex-col gap-1.5">
              <Label>{t("enforcement.typeLabel")}</Label>
              <div className="flex flex-wrap gap-2">
                {(["cease_desist", "takedown"] as MatterType[]).map((mt) => (
                  <button
                    key={mt}
                    type="button"
                    onClick={() => {
                      setMatterType(mt);
                      setMode("send");
                    }}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-sm transition-colors",
                      matterType === mt
                        ? "border-brand bg-brand/10 text-brand font-medium"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {t(`enforcement.matterType.${mt}`)}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>{t("enforcement.modeLabel")}</Label>
              <div className="flex flex-wrap gap-2">
                {MODE_OPTIONS[matterType].map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setMode(opt.value)}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-sm transition-colors",
                      mode === opt.value
                        ? "border-brand bg-brand/10 text-brand font-medium"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="cp">{t("enforcement.counterpartyLabel")}</Label>
              <Input
                id="cp"
                value={counterparty}
                onChange={(e) => setCounterparty(e.target.value)}
                placeholder={t("enforcement.counterpartyPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="facts">{t("enforcement.factsLabel")}</Label>
              <Textarea
                id="facts"
                value={facts}
                onChange={(e) => setFacts(e.target.value)}
                rows={4}
                placeholder={t("enforcement.factsPlaceholder")}
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={creating}>
                {creating && <Spinner className="mr-1.5 h-4 w-4" />}
                {t("enforcement.createAndDraft")}
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
          {t("enforcement.empty")}
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((m) => (
            <li key={m.id}>
              <Link
                href={`${ROUTES.IP_ENFORCEMENT}/${m.id}`}
                className="hover:border-brand/40 flex items-start gap-3 rounded-xl border p-4 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <span className="bg-brand/10 text-brand inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium">
                      {t(`enforcement.matterType.${m.matter_type}`)}
                    </span>
                    <span className="text-muted-foreground text-xs">
                      {t(`enforcement.modes.${m.mode}`)}
                    </span>
                    <EnforcementStatusBadge value={m.status} />
                  </div>
                  <p className="truncate text-sm font-medium">
                    {m.counterparty || t("enforcement.noCounterparty")}
                  </p>
                  {m.response_deadline && (
                    <p className="text-muted-foreground text-xs">
                      {t("enforcement.deadline")}: {m.response_deadline}
                    </p>
                  )}
                </div>
                <time className="text-muted-foreground shrink-0 text-xs">
                  {new Date(m.created_at).toLocaleDateString("zh-CN")}
                </time>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
