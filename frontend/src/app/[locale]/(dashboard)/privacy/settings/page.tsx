"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, Loader2, Settings2 } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { privacyApi } from "@/lib/privacy";
import { ROUTES } from "@/lib/constants";

export default function PrivacySettingsPage() {
  const t = useTranslations("privacy");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [regulatory, setRegulatory] = useState("");
  const [dataResidency, setDataResidency] = useState("");
  const [dpoInfo, setDpoInfo] = useState("");
  const [profileContent, setProfileContent] = useState("");

  useEffect(() => {
    let cancelled = false;
    privacyApi
      .getProfile()
      .then((p) => {
        if (cancelled) return;
        const footprint = p.regulatory_footprint;
        setRegulatory(Array.isArray(footprint) ? footprint.join("、") : "");
        setDataResidency((p.data_residency as string) ?? "");
        setDpoInfo((p.dpo_info as string) ?? "");
        setProfileContent((p.profile_content as string) ?? "");
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const footprint = regulatory
        .split(/[、,，]/)
        .map((s) => s.trim())
        .filter(Boolean);
      await privacyApi.updateProfile({
        regulatory_footprint: footprint.length > 0 ? footprint : null,
        data_residency: dataResidency.trim() || null,
        dpo_info: dpoInfo.trim() || null,
        profile_content: profileContent.trim() || null,
      });
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

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
          href={ROUTES.PRIVACY}
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("settings.back")}
        </Link>
        <h1 className="mb-1 flex items-center gap-2 text-2xl font-bold">
          <Settings2 className="text-brand h-6 w-6" />
          {t("settings.title")}
        </h1>
        <p className="text-muted-foreground">{t("settings.description")}</p>
      </div>

      {error && (
        <p className="border-destructive/30 bg-destructive/5 text-destructive mb-6 rounded-lg border px-4 py-2.5 text-sm">
          {error}
        </p>
      )}
      {saved && (
        <p className="mb-6 rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-700">
          {t("settings.saved")}
        </p>
      )}

      <div className="flex flex-col gap-6">
        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <h2 className="text-sm font-semibold tracking-wide uppercase">
              {t("settings.basicSettings")}
            </h2>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-reg">{t("settings.regulatoryLabel")}</Label>
              <Input
                id="set-reg"
                value={regulatory}
                onChange={(e) => setRegulatory(e.target.value)}
                placeholder={t("settings.regulatoryPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-residency">{t("settings.dataResidency")}</Label>
              <Input
                id="set-residency"
                value={dataResidency}
                onChange={(e) => setDataResidency(e.target.value)}
                placeholder={t("settings.dataResidencyPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-dpo">{t("settings.dpoLabel")}</Label>
              <Input
                id="set-dpo"
                value={dpoInfo}
                onChange={(e) => setDpoInfo(e.target.value)}
                placeholder={t("settings.dpoPlaceholder")}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-4 p-6">
            <h2 className="text-sm font-semibold tracking-wide uppercase">
              {t("settings.profileSection")}
            </h2>
            <p className="text-muted-foreground text-xs">{t("settings.profileHint")}</p>
            <Textarea
              value={profileContent}
              onChange={(e) => setProfileContent(e.target.value)}
              rows={14}
              placeholder={t("settings.profilePlaceholder")}
              className="font-mono text-xs"
            />
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving}>
            {saving && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
            {t("settings.save")}
          </Button>
        </div>
      </div>
    </div>
  );
}
