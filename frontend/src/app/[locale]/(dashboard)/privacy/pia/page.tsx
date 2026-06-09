"use client";

import { useTranslations } from "next-intl";
import { ClipboardCheck } from "lucide-react";
import { SkillRunner } from "@/components/privacy";

export default function PrivacyPiaPage() {
  const t = useTranslations("privacy");
  return (
    <SkillRunner
      action="pia"
      icon={ClipboardCheck}
      title={t("pia.title")}
      description={t("pia.description")}
      subjectLabel={t("pia.subjectLabel")}
      subjectPlaceholder={t("pia.subjectPlaceholder")}
      promptLabel={t("pia.promptLabel")}
      promptPlaceholder={t("pia.promptPlaceholder")}
      runLabel={t("pia.runLabel")}
    />
  );
}
