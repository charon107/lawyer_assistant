"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { ArrowLeft, Loader2, Settings2 } from "lucide-react";
import { Button, Card, CardContent, Input, Label, Spinner, Textarea } from "@/components/ui";
import { cn } from "@/lib/utils";
import { ipApi } from "@/lib/ip";
import { ROUTES } from "@/lib/constants";
import type { UserRole } from "@/types/ip";

const ROLES: { value: UserRole; key: string }[] = [
  { value: "attorney", key: "attorney" },
  { value: "patent_agent", key: "patentAgent" },
  { value: "non_attorney_with_lawyer", key: "nonAttorneyWithLawyer" },
  { value: "non_attorney_without", key: "nonAttorneyWithout" },
];

export default function IpSettingsPage() {
  const t = useTranslations("ip");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [userRole, setUserRole] = useState<UserRole>("attorney");
  const [ipScope, setIpScope] = useState("");
  const [jurisdictions, setJurisdictions] = useState("");
  const [stance, setStance] = useState("");
  const [profileContent, setProfileContent] = useState("");

  useEffect(() => {
    let cancelled = false;
    ipApi
      .getProfile()
      .then((p) => {
        if (cancelled) return;
        setUserRole(((p.user_role as UserRole) ?? "attorney"));
        const scope = p.ip_scope;
        setIpScope(Array.isArray(scope) ? scope.join("、") : "");
        const juris = p.registration_jurisdictions;
        setJurisdictions(Array.isArray(juris) ? juris.join("、") : "");
        const posture = p.enforcement_posture as Record<string, unknown> | null;
        setStance(((posture?.default_stance as string) ?? ""));
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

  const splitList = (s: string): string[] =>
    s
      .split(/[、,，]/)
      .map((x) => x.trim())
      .filter(Boolean);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const scope = splitList(ipScope);
      const juris = splitList(jurisdictions);
      await ipApi.updateProfile({
        user_role: userRole,
        ip_scope: scope.length > 0 ? scope : null,
        registration_jurisdictions: juris.length > 0 ? juris : null,
        enforcement_posture: stance.trim() ? { default_stance: stance.trim() } : null,
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
          href={ROUTES.IP}
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
              <Label>{t("settings.roleLabel")}</Label>
              <div className="grid gap-2 sm:grid-cols-2">
                {ROLES.map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => setUserRole(r.value)}
                    className={cn(
                      "rounded-lg border px-3.5 py-2.5 text-left text-sm transition-colors",
                      userRole === r.value
                        ? "border-brand bg-brand/5 ring-brand/20 ring-1"
                        : "border-border hover:border-brand/40",
                    )}
                  >
                    {t(`settings.roles.${r.key}`)}
                  </button>
                ))}
              </div>
              {userRole === "patent_agent" && (
                <p className="text-muted-foreground text-xs">{t("settings.patentAgentNote")}</p>
              )}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-scope">{t("settings.ipScopeLabel")}</Label>
              <Input
                id="set-scope"
                value={ipScope}
                onChange={(e) => setIpScope(e.target.value)}
                placeholder={t("settings.ipScopePlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-juris">{t("settings.jurisdictionsLabel")}</Label>
              <Input
                id="set-juris"
                value={jurisdictions}
                onChange={(e) => setJurisdictions(e.target.value)}
                placeholder={t("settings.jurisdictionsPlaceholder")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="set-stance">{t("settings.stanceLabel")}</Label>
              <Input
                id="set-stance"
                value={stance}
                onChange={(e) => setStance(e.target.value)}
                placeholder={t("settings.stancePlaceholder")}
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
