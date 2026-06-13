"use client";

import { useTranslations } from "next-intl";
import { Clock } from "lucide-react";
import { SkillRunner } from "@/components/litigation";

export default function LitigationChronologyPage() {
  const t = useTranslations("litigation");
  return (
    <SkillRunner
      action="chronology"
      icon={Clock}
      title={t("chronology.title")}
      description={t("chronology.description")}
      promptLabel={t("chronology.promptLabel")}
      promptPlaceholder={t("chronology.promptPlaceholder")}
      runLabel={t("chronology.runLabel")}
    />
  );
}
