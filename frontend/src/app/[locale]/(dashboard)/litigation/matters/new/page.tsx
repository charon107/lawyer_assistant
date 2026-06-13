"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import { ArrowLeft } from "lucide-react";

const OUR_SIDE_OPTS = ["plaintiff", "defendant", "third_party"] as const;
const STAGE_OPTS = ["庭前", "证据交换", "庭审", "上诉", "执行"] as const;
const RISK_OPTS = ["低", "中", "高", "严重"] as const;
const SELECT_CLS = "border-input bg-background w-full rounded-lg border px-3 py-2 text-sm";

export default function NewMatterPage() {
  const t = useTranslations("litigation");
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    case_name: "",
    case_number: "",
    court: "",
    cause_of_action: "",
    our_side: "",
    counterparty: "",
    risk: "",
    stage: "",
    initial_theory: "",
  });

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const m = await litigationApi.createMatter(form);
      router.push(`${ROUTES.LITIGATION_MATTERS}/${m.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("matters.createError"));
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <Link
        href={ROUTES.LITIGATION_MATTERS}
        className="text-muted-foreground mb-4 inline-flex items-center gap-1 text-sm hover:underline"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> {t("matters.backToList")}
      </Link>

      <h1 className="mb-6 text-xl font-bold">{t("matters.newTitle")}</h1>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border px-4 py-2 text-sm">
          {error}
        </p>
      )}

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="case_name">{t("matters.form.caseName")} *</Label>
              <Input
                id="case_name"
                required
                value={form.case_name}
                onChange={(e) => update("case_name", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="case_number">{t("matters.form.caseNumber")}</Label>
              <Input
                id="case_number"
                value={form.case_number}
                onChange={(e) => update("case_number", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="court">{t("matters.form.court")}</Label>
              <Input id="court" value={form.court} onChange={(e) => update("court", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cause_of_action">{t("matters.form.causeOfAction")}</Label>
              <Input
                id="cause_of_action"
                value={form.cause_of_action}
                onChange={(e) => update("cause_of_action", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="our_side">{t("matters.form.ourSide")}</Label>
                <select
                  id="our_side"
                  className={SELECT_CLS}
                  value={form.our_side}
                  onChange={(e) => update("our_side", e.target.value)}
                >
                  <option value="">—</option>
                  {OUR_SIDE_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`matters.ourSideOpt.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="counterparty">{t("matters.form.counterparty")}</Label>
                <Input
                  id="counterparty"
                  value={form.counterparty}
                  onChange={(e) => update("counterparty", e.target.value)}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="risk">{t("matters.form.risk")}</Label>
                <select
                  id="risk"
                  className={SELECT_CLS}
                  value={form.risk}
                  onChange={(e) => update("risk", e.target.value)}
                >
                  <option value="">—</option>
                  {RISK_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`badges.risk.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="stage">{t("matters.form.stage")}</Label>
                <select
                  id="stage"
                  className={SELECT_CLS}
                  value={form.stage}
                  onChange={(e) => update("stage", e.target.value)}
                >
                  <option value="">—</option>
                  {STAGE_OPTS.map((o) => (
                    <option key={o} value={o}>
                      {t(`matters.stageOpt.${o}`)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="initial_theory">{t("matters.form.initialTheory")}</Label>
              <Textarea
                id="initial_theory"
                rows={3}
                value={form.initial_theory}
                onChange={(e) => update("initial_theory", e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" disabled={saving}>
              {saving ? <Spinner className="h-4 w-4" /> : t("matters.submit")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
