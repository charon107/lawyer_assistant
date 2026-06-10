"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, BadgeCheck, Plus } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner } from "@/components/ui";
import { AssetStatusBadge } from "@/components/ip";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import { ipApi } from "@/lib/ip";
import type { AssetType, DeadlineEntry, IpPortfolioAsset, PortfolioReport } from "@/types/ip";

const ASSET_TYPES: AssetType[] = [
  "trademark",
  "patent_invention",
  "patent_utility",
  "patent_design",
  "copyright",
  "domain",
  "other",
];

const BUCKET_META: { key: string; cls: string }[] = [
  { key: "grace_lapsed", cls: "border-red-300 bg-red-50 dark:bg-red-950/20" },
  { key: "due_30", cls: "border-orange-300 bg-orange-50 dark:bg-orange-950/20" },
  { key: "due_60", cls: "border-amber-300 bg-amber-50 dark:bg-amber-950/20" },
  { key: "due_90", cls: "border-yellow-300 bg-yellow-50 dark:bg-yellow-950/20" },
  { key: "agent_managed", cls: "border-blue-300 bg-blue-50 dark:bg-blue-950/20" },
  { key: "unknown", cls: "border-stone-300 bg-stone-50 dark:bg-stone-900/20" },
];

export default function IpPortfolioPage() {
  const t = useTranslations("ip");
  const [assets, setAssets] = useState<IpPortfolioAsset[]>([]);
  const [report, setReport] = useState<PortfolioReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);

  const [assetType, setAssetType] = useState<AssetType>("trademark");
  const [title, setTitle] = useState("");
  const [jurisdiction, setJurisdiction] = useState("CN");
  const [regDate, setRegDate] = useState("");
  const [filingDate, setFilingDate] = useState("");

  const load = () => {
    setLoading(true);
    Promise.all([ipApi.listPortfolio(0, 200), ipApi.portfolioReport()])
      .then(([list, rep]) => {
        setAssets(list.items);
        setReport(rep);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      await ipApi.createPortfolioAsset({
        asset_type: assetType,
        title: title.trim() || null,
        jurisdiction: jurisdiction.trim() || null,
        registration_date: regDate || null,
        filing_date: filingDate || null,
      });
      setTitle("");
      setRegDate("");
      setFilingDate("");
      setShowForm(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    } finally {
      setCreating(false);
    }
  };

  const renderBucket = (key: string, entries: DeadlineEntry[], cls: string) => {
    if (!entries || entries.length === 0) return null;
    return (
      <div key={key} className={cn("rounded-xl border p-4", cls)}>
        <h3 className="mb-2 text-sm font-semibold">
          {t(`portfolio.buckets.${key}`)}（{entries.length}）
        </h3>
        <ul className="flex flex-col gap-1.5">
          {entries.map((e, i) => (
            <li key={`${e.id}-${i}`} className="text-sm">
              <span className="font-medium">{e.title || e.id}</span>
              <span className="text-muted-foreground">
                {" "}
                · {e.jurisdiction || "—"} · {e.deadline_type}
                {e.due_date ? ` · ${t("portfolio.due")} ${e.due_date}` : ""}
              </span>
            </li>
          ))}
        </ul>
      </div>
    );
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
          <BadgeCheck className="text-brand h-6 w-6" />
          {t("portfolio.title")}
        </h1>
        <Button onClick={() => setShowForm((v) => !v)} variant={showForm ? "ghost" : "default"}>
          <Plus className="mr-1.5 h-4 w-4" />
          {t("portfolio.addAsset")}
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
              <Label>{t("portfolio.assetTypeLabel")}</Label>
              <div className="flex flex-wrap gap-2">
                {ASSET_TYPES.map((at) => (
                  <button
                    key={at}
                    type="button"
                    onClick={() => setAssetType(at)}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-sm transition-colors",
                      assetType === at
                        ? "border-brand bg-brand/10 text-brand font-medium"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {t(`portfolio.assetType.${at}`)}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="p-title">{t("portfolio.assetTitleLabel")}</Label>
                <Input id="p-title" value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="p-juris">{t("portfolio.jurisdictionLabel")}</Label>
                <Input
                  id="p-juris"
                  value={jurisdiction}
                  onChange={(e) => setJurisdiction(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="p-reg">{t("portfolio.registrationDateLabel")}</Label>
                <Input
                  id="p-reg"
                  type="date"
                  value={regDate}
                  onChange={(e) => setRegDate(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="p-file">{t("portfolio.filingDateLabel")}</Label>
                <Input
                  id="p-file"
                  type="date"
                  value={filingDate}
                  onChange={(e) => setFilingDate(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleCreate} disabled={creating}>
                {creating && <Spinner className="mr-1.5 h-4 w-4" />}
                {t("portfolio.save")}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex min-h-[30vh] items-center justify-center">
          <Spinner className="text-brand h-6 w-6" />
        </div>
      ) : (
        <>
          {report && report.summary && (
            <section className="mb-8">
              <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
                {t("portfolio.renewalReport")}
              </h2>
              <div className="flex flex-col gap-3">
                {BUCKET_META.map((b) => renderBucket(b.key, report.buckets[b.key] ?? [], b.cls))}
                {BUCKET_META.every((b) => (report.buckets[b.key] ?? []).length === 0) && (
                  <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-6 text-center text-sm">
                    {t("portfolio.noUpcoming")}
                  </p>
                )}
              </div>
            </section>
          )}

          <section>
            <h2 className="mb-3 text-sm font-semibold tracking-wide uppercase">
              {t("portfolio.register")}
            </h2>
            {assets.length === 0 ? (
              <p className="text-muted-foreground rounded-xl border border-dashed px-4 py-10 text-center text-sm">
                {t("portfolio.empty")}
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {assets.map((a) => (
                  <li
                    key={a.id}
                    className="flex items-start gap-3 rounded-xl border p-4"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <span className="bg-brand/10 text-brand inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium">
                          {t(`portfolio.assetType.${a.asset_type}`)}
                        </span>
                        <AssetStatusBadge value={a.status} />
                        <span className="text-muted-foreground text-xs">{a.jurisdiction || "—"}</span>
                      </div>
                      <p className="truncate text-sm font-medium">{a.title || t("portfolio.unnamed")}</p>
                      {(a.registration_date || a.filing_date) && (
                        <p className="text-muted-foreground text-xs">
                          {a.registration_date
                            ? `${t("portfolio.registrationDateLabel")}: ${a.registration_date}`
                            : `${t("portfolio.filingDateLabel")}: ${a.filing_date}`}
                        </p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
