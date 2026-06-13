"use client";

import { useTranslations } from "next-intl";
import { FileText } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationBriefSectionPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="brief_section"
      icon={FileText}
      title={t("briefSection.title")}
      description={t("briefSection.description")}
      promptLabel={t("briefSection.promptLabel")}
      promptPlaceholder={t("briefSection.promptPlaceholder")}
      runLabel={t("briefSection.runLabel")}
    />
  );
}
