"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Button, Card, CardContent, Spinner } from "@/components/ui";
import { ROUTES } from "@/lib/constants";
import { litigationApi } from "@/lib/litigation";
import type { LitigationProfile } from "@/types/litigation";
import { Settings2 } from "lucide-react";

export default function LitigationSettingsPage() {
  const t = useTranslations("litigation");
  const router = useRouter();
  const [profile, setProfile] = useState<LitigationProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setProfile(await litigationApi.getProfile());
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading)
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="text-brand h-6 w-6" />
      </div>
    );
  if (!profile)
    return <p className="text-muted-foreground p-10 text-center text-sm">{t("settings.needSetup")}</p>;

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-bold">
        <Settings2 className="text-brand h-6 w-6" />
        {t("settings.title")}
      </h1>

      <Card className="mb-4">
        <CardContent className="space-y-4 p-6">
          <h2 className="font-semibold">{t("settings.practiceSection")}</h2>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              {t("settings.userRole")}：{profile.user_role}
            </div>
            <div>
              {t("settings.practiceRole")}：{profile.practice_role}
            </div>
            <div>
              {t("settings.partyRole")}：{profile.party_role}
            </div>
            <div>
              {t("settings.setupDepth")}：{profile.setup_depth}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 p-6">
          <h2 className="font-semibold">{t("settings.riskSection")}</h2>
          <p className="text-muted-foreground text-xs">{t("settings.riskNote")}</p>
          <Button variant="outline" size="sm" onClick={() => router.push(ROUTES.LITIGATION_SETUP)}>
            {t("settings.rerun")}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
