"use client";

import { useTranslations } from "next-intl";
import { Users } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationOcStatusPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="oc_status"
      icon={Users}
      title={t("ocStatus.title")}
      description={t("ocStatus.description")}
      promptLabel={t("ocStatus.promptLabel")}
      promptPlaceholder={t("ocStatus.promptPlaceholder")}
      runLabel={t("ocStatus.runLabel")}
    />
  );
}
