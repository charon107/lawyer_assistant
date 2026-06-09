"use client";

import { useTranslations } from "next-intl";
import { ListChecks } from "lucide-react";
import { SkillRunner } from "@/components/privacy";

export default function PrivacyTriagePage() {
  const t = useTranslations("privacy");
  return (
    <SkillRunner
      action="triage"
      icon={ListChecks}
      title={t("triage.title")}
      description={t("triage.description")}
      subjectLabel={t("triage.subjectLabel")}
      subjectPlaceholder={t("triage.subjectPlaceholder")}
      promptLabel={t("triage.promptLabel")}
      promptPlaceholder={t("triage.promptPlaceholder")}
      runLabel={t("triage.runLabel")}
    />
  );
}
