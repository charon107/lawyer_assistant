"use client";

import { useTranslations } from "next-intl";
import { Scale } from "lucide-react";
import { SkillRunner } from "@/components/privacy";

export default function PrivacyGapPage() {
  const t = useTranslations("privacy");
  return (
    <SkillRunner
      action="gap"
      icon={Scale}
      title={t("gap.title")}
      description={t("gap.description")}
      subjectLabel={t("gap.subjectLabel")}
      subjectPlaceholder={t("gap.subjectPlaceholder")}
      promptLabel={t("gap.promptLabel")}
      promptPlaceholder={t("gap.promptPlaceholder")}
      runLabel={t("gap.runLabel")}
    />
  );
}
